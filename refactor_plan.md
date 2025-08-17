Refactor Plan: Reorganize codebase into domain-oriented /src layout with compatibility wrappers

Overview
- Objective: Move toward a domain-oriented /src layout (knowledge_graph, document_generator, storage, workflow, ingestion, shared) while preserving runtime behavior, tests, and existing imports. Use staged moves and compatibility wrappers to minimize risk and enable incremental validation.

Target layout (high-level)
- /src
  - /knowledge_graph/api
  - /document_generator/api
  - /storage/api
  - /workflow/api
  - /ingestion/api
  - /shared
- /trash
- /docs
- Root entrypoints (e.g., app.py) remain usable via wrappers or updated imports where feasible

Migration strategy (phases)
- Phase A – scaffolding
  - Create /src with the domain folders listed above and add minimal __init__.py as needed to establish namespace packages (namespace packages are acceptable in Python 3+).
  - Create thin bridge wrappers in legacy paths to re-export symbols from the new /src modules (see Phase B).
- Phase B – domain migration (incremental)
  - Move a subset of modules per domain into the corresponding /src path and create wrappers so existing imports continue to function.
  - Examples:
    - Move knowledge_graph.py, knowledge_graph_extensions.py, enhanced_knowledge_graph.py into /src/knowledge_graph/api and expose same public APIs via wrappers in the old location.
    - Move lawyerfactory/document_generator/generator.py and lawyerfactory/document_generator/ai_document_generator.py into /src/document_generator/api and expose via wrappers.
    - Move lawyerfactory/file-storage.py into /src/storage/api/file_storage.py and ensure compatibility wrappers exist.
    - Move lawyerfactory/enhanced_workflow.py into /src/workflow/api/enhanced_workflow.py and add wrappers in the legacy path.
    - Move maestro/bots/ingest-server.py into /src/ingestion/api/ingest_server.py and wrappers as needed.
- Phase C – validation
  - Run unit and integration tests to identify broken imports or circular dependencies.
  - Add or adjust compatibility wrappers as needed to keep tests green.
- Phase D – cleanup
  - Remove obviously dead code from /trash once paths are stabilized.
  - Prepare a minimal root README and consolidated docs (root + subdir notes).
- Artifacts to emit
  - current_tree.md
  - proposed_tree.md
  - dep_graph.json
  - refactor_plan.md (this file)
  - move_script.(sh|py)
  - trash/INDEX.md
  - undo script to revert moves

Dependency and import considerations
- Where feasible, preserve existing import paths by using compatibility wrappers that re-export from the new /src locations.
- If a file name with illegal Python module syntax (e.g., file-storage.py) is encountered, establish a compatibility alias by:
  - Creating a new wrapper module with a valid Python name in the old path that re-exports from the real target path.
  - Optionally renaming the file in a future Phase after ensuring all imports are updated or wrappers are in place.
- Documentation and tests should continue to run without modification in Phase A, with changes incrementally validated in Phase B.

Planned deliverables and next steps
- Create /src scaffold and initial wrappers (Phase A).
- In subsequent steps, implement Phase B moves and additional wrappers, then update tests as needed.
- Emit the requested artifacts (current_tree.md, proposed_tree.md, dep_graph.json, refactor_plan.md, move_script.(sh|py), trash/INDEX.md) and an undo script.

Notes
- This is a staged approach to minimize disruption. If you want me to proceed with Phase A scaffolding immediately, say “Proceed with Phase A.” I will then create the /src scaffold and initial wrappers as a first surgical change and report back with a confirmation snapshot and the next actions.