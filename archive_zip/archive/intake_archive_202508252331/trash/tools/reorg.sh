#!/usr/bin/env bash
set -euo pipefail

# ----- guard: ensure we're at repo root -----
if [ ! -f "requirements.txt" ]; then
  echo "Run from the repo root (where requirements.txt lives)." >&2
  exit 1
fi

# ----- create target tree (directories only) -----
mkdir -p apps/api/routes apps/api/dependencies apps/cli apps/ui/templates apps/ui/static/css apps/ui/static/js
mkdir -p src/lawyerfactory/{lf_core,ingest/{readers,assessors,pipelines},vectors/{stores},kg/{adapters},research/{retrievers},outline,claims,evidence,compose/{maestro,promptkits,strategies,bots},export/{renderers,templates},infra}
mkdir -p data/{vectors,kg,workflow,ingest} output/{evidence,claims,outline,drafts,final} configs scripts tests/fixtures
mkdir -p docs

# ----- helper: mv if exists & not already at target -----
mv_safe () {
  local src="$1" dst="$2"
  if [ -e "$src" ]; then
    mkdir -p "$(dirname "$dst")"
    if [ "$src" != "$dst" ]; then
      git mv -k "$src" "$dst" 2>/dev/null || { mkdir -p "$(dirname "$dst")"; /bin/mv "$src" "$dst"; git add -A "$dst"; }
      echo "moved: $src -> $dst"
    fi
  fi
}

# ----- DOCS (curate names, keep all content) -----
mv_safe docs/AI_DOCUMENT_GENERATOR_GUIDE.md docs/ai_document_generator_guide.md
mv_safe docs/FORM_ANALYSIS.md docs/form_analysis.md
mv_safe docs/document_ingestion_pipeline.md docs/ingest_pipeline.md
mv_safe docs/draft_document_processing_implementation.md docs/drafting_pipeline.md
mv_safe docs/harvard_workflow_visualization.md docs/ui_workflow_visualization.md
mv_safe docs/implementation_roadmap.md docs/roadmap.md
mv_safe docs/knowledge_graph_schema.md docs/kg_schema.md
mv_safe docs/maestro_orchestration_spec.md docs/orchestration_maestro_spec.md
mv_safe docs/orchestration_implementation.md docs/orchestration_implementation.md
mv_safe docs/research_bot_implementation.md docs/research.md
mv_safe docs/skeletal_outline_design.md docs/outline_design.md
mv_safe docs/system_architecture.md docs/architecture.md
mv_safe docs/team_chart.md docs/team.md

# ----- APP ENTRYPOINTS / UI -----
mv_safe app.py apps/api/main.py
mv_safe templates/enhanced_factory.html apps/ui/templates/enhanced_factory.html
mv_safe templates/harvard_workflow_visualization.html apps/ui/templates/harvard_workflow_visualization.html
mv_safe static/css/harvard-workflow.css apps/ui/static/css/harvard-workflow.css
mv_safe static/js/claims-matrix.js apps/ui/static/js/claims-matrix.js
mv_safe static/js/evidence-table.js apps/ui/static/js/evidence-table.js
mv_safe static/js/harvard-progress-tracker.js apps/ui/static/js/harvard-progress-tracker.js
mv_safe static/js/harvard-ui-manager.js apps/ui/static/js/harvard-ui-manager.js
mv_safe static/js/harvard-workflow-app.js apps/ui/static/js/harvard-workflow-app.js
mv_safe static/js/harvard-workflow-visualization.js apps/ui/static/js/harvard-workflow-visualization.js
mv_safe factory.html apps/ui/templates/factory.html

