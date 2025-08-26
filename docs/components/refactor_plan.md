# Refactor Plan - LawyerFactory Codebase Reorganization

## Overview
This plan outlines the systematic reorganization of the LawyerFactory codebase from the current mixed structure to the proposed clean, phase-based architecture.

## Current Structure Analysis

### Problems Identified:
1. **Multiple organizational patterns**: Mix of phase-based and function-based organization
2. **Duplicate implementations**: Same functionality in multiple locations
3. **Deep nesting**: Some paths exceed 5-6 levels deep
4. **Inconsistent naming**: Mixed naming conventions
5. **Scattered components**: Related functionality spread across multiple directories

### Key Duplicate Areas:
- **Maestro orchestration**: 3 different locations
- **File storage**: 4 different implementations
- **Knowledge graph**: Components in both `src/knowledge_graph/` and `src/lawyerfactory/kg/`

## Target Structure

```
/src/lawyerfactory/
├── phases/phaseA01_intake/{api,services,repositories,ui}/
├── phases/phaseA02_research/{api,services,repositories,ui}/
├── phases/03_outline/{api,services,repositories,ui}/
├── phases/04_human_review/{api,services,repositories,ui}/
├── phases/05_drafting/{api,services,repositories,ui}/
├── phases/06_post_production/{api,services,repositories,ui}/
├── phases/07_orchestration/{api,services,repositories,ui}/
├── knowledge_graph/{api,services,repositories,ui}/
├── infrastructure/{api,services,repositories,ui}/
├── shared/
└── config/
```

## Migration Mapping

### Phase 1: Infrastructure Consolidation

#### File Storage Components
| Current Path | New Path | Status |
|-------------|----------|---------|
| `src/lawyerfactory/file_storage.py` | `src/lawyerfactory/infrastructure/services/file_storage_manager.py` | MIGRATE |
| `src/lawyerfactory/infra/file_storage.py` | `src/lawyerfactory/infrastructure/services/file_storage_manager.py` | MERGE |
| `src/lawyerfactory/infra/file_storage_api.py` | `src/lawyerfactory/infrastructure/api/file_storage.py` | MIGRATE |
| `lawyerfactory/file-storage.py` | `src/lawyerfactory/infrastructure/services/legacy_file_storage.py` | ARCHIVE |

#### Database Components
| Current Path | New Path | Status |
|-------------|----------|---------|
| `src/lawyerfactory/infra/databases.py` | `src/lawyerfactory/infrastructure/services/database_manager.py` | MIGRATE |
| `src/lawyerfactory/infra/repository.py` | `src/lawyerfactory/infrastructure/repositories/base_repository.py` | MIGRATE |

### Phase 2: Knowledge Graph Consolidation

#### Knowledge Graph Components
| Current Path | New Path | Status |
|-------------|----------|---------|
| `src/knowledge_graph/api/jurisdiction_manager.py` | `src/lawyerfactory/knowledge_graph/api/jurisdiction_manager.py` | MIGRATE |
| `src/knowledge_graph/api/knowledge_graph.py` | `src/lawyerfactory/knowledge_graph/api/knowledge_graph.py` | MIGRATE |
| `src/knowledge_graph/api/legal_relationship_detector.py` | `src/lawyerfactory/knowledge_graph/api/legal_relationship_detector.py` | MIGRATE |
| `src/lawyerfactory/kg/enhanced_graph.py` | `src/lawyerfactory/knowledge_graph/services/enhanced_graph.py` | MIGRATE |
| `src/lawyerfactory/kg/graph_api.py` | `src/lawyerfactory/knowledge_graph/api/graph_api.py` | MIGRATE |
| `src/lawyerfactory/kg/graph_root.py` | `src/lawyerfactory/knowledge_graph/services/graph_builder.py` | MIGRATE |
| `src/lawyerfactory/kg/graph.py` | `src/lawyerfactory/knowledge_graph/services/graph_integration.py` | MIGRATE |
| `src/lawyerfactory/kg/jurisdiction.py` | `src/lawyerfactory/knowledge_graph/services/jurisdiction_service.py` | MIGRATE |
| `src/lawyerfactory/kg/legal_authorities.py` | `src/lawyerfactory/knowledge_graph/services/legal_authorities.py` | MIGRATE |
| `src/lawyerfactory/kg/relations.py` | `src/lawyerfactory/knowledge_graph/services/relations.py` | MIGRATE |
| `src/lawyerfactory/kg/integration.py` | `src/lawyerfactory/knowledge_graph/services/integration.py` | MIGRATE |

