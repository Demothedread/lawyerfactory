#!/usr/bin/env python3
"""
streamlined_move_script.py — Intelligent codebase reorganization for LawyerFactory.

This script implements a streamlined organization strategy that:
1. Preserves the excellent phase-based workflow structure
2. Consolidates infrastructure components
3. Reorganizes agents by function rather than arbitrary groupings
4. Removes clutter and duplication
5. Creates a clean, maintainable codebase structure

Usage:
  python streamlined_move_script.py --dry-run  # Preview all moves
  python streamlined_move_script.py --apply    # Execute moves
  python streamlined_move_script.py --phase 1  # Execute only phase 1 moves
"""

import json
import os
import shutil
from pathlib import Path
from typing import Dict, List, Tuple

# Streamlined migration mapping - preserves what's working, fixes what's broken
STREAMLINED_MIGRATION = {
    # Infrastructure consolidation - merge scattered components
    "src/lawyerfactory/infra/file_storage.py": "src/lawyerfactory/infrastructure/storage/file_storage_manager.py",
    "src/lawyerfactory/infra/file_storage_api.py": "src/lawyerfactory/infrastructure/storage/file_storage_api.py",
    "src/lawyerfactory/infra/databases.py": "src/lawyerfactory/infrastructure/storage/database_manager.py",
    "src/lawyerfactory/infra/repository.py": "src/lawyerfactory/infrastructure/storage/base_repository.py",
    "lawyerfactory/file-storage.py": "src/lawyerfactory/infrastructure/storage/legacy_file_storage.py",

    # Knowledge Graph consolidation - unify scattered KG components
    "src/knowledge_graph/api/jurisdiction_manager.py": "src/lawyerfactory/knowledge_graph/core/jurisdiction_manager.py",
    "src/knowledge_graph/api/knowledge_graph.py": "src/lawyerfactory/knowledge_graph/core/knowledge_graph.py",
    "src/knowledge_graph/api/legal_relationship_detector.py": "src/lawyerfactory/knowledge_graph/core/legal_relationship_detector.py",
    "src/lawyerfactory/kg/enhanced_graph.py": "src/lawyerfactory/knowledge_graph/core/enhanced_graph.py",
    "src/lawyerfactory/kg/graph_api.py": "src/lawyerfactory/knowledge_graph/api/graph_api.py",
    "src/lawyerfactory/kg/graph_root.py": "src/lawyerfactory/knowledge_graph/core/graph_builder.py",
    "src/lawyerfactory/kg/graph.py": "src/lawyerfactory/knowledge_graph/core/graph_integration.py",
    "src/lawyerfactory/kg/jurisdiction.py": "src/lawyerfactory/knowledge_graph/core/jurisdiction_service.py",
    "src/lawyerfactory/kg/legal_authorities.py": "src/lawyerfactory/knowledge_graph/core/legal_authorities.py",
    "src/lawyerfactory/kg/relations.py": "src/lawyerfactory/knowledge_graph/core/relations.py",
    "src/lawyerfactory/kg/integration.py": "src/lawyerfactory/knowledge_graph/integrations/integration.py",

    # Agent reorganization - group by function, not arbitrary structure
    "src/lawyerfactory/compose/bots/caselaw_researcher.py": "src/lawyerfactory/agents/research/caselaw_researcher.py",
    "src/lawyerfactory/compose/bots/citation_formatter.py": "src/lawyerfactory/agents/research/citation_formatter.py",
    "src/lawyerfactory/compose/bots/research.py": "src/lawyerfactory/agents/research/research.py",
    "src/lawyerfactory/compose/bots/rules_of_law.py": "src/lawyerfactory/agents/research/rules_of_law.py",
    "src/lawyerfactory/compose/bots/civil_procedure_specialist.py": "src/lawyerfactory/agents/drafting/civil_procedure_specialist.py",
    "src/lawyerfactory/compose/bots/editor.py": "src/lawyerfactory/agents/drafting/editor.py",
    "src/lawyerfactory/compose/bots/procedure.py": "src/lawyerfactory/agents/drafting/procedure.py",
    "src/lawyerfactory/compose/bots/writer.py": "src/lawyerfactory/agents/drafting/writer.py",
    "src/lawyerfactory/compose/bots/fact_objectivity_agent.py": "src/lawyerfactory/agents/analysis/fact_objectivity_agent.py",
    "src/lawyerfactory/compose/bots/issuespotter.py": "src/lawyerfactory/agents/analysis/issuespotter.py",
    "src/lawyerfactory/compose/bots/legal_claim_validator.py": "src/lawyerfactory/agents/analysis/legal_claim_validator.py",
    "src/lawyerfactory/compose/bots/legal_validation_agent.py": "src/lawyerfactory/agents/review/legal_validation_agent.py",
    "src/lawyerfactory/compose/bots/reader.py": "src/lawyerfactory/agents/intake/reader.py",

    # Maestro consolidation - keep the best implementation
    "src/lawyerfactory/compose/maestro/enhanced_maestro.py": "src/lawyerfactory/phases/07_orchestration/maestro.py",
    "src/lawyerfactory/compose/maestro/base.py": "src/lawyerfactory/phases/07_orchestration/base_maestro.py",
    "src/lawyerfactory/compose/maestro/maestro.py": "src/lawyerfactory/phases/07_orchestration/workflow_engine.py",
    "src/lawyerfactory/compose/maestro/maestro_bot.py": "src/lawyerfactory/phases/07_orchestration/maestro_bot.py",
    "src/lawyerfactory/compose/maestro/workflow_models.py": "src/lawyerfactory/phases/07_orchestration/workflow_models.py",
    "src/lawyerfactory/compose/maestro/workflow_api.py": "src/lawyerfactory/phases/07_orchestration/workflow_api.py",
    "src/lawyerfactory/compose/maestro/events.py": "src/lawyerfactory/phases/07_orchestration/events.py",
    "src/lawyerfactory/compose/maestro/errors.py": "src/lawyerfactory/phases/07_orchestration/error_handler.py",
    "src/lawyerfactory/compose/maestro/checkpoints.py": "src/lawyerfactory/phases/07_orchestration/state_manager.py",
    "src/lawyerfactory/compose/maestro/compat_wrappers.py": "src/lawyerfactory/phases/07_orchestration/compatibility.py",

    # Phase-specific improvements - keep the good structure, improve organization
    "src/lawyerfactory/phases/phaseA01_intake/evidence/table.py": "src/lawyerfactory/phases/phaseA01_intake/evidence_table.py",
    "src/lawyerfactory/phases/phaseA01_intake/ingestion/assessor.py": "src/lawyerfactory/phases/phaseA01_intake/assessor.py",
    "src/lawyerfactory/phases/phaseA01_intake/ingestion/knowledge_graph_extensions.py": "src/lawyerfactory/phases/phaseA01_intake/kg_extensions.py",
    "src/lawyerfactory/phases/phaseA01_intake/ingestion/server.py": "src/lawyerfactory/phases/phaseA01_intake/intake_server.py",

    "src/lawyerfactory/phases/02_research/agents/research_bot.py": "src/lawyerfactory/phases/02_research/research_bot.py",
    "src/lawyerfactory/phases/02_research/retrievers/cache.py": "src/lawyerfactory/phases/02_research/cache.py",
    "src/lawyerfactory/phases/02_research/retrievers/integration.py": "src/lawyerfactory/phases/02_research/retriever_integration.py",

    "src/lawyerfactory/claims/matrix.py": "src/lawyerfactory/phases/03_outline/claims_matrix.py",
    "src/lawyerfactory/phases/03_outline/claims/cause_of_action_definition_engine.py": "src/lawyerfactory/phases/03_outline/cause_of_action_engine.py",
    "src/lawyerfactory/phases/03_outline/claims/detect.py": "src/lawyerfactory/phases/03_outline/claims_detector.py",
    "src/lawyerfactory/phases/03_outline/claims/research_api.py": "src/lawyerfactory/phases/03_outline/research_api.py",
    "src/lawyerfactory/phases/03_outline/outline/generator.py": "src/lawyerfactory/phases/03_outline/outline_generator.py",
    "src/lawyerfactory/phases/03_outline/outline/integration.py": "src/lawyerfactory/phases/03_outline/outline_integration.py",
    "src/lawyerfactory/phases/03_outline/shotlist/shotlist.py": "src/lawyerfactory/phases/03_outline/shotlist_generator.py",

    "src/lawyerfactory/phases/05_drafting/generator/editor_bot.py": "src/lawyerfactory/phases/05_drafting/editor_bot.py",
    "src/lawyerfactory/phases/05_drafting/generator/procedure_bot.py": "src/lawyerfactory/phases/05_drafting/procedure_bot.py",
    "src/lawyerfactory/phases/05_drafting/generator/writer_bot.py": "src/lawyerfactory/phases/05_drafting/writer_bot.py",
    "src/lawyerfactory/phases/05_drafting/promptkits/prompt_deconstruction.py": "src/lawyerfactory/phases/05_drafting/prompt_deconstruction.py",
    "src/lawyerfactory/phases/05_drafting/promptkits/prompt_integration.py": "src/lawyerfactory/phases/05_drafting/prompt_integration.py",

    "src/lawyerfactory/post_production/citations.py": "src/lawyerfactory/phases/06_post_production/citations.py",
    "src/lawyerfactory/post_production/pdf_generator.py": "src/lawyerfactory/phases/06_post_production/pdf_generator.py",
    "src/lawyerfactory/post_production/verification.py": "src/lawyerfactory/phases/06_post_production/verification.py",
    "src/lawyerfactory/phases/06_post_production/formatters/document_export_system.py": "src/lawyerfactory/phases/06_post_production/document_export_system.py",
    "src/lawyerfactory/phases/06_post_production/formatters/legal_document_templates.py": "src/lawyerfactory/phases/06_post_production/document_templates.py",
    "src/lawyerfactory/phases/06_post_production/validators/cascading_decision_tree_engine.py": "src/lawyerfactory/phases/06_post_production/cascading_decision_tree.py",
    "src/lawyerfactory/phases/06_post_production/validators/legal_authority_validator.py": "src/lawyerfactory/phases/06_post_production/legal_authority_validator.py",

    # UI and API reorganization
    "apps/ui/templates/attorney_review_interface.py": "src/lawyerfactory/phases/04_human_review/attorney_review_interface.py",
    "src/lawyerfactory/ui/legal_intake_form.py": "src/lawyerfactory/phases/phaseA01_intake/legal_intake_form.py",
    "src/lawyerfactory/ui/orchestration_dashboard.py": "src/lawyerfactory/phases/07_orchestration/orchestration_dashboard.py",
    "apps/api/routes/evidence.py": "src/lawyerfactory/phases/phaseA01_intake/evidence_routes.py",
}

