# Current Codebase Structure

## Root Level
```
lawyerfactory/
├── README.md (✅ Updated with knowledge graph integration)
├── SYSTEM_DOCUMENTATION.md (✅ Updated with knowledge graph integration)
├── trash/ (🗑️ Contains moved files)
│   ├── INDEX.md
│   ├── enhanced_categorization_demo.py
│   ├── enhanced_knowledge_graph.py
│   ├── kanban_cli.py
│   ├── knowledge_graph.py
│   ├── legal_authority_validator.py
│   ├── legal_research_integration.py
│   ├── models.py
│   └── [various test files]
├── data/
│   └── knowledge_graph.json (📊 Core reference framework)
├── src/
│   ├── __init__.py
│   ├── lawyerfactory/
│   │   ├── __init__.py
│   │   ├── enhanced_workflow.py
│   │   ├── agents/
│   │   │   ├── orchestration/
│   │   │   │   ├── maestro.py
│   │   │   │   └── workflow_engine.py
│   │   │   ├── intake/
│   │   │   │   ├── reader.py
│   │   │   │   └── assessor.py
│   │   │   ├── research/
│   │   │   │   ├── legal_researcher.py
│   │   │   │   ├── court_authority_helper.py
│   │   │   │   └── retrievers/
│   │   │   ├── drafting/
│   │   │   │   ├── writer.py
│   │   │   │   └── templates/
│   │   │   ├── review/
│   │   │   │   ├── editor.py
│   │   │   │   └── quality_checker.py
│   │   │   └── formatting/
│   │   │       ├── legal_formatter.py
│   │   │       └── paralegal.py
│   │   ├── phases/
│   │   │   ├── phaseA01_intake/
│   │   │   │   ├── assessor.py
│   │   │   │   ├── enhanced_document_categorizer.py
│   │   │   │   ├── evidence_ingestion.py
│   │   │   │   ├── intake_processor.py
│   │   │   │   ├── legal_intake_form.py
│   │   │   │   ├── llm_integration.py
│   │   │   │   ├── reader.py
│   │   │   │   ├── vector_cluster_manager.py
│   │   │   │   └── [other intake files]
│   │   │   ├── phaseA02_research/
│   │   │   │   ├── enhanced_research_bot.py
│   │   │   │   └── retrievers/
│   │   │   ├── phaseA03_outline/
│   │   │   │   ├── outline_generator.py
│   │   │   │   └── claims/
│   │   │   ├── phaseB01_review/
│   │   │   │   └── attorney_review_interface.py
│   │   │   ├── phaseB02_drafting/
│   │   │   │   ├── drafting_validator.py
│   │   │   │   ├── prompt_deconstruction.py
│   │   │   │   └── writer_bot.py
│   │   │   ├── phaseC01_editing/
│   │   │   │   ├── citations.py
│   │   │   │   └── pdf_generator.py
│   │   │   └── phaseC02_orchestration/
│   │   │       ├── maestro.py
│   │   │       └── workflow_engine.py
│   │   ├── infrastructure/ (⚠️ Potential duplicate with infra/)
│   │   │   └── storage/
│   │   ├── infra/ (⚠️ Potential duplicate with infrastructure/)
│   │   │   ├── databases.py
│   │   │   ├── repository.py
│   │   │   └── storage_api_init.py
│   │   ├── knowledge_graph/ (⚠️ Potential duplicate with kg/)
│   │   │   ├── api/
│   │   │   ├── core/
│   │   │   └── integrations/
│   │   ├── kg/ (⚠️ Potential duplicate with knowledge_graph/)
│   │   │   ├── enhanced_graph.py
│   │   │   ├── graph_api.py
│   │   │   └── relations.py
│   │   ├── storage/
│   │   │   ├── unified_storage_api.py
│   │   │   └── enhanced_unified_storage_api.py
│   │   ├── vectors/
│   │   │   ├── enhanced_vector_store.py
│   │   │   ├── evidence_ingestion.py
│   │   │   └── llm_rag_integration.py
│   │   └── ui/
│   │       └── legal_intake_form.py
│   ├── shared/
│   └── storage/
├── apps/
│   ├── api/
│   │   ├── server.py
│   │   └── routes/
│   ├── ui/
│   │   └── templates/
│   │       ├── consolidated_factory.html
│   │       ├── multiswarm_dashboard.html
│   │       └── [other templates]
│   └── cli/
├── templates/
│   ├── orchestration/
│   └── visualphases.html
└── [various config and utility files]
```

## Key Issues Identified

### 1. **Duplicate/Redundant Directories**
- `infrastructure/` vs `infra/` - Both contain infrastructure code
- `knowledge_graph/` vs `kg/` - Both contain knowledge graph functionality
- Multiple nested directories with similar purposes

### 2. **Files Moved to Trash**
- ✅ Shim files (backward compatibility redirects)
- ✅ Demo files (not core functionality)
- ✅ Build artifacts (`.egg-info`, `.DS_Store`)
- ✅ Test files moved during cleanup

### 3. **Structural Issues**
- Deep nesting in phases (phaseA01_intake, phaseA02_research, etc.)
- Some directories have both Python modules and subdirectories
- Mixed organizational patterns (some by function, some by phase)

### 4. **Remaining Issues**
- Some duplicate functionality in different phase directories
- Inconsistent naming conventions
- Some files may be outdated or redundant

## Next Steps
1. Resolve duplicate directories (`infrastructure` vs `infra`, `knowledge_graph` vs `kg`)
2. Flatten overly deep directory structures
3. Consolidate similar functionality
4. Update import statements after restructuring
5. Test all functionality after changes