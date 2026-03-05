#!/usr/bin/env python3
"""Test script to verify core imports work correctly (syntax only - no ML deps)."""

from pathlib import Path
import py_compile
import sys

print('Testing Python syntax and module structure...')
print('=' * 50)

# Key files to check
files_to_check = [
    'src/lawyerfactory/claims/matrix.py',
    'src/lawyerfactory/kg/graph_api.py',
    'src/lawyerfactory/compose/maestro/enhanced_maestro.py',
    'src/lawyerfactory/compose/maestro/workflow_enhanced.py',
    'src/lawyerfactory/phases/phaseA03_outline/claims_matrix.py',
    'src/lawyerfactory/phases/phaseA03_outline/claims/cause_of_action_definition_engine.py',
    'src/lawyerfactory/outline/integration_legacy.py',
    'src/lawyerfactory/knowledge_graph/core/enhanced_graph.py',
    'src/lawyerfactory/research/retrievers/integration.py',
    'apps/api/server.py',
]

passed = 0
failed = 0
errors = []

for filepath in files_to_check:
    try:
        py_compile.compile(filepath, doraise=True)
        print(f'✓ {filepath}')
        passed += 1
    except py_compile.PyCompileError as e:
        print(f'✗ {filepath}: {e}')
        errors.append((filepath, str(e)))
        failed += 1

print('=' * 50)
print(f'Results: {passed}/{passed+failed} files have valid syntax')

if errors:
    print('\nFiles with syntax errors:')
    for name, error in errors:
        print(f'  - {name}')
    sys.exit(1)
else:
    print('\nAll key files have valid Python syntax!')
    sys.exit(0)
