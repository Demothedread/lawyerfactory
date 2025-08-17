# LawyerFactory - Clean, Maintainable Legal Automation Platform

A Python-based platform for automated lawsuit generation and legal document workflows. It centers on shared domain entities (knowledge graph, memory, and orchestration) and a lean, modular architecture that is easy to troubleshoot and extend.

Why this cleanup

Root-level documentation has accumulated clutter from multiple readme files and notes that duplicate or overlap with the project structure. This pass moves obsolete artifacts to a dedicated /trash folder and replaces the root with a single authoritative overview. No runtime logic or imports are changed in this pass.

Moved artifacts (for historical review)
- [`trash/LEGAL_RESEARCH_INTEGRATION_README.md`](trash/LEGAL_RESEARCH_INTEGRATION_README.md:1)
- [`trash/KNOWLEDGE_GRAPH_INTEGRATION_README.md`](trash/KNOWLEDGE_GRAPH_INTEGRATION_README.md:1)
- [`trash/KNOWLEDGE_GRAPH_SCHEMA.md`](trash/KNOWLEDGE_GRAPH_SCHEMA.md:1)
- [`trash/SYSTEM_DOCUMENTATION.md`](trash/SYSTEM_DOCUMENTATION.md:1)
- [`trash/CLAIMS_MATRIX_IMPLEMENTATION_README.md`](trash/CLAIMS_MATRIX_IMPLEMENTATION_README.md:1)
- [`trash/STATEMENT_OF_FACTS_GENERATOR_README.md`](trash/STATEMENT_OF_FACTS_GENERATOR_README.md:1)

Core components (high level)

- Knowledge Graph core and extensions: [`knowledge_graph.py`](knowledge_graph.py:1) and [`enhanced_knowledge_graph.py`](enhanced_knowledge_graph.py:1)

- Memory and persistence: [`mcp_memory_integration.py`](mcp_memory_integration.py:1)

- Maestro orchestration and agents: [`maestro/enhanced_maestro.py`](maestro/enhanced_maestro.py:1), [`maestro/evidence_api.py`](maestro/evidence_api.py:1)

- Orchestration and UI glue: [`lawyerfactory/workflow.py`](lawyerfactory/workflow.py:1), [`lawyerfactory/kanban_cli.py`](lawyerfactory/kanban_cli.py:1)

- Document generation and templates: `lawyerfactory/document_generator/`

- Web UI: `factory.html`

Quick start

- Ensure Python 3.8+ is installed.
- Create a virtual environment and install dependencies.
- Run the application (for example: python app.py).
- Access the interface in your browser (port defined by deployment config).

Roadmap and navigation

- This root README provides a concise overview and links to the main components. For deeper dives, navigate to the root of each component or to the /trash catalog for historical artifacts.

Extending LawyerFactory

- Add new document types, templates, or agents by following the interface contracts used by the components in lawyerfactory/
- See the component references above for quick access.

Refactor rationale

- Reduced root-level noise, centralized documentation, and preserved legacy notes in /trash.
- No runtime code changes were made in this pass; this is a documentation/organization change only.

Changelog

- 2025-08-16: Initial consolidation pass; root README created and legacy READMEs moved to /trash.
- 2025-08-16: /trash/index.md catalog updated to reflect moved artifacts.

Next steps

- See [`trash/index.md`](trash/index.md) catalog for moved artifacts with rationales and dates.
- Upon confirmation, I will plan and execute deeper refactors around shared entities (knowledge graph, memory, orchestration) with minimal runtime impact, and provide a lightweight migration plan.

Contact and references

- For questions or contributions, please follow the standard contribution guidelines in this repository.