# ----- TOP-LEVEL SCRIPTS / CONFIGS / OUTPUT / DATA -----
mv_safe scripts/run_foreground.sh scripts/run_foreground.sh
mv_safe deployment.yml configs/deployment.yml
mv_safe requirements.txt requirements.txt
mv_safe local_vectors.jsonl data/vectors/local.jsonl
mv_safe workflow_storage/enhanced_kg.db data/kg/enhanced_kg.db
mv_safe workflow_storage/workflow_states.db data/workflow/workflow_states.db
# knowledge_graphs folder (and weirdly-typed path) to data/kg
if [ -d knowledge_graphs ]; then
  git mv -k knowledge_graphs data/kg 2>/dev/null || { /bin/mv knowledge_graphs data/kg; git add -A data/kg; }
  echo "moved: knowledge_graphs -> data/kg"
fi
if [ -f "lawyM,HLJVerfactory/knowledge_graphs/main.db" ]; then
  mkdir -p data/kg
  git mv -k "lawyM,HLJVerfactory/knowledge_graphs/main.db" data/kg/main.db 2>/dev/null || { /bin/mv "lawyM,HLJVerfactory/knowledge_graphs/main.db" data/kg/main.db; git add -A data/kg/main.db; }
  echo "rescued: lawyM,HLJVerfactory/knowledge_graphs/main.db -> data/kg/main.db"
fi

# ----- LAWYERFACTORY (legacy parallel package) → src/lawyerfactory/* -----
mv_safe lawyerfactory/__init__.py src/lawyerfactory/__init__.py
mv_safe lawyerfactory/models.py src/lawyerfactory/lf_core/models.py
mv_safe lawyerfactory/document_type_framework.py src/lawyerfactory/lf_core/document_types.py
mv_safe lawyerfactory/agent_config_system.py src/lawyerfactory/lf_core/agent_config.py
mv_safe lawyerfactory/knowledge_graph.py src/lawyerfactory/kg/graph.py
mv_safe lawyerfactory/mcp_memory_integration.py src/lawyerfactory/vectors/memory_compression.py
mv_safe lawyerfactory/enhanced_workflow.py src/lawyerfactory/compose/maestro/workflow.py
mv_safe lawyerfactory/workflow.py src/lawyerfactory/compose/maestro/workflow_legacy.py
mv_safe lawyerfactory/file-storage.py src/lawyerfactory/infra/file_storage.py
mv_safe lawyerfactory/kanban_cli.py apps/cli/lf.py
mv_safe lawyerfactory/prompt_deconstruction.py src/lawyerfactory/compose/promptkits/prompt_deconstruction.py
mv_safe lawyerfactory/prompt_integration.py src/lawyerfactory/compose/promptkits/prompt_integration.py

# ----- MAESTRO ORCHESTRATION -----
mv_safe maestro/__init__.py src/lawyerfactory/compose/maestro/__init__.py
mv_safe maestro/agent_registry.py src/lawyerfactory/compose/maestro/registry.py
mv_safe maestro/bot_interface.py src/lawyerfactory/compose/maestro/base.py
mv_safe maestro/checkpoint_manager.py src/lawyerfactory/compose/maestro/checkpoints.py
mv_safe maestro/compat_wrappers.py src/lawyerfactory/compose/maestro/compat_wrappers.py
mv_safe maestro/database.py src/lawyerfactory/infra/databases.py
mv_safe maestro/enhanced_maestro.py src/lawyerfactory/compose/maestro/enhanced_maestro.py
mv_safe maestro/error_handling.py src/lawyerfactory/compose/maestro/errors.py
mv_safe maestro/event_system.py src/lawyerfactory/compose/maestro/events.py
mv_safe maestro/evidence_api.py apps/api/routes/evidence.py
mv_safe maestro/evidence_table.py src/lawyerfactory/evidence/table.py
mv_safe maestro/maestro.py src/lawyerfactory/compose/maestro/maestro.py
mv_safe maestro/maestro_skeletal_outline_bot.py src/lawyerfactory/outline/integration.py
mv_safe maestro/workflow_models.py src/lawyerfactory/compose/maestro/workflow_models.py

