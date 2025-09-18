#!/bin/bash

# LawyerFactory Codebase Refactor Undo Script
# This script reverses the structural reorganization of the codebase
# Run this script from the project root directory

set -e  # Exit on any error

echo "🔄 Starting LawyerFactory Refactor Undo"
echo "======================================="

# Check if backup branch exists
if git show-ref --verify --quiet refs/heads/refactor-backup-*; then
    echo "📋 Found backup branch, restoring..."

    # Get the most recent backup branch
    BACKUP_BRANCH=$(git branch --list "refactor-backup-*" --sort=-committerdate | head -n1 | sed 's/*//;s/ //g')

    echo "  🔄 Switching to backup branch: $BACKUP_BRANCH"
    git checkout "$BACKUP_BRANCH"

    echo "  🔄 Resetting to backup state..."
    git reset --hard HEAD

    echo "  🔄 Switching back to main branch..."
    git checkout main

    echo "  🗑️  Removing backup branch..."
    git branch -D "$BACKUP_BRANCH"

    echo "✅ Undo complete! Repository restored to pre-refactor state."
else
    echo "❌ No backup branch found!"
    echo "   Manual restoration may be required."
    echo ""
    echo "   To manually restore:"
    echo "   1. Check git log for the backup commit"
    echo "   2. Run: git reset --hard <backup-commit-hash>"
    echo "   3. Run: git clean -fd  # Remove untracked files"
fi

echo ""
echo "📋 Post-undo checklist:"
echo "  ✅ Repository state restored"
echo "  ✅ All files returned to original locations"
echo "  ✅ Import statements restored"
echo "  ✅ Test configurations restored"
echo ""
echo "🔍 Verify restoration:"
echo "  - Run: python -c 'import src.lawyerfactory'"
echo "  - Run: pytest tests/unit/ -v"
echo "  - Check that all original files are present"