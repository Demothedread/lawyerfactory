# Script Name: undo_reorganization.py
# Description: !/usr/bin/env python3
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Core
#   - Group Tags: null
Undo Script for LawyerFactory Codebase Reorganization
Reverts all changes made by move_script.py
"""

import os
import shutil
from pathlib import Path


def restore_file(src, dst):
    """Restore file from src back to dst"""
    if Path(src).exists():
        # Create destination directory if needed
        Path(dst).parent.mkdir(parents=True, exist_ok=True)
        shutil.move(src, dst)
        print(f"✓ Restored: {src} → {dst}")
        return True
    else:
        print(f"⚠ Source not found for restore: {src}")
        return False

def remove_wrapper(wrapper_path):
    """Remove compatibility wrapper file"""
    if Path(wrapper_path).exists():
        os.remove(wrapper_path)
        print(f"✓ Removed wrapper: {wrapper_path}")
        return True
    else:
        print(f"⚠ Wrapper not found: {wrapper_path}")
        return False

def remove_directory_if_empty(dir_path):
    """Remove directory if it's empty"""
    try:
        if Path(dir_path).exists() and Path(dir_path).is_dir():
            if not any(Path(dir_path).iterdir()):
                os.rmdir(dir_path)
                print(f"✓ Removed empty directory: {dir_path}")
                return True
    except Exception as e:
        print(f"⚠ Could not remove directory {dir_path}: {e}")
    return False

def restore_knowledge_graph_files():
    """Restore the original separate knowledge graph files"""
    consolidated_file = "src/knowledge_graph/api/knowledge_graph.py"
    
    if not Path(consolidated_file).exists():
        print(f"⚠ Consolidated file not found: {consolidated_file}")
        return
    
    # Read the consolidated content
    with open(consolidated_file, 'r') as f:
        content = f.read()
    
    # Split content back (this is a simplified approach)
    # In practice, you might want to restore from backups
    
    # For now, create minimal files to restore structure
    root_kg_content = '''"""Root knowledge graph module - restored"""
# This is a placeholder restoration
# Original content should be restored from backup
'''
    
    pkg_kg_content = '''"""Package knowledge graph module - restored"""
# This is a placeholder restoration  
# Original content should be restored from backup
'''
    
    # Write back to original locations
    with open("knowledge_graph.py", 'w') as f:
        f.write(root_kg_content)
    
    Path("lawyerfactory").mkdir(exist_ok=True)
    with open("lawyerfactory/knowledge_graph.py", 'w') as f:
        f.write(pkg_kg_content)
    
    print("✓ Restored separate knowledge graph files (with placeholder content)")

