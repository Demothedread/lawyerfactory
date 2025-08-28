# Script Name: move_script.py
# Description: !/usr/bin/env python3
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Core
#   - Group Tags: null
LawyerFactory Codebase Reorganization Script
Moves files to new domain-oriented /src structure with compatibility wrappers
"""

import shutil
from pathlib import Path


def create_directory(path):
    """Create directory if it doesn't exist"""
    Path(path).mkdir(parents=True, exist_ok=True)
    print(f"✓ Created directory: {path}")

def move_file(src, dst):
    """Move file from src to dst, creating directories as needed"""
    dst_path = Path(dst)
    create_directory(dst_path.parent)
    
    if Path(src).exists():
        shutil.move(src, dst)
        print(f"✓ Moved: {src} → {dst}")
        return True
    else:
        print(f"⚠ Source not found: {src}")
        return False

def create_wrapper(wrapper_path, target_import):
    """Create a compatibility wrapper that re-exports from new location"""
    create_directory(Path(wrapper_path).parent)
    
    wrapper_content = f'''"""
Compatibility wrapper - imports from new location
This file maintains backward compatibility during refactoring
"""
from {target_import} import *

'''
    
    with open(wrapper_path, 'w') as f:
        f.write(wrapper_content)
    print(f"✓ Created wrapper: {wrapper_path} → {target_import}")

def create_init_file(path):
    """Create __init__.py file"""
    init_path = Path(path) / "__init__.py"
    with open(init_path, 'w') as f:
        f.write('"""Package initialization file"""\n')
    print(f"✓ Created: {init_path}")

def consolidate_knowledge_graph_files():
    """Merge duplicate knowledge_graph.py files"""
    root_kg = "knowledge_graph.py"
    pkg_kg = "lawyerfactory/knowledge_graph.py"
    target = "src/knowledge_graph/api/knowledge_graph.py"
    
    # Read both files if they exist
    root_content = ""
    pkg_content = ""
    
    if Path(root_kg).exists():
        with open(root_kg, 'r') as f:
            root_content = f.read()
    
    if Path(pkg_kg).exists():
        with open(pkg_kg, 'r') as f:
            pkg_content = f.read()
    
    # Create consolidated content
    consolidated = f'''"""
Consolidated Knowledge Graph Module
Merged from root knowledge_graph.py and lawyerfactory/knowledge_graph.py
"""

# === Content from root knowledge_graph.py ===
{root_content}

# === Content from lawyerfactory/knowledge_graph.py ===
{pkg_content}
'''
    
    # Write to target location
    create_directory(Path(target).parent)
    with open(target, 'w') as f:
        f.write(consolidated)
    
    print(f"✓ Consolidated knowledge graph files → {target}")

