#!/usr/bin/env python3
"""
fix_imports.py — rewrite old module paths to the new lawyerfactory layout.

Usage:
  # dry-run (default)
  python fix_imports.py

  # write changes in-place
  python fix_imports.py --apply

  # limit to certain paths
# Script Name: fix_imports.py
# Description: !/usr/bin/env python3
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Core
#   - Group Tags: null
  python fix_imports.py --apply src/ tests/

Notes:
- Only touches *.py files outside excluded dirs.
- Handles both `import X` and `from X import Y`.
- Picks the LONGEST matching old-prefix for robust remaps.
"""
import argparse
import ast
import os
import pathlib
import re

# ---- 1) Old → New module path map (prefix-aware; longest key wins) ----
MAP = {
    # legacy top-level
    "lawyerfactory.models": "lawyerfactory.lf_core.models",
    "lawyerfactory.agent_config_system": "lawyerfactory.lf_core.agent_config",
    "lawyerfactory.document_type_framework": "lawyerfactory.lf_core.document_types",
    "lawyerfactory.knowledge_graph": "lawyerfactory.kg.graph",
    "lawyerfactory.mcp_memory_integration": "lawyerfactory.vectors.memory_compression",
    "lawyerfactory.enhanced_workflow": "lawyerfactory.compose.maestro.workflow",
    "lawyerfactory.workflow": "lawyerfactory.compose.maestro.workflow",
    "lawyerfactory.file_storage": "lawyerfactory.infra.file_storage",   # if used
    "lawyerfactory.file-storage": "lawyerfactory.infra.file_storage",   # belt & suspenders

    # maestro core
    "maestro.maestro": "lawyerfactory.compose.maestro.maestro",
    "maestro.enhanced_maestro": "lawyerfactory.compose.maestro.enhanced_maestro",
    "maestro.agent_registry": "lawyerfactory.compose.maestro.registry",
    "maestro.bot_interface": "lawyerfactory.compose.maestro.base",
    "maestro.checkpoint_manager": "lawyerfactory.compose.maestro.checkpoints",
    "maestro.event_system": "lawyerfactory.compose.maestro.events",
    "maestro.error_handling": "lawyerfactory.compose.maestro.errors",
    "maestro.workflow_models": "lawyerfactory.compose.maestro.workflow_models",
    "maestro.maestro_skeletal_outline_bot": "lawyerfactory.outline.integration",
    "maestro.bots.maestro_bot": "lawyerfactory.compose.maestro.maestro_bot",

    # bots
    "maestro.bots.reader_bot": "lawyerfactory.compose.bots.reader",
    "maestro.bots.writer_bot": "lawyerfactory.compose.bots.writer",
    "maestro.bots.legal_editor": "lawyerfactory.compose.bots.editor",
    "maestro.bots.legal_procedure_bot": "lawyerfactory.compose.bots.procedure",
    "maestro.bots.research_bot": "lawyerfactory.compose.bots.research",

    # ingestion
    "src.ingestion.api": "lawyerfactory.ingest",  # generic
    "src.ingestion.api.ingest_server": "lawyerfactory.ingest.server",
    "src.ingestion.api.assessor": "lawyerfactory.ingest.assessors.assessor",
    "src.ingestion.api.ai_document_agent": "lawyerfactory.ingest.pipelines.ai_document_agent",
    "src.ingestion.api.cause_of_action_detector": "lawyerfactory.claims.detect",
    "src.ingestion.api.cause_of_action_definition_engine": "lawyerfactory.claims.cause_of_action_definition_engine",

    # claims
    "src.claims_matrix.claims_matrix_research_api": "lawyerfactory.claims.research_api",
    "src.claims_matrix.comprehensive_claims_matrix_integration": "lawyerfactory.claims.matrix",

    # knowledge graph
    "src.knowledge_graph.api.knowledge_graph": "lawyerfactory.kg.graph_api",
    "src.knowledge_graph.api.jurisdiction_manager": "lawyerfactory.kg.jurisdiction",
    "src.knowledge_graph.api.legal_relationship_detector": "lawyerfactory.kg.relations",
    "src.knowledge_graph.api.knowledge_graph_extensions": "lawyerfactory.kg.extensions",
    "src.knowledge_graph.api.knowledge_graph_integration": "lawyerfactory.kg.integration",
    "src.knowledge_graph.api.enhanced_knowledge_graph": "lawyerfactory.kg.enhanced_graph",
    "src.knowledge_graph": "lawyerfactory.kg",

    # research
    "src.research.legal_research_integration": "lawyerfactory.research.retrievers.integration",
    "src.research.legal_research_cache_manager": "lawyerfactory.research.cache",
    "src.research.legal_authority_validator": "lawyerfactory.research.validate",

    # outline
    "src.skeletal_outline.skeletal_outline_generator": "lawyerfactory.outline.generator",
    "src.skeletal_outline.skeletal_outline_integration": "lawyerfactory.outline.integration_legacy",

    # storage/infra
    "src.storage.api.file_storage": "lawyerfactory.infra.file_storage_api",
    "src.storage": "lawyerfactory.infra",

    # workflow (old api layer)
    "src.workflow.api.enhanced_workflow": "lawyerfactory.compose.maestro.workflow_enhanced",
    "src.workflow.api.workflow": "lawyerfactory.compose.maestro.workflow_api",
    "src.workflow": "lawyerfactory.compose",

    # document generator → export/compose
    "src.document_generator.api.document_export_system": "lawyerfactory.export.renderers.document_export_system",
    "src.document_generator.api.enhanced_draft_processor": "lawyerfactory.compose.strategies.enhanced_draft_processor",
    "src.document_generator.api": "lawyerfactory.export.renderers",
    "src.document_generator": "lawyerfactory.export",

    # top-level one-offs now housed
    "knowledge_graph": "lawyerfactory.kg.graph_root",
    "repository": "lawyerfactory.infra.repository",
    "prompt_chain_orchestrator": "lawyerfactory.compose.maestro.prompt_chain_orchestrator",
    "cascading_decision_tree_engine": "lawyerfactory.compose.strategies.cascading_decision_tree_engine",
    "statement_of_facts_generator": "lawyerfactory.evidence.shotlist",  # canonicalized

    # evidence shotlist canonical target (for future-proofing)
    "lawyerfactory.statement_of_facts_generator": "lawyerfactory.evidence.shotlist",
}

