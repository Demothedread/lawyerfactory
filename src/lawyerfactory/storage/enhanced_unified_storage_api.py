rc/lawyerfactory/storage/enhanced_unified_storage_api.py</path>
<content">
Enhanced Unified Storage API for LawyerFactory

This module provides an enhanced unified storage system that incorporates:
- Blob storage abstractions (S3 and Local) from enhanced vector store
- Three-tier storage: S3 Raw → Evidence Table → Vector Store
- ObjectID tracking across all storage tiers
- Automatic processing pipeline for uploads
- Research loop integration for new files

Key Features:
- ObjectID tracking across all storage tiers
- Automatic processing through all storage systems
- Clean integration with existing components
- Research loop support for new files
- No bloat, modular design for troubleshooting
"

import asyncio
import json
import logging
import uuid
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

# Import blob storage abstractions from enhanced vector store
try:
    from lawyerfactory.vectors.enhanced_vector_store import (
        BlobStore, LocalDirBlobStore, S3BlobStore,
        VectorStoreType, ValidationType
    )
    BLOB_STORE_AVAILABLE = True
except ImportError:
    BLOB_STORE_AVAILABLE = False
    logger.warning("Blob storage abstractions not available")

logger = logging.getLogger(__name__)


@dataclass
class StorageResult:
    """Result of a storage operation"""
    success: bool
    object_id: str
    s3_url: Optional[str] = None
    evidence_id: Optional[str] = None
    vector_ids: List[str] = field(default_factory=list)
    error: Optional[str] = None
    processing_time: float = 0.0


@dataclass
class EvidenceMetadata:
    """Enhanced metadata for evidence storage"""
    object_id: str
    original_filename: str
    content_type: str
    file_size: int
    upload_timestamp: datetime
    source_phase: str
    user_id: Optional[str] = None
    case_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    custom_metadata: Dict[str, Any] = field(default_factory=dict)


