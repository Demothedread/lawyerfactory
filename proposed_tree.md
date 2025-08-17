# Proposed Tree Structure (After Reorganization)

## New Domain-Oriented Layout

### /src (New organized structure)
```
src/
├── knowledge_graph/
│   └── api/
│       ├── __init__.py
│       ├── knowledge_graph.py (consolidated from root + lawyerfactory)
│       ├── enhanced_knowledge_graph.py (moved from root)
│       ├── knowledge_graph_extensions.py (moved from root)
│       └── knowledge_graph_integration.py (moved from root)
├── document_generator/
│   └── api/
│       ├── __init__.py
│       ├── ai_document_generator.py (from lawyerfactory/document_generator/)
│       ├── generator.py (from lawyerfactory/document_generator/)
│       ├── document_export_system.py (moved from root)
│       ├── enhanced_draft_processor.py (moved from root)
│       └── modules/ (entire subtree from lawyerfactory/document_generator/)
├── storage/
│   └── api/
│       ├── __init__.py
│       └── file_storage.py (renamed from file-storage.py, moved from lawyerfactory/)
├── workflow/
│   └── api/
│       ├── __init__.py
│       ├── enhanced_workflow.py (moved from lawyerfactory/)
│       └── workflow.py (moved from lawyerfactory/)
├── ingestion/
│   └── api/
│       ├── __init__.py
│       └── ingest_server.py (moved from maestro/bots/)
└── shared/
    ├── __init__.py
    ├── models.py (moved from lawyerfactory/)
    ├── agent_config_system.py (moved from lawyerfactory/)
    └── document_type_framework.py (moved from lawyerfactory/)
```

### Root Level (Cleaned up)
```
├── app.py (main entrypoint - preserved)
├── deploy_lawyerfactory.py (deployment script - preserved)
├── start_enhanced_factory.py (startup script - preserved)
├── tests/ (preserved as-is)
├── docs/ (preserved, consolidated)
├── static/ (preserved as-is)
├── templates/ (preserved as-is)
├── Tesla/ (case data - preserved as-is)
├── trash/ (staging area for unused files)
└── src/ (new organized structure)
```

## Migration Mapping

### Knowledge Graph Domain
- `knowledge_graph.py` → `src/knowledge_graph/api/knowledge_graph.py`
- `lawyerfactory/knowledge_graph.py` → **MERGED** into `src/knowledge_graph/api/knowledge_graph.py`
- `enhanced_knowledge_graph.py` → `src/knowledge_graph/api/enhanced_knowledge_graph.py`
- `knowledge_graph_extensions.py` → `src/knowledge_graph/api/knowledge_graph_extensions.py`
- `knowledge_graph_integration.py` → `src/knowledge_graph/api/knowledge_graph_integration.py`

### Document Generation Domain
- `lawyerfactory/document_generator/` → `src/document_generator/api/`
- `document_export_system.py` → `src/document_generator/api/document_export_system.py`
- `enhanced_draft_processor.py` → `src/document_generator/api/enhanced_draft_processor.py`

### Storage Domain
- `lawyerfactory/file-storage.py` → `src/storage/api/file_storage.py` (renamed)

### Workflow Domain
- `lawyerfactory/enhanced_workflow.py` → `src/workflow/api/enhanced_workflow.py`
- `lawyerfactory/workflow.py` → `src/workflow/api/workflow.py`

### Ingestion Domain
- `maestro/bots/ingest-server.py` → `src/ingestion/api/ingest_server.py`

### Shared Components
- `lawyerfactory/models.py` → `src/shared/models.py`
- `lawyerfactory/agent_config_system.py` → `src/shared/agent_config_system.py`
- `lawyerfactory/document_type_framework.py` → `src/shared/document_type_framework.py`

### Files to Stage in /trash
- `attorney_review_interface.py` (candidate for legal analysis domain or shared)
- `cascading_decision_tree_engine.py` (candidate for legal analysis domain)
- `cause_of_action_definition_engine.py` (candidate for legal analysis domain)
- `comprehensive_claims_matrix_integration.py` (candidate for legal analysis domain)
- `claims_matrix_research_api.py` (candidate for legal analysis domain)
- `lawyerfactory/prompt_deconstruction.py` (evaluate usage)
- `lawyerfactory/prompt_integration.py` (evaluate usage)
- `lawyerfactory/mcp_memory_integration.py` (evaluate for shared or separate domain)
- `lawyerfactory/kanban_cli.py` (evaluate for workflow or utilities)

## Compatibility Strategy

### Import Wrappers
Create compatibility wrappers in original locations:

```python
# lawyerfactory/enhanced_workflow.py (wrapper)
from src.workflow.api.enhanced_workflow import *

# lawyerfactory/knowledge_graph.py (wrapper)
from src.knowledge_graph.api.knowledge_graph import *

# knowledge_graph.py (root wrapper)
from src.knowledge_graph.api.knowledge_graph import *
```

### Updated Import Paths (Target State)
```python
# New import style (after migration complete)
from src.knowledge_graph.api import EnhancedKnowledgeGraph
from src.document_generator.api import AIDocumentGenerator
from src.workflow.api import EnhancedWorkflowManager
from src.storage.api import file_storage
from src.shared import models
```

## Benefits of New Structure

1. **Clear Domain Separation**: Each domain has its own namespace
2. **Reduced Root Clutter**: Only essential files remain at root
3. **Consistent API Pattern**: All domains follow /api pattern
4. **Shared Components**: Common utilities in /shared prevent duplication
5. **Import Clarity**: Clear import paths showing domain relationships
6. **Scalability**: Easy to add new domains or split existing ones
7. **Testing**: Domain-specific testing becomes easier

## Migration Phases

### Phase A: Scaffolding ✅ COMPLETE
- Created /src structure with domain folders
- Domain folders: knowledge_graph, document_generator, storage, workflow, ingestion, shared

### Phase B: File Migration (Next)
- Move files to new locations with compatibility wrappers
- Consolidate duplicate knowledge graph files
- Rename file-storage.py to file_storage.py

### Phase C: Import Refactoring
- Update all imports to use new paths
- Remove compatibility wrappers gradually
- Test at each step

### Phase D: Cleanup
- Move unused files to /trash
- Update documentation
- Generate final artifacts