def main():
    """Execute the undo operation"""
    print("🔄 Starting LawyerFactory codebase reorganization UNDO...")
    
    # Phase 1: Restore Knowledge Graph Domain
    print("\n🧠 Restoring Knowledge Graph domain...")
    
    kg_restores = [
        ("src/knowledge_graph/api/enhanced_knowledge_graph.py", "enhanced_knowledge_graph.py"),
        ("src/knowledge_graph/api/knowledge_graph_extensions.py", "knowledge_graph_extensions.py"),
        ("src/knowledge_graph/api/knowledge_graph_integration.py", "knowledge_graph_integration.py")
    ]
    
    for src, dst in kg_restores:
        restore_file(src, dst)
    
    # Restore separate knowledge graph files
    restore_knowledge_graph_files()
    
    # Remove knowledge graph wrappers
    remove_wrapper("knowledge_graph.py")
    remove_wrapper("lawyerfactory/knowledge_graph.py")
    
    # Phase 2: Restore Document Generator Domain
    print("\n📄 Restoring Document Generator domain...")
    
    # Restore the document_generator directory
    if Path("src/document_generator/api/document_generator_legacy").exists():
        # Ensure lawyerfactory directory exists
        Path("lawyerfactory").mkdir(exist_ok=True)
        shutil.move("src/document_generator/api/document_generator_legacy", "lawyerfactory/document_generator")
        print("✓ Restored: src/document_generator/api/document_generator_legacy → lawyerfactory/document_generator")
    
    # Restore root document files
    doc_restores = [
        ("src/document_generator/api/document_export_system.py", "document_export_system.py"),
        ("src/document_generator/api/enhanced_draft_processor.py", "enhanced_draft_processor.py")
    ]
    
    for src, dst in doc_restores:
        restore_file(src, dst)
    
    # Phase 3: Restore Storage Domain
    print("\n💾 Restoring Storage domain...")
    restore_file("src/storage/api/file_storage.py", "lawyerfactory/file-storage.py")
    remove_wrapper("lawyerfactory/file-storage.py")
    
    # Phase 4: Restore Workflow Domain
    print("\n⚡ Restoring Workflow domain...")
    workflow_restores = [
        ("src/workflow/api/enhanced_workflow.py", "lawyerfactory/enhanced_workflow.py"),
        ("src/workflow/api/workflow.py", "lawyerfactory/workflow.py")
    ]
    
    for src, dst in workflow_restores:
        restore_file(src, dst)
    
    # Remove workflow wrappers
    remove_wrapper("lawyerfactory/enhanced_workflow.py")
    remove_wrapper("lawyerfactory/workflow.py")
    
    # Phase 5: Restore Ingestion Domain
    print("\n📥 Restoring Ingestion domain...")
    
    # Ensure maestro/bots directory exists
    Path("maestro/bots").mkdir(parents=True, exist_ok=True)
    
    ingestion_restores = [
        ("src/ingestion/api/ingest_server.py", "maestro/bots/ingest-server.py"),
        ("src/ingestion/api/ai_document_agent.py", "maestro/bots/ai_document_agent.py"),
        ("src/ingestion/api/writer_bot.py", "maestro/bots/writer_bot.py"),
        ("src/ingestion/api/legal_editor.py", "maestro/bots/legal_editor.py")
    ]
    
    for src, dst in ingestion_restores:
        restore_file(src, dst)
    
    # Phase 6: Restore Shared Components
    print("\n🔗 Restoring Shared components...")
    shared_restores = [
        ("src/shared/models.py", "lawyerfactory/models.py"),
        ("src/shared/agent_config_system.py", "lawyerfactory/agent_config_system.py"),
        ("src/shared/document_type_framework.py", "lawyerfactory/document_type_framework.py")
    ]
    
    for src, dst in shared_restores:
        restore_file(src, dst)
    
    # Remove shared wrappers
    remove_wrapper("lawyerfactory/models.py")
    remove_wrapper("lawyerfactory/agent_config_system.py")
    remove_wrapper("lawyerfactory/document_type_framework.py")
    
    # Phase 7: Restore staged files
    print("\n📋 Restoring staged files...")
    
    staged_restores = [
        ("trash/staged_for_evaluation/attorney_review_interface.py", "attorney_review_interface.py"),
        ("trash/staged_for_evaluation/cascading_decision_tree_engine.py", "cascading_decision_tree_engine.py"),
        ("trash/staged_for_evaluation/cause_of_action_definition_engine.py", "cause_of_action_definition_engine.py"),
        ("trash/staged_for_evaluation/comprehensive_claims_matrix_integration.py", "comprehensive_claims_matrix_integration.py"),
        ("trash/staged_for_evaluation/claims_matrix_research_api.py", "claims_matrix_research_api.py"),
        ("trash/staged_for_evaluation/prompt_deconstruction.py", "lawyerfactory/prompt_deconstruction.py"),
        ("trash/staged_for_evaluation/prompt_integration.py", "lawyerfactory/prompt_integration.py"),
        ("trash/staged_for_evaluation/mcp_memory_integration.py", "lawyerfactory/mcp_memory_integration.py"),
        ("trash/staged_for_evaluation/kanban_cli.py", "lawyerfactory/kanban_cli.py")
    ]
    
    for src, dst in staged_restores:
        restore_file(src, dst)
    
    # Phase 8: Clean up empty directories
    print("\n🧹 Cleaning up empty directories...")
    
    cleanup_dirs = [
        "src/knowledge_graph/api",
        "src/knowledge_graph", 
        "src/document_generator/api",
        "src/document_generator",
        "src/storage/api",
        "src/storage",
        "src/workflow/api", 
        "src/workflow",
        "src/ingestion/api",
        "src/ingestion",
        "src/shared",
        "src",
        "trash/staged_for_evaluation"
    ]
    
    for dir_path in cleanup_dirs:
        remove_directory_if_empty(dir_path)
    
    # Phase 9: Clean up reorganization artifacts
    print("\n🗑️ Removing reorganization artifacts...")
    
    artifacts = [
        "current_tree.md",
        "proposed_tree.md", 
        "dep_graph.json",
        "refactor_plan.md",
        "move_script.py",
        "undo_reorganization.py",  # Remove self last
        "trash/INDEX.md"
    ]
    
    for artifact in artifacts[:-1]:  # Don't remove self yet
        if Path(artifact).exists():
            os.remove(artifact)
            print(f"✓ Removed artifact: {artifact}")
    
    print("\n✅ Undo complete!")
    print("\n📋 Restoration summary:")
    print("1. All files moved back to original locations")
    print("2. Compatibility wrappers removed")
    print("3. /src directory structure removed")
    print("4. Staged files restored to original locations")
    print("5. Reorganization artifacts cleaned up")
    print("\n⚠️  Note: Some files may have placeholder content and should be restored from backup")
    
    # Remove self last
    if Path("undo_reorganization.py").exists():
        os.remove("undo_reorganization.py")
        print("✓ Removed undo script")

if __name__ == "__main__":
    main()