class EnhancedUnifiedStorageAPI:
    """
    Enhanced Unified Storage API that coordinates all storage operations across LawyerFactory.

    This is the single entry point for all storage operations, ensuring:
    - Consistent ObjectID tracking across all tiers
    - Automatic processing through all storage systems
    - Clean integration with existing components
    - Research loop support for new files
    """

    def __init__(self, storage_path: str = "data/storage"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Initialize blob storage (S3 or Local)
        self.blob_store = self._initialize_blob_store()

        # Initialize storage tier clients
        self.s3_client = None
        self.evidence_table = None
        self.vector_store = None

        # ObjectID registry for tracking
        self.object_registry_path = self.storage_path / "object_registry.json"
        self.object_registry = self._load_object_registry()

        logger.info("Enhanced Unified Storage API initialized")

    def _initialize_blob_store(self) -> Optional[BlobStore]:
        """Initialize blob storage based on configuration"""
        if not BLOB_STORE_AVAILABLE:
            logger.warning("Blob store not available, using None")
            return None

        # Check for S3 configuration
        s3_bucket = os.getenv("LF_S3_BUCKET")
        s3_region = os.getenv("LF_S3_REGION")
        s3_prefix = os.getenv("LF_S3_PREFIX", "lawyerfactory")

        if s3_bucket:
            try:
                return S3BlobStore(bucket=s3_bucket, region=s3_region, base_prefix=s3_prefix)
            except Exception as e:
                logger.warning(f"Failed to initialize S3 blob store: {e}")

        # Default to local directory storage
        local_dir = Path(os.getenv("LF_LOCAL_UPLOAD_DIR", "uploads"))
        return LocalDirBlobStore(base_path=local_dir)

    def _load_object_registry(self) -> Dict[str, Dict[str, Any]]:
        """Load the object registry from disk"""
        if self.object_registry_path.exists():
            try:
                with open(self.object_registry_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load object registry: {e}")
        return {}

    def _save_object_registry(self):
        """Save the object registry to disk"""
        try:
            with open(self.object_registry_path, 'w', encoding='utf-8') as f:
                json.dump(self.object_registry, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save object registry: {e}")

    def register_storage_client(self, client_type: str, client):
        """Register a storage tier client"""
        if client_type == "s3":
            self.s3_client = client
        elif client_type == "evidence":
            self.evidence_table = client
        elif client_type == "vector":
            self.vector_store = client
        else:
            logger.warning(f"Unknown client type: {client_type}")

    def _build_object_key(self, filename: str, store_type: str, metadata: Dict[str, Any]) -> str:
        """Create a directory-like key: {store_type}/{case_id|unknown}/{YYYY}/{MM}/{uuid}_{filename}"""
        today = datetime.now()
        case_id = str(metadata.get("case_id") or metadata.get("matter_id") or "unknown")
        safe_name = filename.replace(os.sep, "_")
        return f"{store_type}/{case_id}/{today.year:04d}/{today.month:02d}/{uuid.uuid4()}_{safe_name}"

    async def store_evidence(self, file_content: bytes, filename: str,
                           metadata: Optional[Dict[str, Any]] = None,
                           source_phase: str = "intake") -> StorageResult:
        """
        Store evidence through the unified pipeline

        Args:
            file_content: Raw file content as bytes
            filename: Original filename
            metadata: Additional metadata for the evidence
            source_phase: Which phase this evidence comes from

        Returns:
            StorageResult with operation details
        """
        start_time = datetime.now()
        object_id = str(uuid.uuid4())

        try:
            # Create evidence metadata
            evidence_metadata = EvidenceMetadata(
                object_id=object_id,
                original_filename=filename,
                content_type=self._guess_content_type(filename),
                file_size=len(file_content),
                upload_timestamp=datetime.now(),
                source_phase=source_phase,
                custom_metadata=metadata or {}
            )

            # Process through all three storage tiers
            s3_result = await self._store_in_s3(file_content, evidence_metadata)
            evidence_result = await self._store_in_evidence_table(file_content, evidence_metadata)
            vector_result = await self._store_in_vector_store(file_content, evidence_metadata)

            # Register the object
            self.object_registry[object_id] = {
                "metadata": evidence_metadata.__dict__,
                "s3_url": s3_result.get("url"),
                "evidence_id": evidence_result.get("evidence_id"),
                "vector_ids": vector_result.get("vector_ids", []),
                "created_at": datetime.now().isoformat(),
                "source_phase": source_phase
            }
            self._save_object_registry()

            processing_time = (datetime.now() - start_time).total_seconds()

            return StorageResult(
                success=True,
                object_id=object_id,
                s3_url=s3_result.get("url"),
                evidence_id=evidence_result.get("evidence_id"),
                vector_ids=vector_result.get("vector_ids", []),
                processing_time=processing_time
            )

        except Exception as e:
            logger.error(f"Failed to store evidence {object_id}: {e}")
            return StorageResult(
                success=False,
                object_id=object_id,
                error=str(e),
                processing_time=(datetime.now() - start_time).total_seconds()
            )

    async def get_evidence(self, object_id: str, target_tier: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve evidence from the unified storage system

        Args:
            object_id: The ObjectID to retrieve
            target_tier: Specific tier to retrieve from ("s3", "evidence", "vector")

        Returns:
            Evidence data from requested tier(s)
        """
        if object_id not in self.object_registry:
            return {"error": "ObjectID not found"}

        registry_entry = self.object_registry[object_id]

        result = {
            "object_id": object_id,
            "metadata": registry_entry.get("metadata", {}),
            "available_tiers": []
        }

        try:
            if target_tier == "s3" or target_tier is None:
                if self.blob_store and registry_entry.get("s3_url"):
                    s3_data = await self._get_from_s3(registry_entry["s3_url"])
                    if s3_data:
                        result["s3_data"] = s3_data
                        result["available_tiers"].append("s3")

            if target_tier == "evidence" or target_tier is None:
                if self.evidence_table and registry_entry.get("evidence_id"):
                    evidence_data = await self._get_from_evidence_table(registry_entry["evidence_id"])
                    if evidence_data:
                        result["evidence_data"] = evidence_data
                        result["available_tiers"].append("evidence")

            if target_tier == "vector" or target_tier is None:
                if self.vector_store and registry_entry.get("vector_ids"):
                    vector_data = await self._get_from_vector_store(registry_entry["vector_ids"])
                    if vector_data:
                        result["vector_data"] = vector_data
                        result["available_tiers"].append("vector")

        except Exception as e:
            logger.error(f"Failed to retrieve evidence {object_id}: {e}")
            result["error"] = str(e)

        return result

    async def search_evidence(self, query: str, search_tier: str = "vector") -> List[Dict[str, Any]]:
        """
        Search for evidence across storage tiers

        Args:
            query: Search query
            search_tier: Which tier to search in ("vector" is most common)

        Returns:
            List of matching evidence with ObjectIDs
        """
        results = []

        try:
            if search_tier == "vector" and self.vector_store:
                vector_results = await self._search_vector_store(query)
                for vector_result in vector_results:
                    vector_id = vector_result.get("vector_id")
                    # Find ObjectID from vector_id
                    for obj_id, registry_entry in self.object_registry.items():
                        if vector_id in registry_entry.get("vector_ids", []):
                            results.append({
                                "object_id": obj_id,
                                "metadata": registry_entry.get("metadata", {}),
                                "relevance_score": vector_result.get("score", 0.0),
                                "vector_data": vector_result
                            })
                            break

            elif search_tier == "evidence" and self.evidence_table:
                evidence_results = await self._search_evidence_table(query)
                for evidence_result in evidence_results:
                    evidence_id = evidence_result.get("evidence_id")
                    # Find ObjectID from evidence_id
                    for obj_id, registry_entry in self.object_registry.items():
                        if registry_entry.get("evidence_id") == evidence_id:
                            results.append({
                                "object_id": obj_id,
                                "metadata": registry_entry.get("metadata", {}),
                                "evidence_data": evidence_result
                            })
                            break

        except Exception as e:
            logger.error(f"Failed to search evidence: {e}")

        return results

    def _guess_content_type(self, filename: str) -> str:
        """Guess content type from filename"""
        import mimetypes
        content_type, _ = mimetypes.guess_type(filename)
        return content_type or "application/octet-stream"

    # Placeholder methods for storage tier operations
    # These will be implemented when integrating with actual storage clients

    async def _store_in_s3(self, file_content: bytes, metadata: EvidenceMetadata) -> Dict[str, Any]:
        """Store file in S3 tier using blob store"""
        if not self.blob_store:
            return {"error": "Blob store not available"}
        try:
            key = self._build_object_key(metadata.original_filename, "s3", metadata.custom_metadata)
            locator = self.blob_store.put_bytes(key, file_content, metadata.content_type)
            return {"url": locator, "key": key}
        except Exception as e:
            logger.error(f"S3 storage failed: {e}")
            return {"error": str(e)}

    async def _store_in_evidence_table(self, file_content: bytes, metadata: EvidenceMetadata) -> Dict[str, Any]:
        """Store structured data in evidence table"""
        if not self.evidence_table:
            return {"error": "Evidence table client not registered"}
        # Implementation will call actual evidence table client
        return {"evidence_id": f"evidence_{metadata.object_id}"}

    async def _store_in_vector_store(self, file_content: bytes, metadata: EvidenceMetadata) -> Dict[str, Any]:
        """Store vectorized content in vector store"""
        if not self.vector_store:
            return {"error": "Vector store client not registered"}
        # Implementation will call actual vector store client
        return {"vector_ids": [f"vector_{metadata.object_id}"]}

    async def _get_from_s3(self, s3_url: str) -> Optional[bytes]:
        """Retrieve file from S3"""
        if not self.blob_store:
            return None
        try:
            # Extract key from URL - this is a simplified implementation
            if s3_url.startswith("s3://"):
                # For S3 URLs, we'd need to implement proper retrieval
                return b"file_content_from_s3"
            else:
                # For local files, we could read from disk
                return b"file_content_from_local"
        except Exception as e:
            logger.error(f"S3 retrieval failed for {s3_url}: {e}")
            return None

    async def _get_from_evidence_table(self, evidence_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve structured data from evidence table"""
        if not self.evidence_table:
            return None
        # Implementation will call actual evidence table client
        return {"evidence_data": "from_table"}

    async def _get_from_vector_store(self, vector_ids: List[str]) -> Optional[Dict[str, Any]]:
        """Retrieve vectorized content from vector store"""
        if not self.vector_store:
            return None
        # Implementation will call actual vector store client
        return {"vector_data": "from_store"}

    async def _search_vector_store(self, query: str) -> List[Dict[str, Any]]:
        """Search vector store"""
        if not self.vector_store:
            return []
        # Implementation will call actual vector store client
        return [{"vector_id": "vector_123", "score": 0.95}]

    async def _search_evidence_table(self, query: str) -> List[Dict[str, Any]]:
        """Search evidence table"""
        if not self.evidence_table:
            return []
        # Implementation will call actual evidence table client
        return [{"evidence_id": "evidence_123"}]


# Global instance for easy access
_enhanced_unified_storage_instance = None

def get_enhanced_unified_storage_api() -> EnhancedUnifiedStorageAPI:
    """Get the global enhanced unified storage API instance"""
    global _enhanced_unified_storage_instance
    if _enhanced_unified_storage_instance is None:
        _enhanced_unified_storage_instance = EnhancedUnifiedStorageAPI()
    return _enhanced_unified_storage_instance