EXCLUDE_DIRS = {
    ".git", ".venv", "venv", "__pycache__", "data", "output", "node_modules",
    "dist", "build", ".mypy_cache", ".pytest_cache", "logs", "misc",
}
FILE_PATTERN = re.compile(r".*\.py$", re.I)

def best_remap(module: str) -> str | None:
    """Return remapped module using longest old-prefix match, else None."""
    candidates = [k for k in MAP.keys() if module == k or module.startswith(k + ".")]
    if not candidates:
        return MAP.get(module)
    longest = max(candidates, key=len)
    new = MAP[longest]
    if module == longest:
        return new
    # preserve the trailing suffix after the matched prefix
    suffix = module[len(longest):]
    if suffix.startswith("."):
        suffix = suffix[1:]
    return f"{new}.{suffix}" if suffix else new

class ImportRewriter(ast.NodeTransformer):
    def __init__(self):
        self.changed = False

    def visit_Import(self, node: ast.Import) -> ast.AST:
        for alias in node.names:
            newname = best_remap(alias.name)
            if newname and newname != alias.name:
                alias.name = newname
                self.changed = True
        return node

    def visit_ImportFrom(self, node: ast.ImportFrom) -> ast.AST:
        # Ignore relative imports (node.level > 0)
        if node.module and node.level == 0:
            newmod = best_remap(node.module)
            if newmod and newmod != node.module:
                node.module = newmod
                self.changed = True
        return node

def iter_py_files(roots):
    for root in roots:
        root = pathlib.Path(root)
        if not root.exists():
            continue
        if root.is_file() and FILE_PATTERN.match(str(root)):
            yield root
            continue
        for p in root.rglob("*.py"):
            if any(part in EXCLUDE_DIRS for part in p.parts):
                continue
            yield p

def rewrite_file(path: pathlib.Path, apply: bool) -> bool:
    src = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return False
    rewriter = ImportRewriter()
    tree = rewriter.visit(tree)
    if not rewriter.changed:
        return False
    new_src = ast.unparse(tree) if hasattr(ast, "unparse") else None
    if new_src is None:
        # Fallback: don’t risk partial writes on older Python
        return False
    if apply:
        path.write_text(new_src, encoding="utf-8")
    return True

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="Write changes to files.")
    ap.add_argument("paths", nargs="*", default=["."], help="Paths to scan (default: repo root).")
    args = ap.parse_args()

    touched = 0
    for f in iter_py_files(args.paths):
        changed = rewrite_file(f, args.apply)
        if changed:
            touched += 1
            rel = os.path.relpath(str(f), os.getcwd())
            print(("[WRITE] " if args.apply else "[DRY ] ") + rel)

    print(f"\nDone. Files updated: {touched} ({'APPLY' if args.apply else 'DRY-RUN'})")
    if not args.apply:
        print("Re-run with --apply to write changes.")

if __name__ == "__main__":
    main()