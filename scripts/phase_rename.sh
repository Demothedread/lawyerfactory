#!/usr/bin/env zsh
set -euo pipefail

ts=$(date +%Y%m%d%H%M)
branch="quattro/update-phase-imports_${ts}"
echo "Creating branch: $branch"
git checkout -b "$branch"

# Mappings: OLD -> NEW
mappings=(
  "01_intake:phaseA01_intake"
  "02_research:phaseA02_research"
  "03_outline:phaseA03_outline"
  "04_human_review:phaseB01_review"
  "05_drafting:phaseB02_drafting"
  "06_editing:phaseC01_editing"
  "07_orchestration:phaseC02_orchestration"
)

# Files to consider (tracked files only, exclude venv/archive)
files=$(git ls-files | grep -v -E '^(law_venv/|archive/|\.git/)' || true)

echo "Processing ${#mappings[@]} mappings over tracked files..."

for entry in "${mappings[@]}"; do
  old=${entry%%:*}
  new=${entry##*:}
  echo "Mapping: $old -> $new"

  # Find files that contain the old token (fast skip if none)
  targets=$(printf "%s\n" $files | xargs grep -Il --line-buffered --null-data "$old" 2>/dev/null || true)
  if [ -z "$targets" ]; then
    echo "  no tracked files reference '$old' (skipping)"
    continue
  fi

  # Replace patterns in-place (macOS-compatible sed -i '')
  for f in ${(z)targets}; do
    # Replace dotted module imports: phases.01_intake -> phases.phaseA01_intake
    if grep -q "phases\\.${old}" "$f"; then
      sed -i '' "s/phases\\.${old}/phases.${new}/g" "$f" || true
    fi
    # Replace path-like imports: phases/01_intake -> phases/phaseA01_intake
    if grep -q "phases/${old}" "$f"; then
      sed -i '' "s#phases/${old}#phases/${new}#g" "$f" || true
    fi
    # Replace src path occurrences: src/lawyerfactory/phases/01_intake
    if grep -q "src/lawyerfactory/phases/${old}" "$f"; then
      sed -i '' "s#src/lawyerfactory/phases/${old}#src/lawyerfactory/phases/${new}#g" "$f" || true
    fi
    # Replace bare token occurrences (use word boundaries to reduce accidental replaces)
    if grep -q -E "\\b${old}\\b" "$f"; then
      sed -i '' -E "s/\\b${old}\\b/${new}/g" "$f" || true
    fi
  done

  # Stage & commit changes for this mapping
  git add -A
  # Only commit if there are staged changes
  if ! git diff --cached --quiet; then
    git commit -m "Rename phase path: ${old} -> ${new}"
    echo "  committed mapping ${old} -> ${new}"
  else
    echo "  no changes to commit for ${old}"
  fi
done

echo "All mappings processed. Showing git status and diff summary."
git status --porcelain
git --no-pager log --oneline -n 10

echo "Recommendation: run tests now (export PYTHONPATH=$(pwd)/src if needed) and review changes. To abort: git reset --hard origin/$(git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null || echo main) && git checkout - && git branch -D $branch"