def create_directories_for_file(filepath: Path):
    """Create all necessary directories for a file path"""
    filepath.parent.mkdir(parents=True, exist_ok=True)

def update_imports_in_file(filepath: Path, old_path: str, new_path: str):
    """Update import statements in a file after moving"""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Convert paths to module paths
        old_module = old_path.replace('/', '.').replace('.py', '')
        new_module = new_path.replace('/', '.').replace('.py', '')

        # Update import statements
        updated_content = content
        patterns = [
            f"from {old_module} import",
            f"import {old_module}",
            f"from .{old_module} import",
            f"from ..{old_module} import",
        ]

        for pattern in patterns:
            if pattern in updated_content:
                new_pattern = pattern.replace(old_module, new_module)
                updated_content = updated_content.replace(pattern, new_pattern)

        # Write back if changed
        if updated_content != content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            return True
        return False

    except Exception as e:
        print(f"Error updating imports in {filepath}: {e}")
        return False

def move_file(source: Path, destination: Path, dry_run: bool = True) -> Tuple[bool, str]:
    """Move a file from source to destination"""
    try:
        if not source.exists():
            return False, f"Source file does not exist: {source}"

        # Create destination directory
        create_directories_for_file(destination)

        if dry_run:
            return True, f"Would move {source} -> {destination}"

        # Copy file to new location
        shutil.copy2(source, destination)
        print(f"✓ Moved {source} -> {destination}")
        return True, f"Moved {source} -> {destination}"

    except Exception as e:
        return False, f"Error moving {source} to {destination}: {e}"

