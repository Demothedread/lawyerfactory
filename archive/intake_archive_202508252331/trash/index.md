# Trash Index - LawyerFactory Codebase Cleanup

This index tracks files staged for removal during the codebase cleanup process.

## Summary
- **Total files staged**: 821
- **Generated**: 2025-08-22T04:37:11.331173
- **Cleanup phase**: Deduplication and pruning

## Categories of Staged Files

### 1. Deprecated Shims (3 files)
Auto-generated redirect files marked for removal:
- `maestro/bot_interface.py` → redirects to `lawyerfactory.compose.maestro.base`
- `maestro/bots/reader_bot.py` → redirects to `lawyerfactory.compose.bots.reader`
- `maestro/bots/maestro_bot.py` → redirects to `lawyerfactory.compose.maestro.maestro_bot`

### 2. Duplicate Implementations (5 files)
Multiple implementations of the same functionality:
- `src/lawyerfactory/compose/maestro/enhanced_maestro.py` (1645 lines) - DUPLICATE
- `src/lawyerfactory/phases/07_orchestration/maestro/enhanced_maestro.py` (5 lines) - SHIM
- `src/lawyerfactory/file_storage.py` (4 lines) - DUPLICATE
- `src/lawyerfactory/infra/file_storage.py` (109 lines) - DUPLICATE
- `src/lawyerfactory/infra/file_storage_api.py` (323 lines) - DUPLICATE

### 3. Case-Specific Files (107 files)
Tesla litigation case data that doesn't belong in main codebase:
- Legal documents, court filings, evidence files
- Case-specific test data and configurations
- Draft documents and research materials

### 4. Minimal Content Files (706 files)
Files with little to no actual content:
- Empty `__init__.py` files
- Files with only whitespace or comments
- Single-line files with minimal functionality

## Recommended Actions

### Immediate (Safe to remove):
- All deprecated shims (3 files)
- Tesla case-specific directory (107 files)
- Empty/minimal files (706 files)

### Requires Review:
- Duplicate implementations (5 files) - need to choose which version to keep

## Recovery
All staged files are moved to `_trash_staging/` directory with full path preservation.
To recover files, move them back from `_trash_staging/` to their original locations.

## Next Steps
1. Review duplicate implementations to choose canonical versions
2. Remove safe files (shims, case-specific, minimal files)
3. Update import statements to point to canonical implementations
4. Run tests to ensure functionality is preserved