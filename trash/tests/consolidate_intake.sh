#!/usr/bin/env zsh
set -euo pipefail

ts=$(date +%Y%m%d%H%M)

# Determine safe branch name: prefer nested "consolidation/intake_${ts}" but fall back
# to "consolidation_intake_${ts}" if a top-level branch "consolidation" exists.
prefix="consolidation"
if git show-ref --verify --quiet "refs/heads/${prefix}"; then
  safe_branch="${prefix}_intake_${ts}"
else
  safe_branch="${prefix}/intake_${ts}"
fi

# If the chosen branch name already exists (rare), append a seconds-based suffix to ensure uniqueness.
if git show-ref --verify --quiet "refs/heads/${safe_branch}"; then
  suffix=$(date +%s)
  safe_branch="${safe_branch}_${suffix}"
fi

branch="$safe_branch"

# Create or checkout the branch robustly.
if git show-ref --verify --quiet "refs/heads/${branch}"; then
  echo "Branch already exists, checking out: ${branch}"
  git checkout "${branch}"
else
  echo "Creating branch: ${branch}"
  git checkout -b "${branch}"
fi

archive_dir="archive/intake_archive_${ts}"
canonical_ingest_dir="src/lawyerfactory/phases/01_intake/ingest_consolidated"

mkdir -p "$archive_dir"
echo "Archive dir: $archive_dir"

# 1) Archive tracked .bak and trash files (git mv when tracked)
echo "Archiving tracked .bak and trash files..."
# Move tracked .bak files
git ls-files -z '*.bak' 2>/dev/null | xargs -0 -I{} bash -c 'mkdir -p "'"${archive_dir}/$(dirname {})"'" && git mv "{}" "'"${archive_dir}/{}"'"' || true

# Move tracked files under trash/ or trash_*/ pattern
git ls-files -z | tr '\0' '\n' | grep -E '^trash/|/trash/|^.*\\.bak$' || true \
  | while read -r f; do
    [ -z "$f" ] && continue
    mkdir -p "$archive_dir/$(dirname "$f")"
    git mv "$f" "$archive_dir/$f" || mv "$f" "$archive_dir/$f"
  done

# 2) Archive untracked .bak and trash files (avoid venv)
echo "Archiving untracked .bak and trash files (excluding law_venv)..."
find . -type f \( -iname '*.bak' -o -path './trash/*' \) -not -path './.git/*' -not -path './law_venv/*' -print0 \
  | while IFS= read -r -d '' f; do
      dest="$archive_dir/$f"
      mkdir -p "$(dirname "$dest")"
      if git ls-files --error-unmatch "$f" >/dev/null 2>&1; then
        git mv "$f" "$dest" || true
      else
        mv "$f" "$dest"
      fi
  done

# 3) Ensure canonical ingest dir exists and move canonical files there
mkdir -p "$canonical_ingest_dir"
echo "Moving canonical files into $canonical_ingest_dir"

# list of canonical files to keep/move (adjust paths if necessary)
declare -a keep_files=(
  "src/lawyerfactory/phases/01_intake/assessor.py"
  "src/lawyerfactory/phases/01_intake/enhanced_intake_processor.py"
  "src/lawyerfactory/phases/01_intake/vector_cluster_manager.py"
  "src/lawyerfactory/agents/intake/reader.py"
  "src/lawyerfactory/phases/01_intake/evidence_ingestion.py"
)

for f in "${keep_files[@]}"; do
  if [ -f "$f" ]; then
    # git mv if tracked, else copy to canonical dir
    dest="$canonical_ingest_dir/$(basename "$f")"
    if git ls-files --error-unmatch "$f" >/dev/null 2>&1; then
      git mv "$f" "$dest" || true
    else
      cp "$f" "$dest"
    fi
  else
    echo "Warning: canonical file not found: $f"
  fi
done

# 4) Archive other intake/ingestion/server duplicates (patterns)
echo "Archiving other intake/ingestion/server duplicates..."
find . -type f \( -iname 'intake_processor*' -o -iname 'intake_server*' -o -iname 'ingestion/*' -o -iname '*ingest*' \) \
  -not -path './src/lawyerfactory/phases/01_intake/*' -not -path './.git/*' -not -path './law_venv/*' -print0 \
  | while IFS= read -r -d '' f; do
      dest="$archive_dir/$f"
      mkdir -p "$(dirname "$dest")"
      if git ls-files --error-unmatch "$f" >/dev/null 2>&1; then
        git mv "$f" "$dest" || true
      else
        mv "$f" "$dest"
      fi
  done

# 5) Replace imports: assessor -> assessor_consolidated
echo "Replacing imports: assessor -> assessor_consolidated (dry-replace first)"
# find files excluding venv and archive
files_to_patch=$(git ls-files -z | tr '\0' '\n' | grep -v -E '^law_venv/|^archive/|^.git' || true)

# Replace patterns
echo "Updating 'from assessor import' -> 'from assessor_consolidated import'"
for file in $files_to_patch; do
  if grep -q "from assessor import" "$file" 2>/dev/null; then
    sed -i '' 's/from assessor import/from assessor_consolidated import/g' "$file" || true
  fi
  if grep -q "import assessor" "$file" 2>/dev/null; then
    # keep compatibility: import assessor_consolidated as assessor
    sed -i '' 's/import assessor/import assessor_consolidated as assessor/g' "$file" || true
  fi
done

# 6) Minor cleanup: remove duplicate __all__ or duplicated simple_categorize in assessor.py
# (manual review recommended; we don't auto-edit complex logic here)
echo "Note: please manually inspect $canonical_ingest_dir/assessor.py for duplicate definitions (__all__, simple_categorize) and remove duplicates."

# 7) Run tests and capture failures
echo "Running test suite (pytest). Output -> consolidation_test_results.txt"
python -m pytest -q 2>&1 | tee consolidation_test_results.txt || true

echo "Git status (changes):"
git status --porcelain

echo "Files changed (git diff names):"
git diff --name-only

echo "Create archive zip of the archive dir for external backup..."
zipfile="archive_intake_${ts}.zip"
zip -r "$zipfile" "$archive_dir" >/dev/null || true
echo "Archive zip: $zipfile"

echo "DONE. Review changes, run the tests locally and fix failures listed in consolidation_test_results.txt"