# ----- BOTS -----
mv_safe maestro/bots/__init__.py src/lawyerfactory/compose/bots/__init__.py
mv_safe maestro/bots/reader_bot.py src/lawyerfactory/compose/bots/reader.py
mv_safe maestro/bots/writer_bot.py src/lawyerfactory/compose/bots/writer.py
mv_safe maestro/bots/legal_editor.py src/lawyerfactory/compose/bots/editor.py
mv_safe maestro/bots/legal_procedure_bot.py src/lawyerfactory/compose/bots/procedure.py
mv_safe maestro/bots/research_bot.py src/lawyerfactory/compose/bots/research.py

# ----- SRC/* modules into new capability layout -----
# claims matrix
mv_safe src/claims_matrix/CLAIMS_MATRIX_IMPLEMENTATION_README.md docs/claims_matrix.md
mv_safe src/claims_matrix/claims_matrix_implementation_plan.md docs/claims_matrix_plan.md
mv_safe src/claims_matrix/claims_matrix_progress.md docs/claims_matrix_progress.md
mv_safe src/claims_matrix/claims_matrix_research_api.py src/lawyerfactory/claims/research_api.py
mv_safe src/claims_matrix/claims_matrix_todo.md docs/claims_matrix_todo.md
mv_safe src/claims_matrix/comprehensive_claims_matrix_integration.py src/lawyerfactory/claims/matrix.py

# document generator api
mv_safe src/document_generator/__init__.py src/lawyerfactory/export/__init__.py
mv_safe src/document_generator/api/__init__.py src/lawyerfactory/export/renderers/__init__.py
mv_safe src/document_generator/api/document_export_system.py src/lawyerfactory/export/renderers/document_export_system.py
mv_safe src/document_generator/api/enhanced_draft_processor.py src/lawyerfactory/compose/strategies/enhanced_draft_processor.py
# legacy area kept for reference
if [ -d src/document_generator/api/document_generator_legacy ]; then
  mv_safe src/document_generator/api/document_generator_legacy src/lawyerfactory/export/renderers/legacy
fi

# ingestion
mv_safe src/ingestion/__init__.py src/lawyerfactory/ingest/__init__.py
mv_safe src/ingestion/api/__init__.py src/lawyerfactory/ingest/pipelines/__init__.py
mv_safe src/ingestion/api/ai_document_agent.py src/lawyerfactory/ingest/pipelines/ai_document_agent.py
mv_safe src/ingestion/api/assessor.py src/lawyerfactory/ingest/assessors/assessor.py
mv_safe src/ingestion/api/cause_of_action_definition_engine.py src/lawyerfactory/claims/cause_of_action_definition_engine.py
mv_safe src/ingestion/api/cause_of_action_detector.py src/lawyerfactory/claims/detect.py
mv_safe src/ingestion/api/ingest_server.py src/lawyerfactory/ingest/server.py

# knowledge graph
mv_safe src/knowledge_graph/__init__.py src/lawyerfactory/kg/__init__.py
mv_safe src/knowledge_graph/api/__init__.py src/lawyerfactory/kg/adapters/__init__.py
mv_safe src/knowledge_graph/api/enhanced_knowledge_graph.py src/lawyerfactory/kg/enhanced_graph.py
mv_safe src/knowledge_graph/api/jurisdiction_manager.py src/lawyerfactory/kg/jurisdiction.py
mv_safe src/knowledge_graph/api/knowledge_graph.py src/lawyerfactory/kg/graph_api.py
mv_safe src/knowledge_graph/api/knowledge_graph_extensions.py src/lawyerfactory/kg/extensions.py
mv_safe src/knowledge_graph/api/knowledge_graph_integration.py src/lawyerfactory/kg/integration.py
mv_safe src/knowledge_graph/api/legal_relationship_detector.py src/lawyerfactory/kg/relations.py

# research
mv_safe src/research/legal_authority_validator.py src/lawyerfactory/research/validate.py
mv_safe src/research/legal_research_cache_manager.py src/lawyerfactory/research/cache.py
mv_safe src/research/legal_research_integration.py src/lawyerfactory/research/retrievers/integration.py

