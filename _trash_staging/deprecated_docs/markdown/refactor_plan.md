# Codebase Refactor Plan - LawyerFactory Multi-Agent Platform

## Executive Summary

This refactor plan addresses the identified structural issues in the LawyerFactory codebase, implementing a clean, maintainable architecture organized around shared entities with clear separation of concerns. The plan follows the prescribed heuristics and organizational guidelines.

## Current State Analysis

### ✅ Completed Actions
- **Documentation Rewrite**: Updated README.md and SYSTEM_DOCUMENTATION.md with knowledge graph integration
- **File Cleanup**: Moved 7+ shim files, demo files, and build artifacts to trash/
- **Structure Analysis**: Identified duplicate directories and deep nesting issues

### 📊 Key Issues Identified
1. **Duplicate Directories**: `infrastructure/` vs `infra/`, `knowledge_graph/` vs `kg/`
2. **Deep Nesting**: Phase directories with unnecessary prefixes (phaseA01_, phaseA02_)
3. **Mixed Organization**: Some directories organized by function, others by phase
4. **Scattered UI**: Interface components spread across multiple locations
5. **Redundant Code**: Similar functionality in different phase directories

## Proposed Architecture

### Target Structure Overview
```
src/
├── shared/           # Common utilities and base classes
├── platform/         # Technical infrastructure (storage, messaging, monitoring)
├── agents/          # AI agent implementations by function
├── knowledge/       # Knowledge representation and processing
├── vectors/         # Vector database and RAG functionality
├── phases/          # Workflow phases (flattened)
└── ui/             # User interface components
```

### Key Improvements
- **Reduced Depth**: Flatten directory structure from 5+ levels to 3-4 levels
- **Clear Separation**: Platform concerns separated from business logic
- **Functional Organization**: Agents grouped by purpose, not phase
- **Unified UI**: All interface components in dedicated directory
- **Consolidated Docs**: Single authoritative README with knowledge graph framework

## Phase-by-Phase Implementation

### Phase 1: Infrastructure Consolidation (High Priority)
**Duration**: 2-3 hours
**Risk Level**: Low
**Impact**: High

#### Objectives
- Merge duplicate infrastructure directories
- Consolidate storage and messaging components
- Establish platform/ as single source of truth

#### Tasks
```bash
# 1. Merge infrastructure directories
mv src/lawyerfactory/infrastructure/* src/lawyerfactory/infra/
rmdir src/lawyerfactory/infrastructure/

# 2. Create platform directory structure
mkdir -p src/platform/{storage,messaging,monitoring,config}

# 3. Move consolidated infrastructure
mv src/lawyerfactory/infra/* src/platform/
```

#### Files to Move
- `src/lawyerfactory/infra/databases.py` → `src/platform/storage/databases.py`
- `src/lawyerfactory/infra/repository.py` → `src/platform/storage/repository.py`
- `src/lawyerfactory/infra/storage_api_init.py` → `src/platform/storage/api_init.py`

#### Import Updates Required
```python
# Before
from lawyerfactory.infra.databases import DatabaseManager

# After
from lawyerfactory.platform.storage.databases import DatabaseManager
```

### Phase 2: Knowledge Graph Consolidation (High Priority)
**Duration**: 1-2 hours
**Risk Level**: Low
**Impact**: High

#### Objectives
- Merge knowledge graph directories
- Establish single knowledge representation layer
- Update all references to use consolidated location

#### Tasks
```bash
# 1. Merge knowledge directories
mv src/lawyerfactory/knowledge_graph/* src/lawyerfactory/kg/
rmdir src/lawyerfactory/knowledge_graph/

# 2. Create knowledge directory structure
mkdir -p src/knowledge/{graph,entities,integration}

# 3. Move consolidated knowledge components
mv src/lawyerfactory/kg/* src/knowledge/graph/
```

#### Files to Move
- `src/lawyerfactory/kg/enhanced_graph.py` → `src/knowledge/graph/enhanced_graph.py`
- `src/lawyerfactory/kg/graph_api.py` → `src/knowledge/graph/graph_api.py`
- `src/lawyerfactory/kg/relations.py` → `src/knowledge/graph/relations.py`

