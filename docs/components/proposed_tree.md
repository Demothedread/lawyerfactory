# Proposed Directory Structure - LawyerFactory

## Overview
This document proposes a reorganized directory structure following the workflow's organization heuristics. The system is a sequenced pipeline (legal workflow), so the primary organization is by execution order (phases), with secondary organization by module type within each phase.

## Current Issues Identified
1. **Multiple locations for similar functionality**:
   - Maestro implementations in 3 different locations
   - File storage implementations scattered across multiple files
   - Knowledge graph components in both `src/knowledge_graph/` and `src/lawyerfactory/kg/`

2. **Mixed organizational patterns**:
   - Some code organized by phase (`src/lawyerfactory/phases/`)
   - Some code organized by function (`src/lawyerfactory/compose/`)
   - Some code in root-level directories (`maestro/`, `lawyerfactory/`)

3. **Deep nesting**:
   - Some paths exceed 4-5 levels deep
   - Complex relative imports

## Proposed Structure

```
/src/lawyerfactory/                    # Main application package
├── __init__.py
├── config/                             # Configuration management
│   ├── __init__.py
│   ├── settings.py
│   └── deployment.py
├── shared/                             # Shared utilities and base classes
│   ├── __init__.py
│   ├── base_classes.py
│   ├── utilities.py
│   ├── constants.py
│   └── exceptions.py
├── phases/                             # Primary organization by workflow phases
│   ├── __init__.py
│   ├── 01_intake/
│   │   ├── __init__.py
│   │   ├── api/                        # API endpoints for intake
│   │   │   ├── __init__.py
│   │   │   ├── routes.py
│   │   │   └── models.py
│   │   ├── services/                   # Business logic for intake
│   │   │   ├── __init__.py
│   │   │   ├── document_processor.py
│   │   │   ├── intake_validator.py
│   │   │   └── evidence_extractor.py
│   │   ├── repositories/               # Data access for intake
│   │   │   ├── __init__.py
│   │   │   ├── intake_repository.py
│   │   │   └── evidence_repository.py
│   │   └── ui/                         # UI components for intake
│   │       ├── __init__.py
│   │       ├── forms.py
│   │       └── intake_dashboard.py
│   ├── 02_research/
│   │   ├── __init__.py
│   │   ├── api/
│   │   ├── services/                   # Research agents and retrievers
│   │   │   ├── research_bot.py
│   │   │   ├── caselaw_researcher.py
│   │   │   ├── citation_formatter.py
│   │   │   └── cache.py
│   │   ├── repositories/
│   │   └── ui/
│   ├── 03_outline/
│   │   ├── __init__.py
│   │   ├── api/
│   │   ├── services/                   # Claims analysis and outline generation
│   │   │   ├── claims_matrix.py
│   │   │   ├── cause_of_action_engine.py
│   │   │   ├── outline_generator.py
│   │   │   └── shotlist_generator.py
│   │   ├── repositories/
│   │   └── ui/
│   ├── 04_human_review/
│   │   ├── __init__.py
│   │   ├── api/
│   │   ├── services/
│   │   ├── repositories/
│   │   └── ui/                         # Human review interfaces
│   │       ├── attorney_review_interface.py
│   │       └── review_dashboard.py
│   ├── 05_drafting/
│   │   ├── __init__.py
│   │   ├── api/
│   │   ├── services/                   # Writing and editing agents
│   │   │   ├── writer_bot.py
│   │   │   ├── editor_bot.py
│   │   │   ├── procedure_bot.py
│   │   │   └── prompt_integrator.py
│   │   ├── repositories/
│   │   └── ui/
│   ├── 06_post_production/
│   │   ├── __init__.py
│   │   ├── api/
│   │   ├── services/                   # Formatting and validation
│   │   │   ├── document_formatter.py
│   │   │   ├── legal_validator.py
│   │   │   ├── pdf_generator.py
│   │   │   └── citations.py
│   │   ├── repositories/
│   │   └── ui/
│   └── 07_orchestration/
│       ├── __init__.py
│       ├── api/
│       ├── services/                   # Workflow orchestration
│       │   ├── maestro.py              # Main orchestrator
│       │   ├── workflow_engine.py
│       │   ├── state_manager.py
│       │   └── error_handler.py
│       ├── repositories/
│       └── ui/                         # Orchestration dashboard
│           └── orchestration_dashboard.py
├── knowledge_graph/                    # Knowledge graph functionality
│   ├── __init__.py
│   ├── api/                            # KG API endpoints
│   │   ├── __init__.py
│   │   ├── knowledge_graph.py
│   │   ├── jurisdiction_manager.py
│   │   └── legal_relationship_detector.py
│   ├── services/                       # KG business logic
│   │   ├── __init__.py
│   │   ├── enhanced_graph.py
│   │   ├── graph_builder.py
│   │   └── graph_integration.py
│   ├── repositories/                   # KG data access
│   │   ├── __init__.py
│   │   ├── graph_repository.py
│   │   └── vector_repository.py
│   └── ui/                             # KG UI components
│       └── kg_visualization.py
├── infrastructure/                     # Infrastructure components
│   ├── __init__.py
│   ├── api/                            # Infrastructure APIs
│   │   ├── __init__.py
│   │   ├── file_storage.py
│   │   └── database.py
│   ├── services/                       # Infrastructure services
│   │   ├── __init__.py
│   │   ├── file_storage_manager.py
│   │   ├── database_manager.py
│   │   └── repository.py
│   └── ui/                             # Infrastructure UI
│       └── file_browser.py
└── ui/                                 # Global UI components
    ├── __init__.py
    ├── static/                         # Static assets
    │   ├── css/
    │   ├── js/
    │   └── assets/
    ├── templates/                      # HTML templates
    │   ├── components/
    │   └── layouts/
    └── apps/                           # UI applications
        ├── claims_matrix/
        └── orchestration_dashboard/

# Separate directories (not under /src)
├── tests/                              # All tests
│   ├── __init__.py
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   └── fixtures/
├── docs/                               # Documentation
│   ├── api/
│   ├── architecture/
│   ├── development/
│   ├── components/
│   └── examples/
├── scripts/                            # Utility scripts
├── configs/                            # Configuration files
├── data/                               # Data files
│   ├── kg/
│   └── vectors/
└── tools/                              # Development tools
```