def find_files_importing_module(module_path: str) -> List[Path]:
    """Find all files that import a specific module"""
    importing_files = []
    module_name = module_path.replace('/', '.').replace('.py', '')

    for py_file in Path('.').rglob('*.py'):
        try:
            with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                if module_name in content and py_file.exists():
                    importing_files.append(py_file)
        except Exception:
            continue

    return importing_files

def execute_migration_phase(phase: int, dry_run: bool = True) -> Dict[str, any]:
    """Execute a specific migration phase"""
    results = {
        'phase': phase,
        'moved_files': [],
        'errors': [],
        'import_updates': []
    }

    # Phase-specific file mappings
    phase_mappings = {
        1: {k: v for k, v in STREAMLINED_MIGRATION.items() if 'infrastructure' in v or 'knowledge_graph' in v},
        2: {k: v for k, v in STREAMLINED_MIGRATION.items() if 'orchestration' in v and 'maestro' in v},
        3: {k: v for k, v in STREAMLINED_MIGRATION.items() if any(f'0{phase}' in v for phase in range(1, 8))},
        4: {k: v for k, v in STREAMLINED_MIGRATION.items() if 'agents' in v},
        5: {k: v for k, v in STREAMLINED_MIGRATION.items() if 'ui' in v or 'api' in v},
    }

    mappings = phase_mappings.get(phase, {})

    for old_path, new_path in mappings.items():
        old_file = Path(old_path)
        new_file = Path(new_path)

        if old_file.exists():
            # Move the file
            moved, message = move_file(old_file, new_file, dry_run)
            if moved:
                results['moved_files'].append({
                    'from': old_path,
                    'to': new_path,
                    'message': message
                })

                # Find and update files that import this module
                if not dry_run:
                    importing_files = find_files_importing_module(old_path)
                    for importing_file in importing_files:
                        if update_imports_in_file(importing_file, old_path, new_path):
                            results['import_updates'].append(str(importing_file))
            else:
                results['errors'].append(message)
        else:
            results['errors'].append(f"Source file not found: {old_path}")

    return results