# shared (fold into lf_core)
mv_safe src/shared/__init__.py src/lawyerfactory/lf_core/__init__.py
mv_safe src/shared/agent_config_system.py src/lawyerfactory/lf_core/agent_config_shared.py
mv_safe src/shared/document_type_framework.py src/lawyerfactory/lf_core/document_types_shared.py
mv_safe src/shared/models.py src/lawyerfactory/lf_core/models_shared.py

# skeletal outline
mv_safe src/skeletal_outline/SKELETAL_OUTLINE_SYSTEM_README.md docs/skeletal_outline_system.md
mv_safe src/skeletal_outline/skeletal_outline_generator.py src/lawyerfactory/outline/generator.py
mv_safe src/skeletal_outline/skeletal_outline_integration.py src/lawyerfactory/outline/integration_legacy.py

# storage
mv_safe src/storage/__init__.py src/lawyerfactory/infra/__init__.py
mv_safe src/storage/api/__init__.py src/lawyerfactory/infra/storage_api_init.py
mv_safe src/storage/api/file_storage.py src/lawyerfactory/infra/file_storage_api.py

# workflow (folded under compose/maestro)
mv_safe src/workflow/__init__.py src/lawyerfactory/compose/__init__.py
mv_safe src/workflow/api/__init__.py src/lawyerfactory/compose/maestro/api_init.py
mv_safe src/workflow/api/enhanced_workflow.py src/lawyerfactory/compose/maestro/workflow_enhanced.py
mv_safe src/workflow/api/workflow.py src/lawyerfactory/compose/maestro/workflow_api.py

# root miscellany / examples
mv_safe attorney_review_interface.py apps/ui/templates/attorney_review_interface.py
mv_safe cascading_decision_tree_engine.py src/lawyerfactory/compose/strategies/cascading_decision_tree_engine.py
mv_safe deploy_lawyerfactory.py scripts/deploy_lawyerfactory.py
mv_safe e2e_ingestion_test.py tests/e2e_ingestion_test.py
mv_safe getdirectory.py scripts/getdirectory.py
mv_safe knowledge_graph.py src/lawyerfactory/kg/graph_root.py
mv_safe legal_document_templates.py src/lawyerfactory/export/templates/legal_document_templates.py
mv_safe prompt_chain_orchestrator.py src/lawyerfactory/compose/maestro/prompt_chain_orchestrator.py
mv_safe start_enhanced_factory.py apps/cli/start_enhanced_factory.py
mv_safe statement_of_facts_generator.py src/lawyerfactory/compose/strategies/statement_of_facts.py
mv_safe tesla_case_validation.py examples/tesla_case_validation.py || true
mv_safe validate_system_integration.py tests/validate_system_integration.py
mv_safe prompt_instructions.md docs/prompt_instructions.md
mv_safe repository.py src/lawyerfactory/infra/repository.py
mv_safe app.py apps/api/main.py

# tests (kept in place; optional renames for parity)
mv_safe tests/test_ai_document_integration.py tests/compose/test_ai_document_integration.py
mv_safe tests/test_assessor.py tests/ingest/test_assessor.py
mv_safe tests/test_comprehensive_integration.py tests/compose/test_comprehensive_integration.py
mv_safe tests/test_enhanced_integration.py tests/compose/test_enhanced_integration.py
mv_safe tests/test_kanban.py tests/cli/test_kanban.py
mv_safe tests/test_knowledge_graph.db tests/fixtures/test_knowledge_graph.db
mv_safe tests/test_orchestration.py tests/compose/test_orchestration.py
mv_safe tests/test_research_bot.py tests/research/test_research_bot.py
mv_safe tests/test_workflow.py tests/compose/test_workflow.py
mv_safe test_claims_matrix.py tests/claims/test_claims_matrix.py
mv_safe test_claims_matrix_core.py tests/claims/test_claims_matrix_core.py
mv_safe test_draft_endpoints.py tests/api/test_draft_endpoints.py
mv_safe test_fixes.py tests/test_fixes.py
mv_safe test_integration_runner.py tests/compose/test_integration_runner.py
mv_safe test_knowledge_graph_integration.py tests/kg/test_knowledge_graph_integration.py
mv_safe test_legal_research_integration.py tests/research/test_legal_research_integration.py
mv_safe test_statement_of_facts_system.py tests/compose/test_statement_of_facts_system.py

