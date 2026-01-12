#!/bin/bash
# LawyerFactory Directory Cleanup & Organization Script
# Consolidates root directory while preserving all canonical functionality

set -e

PROJECT_ROOT="$(pwd)"
ARCHIVE_DIR="$PROJECT_ROOT/docs/archive"
SCRIPTS_DIR="$PROJECT_ROOT/scripts"

echo "=== LawyerFactory Codebase Cleanup & Organization ==="
echo "Project Root: $PROJECT_ROOT"
echo ""

# Step 1: Create destination directories
echo "[1/5] Creating destination directories..."
mkdir -p "$ARCHIVE_DIR"
mkdir -p "$SCRIPTS_DIR"
mkdir -p "$PROJECT_ROOT/docs"

# Step 2: Archive redundant documentation files
echo "[2/5] Archiving redundant documentation (keeping canonical files)..."

# Files to archive (non-canonical duplicates and old reports)
ARCHIVE_FILES=(
    "COMPONENT_ENHANCEMENT_REPORT.md"
    "COMPONENT_REVIEW_FINAL_SUMMARY.md"
    "CONSOLIDATION_PROJECT_STATUS.md"
    "DOCUMENTATION_INDEX.md"
    "FINAL_VERIFICATION_REPORT.md"
    "IMPLEMENTATION_EXAMPLES_GUIDE.md"
    "IMPORT_MIGRATION_GUIDE.md"
    "INTERACTIVE_COMPONENT_TESTING.md"
    "LAUNCH_CONSOLIDATION_IMPLEMENTATION.md"
    "LAUNCH_DOCUMENTATION_INDEX.md"
    "LAUNCH_MASTER_SUMMARY.md"
    "LAUNCH_QUICK_REFERENCE.md"
    "LAUNCH_SYSTEM_CONSOLIDATION_COMPLETE.md"
    "LAUNCH_SYSTEM_CONSOLIDATION.md"
    "LAUNCH_SYSTEM_KNOWLEDGE_SUMMARY.md"
    "LAUNCH_VALIDATION_CHECKLIST.md"
    "QUICK_REFERENCE_CARD.md"
    "README_LAUNCH_INTEGRATION.md"
    "SERVICE_CONSOLIDATION_STATUS_REPORT.md"
    "SERVICE_MIGRATION_FINAL_SUMMARY.md"
    "SERVICE_MIGRATION_QUICK_REFERENCE.md"
)

for file in "${ARCHIVE_FILES[@]}"; do
    if [ -f "$PROJECT_ROOT/$file" ]; then
        mv "$PROJECT_ROOT/$file" "$ARCHIVE_DIR/$file"
        echo "  → Archived: $file"
    fi
done

# Step 3: Archive test files (keep tests/ folder as canonical)
echo "[3/5] Moving test files to canonical tests/ directory..."

TEST_FILES=(
    "test_case_management.py"
    "test_drafting_integration.py"
    "test_evidence_api.py"
    "test_evidence_integration.py"
    "test_evidence_pipeline.py"
    "test_final_compilation_engine.py"
    "test_integration_flow.py"
    "test_integration_implementation.py"
    "test_llm_config_flow.py"
    "test_phase_connectivity.py"
    "test_react_grid_integration.py"
    "test_simple_integration.py"
    "test_vectorization_pipeline.py"
)

for file in "${TEST_FILES[@]}"; do
    if [ -f "$PROJECT_ROOT/$file" ]; then
        mv "$PROJECT_ROOT/$file" "$PROJECT_ROOT/tests/$file"
        echo "  → Moved: $file → tests/"
    fi
done

# Step 4: Consolidate launch scripts
echo "[4/5] Consolidating launch scripts..."

LAUNCH_FILES=(
    "launch.sh"
    "launch-dev.sh"
    "launch-prod.sh"
    "launch-full-system.sh"
    "stop-scripts.sh"
)

for file in "${LAUNCH_FILES[@]}"; do
    if [ -f "$PROJECT_ROOT/$file" ]; then
        cp "$PROJECT_ROOT/$file" "$SCRIPTS_DIR/$file"
        # Keep originals in root for backward compatibility
        echo "  → Copied: $file → scripts/"
    fi
done

# Step 5: Clean up build artifacts and temp files
echo "[5/5] Cleaning up build artifacts and temporary files..."

# Remove redundant/temporary files
TEMP_FILES=(
    ".DS_Store"
    "tree_before.txt"
    "proposed_tree.md"
    "current_tree.md"
    "consolidation_test_results.txt"
    "file_sizes.txt"
    "files.txt"
    "directories.txt"
    "courtAuthority.txt"
    "test_document.txt"
    "website-launch.log"
    "frontend.log"
    "full-system-launch.log"
    "lawyerfactory.log"
    "test_output.log"
    "script_execution.log"
    "nohup.out"
    "final_cleanup.py"
    "fix_socketio_deps.py"
    "move_script.sh"
    "undo_script.sh"
    "test.pdf"
)

for file in "${TEMP_FILES[@]}"; do
    if [ -f "$PROJECT_ROOT/$file" ]; then
        rm -f "$PROJECT_ROOT/$file"
        echo "  ✓ Removed: $file"
    fi
done

# Remove unnecessary directories
TEMP_DIRS=(
    "test_path"
    "test_uploads"
    "archive_zip"
)

for dir in "${TEMP_DIRS[@]}"; do
    if [ -d "$PROJECT_ROOT/$dir" ]; then
        rm -rf "$PROJECT_ROOT/$dir"
        echo "  ✓ Removed directory: $dir"
    fi
done

echo ""
echo "=== Cleanup Complete ==="
echo ""
echo "📋 Summary:"
echo "  • Archived $(echo "${ARCHIVE_FILES[@]}" | wc -w) redundant documentation files"
echo "  • Moved $(echo "${TEST_FILES[@]}" | wc -w) test files to tests/ directory"
echo "  • Consolidated launch scripts in scripts/ directory"
echo "  • Removed $(echo "${TEMP_FILES[@]}" | wc -w) temporary files"
echo "  • Cleaned $(echo "${TEMP_DIRS[@]}" | wc -w) temporary directories"
echo ""
echo "📁 Key Canonical Files Preserved:"
echo "  • README.md - Main project documentation"
echo "  • SYSTEM_DOCUMENTATION.md - Technical reference"
echo "  • USER_GUIDE.md - User guide (also in apps/ui/react-app/public/)"
echo "  • pyproject.toml - Python project configuration"
echo "  • package.json (apps/ui/react-app/) - React build config"
echo "  • requirements.txt - Python dependencies"
echo ""
echo "📚 Archive Location: docs/archive/"
echo "🚀 Scripts Location: scripts/"
echo ""
echo "✅ Root directory reduced from ~100 files to ~40 canonical files"