## Key Improvements

### 1. Clear Separation of Concerns
- **Phases**: Primary organization by workflow execution order
- **Domains**: Secondary organization by functionality (api, services, repositories, ui)
- **Shared**: Common utilities and base classes
- **Infrastructure**: Technical infrastructure components

### 2. Consistent Structure
- Every phase follows the same pattern: `api/`, `services/`, `repositories/`, `ui/`
- Clear boundaries between different types of code
- Predictable file locations

### 3. Reduced Nesting
- Maximum depth reduced from 6-7 levels to 4-5 levels
- Clearer import paths
- Easier navigation

### 4. Consolidated Functionality
- Single location for maestro orchestration
- Consolidated file storage implementation
- Unified knowledge graph components

## Migration Strategy

### Phase 1: Create New Structure
1. Create the new directory structure
2. Copy files to new locations (don't move yet)
3. Update import statements in copied files

### Phase 2: Update References
1. Update all import statements throughout codebase
2. Update configuration files
3. Update documentation references

### Phase 3: Remove Old Structure
1. Move old files to trash staging
2. Verify all functionality works
3. Remove old directories

## Benefits

1. **Maintainability**: Clear organization makes it easier to find and modify code
2. **Scalability**: Consistent patterns make it easier to add new features
3. **Onboarding**: New developers can quickly understand the codebase structure
4. **Testing**: Clear separation makes unit testing more straightforward
5. **Deployment**: Cleaner structure simplifies packaging and deployment

## Implementation Priority

### High Priority (Immediate)
- Create new directory structure
- Move infrastructure components (file storage, database)
- Consolidate duplicate maestro implementations

### Medium Priority (Next Sprint)
- Reorganize phase-specific code
- Update import statements
- Move knowledge graph components

### Low Priority (Future)
- Reorganize UI components
- Update documentation
- Clean up remaining legacy files