### Phase 3: Maestro Orchestration Consolidation

#### Maestro Components
| Current Path | New Path | Status |
|-------------|----------|---------|
| `src/lawyerfactory/compose/maestro/enhanced_maestro.py` | `src/lawyerfactory/phases/07_orchestration/services/maestro.py` | MIGRATE |
| `src/lawyerfactory/phases/07_orchestration/maestro/enhanced_maestro.py` | DELETE (shim) | DELETE |
| `maestro/enhanced_maestro.py` | DELETE (deprecated) | DELETE |

#### Maestro Supporting Components
| Current Path | New Path | Status |
|-------------|----------|---------|
| `src/lawyerfactory/compose/maestro/base.py` | `src/lawyerfactory/phases/07_orchestration/services/base_maestro.py` | MIGRATE |
| `src/lawyerfactory/compose/maestro/maestro.py` | `src/lawyerfactory/phases/07_orchestration/services/workflow_engine.py` | MIGRATE |
| `src/lawyerfactory/compose/maestro/maestro_bot.py` | `src/lawyerfactory/phases/07_orchestration/services/maestro_bot.py` | MIGRATE |
| `src/lawyerfactory/compose/maestro/workflow_models.py` | `src/lawyerfactory/phases/07_orchestration/services/workflow_models.py` | MIGRATE |
| `src/lawyerfactory/compose/maestro/workflow_api.py` | `src/lawyerfactory/phases/07_orchestration/api/workflow_api.py` | MIGRATE |
| `src/lawyerfactory/compose/maestro/events.py` | `src/lawyerfactory/phases/07_orchestration/services/event_system.py` | MIGRATE |
| `src/lawyerfactory/compose/maestro/errors.py` | `src/lawyerfactory/phases/07_orchestration/services/error_handler.py` | MIGRATE |
| `src/lawyerfactory/compose/maestro/checkpoints.py` | `src/lawyerfactory/phases/07_orchestration/services/state_manager.py` | MIGRATE |
| `src/lawyerfactory/compose/maestro/compat_wrappers.py` | `src/lawyerfactory/phases/07_orchestration/services/compatibility.py` | MIGRATE |

### Phase 4: Phase-Specific Reorganization

#### Intake Phase (phaseA01_intake)
| Current Path | New Path | Status |
|-------------|----------|---------|
| `src/lawyerfactory/phases/phaseA01_intake/evidence/table.py` | `src/lawyerfactory/phases/phaseA01_intake/services/evidence_table.py` | MIGRATE |
| `src/lawyerfactory/phases/phaseA01_intake/ingestion/assessor.py` | `src/lawyerfactory/phases/phaseA01_intake/services/assessor.py` | MIGRATE |
| `src/lawyerfactory/phases/phaseA01_intake/ingestion/knowledge_graph_extensions.py` | `src/lawyerfactory/phases/phaseA01_intake/services/kg_extensions.py` | MIGRATE |
| `src/lawyerfactory/phases/phaseA01_intake/ingestion/server.py` | `src/lawyerfactory/phases/phaseA01_intake/services/intake_server.py` | MIGRATE |
| `src/lawyerfactory/phases/phaseA01_intake/intake_processor.py` | `src/lawyerfactory/phases/phaseA01_intake/services/intake_processor.py` | MIGRATE |

#### Research Phase (02_research)
| Current Path | New Path | Status |
|-------------|----------|---------|
| `src/lawyerfactory/phases/phaseA02_research/agents/research_bot.py` | `src/lawyerfactory/phases/phaseA02_research/services/research_bot.py` | MIGRATE |
| `src/lawyerfactory/phases/phaseA02_research/retrievers/cache.py` | `src/lawyerfactory/phases/phaseA02_research/services/cache.py` | MIGRATE |
| `src/lawyerfactory/phases/phaseA02_research/retrievers/integration.py` | `src/lawyerfactory/phases/phaseA02_research/services/retriever_integration.py` | MIGRATE |

