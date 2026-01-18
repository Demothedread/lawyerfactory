"""
Compatibility shim for the enhanced unified storage API.
"""

from .core.unified_storage_api import (
    EnhancedUnifiedStorageAPI,
    get_enhanced_unified_storage_api,
)

__all__ = ["EnhancedUnifiedStorageAPI", "get_enhanced_unified_storage_api"]
