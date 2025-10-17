# Proposed Codebase Structure

## Target Architecture

Following the instruction set guidelines, the proposed structure organizes code around shared entities with clear separation of concerns:

```
lawyerfactory/
├── README.md (📖 Single authoritative documentation)
├── SYSTEM_DOCUMENTATION.md (🔧 Technical system docs)
├── data/
│   └── knowledge_graph.json (📊 Core reference framework)
├── src/
│   ├── shared/ (🔄 Common utilities and base classes)
│   │   ├── __init__.py
│   │   ├── utils/
│   │   ├── models/
│   │   ├── exceptions/
│   │   └── constants/
│   ├── platform/ (🏗️ Technical infrastructure)
│   │   ├── storage/
│   │   │   ├── unified_storage_api.py
│   │   │   ├── enhanced_unified_storage_api.py
│   │   │   └── file_handlers/
│   │   ├── messaging/
│   │   │   ├── events.py
│   │   │   └── communication.py
│   │   ├── monitoring/
│   │   │   ├── logging/
│   │   │   ├── metrics/
│   │   │   └── health_checks/
│   │   └── config/
│   │       ├── settings.py
│   │       └── environment.py
│   ├── agents/ (🤖 AI agent implementations)
│   │   ├── __init__.py
│   │   ├── base/
│   │   │   ├── agent_interface.py
│   │   │   ├── workflow_models.py
│   │   │   └── communication.py
│   │   ├── orchestration/
│   │   │   ├── maestro.py
│   │   │   └── workflow_engine.py
│   │   ├── intake/
│   │   │   ├── reader.py
│   │   │   ├── assessor.py
│   │   │   └── intake_processor.py
│   │   ├── research/
│   │   │   ├── legal_researcher.py
│   │   │   ├── court_authority_helper.py
│   │   │   └── retrievers/
│   │   ├── drafting/
│   │   │   ├── writer.py
│   │   │   ├── templates/
│   │   │   └── validators/
│   │   ├── review/
│   │   │   ├── editor.py
│   │   │   └── quality_checker.py
│   │   └── formatting/
│   │       ├── legal_formatter.py
│   │       ├── citations.py
│   │       └── paralegal.py
│   ├── knowledge/ (🧠 Knowledge representation)
│   │   ├── __init__.py
│   │   ├── graph/
│   │   │   ├── enhanced_graph.py
│   │   │   ├── graph_api.py
│   │   │   ├── relations.py
│   │   │   └── visualization.py
│   │   ├── entities/
│   │   │   ├── extraction.py
│   │   │   └── classification.py
│   │   └── integration/
│   │       ├── llm_integration.py
│   │       └── external_apis.py
│   ├── vectors/ (🔍 Vector processing)
│   │   ├── __init__.py
│   │   ├── stores/
│   │   │   ├── enhanced_vector_store.py
│   │   │   ├── evidence_ingestion.py
│   │   │   └── cloud_integration.py
│   │   ├── processing/
│   │   │   ├── embedding.py
│   │   │   ├── clustering.py
│   │   │   └── similarity.py
│   │   └── rag/
│   │       ├── llm_rag_integration.py
│   │       ├── context_retrieval.py
│   │       └── prompt_engineering.py
│   ├── phases/ (📋 Workflow phases - consolidated)
│   │   ├── __init__.py
│   │   ├── intake/
│   │   │   ├── enhanced_document_categorizer.py
│   │   │   ├── legal_intake_form.py
│   │   │   └── vector_cluster_manager.py
│   │   ├── research/
│   │   │   ├── enhanced_research_bot.py
│   │   │   └── research_integration.py
│   │   ├── outline/
│   │   │   ├── outline_generator.py
│   │   │   ├── claims_matrix.py
│   │   │   └── shotlist_generator.py
│   │   ├── drafting/
│   │   │   ├── drafting_validator.py
│   │   │   ├── prompt_deconstruction.py
│   │   │   └── prompt_integration.py
│   │   ├── review/
│   │   │   └── attorney_review_interface.py
│   │   ├── editing/
│   │   │   ├── citations.py
│   │   │   ├── pdf_generator.py
│   │   │   └── document_templates.py
│   │   └── orchestration/
│   │       ├── maestro.py
│   │       ├── workflow_engine.py
│   │       └── state_manager.py
│   └── ui/ (🎨 User interfaces)
│       ├── __init__.py
│       ├── templates/
│       │   ├── consolidated_factory.html
│       │   ├── multiswarm_dashboard.html
│       │   └── components/
│       ├── static/
│       │   ├── css/
│       │   ├── js/
│       │   └── images/
│       └── api/
│           ├── endpoints.py
│           └── websocket.py
├── apps/ (🚀 Application interfaces)
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── server.py
│   │   ├── routes/
│   │   │   ├── evidence.py
│   │   │   └── workflow.py
│   │   └── middleware/
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── templates/
│   │   └── static/
│   └── cli/
│       ├── __init__.py
│       └── commands/
├── tests/ (🧪 Test suites)
│   ├── __init__.py
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   └── fixtures/
├── docs/ (📚 Documentation)
│   ├── api/
│   ├── guides/
│   ├── architecture/
│   └── development/
├── scripts/ (⚙️ Utility scripts)
│   ├── setup.sh
│   ├── deploy.sh
│   ├── backup.sh
│   └── maintenance/
├── config/ (⚙️ Configuration)
│   ├── default.yaml
│   ├── development.yaml
│   ├── production.yaml
│   └── environment.py
└── trash/ (🗑️ Archived files)
    ├── INDEX.md
    └── [archived files]
```

## Key Improvements

### 1. **Clear Separation of Concerns**
- **shared/**: Common utilities used across the system
- **platform/**: Technical infrastructure (storage, messaging, monitoring)
- **agents/**: AI agent implementations organized by function
- **knowledge/**: Knowledge representation and processing
- **vectors/**: Vector database and RAG functionality
- **phases/**: Workflow phases (flattened from deep nesting)
- **ui/**: User interface components

### 2. **Reduced Directory Depth**
- Flattened phase directories (removed phaseA01_, phaseA02_ prefixes)
- Consolidated duplicate directories
- Logical grouping by functionality

### 3. **Improved Discoverability**
- Clear naming conventions
- Consistent structure across modules
- Logical file placement

### 4. **Better Maintainability**
- Separation of technical infrastructure from business logic
- Clear boundaries between components
- Easier testing and development

## Migration Strategy

### Phase 1: Infrastructure Consolidation
- Merge `infrastructure/` and `infra/` → `platform/`
- Merge `knowledge_graph/` and `kg/` → `knowledge/`
- Move storage components to `platform/storage/`

### Phase 2: Agent Reorganization
- Move all agent implementations to `agents/` by function
- Consolidate duplicate agent files
- Update import statements

### Phase 3: Phase Flattening
- Remove phase prefixes (phaseA01_, phaseA02_, etc.)
- Reorganize into logical phase directories
- Update all import references

### Phase 4: UI Consolidation
- Move UI components to dedicated `ui/` directory
- Separate templates, static files, and API endpoints
- Consolidate duplicate templates

### Phase 5: Testing & Validation
- Update all test files to reflect new structure
- Run comprehensive test suite
- Validate all import statements