def main():
    """Execute the reorganization"""
    print("🚀 Starting LawyerFactory codebase reorganization...")
    
    # Phase 1: Create all __init__.py files
    print("\n📁 Creating package structure...")
    init_dirs = [
        "src",
        "src/knowledge_graph",
        "src/knowledge_graph/api", 
        "src/document_generator",
        "src/document_generator/api",
        "src/storage",
        "src/storage/api",
        "src/workflow", 
        "src/workflow/api",
        "src/ingestion",
        "src/ingestion/api",
        "src/shared"
    ]
    
    for dir_path in init_dirs:
        create_init_file(dir_path)
    
    # Phase 2: Knowledge Graph Domain
    print("\n🧠 Migrating Knowledge Graph domain...")
    consolidate_knowledge_graph_files()
    
    # Move other knowledge graph files
    kg_moves = [
        ("enhanced_knowledge_graph.py", "src/knowledge_graph/api/enhanced_knowledge_graph.py"),
        ("knowledge_graph_extensions.py", "src/knowledge_graph/api/knowledge_graph_extensions.py"), 
        ("knowledge_graph_integration.py", "src/knowledge_graph/api/knowledge_graph_integration.py")
    ]
    
    for src, dst in kg_moves:
        move_file(src, dst)
    
    # Create wrappers for knowledge graph
    create_wrapper("knowledge_graph.py", "src.knowledge_graph.api.knowledge_graph")
    create_wrapper("lawyerfactory/knowledge_graph.py", "src.knowledge_graph.api.knowledge_graph")
    
    # Phase 3: Document Generator Domain  
    print("\n📄 Migrating Document Generator domain...")
    
    # Move the entire document_generator directory
    if Path("lawyerfactory/document_generator").exists():
        shutil.move("lawyerfactory/document_generator", "src/document_generator/api/document_generator_legacy")
        print("✓ Moved: lawyerfactory/document_generator → src/document_generator/api/document_generator_legacy")
    
    # Move root document files
    doc_moves = [
        ("document_export_system.py", "src/document_generator/api/document_export_system.py"),
        ("enhanced_draft_processor.py", "src/document_generator/api/enhanced_draft_processor.py")
    ]
    
    for src, dst in doc_moves:
        move_file(src, dst)
    
    # Phase 4: Storage Domain
    print("\n💾 Migrating Storage domain...")
    move_file("lawyerfactory/file-storage.py", "src/storage/api/file_storage.py")
    create_wrapper("lawyerfactory/file-storage.py", "src.storage.api.file_storage")
    
    # Phase 5: Workflow Domain
    print("\n⚡ Migrating Workflow domain...")
    workflow_moves = [
        ("lawyerfactory/enhanced_workflow.py", "src/workflow/api/enhanced_workflow.py"),
        ("lawyerfactory/workflow.py", "src/workflow/api/workflow.py")
    ]
    
    for src, dst in workflow_moves:
        move_file(src, dst)
    
    # Create workflow wrappers
    create_wrapper("lawyerfactory/enhanced_workflow.py", "src.workflow.api.enhanced_workflow")
    create_wrapper("lawyerfactory/workflow.py", "src.workflow.api.workflow")
    
    # Phase 6: Ingestion Domain
    print("\n📥 Migrating Ingestion domain...")
    ingestion_moves = [
        ("maestro/bots/ingest-server.py", "src/ingestion/api/ingest_server.py"),
        ("maestro/bots/ai_document_agent.py", "src/ingestion/api/ai_document_agent.py"),
        ("maestro/bots/writer_bot.py", "src/ingestion/api/writer_bot.py"),
        ("maestro/bots/legal_editor.py", "src/ingestion/api/legal_editor.py")
    ]
    
    for src, dst in ingestion_moves:
        move_file(src, dst)
    
    # Phase 7: Shared Components
    print("\n🔗 Migrating Shared components...")
    shared_moves = [
        ("lawyerfactory/models.py", "src/shared/models.py"),
        ("lawyerfactory/agent_config_system.py", "src/shared/agent_config_system.py"),
        ("lawyerfactory/document_type_framework.py", "src/shared/document_type_framework.py")
    ]
    
    for src, dst in shared_moves:
        move_file(src, dst)
    
    # Create shared wrappers
    create_wrapper("lawyerfactory/models.py", "src.shared.models")
    create_wrapper("lawyerfactory/agent_config_system.py", "src.shared.agent_config_system")
    create_wrapper("lawyerfactory/document_type_framework.py", "src.shared.document_type_framework")
    
    # Phase 8: Stage files for evaluation in trash
    print("\n🗑️ Staging files for evaluation...")
    
    # Create trash directory
    create_directory("trash/staged_for_evaluation")
    
    staging_candidates = [
        "attorney_review_interface.py",
        "cascading_decision_tree_engine.py", 
        "cause_of_action_definition_engine.py",
        "comprehensive_claims_matrix_integration.py",
        "claims_matrix_research_api.py",
        "lawyerfactory/prompt_deconstruction.py",
        "lawyerfactory/prompt_integration.py",
        "lawyerfactory/mcp_memory_integration.py",
        "lawyerfactory/kanban_cli.py"
    ]
    
    for candidate in staging_candidates:
        if Path(candidate).exists():
            filename = Path(candidate).name
            dst = f"trash/staged_for_evaluation/{filename}"
            shutil.copy2(candidate, dst)
            print(f"✓ Staged for evaluation: {candidate} → {dst}")
    
    print("\n✅ Reorganization complete!")
    print("\n📋 Next steps:")
    print("1. Run tests to verify compatibility wrappers work")
    print("2. Update import statements gradually") 
    print("3. Review files in trash/staged_for_evaluation")
    print("4. Remove compatibility wrappers once imports are updated")

if __name__ == "__main__":
    main()