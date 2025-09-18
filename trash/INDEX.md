# Trash Folder Index

This folder contains files that have been moved during the codebase refactoring process. These files are preserved for reference but are no longer part of the active codebase.

## Moved Files

### Shim Files (Backward Compatibility)
- `enhanced_knowledge_graph.py` - Redirects to `lawyerfactory.kg.enhanced_graph`
- `knowledge_graph.py` - Redirects to `lawyerfactory.kg.graph_api`
- `legal_authority_validator.py` - Redirects to `lawyerfactory.research.validate`
- `legal_research_integration.py` - Redirects to `lawyerfactory.research.retrievers.integration`

### Demo/Utility Files
- `enhanced_categorization_demo.py` - Demonstration script for categorization system
- `kanban_cli.py` - CLI bridge to kanban functionality
- `models.py` - Redirects to `lawyerfactory.lf_core.models`

### Build Artifacts
- `lawyerfactory.egg-info/` - Python package build metadata

### System Files
- `.DS_Store` files - macOS system files

## Refactor Decisions

### Why These Files Were Moved to Trash

1. **Shim Files**: These were created to maintain backward compatibility during refactoring but are no longer needed as the codebase has stabilized.

2. **Demo Files**: Demonstration and example scripts that are not part of the core functionality.

3. **Build Artifacts**: Generated files that should not be in version control.

4. **System Files**: OS-specific files that should not be in version control.

### Preservation Strategy

- Files are moved rather than deleted to preserve any potential value
- All files remain accessible for reference
- No breaking changes to existing functionality
- Future cleanup can remove these files after verification

## Recovery Instructions

To restore any file from trash:

```bash
# Move file back to original location
mv trash/filename.py src/original/path/

# Or copy to a different location
cp trash/filename.py desired/location/
```

## Next Steps

1. Verify that no imports are broken after moving shim files
2. Test core functionality to ensure nothing was disrupted
3. Consider permanent deletion after confirmation
4. Update any documentation referencing moved files

---

*Generated during codebase refactoring on $(date)*