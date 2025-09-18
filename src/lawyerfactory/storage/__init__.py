"""
Consolidated Storage Module for LawyerFactory

This module provides a unified interface to all storage operations across the LawyerFactory system.
It consolidates the triple storage system:

1. Local Storage - Temporary processing and immediate access
2. Cloud Storage - Permanent S3-based object storage
3. Vector Storage - Tokenized content for semantic search and RAG
4. Evidence Storage - Structured data with user editing capabilities

Key Features:
- ObjectID tracking across all storage tiers
- Automatic processing pipeline for uploads
- Research loop integration for new files
- Phase-specific data access patterns
- No bloat, clean integration with existing systems
"""

from typing import Any

from .cloud.base_repository import add_entry, init_repo, list_entries

# Integrated evidence ingestion
from .cloud.cloud_storage_integration import (
    CloudStorageManager,
    IntegratedEvidenceIngestion,
    StorageTier,
)
from .cloud.database_manager import Database

# Evidence ingestion pipeline
from .core.evidence_ingestion import EvidenceIngestionPipeline, integrate_with_intake_processor

# Core unified storage APIs
from .core.unified_storage_api import EnhancedUnifiedStorageAPI, get_enhanced_unified_storage_api
from .evidence.shotlist import ShotlistBuilder

# Evidence storage components
from .evidence.table import EnhancedEvidenceTable, EvidenceType, PrivilegeMarker, RelevanceLevel

# Vector storage components
from .vectors.enhanced_vector_store import (
    EnhancedVectorStoreManager,
    ValidationType,
    VectorStoreType,
)

# Cloud storage components
# from .cloud.s3bucket_temp_serv import app as s3_app  # FastAPI S3 service - commented out due to filename with hyphen
# from .core.enhanced_unified_storage_api import (
#     EnhancedUnifiedStorageAPI,
#     get_enhanced_unified_storage_api,
# )


# from .vectors.llm_rag_integration import LLM_RAG_Integration  # commented out - module not found
# from .vectors.memory_compression import MemoryCompressionManager  # commented out - module not found
# from .vectors.research_integration import ResearchIntegrationManager  # commented out - module not found

# Global instances for easy access
_unified_storage_instance = None
_enhanced_unified_storage_instance = None


def get_unified_storage() -> EnhancedUnifiedStorageAPI:
    """Get the global unified storage API instance"""
    global _unified_storage_instance
    if _unified_storage_instance is None:
        _unified_storage_instance = EnhancedUnifiedStorageAPI()
    return _unified_storage_instance


def get_enhanced_unified_storage() -> EnhancedUnifiedStorageAPI:
    """Get the global enhanced unified storage API instance"""
    global _enhanced_unified_storage_instance
    if _enhanced_unified_storage_instance is None:
        _enhanced_unified_storage_instance = EnhancedUnifiedStorageAPI()
    return _enhanced_unified_storage_instance


# Convenience functions for common operations
async def store_evidence_file(
    file_content: bytes,
    filename: str,
    metadata: dict[str, Any] | None = None,
    source_phase: str = "intake",
):
    """Convenience function to store evidence through the unified pipeline"""
    storage = get_unified_storage()
    return await storage.store_evidence(file_content, filename, metadata, source_phase)


async def retrieve_evidence(object_id: str, target_tier: str | None = None):
    """Convenience function to retrieve evidence from storage"""
    storage = get_unified_storage()
    return await storage.get_evidence(object_id, target_tier)


async def search_evidence(query: str, search_tier: str = "vector"):
    """Convenience function to search evidence across storage tiers"""
    storage = get_unified_storage()
    return await storage.search_evidence(query, search_tier)


# Export all public classes and functions
__all__ = [
    # Core APIs
    "EnhancedUnifiedStorageAPI",
    "get_enhanced_unified_storage_api",
    "get_unified_storage",
    "get_enhanced_unified_storage",
    # Cloud Storage
    "Database",
    "CloudStorageManager",
    "StorageTier",
    "init_repo",
    "add_entry",
    "list_entries",
    # Vector Storage
    "EnhancedVectorStoreManager",
    "VectorStoreType",
    "ValidationType",
    # Evidence Storage
    "EnhancedEvidenceTable",
    "EvidenceType",
    "PrivilegeMarker",
    "RelevanceLevel",
    "ShotlistBuilder",
    # Evidence Processing
    "EvidenceIngestionPipeline",
    "integrate_with_intake_processor",
    # Convenience Functions
    "store_evidence_file",
    "retrieve_evidence",
    "search_evidence",
    # Integrated Evidence Ingestion
    "IntegratedEvidenceIngestion",
]