#### Outline Phase (03_outline)
| Current Path | New Path | Status |
|-------------|----------|---------|
| `src/lawyerfactory/claims/matrix.py` | `src/lawyerfactory/phases/03_outline/services/claims_matrix.py` | MIGRATE |
| `src/lawyerfactory/phases/03_outline/claims/cause_of_action_definition_engine.py` | `src/lawyerfactory/phases/03_outline/services/cause_of_action_engine.py` | MIGRATE |
| `src/lawyerfactory/phases/03_outline/claims/detect.py` | `src/lawyerfactory/phases/03_outline/services/claims_detector.py` | MIGRATE |
| `src/lawyerfactory/phases/03_outline/claims/matrix.py` | MERGE with claims_matrix.py | MERGE |
| `src/lawyerfactory/phases/03_outline/claims/research_api.py` | `src/lawyerfactory/phases/03_outline/api/research_api.py` | MIGRATE |
| `src/lawyerfactory/phases/03_outline/outline/generator.py` | `src/lawyerfactory/phases/03_outline/services/outline_generator.py` | MIGRATE |
| `src/lawyerfactory/phases/03_outline/outline/integration.py` | `src/lawyerfactory/phases/03_outline/services/outline_integration.py` | MIGRATE |
| `src/lawyerfactory/phases/03_outline/shotlist/shotlist.py` | `src/lawyerfactory/phases/03_outline/services/shotlist_generator.py` | MIGRATE |

#### Drafting Phase (05_drafting)
| Current Path | New Path | Status |
|-------------|----------|---------|
| `src/lawyerfactory/phases/05_drafting/generator/editor_bot.py` | `src/lawyerfactory/phases/05_drafting/services/editor_bot.py` | MIGRATE |
| `src/lawyerfactory/phases/05_drafting/generator/procedure_bot.py` | `src/lawyerfactory/phases/05_drafting/services/procedure_bot.py` | MIGRATE |
| `src/lawyerfactory/phases/05_drafting/generator/writer_bot.py` | `src/lawyerfactory/phases/05_drafting/services/writer_bot.py` | MIGRATE |
| `src/lawyerfactory/phases/05_drafting/promptkits/prompt_deconstruction.py` | `src/lawyerfactory/phases/05_drafting/services/prompt_deconstruction.py` | MIGRATE |
| `src/lawyerfactory/phases/05_drafting/promptkits/prompt_integration.py` | `src/lawyerfactory/phases/05_drafting/services/prompt_integration.py` | MIGRATE |

#### Post-Production Phase (06_post_production)
| Current Path | New Path | Status |
|-------------|----------|---------|
| `src/lawyerfactory/post_production/citations.py` | `src/lawyerfactory/phases/06_post_production/services/citations.py` | MIGRATE |
| `src/lawyerfactory/post_production/pdf_generator.py` | `src/lawyerfactory/phases/06_post_production/services/pdf_generator.py` | MIGRATE |
| `src/lawyerfactory/post_production/verification.py` | `src/lawyerfactory/phases/06_post_production/services/verification.py` | MIGRATE |
| `src/lawyerfactory/phases/06_post_production/formatters/document_export_system.py` | `src/lawyerfactory/phases/06_post_production/services/document_export_system.py` | MIGRATE |
| `src/lawyerfactory/phases/06_post_production/formatters/legal_document_templates.py` | `src/lawyerfactory/phases/06_post_production/services/document_templates.py` | MIGRATE |
| `src/lawyerfactory/phases/06_post_production/validators/cascading_decision_tree_engine.py` | `src/lawyerfactory/phases/06_post_production/services/cascading_decision_tree.py` | MIGRATE |
| `src/lawyerfactory/phases/06_post_production/validators/legal_authority_validator.py` | `src/lawyerfactory/phases/06_post_production/services/legal_authority_validator.py` | MIGRATE |

### Phase 5: Bot and Agent Reorganization