def create_directory_structure(dry_run: bool = True):
    """Create the new directory structure"""
    directories = [
        "src/lawyerfactory/config",
        "src/lawyerfactory/shared",
        "src/lawyerfactory/infrastructure/storage",
        "src/lawyerfactory/infrastructure/messaging",
        "src/lawyerfactory/infrastructure/monitoring",
        "src/lawyerfactory/knowledge_graph/core",
        "src/lawyerfactory/knowledge_graph/integrations",
        "src/lawyerfactory/knowledge_graph/models",
        "src/lawyerfactory/knowledge_graph/api",
        "src/lawyerfactory/agents/base",
        "src/lawyerfactory/agents/intake",
        "src/lawyerfactory/agents/research",
        "src/lawyerfactory/agents/analysis",
        "src/lawyerfactory/agents/drafting",
        "src/lawyerfactory/agents/review",
        "src/lawyerfactory/agents/post_processing",
        "src/lawyerfactory/services",
        "src/lawyerfactory/models",
        "src/lawyerfactory/api/routes",
        "docs/architecture",
        "docs/api",
        "docs/guides",
        "docs/legal",
        "_trash_staging",
    ]

    for dir_path in directories:
        path = Path(dir_path)
        if dry_run:
            print(f"Would create directory: {path}")
        else:
            path.mkdir(parents=True, exist_ok=True)
            print(f"✓ Created directory: {path}")

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Streamlined codebase reorganization')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without executing')
    parser.add_argument('--apply', action='store_true', help='Execute the migration')
    parser.add_argument('--phase', type=int, choices=[1, 2, 3, 4, 5], help='Execute specific phase only')
    parser.add_argument('--all-phases', action='store_true', help='Execute all phases')
    parser.add_argument('--create-dirs', action='store_true', help='Create directory structure')

    args = parser.parse_args()

    if not any([args.dry_run, args.apply, args.all_phases, args.phase, args.create_dirs]):
        args.dry_run = True  # Default to dry run

    if args.create_dirs:
        print("Creating directory structure...")
        create_directory_structure(dry_run=args.dry_run)
        return

    if args.phase:
        print(f"Executing streamlined migration phase {args.phase}...")
        results = execute_migration_phase(args.phase, dry_run=args.dry_run)
        print(f"Phase {args.phase} completed:")
        print(f"  - Files moved: {len(results['moved_files'])}")
        print(f"  - Errors: {len(results['errors'])}")
        print(f"  - Import updates: {len(results['import_updates'])}")

    elif args.all_phases:
        for phase in range(1, 6):
            print(f"\nExecuting streamlined migration phase {phase}...")
            results = execute_migration_phase(phase, dry_run=args.dry_run)
            print(f"Phase {phase} completed:")
            print(f"  - Files moved: {len(results['moved_files'])}")
            print(f"  - Errors: {len(results['errors'])}")
            print(f"  - Import updates: {len(results['import_updates'])}")

    else:
        # Show summary of all planned moves
        print("Streamlined Migration Summary:")
        print(f"Total files to move: {len(STREAMLINED_MIGRATION)}")

        for phase in range(1, 6):
            phase_mappings = {
                1: {k: v for k, v in STREAMLINED_MIGRATION.items() if 'infrastructure' in v or 'knowledge_graph' in v},
                2: {k: v for k, v in STREAMLINED_MIGRATION.items() if 'orchestration' in v and 'maestro' in v},
                3: {k: v for k, v in STREAMLINED_MIGRATION.items() if any(f'0{phase}' in v for phase in range(1, 8))},
                4: {k: v for k, v in STREAMLINED_MIGRATION.items() if 'agents' in v},
                5: {k: v for k, v in STREAMLINED_MIGRATION.items() if 'ui' in v or 'api' in v},
            }
            mappings = phase_mappings.get(phase, {})
            print(f"Phase {phase}: {len(mappings)} files")

if __name__ == '__main__':
    main()