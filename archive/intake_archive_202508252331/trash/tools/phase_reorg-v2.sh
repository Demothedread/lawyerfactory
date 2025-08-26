#!/usr/bin/env bash
set -euo pipefail

echo "== LawyerFactory phase-oriented reorg =="
echo "Running from: $(pwd)"

# ---------- helpers ----------
mv_safe () {
  # mv_safe <src1> [<src2> ...] --to <dest>
  local dest=""
  local sources=()
  local args=("$@")
  local i
  for ((i=0; i<${#args[@]}; i++)); do
    if [[ "${args[$i]}" == "--to" ]]; then
      dest="${args[$((i+1))]}"
      break
    else
      sources+=("${args[$i]}")
    fi
  done
  if [[ -z "$dest" ]]; then
    echo "mv_safe: missing --to <dest>" >&2; exit 1
  fi
  mkdir -p "$(dirname "$dest")"
  for s in "${sources[@]}"; do
    if [[ -e "$s" ]]; then
      git mv -k "$s" "$dest" 2>/dev/null || { /bin/mv "$s" "$dest"; git add -A "$dest"; }
      echo "moved: $s -> $dest"
      return 0
    fi
  done
  return 1
}

ensure_pkg () {
  # ensure_pkg <dir1> <dir2> ...
  for d in "$@"; do
    mkdir -p "$d"
    [[ -f "$d/__init__.py" ]] || { echo "# pkg" > "$d/__init__.py"; git add -A "$d/__init__.py" >/dev/null 2>&1 || true; }
  done
}

shim_top () {
  # shim_top <old_module_basename.py> <new_import_path>
  local mod="$1"; local target="$2"
  if [[ ! -f "$mod" ]]; then
    cat > "$mod" <<PY
# AUTO-SHIM (top-level): deprecated module
import warnings as _w
_w.warn("Import '$mod' is deprecated; use '$target'.", DeprecationWarning, stacklevel=2)
from $target import *  # noqa: F401,F403
PY
    git add -A "$mod" >/dev/null 2>&1 || true
    echo "shimmed: $mod -> $target"
  fi
}

shim_pkg () {
  # shim_pkg <pkg_rel_path_without_.py> <new_import_path>
  local rel="$1"; local target="$2"
  local path="src/lawyerfactory/${rel}.py"
  mkdir -p "$(dirname "$path")"
  if [[ ! -f "$path" ]]; then
    cat > "$path" <<PY
# AUTO-SHIM (package): deprecated path lawyerfactory.$rel
import warnings as _w
_w.warn("Use '$target' instead of 'lawyerfactory.$rel'.", DeprecationWarning, stacklevel=2)
from $target import *  # noqa: F401,F403
PY
    git add -A "$path" >/dev/null 2>&1 || true
    echo "shimmed: lawyerfactory.$rel -> $target"
  fi
}

# ---------- ensure src-layout packaging ----------
if [[ ! -f pyproject.toml && ! -f setup.cfg ]]; then
  cat > pyproject.toml <<'TOML'
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "lawyerfactory"
version = "0.0.0"
requires-python = ">=3.10"
description = "LawyerFactory monorepo (src-layout)"
dependencies = []

[tool.setuptools]
package-dir = {"" = "src"}
TOML
  echo "created: pyproject.toml"
fi

# ---------- define phase folders (01→07) ----------
PH_ROOT="src/lawyerfactory/phases"
P01="$PH_ROOT/phaseA01_intake"                 # ingestion + initial evidence table scaffolding
P02="$PH_ROOT/02_research"               # early research + authority cache/validators
P03="$PH_ROOT/03_outline"                # evidence→shotlist (chronology), claims matrix, skeletal outline
P04="$PH_ROOT/04_human_review"           # UI review / I/O (download/upload), freeze/unfreeze
P05="$PH_ROOT/05_drafting"               # longform drafting with prompt-batching, section-by-section
P06="$PH_ROOT/06_post_production"        # validation, formatting, bluebook cites, 12(b) checks
P07="$PH_ROOT/07_orchestration"          # maestro DAG, registry, checkpoints, events

ensure_pkg "$PH_ROOT" \
  "$P01/ingestion" "$P01/evidence" \
  "$P02/agents" "$P02/retrievers" \
  "$P03/shotlist" "$P03/claims" "$P03/outline" \
  "$P04/ui" "$P04/io" \
  "$P05/generator" "$P05/promptkits" \
  "$P06/validators" "$P06/formatters" \
  "$P07/maestro" "$P07/state"

# ---------- move core modules into phases (accept legacy or interim locations) ----------
# Intake / ingestion (P01)
mv_safe src/ingestion/api/ingest_server.py src/lawyerfactory/ingest/server.py                          --to "$P01/ingestion/server.py" || true
mv_safe src/ingestion/api/assessor.py src/lawyerfactory/ingest/assessors/assessor.py                   --to "$P01/ingestion/assessor.py" || true
mv_safe src/ingestion/api/ai_document_agent.py src/lawyerfactory/ingest/pipelines/ai_document_agent.py --to "$P01/ingestion/ai_document_agent.py" || true
mv_safe knowledge_graph.py src/lawyerfactory/kg/graph_root.py                                          --to "$P01/ingestion/knowledge_graph_root.py" || true
mv_safe src/knowledge_graph/api/knowledge_graph_extensions.py src/lawyerfactory/kg/extensions.py       --to "$P01/ingestion/knowledge_graph_extensions.py" || true
# Evidence table (initial scaffold lives in P01; generators in P03)
mv_safe maestro/evidence_table.py src/lawyerfactory/evidence/table.py                                  --to "$P01/evidence/table.py" || true

# Research (P02)
mv_safe maestro/bots/research_bot.py src/lawyerfactory/compose/bots/research.py                        --to "$P02/agents/research_bot.py" || true
mv_safe src/research/legal_research_integration.py src/lawyerfactory/research/retrievers/integration.py --to "$P02/retrievers/integration.py" || true
mv_safe src/research/legal_research_cache_manager.py src/lawyerfactory/research/cache.py               --to "$P02/retrievers/cache.py" || true
mv_safe src/research/legal_authority_validator.py src/lawyerfactory/research/validate.py               --to "$P06/validators/legal_authority_validator.py" || true  # validator used again in P06

# Outline builders (P03): shotlist (chronology), claims matrix, skeletal outline
# Shotlist generator (canonical)
mv_safe statement_of_facts_generator.py src/lawyerfactory/evidence/shotlist.py                         --to "$P03/shotlist/shotlist.py" || true
mv_safe src/lawyerfactory/evidence/shotlist.py                                                         --to "$P03/shotlist/shotlist.py" || true
# Claims matrix
mv_safe src/claims_matrix/claims_matrix_research_api.py src/lawyerfactory/claims/research_api.py       --to "$P03/claims/research_api.py" || true
mv_safe src/claims_matrix/comprehensive_claims_matrix_integration.py src/lawyerfactory/claims/matrix.py --to "$P03/claims/matrix.py" || true
mv_safe src/ingestion/api/cause_of_action_detector.py src/lawyerfactory/claims/detect.py               --to "$P03/claims/detect.py" || true
mv_safe src/ingestion/api/cause_of_action_definition_engine.py src/lawyerfactory/claims/cause_of_action_definition_engine.py --to "$P03/claims/cause_of_action_definition_engine.py" || true
# Skeletal outline
mv_safe src/skeletal_outline/skeletal_outline_generator.py src/lawyerfactory/outline/generator.py      --to "$P03/outline/generator.py" || true
mv_safe src/skeletal_outline/skeletal_outline_integration.py src/lawyerfactory/outline/integration.py  --to "$P03/outline/integration.py" || true

# Human review (P04)
mv_safe templates/enhanced_factory.html apps/ui/templates/enhanced_factory.html                        --to "$P04/ui/enhanced_factory.html" || true
mv_safe app.py apps/api/main.py                                                                        --to "$P04/ui/api_app_main.py" || true
# I/O adapters (download/upload of CSV/JSON artifacts)
mv_safe src/storage/api/file_storage.py src/lawyerfactory/infra/file_storage_api.py                    --to "$P04/io/file_storage.py" || true

# Drafting (P05): prompt batching, writer/editor/procedure bots
mv_safe src/document_generator/api/enhanced_draft_processor.py src/lawyerfactory/compose/strategies/enhanced_draft_processor.py --to "$P05/generator/enhanced_draft_processor.py" || true
mv_safe maestro/bots/writer_bot.py src/lawyerfactory/compose/bots/writer.py                            --to "$P05/generator/writer_bot.py" || true
mv_safe maestro/bots/legal_editor.py src/lawyerfactory/compose/bots/editor.py                          --to "$P05/generator/editor_bot.py" || true
mv_safe maestro/bots/legal_procedure_bot.py src/lawyerfactory/compose/bots/procedure.py                --to "$P05/generator/procedure_bot.py" || true
mv_safe lawyerfactory/document_generator src/lawyerfactory/document_generator                          --to "$P05/generator/document_generator" || true
# Prompt-kits (one-prompt-per-section)
mv_safe lawyerfactory/prompt_deconstruction.py src/lawyerfactory/compose/promptkits/prompt_deconstruction.py --to "$P05/promptkits/prompt_deconstruction.py" || true
mv_safe lawyerfactory/prompt_integration.py src/lawyerfactory/compose/promptkits/prompt_integration.py       --to "$P05/promptkits/prompt_integration.py" || true

# Post-production (P06): validation, formatting, bluebook, 12(b), autofill PDFs
mv_safe src/document_generator/api/document_export_system.py src/lawyerfactory/export/renderers/document_export_system.py --to "$P06/formatters/document_export_system.py" || true
mv_safe legal_document_templates.py src/lawyerfactory/export/templates/legal_document_templates.py     --to "$P06/formatters/legal_document_templates.py" || true
mv_safe cascading_decision_tree_engine.py src/lawyerfactory/compose/strategies/cascading_decision_tree_engine.py --to "$P06/validators/cascading_decision_tree_engine.py" || true

# Orchestration (P07): maestro DAG, checkpoints/state, registry
mv_safe maestro/enhanced_maestro.py src/lawyerfactory/compose/maestro/enhanced_maestro.py              --to "$P07/maestro/enhanced_maestro.py" || true
mv_safe maestro/maestro.py src/lawyerfactory/compose/maestro/maestro.py                                --to "$P07/maestro/maestro.py" || true
mv_safe maestro/agent_registry.py src/lawyerfactory/compose/maestro/registry.py                        --to "$P07/maestro/registry.py" || true
mv_safe maestro/event_system.py src/lawyerfactory/compose/maestro/events.py                            --to "$P07/maestro/events.py" || true
mv_safe maestro/error_handling.py src/lawyerfactory/compose/maestro/errors.py                          --to "$P07/maestro/errors.py" || true
mv_safe maestro/workflow_models.py src/lawyerfactory/compose/maestro/workflow_models.py                --to "$P07/maestro/workflow_models.py" || true
mv_safe maestro/checkpoint_manager.py src/lawyerfactory/compose/maestro/checkpoints.py                  --to "$P07/state/checkpoints.py" || true
mv_safe workflow_storage/workflow_states.db data/workflow/workflow_states.db                           --to "$P07/state/workflow_states.db" || true
mv_safe deploy_lawyerfactory.py scripts/deploy_lawyerfactory.py                                        --to "$P07/maestro/deploy_lawyerfactory.py" || true
mv_safe start_enhanced_factory.py apps/cli/start_enhanced_factory.py                                    --to "$P07/maestro/start_enhanced_factory.py" || true

# ---------- compat shims for legacy imports ----------
# top-level modules commonly used by tests
shim_top knowledge_graph.py            lawyerfactory.phases.phaseA01_intake.ingestion.knowledge_graph_root
shim_top enhanced_knowledge_graph.py   lawyerfactory.kg.enhanced_graph
shim_top cause_of_action_detector.py   lawyerfactory.phases.03_outline.claims.detect
shim_top document_export_system.py     lawyerfactory.phases.06_post_production.formatters.document_export_system
shim_top assessor.py                   lawyerfactory.phases.phaseA01_intake.ingestion.assessor

# package names that might be referenced directly
shim_pkg enhanced_workflow             lawyerfactory.compose.maestro.workflow
shim_pkg models                        lawyerfactory.lf_core.models
shim_pkg knowledge_graph               lawyerfactory.kg.graph
shim_pkg file_storage                  lawyerfactory.infra.file_storage

# CLI bridge expected by tests
if [[ ! -f src/lawyerfactory/kanban_cli.py && -f apps/cli/lf.py ]]; then
  cat > src/lawyerfactory/kanban_cli.py <<'PY'
from apps.cli.lf import *  # noqa: F401,F403
PY
  git add -A src/lawyerfactory/kanban_cli.py >/dev/null 2>&1 || true
  echo "bridge: src/lawyerfactory/kanban_cli.py -> apps/cli/lf.py"
fi

# ---------- ensure editable install so imports resolve ----------
pip -q install -e . >/dev/null || true

echo "== Phase reorg complete. Review with 'git status' and run tests."