### Phase 3: Agent Reorganization (Medium Priority)
**Duration**: 4-6 hours
**Risk Level**: Medium
**Impact**: High

#### Objectives
- Reorganize agents by functional purpose
- Consolidate duplicate agent implementations
- Update workflow orchestration to use new structure

#### Tasks
```bash
# 1. Create functional agent directories
mkdir -p src/agents/{orchestration,intake,research,drafting,review,formatting}

# 2. Move agents by function
mv src/lawyerfactory/agents/orchestration/* src/agents/orchestration/
mv src/lawyerfactory/phases/phaseA01_intake/reader.py src/agents/intake/
mv src/lawyerfactory/phases/phaseA01_intake/assessor.py src/agents/intake/
mv src/lawyerfactory/agents/research/* src/agents/research/
mv src/lawyerfactory/agents/drafting/* src/agents/drafting/
mv src/lawyerfactory/agents/review/* src/agents/review/
mv src/lawyerfactory/agents/formatting/* src/agents/formatting/
```

#### Import Updates Required
```python
# Before
from lawyerfactory.phases.phaseA01_intake.reader import ReaderBot

# After
from lawyerfactory.agents.intake.reader import ReaderBot
```

### Phase 4: Phase Directory Flattening (Medium Priority)
**Duration**: 3-4 hours
**Risk Level**: Medium
**Impact**: Medium

#### Objectives
- Remove phase prefixes (phaseA01_, phaseA02_, etc.)
- Reorganize into logical phase directories
- Maintain workflow functionality

#### Tasks
```bash
# 1. Create flattened phase directories
mkdir -p src/phases/{intake,research,outline,drafting,review,editing,orchestration}

# 2. Move phase-specific files
mv src/lawyerfactory/phases/phaseA01_intake/* src/phases/intake/
mv src/lawyerfactory/phases/phaseA02_research/* src/phases/research/
mv src/lawyerfactory/phases/phaseA03_outline/* src/phases/outline/
mv src/lawyerfactory/phases/phaseB02_drafting/* src/phases/drafting/
mv src/lawyerfactory/phases/phaseB01_review/* src/phases/review/
mv src/lawyerfactory/phases/phaseC01_editing/* src/phases/editing/
mv src/lawyerfactory/phases/phaseC02_orchestration/* src/phases/orchestration/
```

#### Import Updates Required
```python
# Before
from lawyerfactory.phases.phaseA01_intake.intake_processor import IntakeProcessor

# After
from lawyerfactory.phases.intake.intake_processor import IntakeProcessor
```

### Phase 5: UI Component Consolidation (Low Priority)
**Duration**: 2-3 hours
**Risk Level**: Low
**Impact**: Low

#### Objectives
- Consolidate all UI components into dedicated directory
- Separate templates, static files, and API endpoints
- Improve frontend organization

#### Tasks
```bash
# 1. Create UI directory structure
mkdir -p src/ui/{templates,static,api}

# 2. Move UI components
mv src/lawyerfactory/ui/* src/ui/
mv apps/ui/templates/* src/ui/templates/
mv apps/ui/static/* src/ui/static/
```

### Phase 6: Shared Utilities Extraction (Medium Priority)
**Duration**: 2-3 hours
**Risk Level**: Low
**Impact**: Medium

#### Objectives
- Extract common utilities used across modules
- Reduce code duplication
- Establish shared utilities library

#### Tasks
```bash
# 1. Create shared directory structure
mkdir -p src/shared/{utils,models,exceptions,constants}

# 2. Extract common utilities
# Move shared utilities from various locations to src/shared/
```

## Risk Assessment & Mitigation

### High-Risk Items
1. **Agent Reorganization**: Could break workflow orchestration
   - **Mitigation**: Update Maestro agent references incrementally
   - **Testing**: Comprehensive workflow testing before/after

2. **Import Path Changes**: Widespread import statement updates required
   - **Mitigation**: Use find/replace with validation
   - **Testing**: Import validation scripts

### Medium-Risk Items
1. **Phase Flattening**: Workflow phase references may break
   - **Mitigation**: Update phase references systematically
   - **Testing**: Phase transition validation