# ----- generate evidence shotlist module if missing (new file) -----
if [ ! -f src/lawyerfactory/evidence/shotlist.py ]; then
  cat > src/lawyerfactory/evidence/shotlist.py <<'PY'
from __future__ import annotations
from typing import List, Dict, Any
import csv
from pathlib import Path

def build_shot_list(evidence_rows: List[Dict[str, Any]], out_path: str | Path) -> Path:
    """
    Build a fact-by-fact shot list from normalized evidence rows.
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["fact_id","source_id","timestamp","summary","entities","citations"]
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for i, row in enumerate(evidence_rows, 1):
            writer.writerow({
                "fact_id": row.get("fact_id", i),
                "source_id": row.get("source_id"),
                "timestamp": row.get("timestamp"),
                "summary": row.get("summary"),
                "entities": "|".join(map(str, row.get("entities", []))),
                "citations": "|".join(map(str, row.get("citations", []))),
            })
    return out_path
PY
  git add src/lawyerfactory/evidence/shotlist.py
  echo "created: src/lawyerfactory/evidence/shotlist.py"
fi

# ----- import-path shims (legacy paths) -----
shim () {
  local old_path="$1" new_import="$2"
  mkdir -p "$(dirname "$old_path")"
  cat > "$old_path" <<PY
# AUTO-GENERATED SHIM: will be removed in next release.
import warnings as _w
_w.warn("Module $old_path is deprecated; import $new_import instead.", DeprecationWarning, stacklevel=2)
from $new_import import *  # noqa: F401,F403
PY
  git add "$old_path"
  echo "shimmed: $old_path -> $new_import"
}

# shims for legacy top-level modules
[ -e lawyerfactory/enhanced_workflow.py ] || shim lawyerfactory/enhanced_workflow.py lawyerfactory.compose.maestro.workflow
[ -e lawyerfactory/workflow.py ] || shim lawyerfactory/workflow.py lawyerfactory.compose.maestro.workflow
[ -e lawyerfactory/file-storage.py ] || shim lawyerfactory/file-storage.py lawyerfactory.infra.file_storage
[ -e lawyerfactory/knowledge_graph.py ] || shim lawyerfactory/knowledge_graph.py lawyerfactory.kg.graph
[ -e lawyerfactory/mcp_memory_integration.py ] || shim lawyerfactory/mcp_memory_integration.py lawyerfactory.vectors.memory_compression
[ -e lawyerfactory/models.py ] || shim lawyerfactory/models.py lawyerfactory.lf_core.models
[ -e lawyerfactory/agent_config_system.py ] || shim lawyerfactory/agent_config_system.py lawyerfactory.lf_core.agent_config
[ -e lawyerfactory/document_type_framework.py ] || shim lawyerfactory/document_type_framework.py lawyerfactory.lf_core.document_types

# maestro shims
[ -e maestro/maestro.py ] || shim maestro/maestro.py lawyerfactory.compose.maestro.maestro
[ -e maestro/enhanced_maestro.py ] || shim maestro/enhanced_maestro.py lawyerfactory.compose.maestro.enhanced_maestro
[ -e maestro/agent_registry.py ] || shim maestro/agent_registry.py lawyerfactory.compose.maestro.registry
[ -e maestro/bot_interface.py ] || shim maestro/bot_interface.py lawyerfactory.compose.maestro.base
[ -e maestro/checkpoint_manager.py ] || shim maestro/checkpoint_manager.py lawyerfactory.compose.maestro.checkpoints
[ -e maestro/event_system.py ] || shim maestro/event_system.py lawyerfactory.compose.maestro.events
[ -e maestro/error_handling.py ] || shim maestro/error_handling.py lawyerfactory.compose.maestro.errors
[ -e maestro/workflow_models.py ] || shim maestro/workflow_models.py lawyerfactory.compose.maestro.workflow_models
[ -e maestro/evidence_table.py ] || shim maestro/evidence_table.py lawyerfactory.evidence.table
[ -e maestro/evidence_api.py ] || shim maestro/evidence_api.py apps.api.routes.evidence

# bots shims
[ -e maestro/bots/reader_bot.py ] || shim maestro/bots/reader_bot.py lawyerfactory.compose.bots.reader
[ -e maestro/bots/writer_bot.py ] || shim maestro/bots/writer_bot.py lawyerfactory.compose.bots.writer
[ -e maestro/bots/legal_editor.py ] || shim maestro/bots/legal_editor.py lawyerfactory.compose.bots.editor
[ -e maestro/bots/legal_procedure_bot.py ] || shim maestro/bots/legal_procedure_bot.py lawyerfactory.compose.bots.procedure
[ -e maestro/bots/research_bot.py ] || shim maestro/bots/research_bot.py lawyerfactory.compose.bots.research

# src/knowledge_graph api shims (common import sites)
[ -e src/knowledge_graph/api/knowledge_graph.py ] || shim src/knowledge_graph/api/knowledge_graph.py lawyerfactory.kg.graph_api
[ -e src/knowledge_graph/api/jurisdiction_manager.py ] || shim src/knowledge_graph/api/jurisdiction_manager.py lawyerfactory.kg.jurisdiction
[ -e src/knowledge_graph/api/legal_relationship_detector.py ] || shim src/knowledge_graph/api/legal_relationship_detector.py lawyerfactory.kg.relations

# workflow api shims
[ -e src/workflow/api/workflow.py ] || shim src/workflow/api/workflow.py lawyerfactory.compose.maestro.workflow_api
[ -e src/workflow/api/enhanced_workflow.py ] || shim src/workflow/api/enhanced_workflow.py lawyerfactory.compose.maestro.workflow_enhanced

# storage api shims
[ -e src/storage/api/file_storage.py ] || shim src/storage/api/file_storage.py lawyerfactory.infra.file_storage_api

# claims shims
[ -e src/claims_matrix/claims_matrix_research_api.py ] || shim src/claims_matrix/claims_matrix_research_api.py lawyerfactory.claims.research_api
[ -e src/claims_matrix/comprehensive_claims_matrix_integration.py ] || shim src/claims_matrix/comprehensive_claims_matrix_integration.py lawyerfactory.claims.matrix

# outline shims
[ -e src/skeletal_outline/skeletal_outline_generator.py ] || shim src/skeletal_outline/skeletal_outline_generator.py lawyerfactory.outline.generator
[ -e src/skeletal_outline/skeletal_outline_integration.py ] || shim src/skeletal_outline/skeletal_outline_integration.py lawyerfactory.outline.integration_legacy

# research shims
[ -e src/research/legal_research_integration.py ] || shim src/research/legal_research_integration.py lawyerfactory.research.retrievers.integration
[ -e src/research/legal_research_cache_manager.py ] || shim src/research/legal_research_cache_manager.py lawyerfactory.research.cache
[ -e src/research/legal_authority_validator.py ] || shim src/research/legal_authority_validator.py lawyerfactory.research.validate

# ==== PATCH: additional moves & shims based on final review ====

# 1) Move maestro_bot to orchestration (not a bot proper)
if [ -f maestro/bots/maestro_bot.py ]; then
  mkdir -p src/lawyerfactory/compose/maestro
  git mv -k maestro/bots/maestro_bot.py src/lawyerfactory/compose/maestro/maestro_bot.py 2>/dev/null || { /bin/mv maestro/bots/maestro_bot.py src/lawyerfactory/compose/maestro/maestro_bot.py; git add -A src/lawyerfactory/compose/maestro/maestro_bot.py; }
  echo "moved: maestro/bots/maestro_bot.py -> src/lawyerfactory/compose/maestro/maestro_bot.py"
fi
# legacy import shim in old location
if [ ! -e maestro/bots/maestro_bot.py ]; then
  mkdir -p maestro/bots
  cat > maestro/bots/maestro_bot.py <<'PY'
# AUTO-GENERATED SHIM: will be removed in next release.
import warnings as _w
_w.warn("maestro/bots/maestro_bot.py is deprecated; use lawyerfactory.compose.maestro.maestro_bot", DeprecationWarning, stacklevel=2)
from lawyerfactory.compose.maestro.maestro_bot import *  # noqa: F401,F403
PY
  git add maestro/bots/maestro_bot.py
  echo "shimmed: maestro/bots/maestro_bot.py -> lawyerfactory.compose.maestro.maestro_bot"
fi

# 2) Statement of Facts generator canonicalization to shotlist
if [ -f statement_of_facts_generator.py ]; then
  # keep canonical engine under evidence/shotlist.py (created earlier)
  # create shim so callers keep working
  cat > statement_of_facts_generator.py <<'PY'
# AUTO-GENERATED SHIM: Statement of Facts generator has been unified with the shot-list builder.
import warnings as _w
_w.warn("Use lawyerfactory.evidence.shotlist.build_shot_list(...) instead of statement_of_facts_generator.py", DeprecationWarning, stacklevel=2)
from lawyerfactory.evidence.shotlist import *  # noqa: F401,F403
PY
  git add statement_of_facts_generator.py
  echo "shimmed: statement_of_facts_generator.py -> lawyerfactory.evidence.shotlist"
fi

# 3) repository.csv → data (seed/fixture)
if [ -f repository.csv ]; then
  mkdir -p data
  git mv -k repository.csv data/repository.csv 2>/dev/null || { /bin/mv repository.csv data/repository.csv; git add -A data/repository.csv; }
  echo "moved: repository.csv -> data/repository.csv"
fi

# 4) ensure workflow checkpoints dir exists (migrate contents if any)
if [ -d workflow_storage/checkpoints ]; then
  mkdir -p data/workflow/checkpoints
  git mv -k workflow_storage/checkpoints/* data/workflow/checkpoints/ 2>/dev/null || { /bin/mv workflow_storage/checkpoints/* data/workflow/checkpoints/ 2>/dev/null || true; git add -A data/workflow/checkpoints/; }
  echo "moved contents: workflow_storage/checkpoints/* -> data/workflow/checkpoints/"
fi

# 5) ignore logs & misc by default (keep if curated)
if [ -d logs ] || [ -d misc ]; then
  touch .gitignore
  if ! grep -qE '^(logs/|misc/)$' .gitignore; then
    printf "\nlogs/\nmisc/\n" >> .gitignore
    git add .gitignore
    echo "updated: .gitignore to exclude logs/ and misc/"
  fi
fi

# 6) add minimal test for shotlist if not present
if [ ! -f tests/evidence/test_shotlist.py ]; then
  mkdir -p tests/evidence
  cat > tests/evidence/test_shotlist.py <<'PY'
from lawyerfactory.evidence.shotlist import build_shot_list
from pathlib import Path
import csv, tempfile

def test_build_shot_list_roundtrip():
    rows = [
        {"source_id":"doc1","timestamp":"2024-01-01","summary":"A thing happened","entities":["A","B"],"citations":["CL:123"]},
        {"source_id":"doc2","timestamp":"2024-01-02","summary":"Another thing","entities":["C"],"citations":[]},
    ]
    with tempfile.TemporaryDirectory() as td:
        out = Path(td)/"shot_list.csv"
        path = build_shot_list(rows, out)
        assert path.exists()
        with path.open() as f:
            r = list(csv.DictReader(f))
        assert len(r) == 2
        assert r[0]["summary"] == "A thing happened"
PY
  git add tests/evidence/test_shotlist.py
  echo "created: tests/evidence/test_shotlist.py"
fi

# ---- finishing notes ----
echo
echo "Reorg staged. Next steps:"
echo "  1) git status  # review"
echo "  2) pytest -q   # fix imports if any residuals"
echo "  3) git commit -m 'refactor: ports/adapters layout + shims'"
echo "PATCH complete. Review with: git status && pytest -q"