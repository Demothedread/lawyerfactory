# Current Tree Structure (Before Reorganization)

## Root Level Files
- app.py (main entrypoint)
- knowledge_graph.py (duplicate/related to lawyerfactory/knowledge_graph.py)
- enhanced_knowledge_graph.py
- knowledge_graph_extensions.py
- knowledge_graph_integration.py
- document_export_system.py
- enhanced_draft_processor.py
- attorney_review_interface.py
- cascading_decision_tree_engine.py
- cause_of_action_definition_engine.py
- comprehensive_claims_matrix_integration.py
- claims_matrix_research_api.py
- deploy_lawyerfactory.py
- start_enhanced_factory.py

## Package Structure
### lawyerfactory/ (main package)
- __init__.py
- agent_config_system.py
- document_type_framework.py
- enhanced_workflow.py
- file-storage.py (note: hyphenated name)
- kanban_cli.py
- knowledge_graph.py
- mcp_memory_integration.py
- models.py
- prompt_deconstruction.py
- prompt_integration.py
- workflow.py

### lawyerfactory/document_generator/
- modules/ (subdirectory)
- output/ (subdirectory)
- templates/ (subdirectory)

### maestro/ (orchestration package)
- bots/ (subdirectory with multiple bot implementations)

### tests/
- test_enhanced_integration.py
- test_comprehensive_integration.py
- test_ai_document_integration.py
- test_workflow.py
- test_kanban.py

### docs/
- Multiple .md files for documentation

### static/
- css/ and js/ subdirectories

### templates/
- HTML templates

### Tesla/ (case-specific data)
- Multiple subdirectories for Tesla case

### trash/
- Moved legacy documentation

## Import Patterns Observed
- `from lawyerfactory.enhanced_workflow import EnhancedWorkflowManager`
- `from lawyerfactory.document_generator.ai_document_generator import AIDocumentGenerator`
- `from lawyerfactory.document_generator.modules.fact_synthesis import synthesize_facts`
- `from lawyerfactory.document_generator.modules.compliance_checker import check_rule_12b6, validate_citations, flag_for_review`
- `from lawyerfactory.document_generator.modules.legal_theory_mapping import map_facts_to_elements, integrate_citations`
- `from lawyerfactory.workflow import progress_task, is_complete`
- `from lawyerfactory.kanban_cli import display_board`

## Issues Identified
1. **Duplicate knowledge graph modules**: Both root-level and package-level knowledge_graph.py files
2. **Scattered domain logic**: Knowledge graph, document generation, workflow scattered across root and package
3. **Inconsistent naming**: file-storage.py uses hyphen (not Python-friendly)
4. **Root-level clutter**: Many domain-specific files in root instead of organized packages
5. **Mixed concerns**: Root level contains both entrypoints and domain logic

## Domain Clustering
Based on imports and functionality:

### Knowledge Graph Domain
- knowledge_graph.py (root)
- lawyerfactory/knowledge_graph.py
- enhanced_knowledge_graph.py
- knowledge_graph_extensions.py
- knowledge_graph_integration.py

### Document Generation Domain
- lawyerfactory/document_generator/ (entire subtree)
- document_export_system.py
- enhanced_draft_processor.py

### Storage Domain
- lawyerfactory/file-storage.py

### Workflow Domain
- lawyerfactory/enhanced_workflow.py
- lawyerfactory/workflow.py

### Orchestration/Ingestion Domain
- maestro/ (entire package)

### Legal Analysis Domain
- attorney_review_interface.py
- cascading_decision_tree_engine.py
- cause_of_action_definition_engine.py
- comprehensive_claims_matrix_integration.py
- claims_matrix_research_api.py