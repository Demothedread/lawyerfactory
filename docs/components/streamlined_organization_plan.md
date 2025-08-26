# Streamlined Organization Plan - LawyerFactory

## Current State Analysis

### ✅ **What's Working Well:**
1. **Phase-based workflow structure** (`src/lawyerfactory/phases/`) - Excellent sequential organization
2. **Clear separation of concerns** - Each phase has distinct responsibilities
3. **Logical naming convention** - Phase numbers make workflow order clear

### ❌ **Problems Identified:**
1. **Duplicate implementations** - Multiple versions of same functionality
2. **Deprecated shim files** - Many files just redirect to newer locations
3. **Backup file clutter** - `.bak` files throughout directories
4. **Mixed organizational patterns** - Some components in `compose/`, others in root
5. **Case-specific data** - Tesla directory with non-reusable content
6. **Scattered documentation** - 30+ markdown files in various locations

## Proposed Streamlined Structure

```
/src/lawyerfactory/
├── config/                          # Centralized configuration
│   ├── __init__.py
│   ├── settings.py
│   ├── deployment.py
│   └── logging.py
├── shared/                          # Shared utilities and base classes
│   ├── __init__.py
│   ├── base_classes.py
│   ├── utilities.py
│   ├── exceptions.py
│   ├── constants.py
│   └── decorators.py
├── infrastructure/                  # Infrastructure components
│   ├── __init__.py
│   ├── storage/                     # File storage, database
│   ├── messaging/                   # Event bus, notifications
│   └── monitoring/                  # Logging, metrics
├── knowledge_graph/                 # Knowledge graph system
│   ├── __init__.py
│   ├── core/                        # Core KG functionality
│   ├── integrations/                # External integrations
│   ├── models/                      # KG data models
│   └── api/                         # KG API endpoints
├── agents/                          # All specialized agents
│   ├── __init__.py
│   ├── base/                        # Base agent classes
│   ├── intake/                      # Document intake agents
│   ├── research/                    # Legal research agents
│   ├── analysis/                    # Claims analysis agents
│   ├── drafting/                    # Document drafting agents
│   ├── review/                      # Review and validation agents
│   └── post_processing/             # Formatting and export agents
├── phases/                          # Core workflow phases
│   ├── __init__.py
│   ├── phaseA01_intake/
│   │   ├── __init__.py
│   │   ├── intake_processor.py      # Main intake logic
│   │   ├── document_classifier.py   # Document classification
│   │   ├── evidence_extractor.py    # Evidence extraction
│   │   └── intake_validator.py      # Input validation
│   ├── 02_research/
│   │   ├── __init__.py
│   ├── 03_outline/
│   │   ├── __init__.py
│   ├── 04_human_review/
│   │   ├── __init__.py
│   ├── 05_drafting/
│   │   ├── __init__.py
│   ├── 06_post_production/
│   │   ├── __init__.py
│   └── 07_orchestration/
│       ├── __init__.py
│       ├── maestro.py               # Main orchestrator
│       ├── workflow_engine.py       # Workflow execution
│       ├── state_manager.py         # State management
│       └── error_handler.py         # Error handling
├── services/                        # Business logic services
│   ├── __init__.py
│   ├── document_processing.py
│   ├── legal_analysis.py
│   ├── workflow_management.py
│   └── integration_services.py
├── models/                          # Data models
│   ├── __init__.py
│   ├── document_models.py
│   ├── workflow_models.py
│   ├── legal_models.py
│   └── api_models.py
└── api/                             # API endpoints
    ├── __init__.py
    ├── main.py
    ├── routes/
    └── middleware/

# Documentation (separate from code)
├── docs/
│   ├── README.md                    # Main documentation index
│   ├── architecture/
│   │   ├── system_architecture.md
│   │   ├── workflow_design.md
│   │   └── data_models.md
│   ├── api/
│   │   ├── api_reference.md
│   │   └── integration_guide.md
│   ├── guides/
│   │   ├── user_manual.md
│   │   ├── development_setup.md
│   │   └── troubleshooting.md
│   └── legal/
│       ├── case_studies.md
│       └── compliance.md

# Tests (separate from code)
├── tests/
│   ├── __init__.py
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   └── fixtures/

# Tools and scripts
├── tools/
│   ├── __init__.py
│   ├── migration_scripts/
│   ├── utilities/
│   └── maintenance/

# Trash staging
└── _trash_staging/                  # For files awaiting deletion
```

## Key Improvements

### 1. **Preserve Phase Structure** ✅
- Keep the excellent `phases/` organization
- Each phase focuses on its specific workflow step
- Clear sequential flow from intake to orchestration

### 2. **Consolidate Infrastructure** 🔧
- Move all infrastructure components to `infrastructure/`
- Consolidate file storage, database, messaging
- Centralize configuration management

### 3. **Reorganize Agents by Function** 🤖
- Move all agents to `agents/` directory
- Group by primary function (research, drafting, etc.)
- Remove duplicate agent implementations

### 4. **Centralize Shared Components** 📦
- Create `shared/` for common utilities
- Consolidate base classes and decorators
- Remove duplicate utility functions

### 5. **Clean Knowledge Graph** 🧠
- Consolidate KG components into single directory
- Remove duplicate implementations
- Clear separation between core KG and integrations

## Migration Strategy

### Phase 1: Infrastructure Consolidation
1. Create new `infrastructure/` directory structure
2. Move file storage components from `infra/` and `file_storage.py`
3. Consolidate database components
4. Update all import statements

### Phase 2: Agent Reorganization
1. Create `agents/` directory with functional groupings
2. Move agents from `compose/bots/` to appropriate functional groups
3. Remove duplicate agent implementations
4. Update import statements

### Phase 3: Knowledge Graph Consolidation
1. Create unified `knowledge_graph/` structure
2. Move components from `kg/` and `knowledge_graph/`
3. Remove duplicate implementations
4. Update import statements

### Phase 4: Cleanup and Optimization
1. Remove deprecated shim files
2. Clean up `.bak` files
3. Remove case-specific data (Tesla directory)
4. Consolidate documentation

## Benefits

1. **Reduced Complexity**: Clearer directory structure with logical groupings
2. **Eliminated Duplication**: Single source of truth for each component
3. **Improved Maintainability**: Related functionality grouped together
4. **Better Discoverability**: Easy to find components by function
5. **Cleaner Codebase**: Removed clutter and obsolete files
6. **Enhanced Scalability**: Structure supports future growth

## Implementation Priority

### High Priority (Immediate)
- Consolidate infrastructure components
- Remove deprecated shim files
- Clean up backup files
- Move case-specific data to trash

### Medium Priority (Next Sprint)
- Reorganize agents by function
- Consolidate knowledge graph components
- Update import statements
- Test functionality after moves

### Low Priority (Future)
- Further optimize phase-specific code
- Enhance documentation structure
- Add automated testing for organization
- Create maintenance scripts

## Success Criteria

1. **All tests pass** after reorganization
2. **No broken imports** in any Python file
3. **Clear directory structure** reflecting system architecture
4. **Eliminated duplication** of functionality
5. **Improved developer experience** with better organization
6. **Maintainable codebase** with logical component grouping

This streamlined organization preserves the excellent workflow-based structure while eliminating clutter, duplication, and confusion. The result will be a clean, maintainable codebase that clearly reflects the sequential nature of the legal document processing workflow.