2. **Directory Consolidation**: Potential file conflicts
   - **Mitigation**: Manual review of duplicate files
   - **Testing**: File integrity checks

### Low-Risk Items
1. **UI Consolidation**: Minimal impact on core functionality
2. **Shared Utilities**: Additive changes only

## Testing Strategy

### Pre-Refactor Testing
```bash
# 1. Run full test suite
pytest tests/ -v --tb=short

# 2. Test critical workflows
python -m pytest tests/integration/test_workflow.py -v

# 3. Validate imports
python scripts/validate_imports.py
```

### Post-Refactor Testing
```bash
# 1. Test all imports
python scripts/test_imports.py

# 2. Run integration tests
pytest tests/integration/ -v

# 3. Test critical user workflows
python scripts/test_workflows.py

# 4. Validate knowledge graph integration
python scripts/test_kg_integration.py
```

### Rollback Plan
```bash
# Emergency rollback script
#!/bin/bash
git checkout refactor-backup-branch
git reset --hard HEAD~1
```

## Success Metrics

### Quantitative Metrics
- **Import Errors**: 0 after refactor
- **Test Pass Rate**: ≥95% after refactor
- **Build Time**: No significant increase
- **Code Complexity**: Maintain or reduce

### Qualitative Metrics
- **Directory Depth**: Reduce from 5+ to 3-4 levels
- **File Discoverability**: Improved by 70%
- **Maintenance Ease**: Improved by 60%
- **Onboarding Time**: Reduced by 40%

## Implementation Timeline

### Week 1: Foundation
- Day 1: Infrastructure consolidation
- Day 2: Knowledge graph consolidation
- Day 3: Testing and validation
- Day 4-5: Documentation updates

### Week 2: Core Reorganization
- Day 6-7: Agent reorganization
- Day 8: Phase flattening
- Day 9: UI consolidation
- Day 10: Shared utilities extraction

### Week 3: Validation & Optimization
- Day 11-12: Comprehensive testing
- Day 13: Performance optimization
- Day 14: Final documentation
- Day 15: Deployment preparation

## Dependencies & Prerequisites

### Required Tools
- Python 3.8+
- pytest for testing
- git for version control
- find/replace tools for bulk updates

### Knowledge Prerequisites
- Understanding of current codebase structure
- Familiarity with import mechanisms
- Knowledge of testing frameworks
- Understanding of CI/CD pipelines

## Communication Plan

### Internal Communication
- **Daily Updates**: Progress reports via team chat
- **Weekly Reviews**: Architecture decision documentation
- **Issue Tracking**: GitHub issues for blockers
- **Knowledge Sharing**: Documentation of changes

### External Communication
- **Stakeholder Updates**: Weekly progress summaries
- **Risk Communication**: Early warning of potential delays
- **Success Celebration**: Recognition of milestones achieved

## Success Criteria

### Functional Success
- ✅ All existing functionality preserved
- ✅ No breaking changes to public APIs
- ✅ All tests passing
- ✅ Zero import errors

### Structural Success
- ✅ Directory depth reduced by 40%
- ✅ Duplicate code eliminated
- ✅ Clear separation of concerns
- ✅ Improved code discoverability

### Operational Success
- ✅ Build times maintained
- ✅ Deployment process unchanged
- ✅ Monitoring and logging preserved
- ✅ Documentation updated and accurate

## Appendices

### Appendix A: File Mapping Reference
```
# Old Path → New Path
src/lawyerfactory/infrastructure/ → src/platform/
src/lawyerfactory/kg/ → src/knowledge/graph/
src/lawyerfactory/phases/phaseA01_intake/ → src/phases/intake/
src/lawyerfactory/agents/ → src/agents/
```

### Appendix B: Import Update Scripts
```python
# Bulk import update script
import os
import re

def update_imports(file_path):
    # Update import statements
    pass
```

### Appendix C: Validation Checklists
- [ ] All Python files import successfully
- [ ] All tests pass
- [ ] No circular import dependencies
- [ ] Documentation reflects new structure
- [ ] CI/CD pipelines updated

---

**Refactor Plan Generated**: $(date)
**Target Completion**: 3 weeks
**Risk Level**: Medium
**Expected Benefits**: 60% improvement in code maintainability