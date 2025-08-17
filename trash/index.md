# Trash Index - Staged and Archived Files

This directory contains files that have been moved, staged for evaluation, or archived during the codebase reorganization.

## Directory Structure

### `/staged_for_evaluation/`
Files that need manual review to determine their final destination or if they should be kept.

#### Legal Analysis Domain Candidates
- `attorney_review_interface.py` - Attorney review workflow interface
- `cascading_decision_tree_engine.py` - Legal decision tree engine
- `cause_of_action_definition_engine.py` - Cause of action definitions
- `comprehensive_claims_matrix_integration.py` - Claims matrix integration
- `claims_matrix_research_api.py` - Claims matrix research API

**Recommendation**: These form a cohesive "Legal Analysis" domain and could be moved to `src/legal_analysis/api/` if actively used.

#### Utility/Integration Candidates  
- `prompt_deconstruction.py` - Prompt processing utilities (from lawyerfactory/)
- `prompt_integration.py` - Prompt integration utilities (from lawyerfactory/)
- `mcp_memory_integration.py` - MCP memory integration (from lawyerfactory/)
- `kanban_cli.py` - Kanban CLI tool (from lawyerfactory/)

**Recommendation**: 
- Prompt utilities → `src/shared/prompt_utils.py` if used across domains
- MCP integration → `src/shared/integrations/` or separate domain if substantial
- Kanban CLI → `src/workflow/cli/` or separate utilities domain

## Legacy Documentation (Previously moved)
The following documentation was previously moved to trash during an earlier cleanup:

- `LEGAL_RESEARCH_INTEGRATION_README.md`
- `KNOWLEDGE_GRAPH_INTEGRATION_README.md` 
- `KNOWLEDGE_GRAPH_SCHEMA.md`
- `SYSTEM_DOCUMENTATION.md`
- `CLAIMS_MATRIX_IMPLEMENTATION_README.md`

## Migration Status

### ✅ Completed Moves
Files successfully moved to new `/src` structure:

**Knowledge Graph Domain** → `src/knowledge_graph/api/`
- `knowledge_graph.py` (consolidated from root + lawyerfactory/)
- `enhanced_knowledge_graph.py`
- `knowledge_graph_extensions.py`
- `knowledge_graph_integration.py`

**Document Generator Domain** → `src/document_generator/api/`
- `lawyerfactory/document_generator/` (entire subtree)
- `document_export_system.py`
- `enhanced_draft_processor.py`

**Storage Domain** → `src/storage/api/`
- `file-storage.py` → `file_storage.py` (renamed)

**Workflow Domain** → `src/workflow/api/`
- `lawyerfactory/enhanced_workflow.py`
- `lawyerfactory/workflow.py`

**Ingestion Domain** → `src/ingestion/api/`
- `maestro/bots/ingest-server.py` → `ingest_server.py`
- `maestro/bots/ai_document_agent.py`
- `maestro/bots/writer_bot.py`
- `maestro/bots/legal_editor.py`

**Shared Components** → `src/shared/`
- `lawyerfactory/models.py`
- `lawyerfactory/agent_config_system.py`
- `lawyerfactory/document_type_framework.py`

### 🔄 Compatibility Wrappers Created
Backward compatibility maintained via wrapper files:
- `knowledge_graph.py` → imports from `src.knowledge_graph.api.knowledge_graph`
- `lawyerfactory/knowledge_graph.py` → imports from `src.knowledge_graph.api.knowledge_graph`
- `lawyerfactory/enhanced_workflow.py` → imports from `src.workflow.api.enhanced_workflow`
- `lawyerfactory/workflow.py` → imports from `src.workflow.api.workflow`
- `lawyerfactory/file-storage.py` → imports from `src.storage.api.file_storage`
- `lawyerfactory/models.py` → imports from `src.shared.models`
- Other lawyerfactory/ wrappers as needed

## Next Steps

### 1. Review Staged Files
Evaluate files in `/staged_for_evaluation/` and decide:
- Move to appropriate domain in `/src`
- Keep in current location if still needed
- Delete if truly unused

### 2. Import Path Updates
Update imports throughout codebase from old paths to new `/src` structure:
```python
# Old
from lawyerfactory.enhanced_workflow import EnhancedWorkflowManager

# New  
from src.workflow.api.enhanced_workflow import EnhancedWorkflowManager
```

### 3. Test Compatibility
Run test suite to ensure compatibility wrappers work correctly:
```bash
python -m pytest tests/
```

### 4. Gradual Wrapper Removal
Once imports are updated, remove compatibility wrappers to complete migration.

## Rollback Information

### Undo Script
Use `undo_reorganization.py` to revert all changes if needed.

### Manual Rollback
If automated rollback fails, manually:
1. Move files back from `/src` to original locations
2. Remove compatibility wrappers
3. Restore files from `/staged_for_evaluation/` to original locations

## Date Created
2025-08-17

## Last Updated  
2025-08-17 - Initial reorganization staging complete