#### Bot Components
| Current Path | New Path | Status |
|-------------|----------|---------|
| `src/lawyerfactory/compose/bots/caselaw_researcher.py` | `src/lawyerfactory/phases/phaseA02_research/services/caselaw_researcher.py` | MIGRATE |
| `src/lawyerfactory/compose/bots/citation_formatter.py` | `src/lawyerfactory/phases/phaseA02_research/services/citation_formatter.py` | MIGRATE |
| `src/lawyerfactory/compose/bots/civil_procedure_specialist.py` | `src/lawyerfactory/phases/05_drafting/services/civil_procedure_specialist.py` | MIGRATE |
| `src/lawyerfactory/compose/bots/editor.py` | `src/lawyerfactory/phases/05_drafting/services/editor.py` | MIGRATE |
| `src/lawyerfactory/compose/bots/fact_objectivity_agent.py` | `src/lawyerfactory/phases/03_outline/services/fact_objectivity_agent.py` | MIGRATE |
| `src/lawyerfactory/compose/bots/issuespotter.py` | `src/lawyerfactory/phases/03_outline/services/issuespotter.py` | MIGRATE |
| `src/lawyerfactory/compose/bots/legal_claim_validator.py` | `src/lawyerfactory/phases/03_outline/services/legal_claim_validator.py` | MIGRATE |
| `src/lawyerfactory/compose/bots/legal_validation_agent.py` | `src/lawyerfactory/phases/04_human_review/services/legal_validation_agent.py` | MIGRATE |
| `src/lawyerfactory/compose/bots/procedure.py` | `src/lawyerfactory/phases/05_drafting/services/procedure.py` | MIGRATE |
| `src/lawyerfactory/compose/bots/reader.py` | `src/lawyerfactory/phases/phaseA01_intake/services/reader.py` | MIGRATE |
| `src/lawyerfactory/compose/bots/research.py` | `src/lawyerfactory/phases/phaseA02_research/services/research.py` | MIGRATE |
| `src/lawyerfactory/compose/bots/rules_of_law.py` | `src/lawyerfactory/phases/phaseA02_research/services/rules_of_law.py` | MIGRATE |
| `src/lawyerfactory/compose/bots/writer.py` | `src/lawyerfactory/phases/05_drafting/services/writer.py` | MIGRATE |

### Phase 6: UI and API Reorganization

#### UI Components
| Current Path | New Path | Status |
|-------------|----------|---------|
| `apps/ui/templates/attorney_review_interface.py` | `src/lawyerfactory/phases/04_human_review/ui/attorney_review_interface.py` | MIGRATE |
| `src/lawyerfactory/ui/legal_intake_form.py` | `src/lawyerfactory/phases/phaseA01_intake/ui/legal_intake_form.py` | MIGRATE |
| `src/lawyerfactory/ui/orchestration_dashboard.py` | `src/lawyerfactory/phases/07_orchestration/ui/orchestration_dashboard.py` | MIGRATE |

#### API Components
| Current Path | New Path | Status |
|-------------|----------|---------|
| `apps/api/routes/evidence.py` | `src/lawyerfactory/phases/phaseA01_intake/api/evidence_routes.py` | MIGRATE |

## Implementation Strategy

### Phase 1: Create New Structure (Week 1)
1. Create all new directories
2. Copy files to new locations (don't delete originals)
3. Update imports in copied files
4. Run tests to verify functionality

### Phase 2: Update References (Week 2)
1. Update all import statements throughout codebase
2. Update configuration files
3. Update documentation references
4. Update test imports

### Phase 3: Cleanup (Week 3)
1. Move old files to trash staging
2. Verify all functionality works
3. Remove old directories
4. Update final documentation

## Risk Mitigation

### Testing Strategy
- Run full test suite after each major migration
- Create integration tests for moved components
- Verify API endpoints still work
- Test UI components in new locations

### Rollback Plan
- Keep original files until migration is verified
- Use trash staging for safe deletion
- Maintain backup of import mappings

### Communication
- Document all path changes
- Update team about major structural changes
- Provide migration guide for external users

## Success Criteria

1. **All tests pass** in new structure
2. **No broken imports** in any Python file
3. **Consistent naming** throughout codebase
4. **Clear documentation** of new structure
5. **Improved maintainability** (easier to find and modify code)
6. **Reduced complexity** (shallower directory structure)

## Timeline

- **Week 1**: Infrastructure and Knowledge Graph consolidation
- **Week 2**: Phase-specific reorganization
- **Week 3**: Bot/Agent reorganization and UI/API cleanup
- **Week 4**: Testing, documentation, and final cleanup

## Tools Needed

1. **Migration script**: Automated file copying and import updating
2. **Import analyzer**: Detect and fix broken imports
3. **Test runner**: Continuous testing during migration
4. **Documentation generator**: Update docs with new structure