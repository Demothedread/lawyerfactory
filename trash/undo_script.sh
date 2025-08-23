#!/bin/bash

# Undo script for lawyerfactory streamlining refactor
# This script restores all files moved to trash back to their original locations

echo "Restoring files from trash..."

# Restore deprecated shim files
echo "Restoring deprecated shim files..."
mv trash/deprecated_shims/agent_config_system.py lawyerfactory/
mv trash/deprecated_shims/document_type_framework.py lawyerfactory/
mv trash/deprecated_shims/enhanced_workflow.py lawyerfactory/
mv trash/deprecated_shims/file-storage.py lawyerfactory/
mv trash/deprecated_shims/knowledge_graph.py lawyerfactory/
mv trash/deprecated_shims/mcp_memory_integration.py lawyerfactory/
mv trash/deprecated_shims/models.py lawyerfactory/
mv trash/deprecated_shims/workflow.py lawyerfactory/

# Restore system files
echo "Restoring system files..."
if [ -f trash/system_files/.DS_Store ]; then
    mv trash/system_files/.DS_Store lawyerfactory/
fi
if [ -d trash/system_files/__pycache__ ]; then
    mv trash/system_files/__pycache__ lawyerfactory/
fi

# Clean up empty trash directories
echo "Cleaning up trash directories..."
rmdir trash/deprecated_shims 2>/dev/null || true
rmdir trash/system_files 2>/dev/null || true
rmdir trash 2>/dev/null || true

echo "All files have been restored to their original locations."
echo "The streamlining refactor has been undone."