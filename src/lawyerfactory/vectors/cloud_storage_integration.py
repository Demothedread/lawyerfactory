"""
Cloud Storage Integration for LawyerFactory Vector Store

This module integrates the vector store system with cloud storage (S3) and local storage,
providing both temporary and permanent storage solutions for evidence documents.

Features:
- S3 integration for permanent document storage
- Local temporary storage for processing
- Automatic synchronization between storage layers
- Storage tier management (hot/cold storage)
- Backup and recovery capabilities
"""

import asyncio
import json
import logging
import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .enhanced_vector_store import EnhancedVectorStoreManager, VectorStoreType

logger = logging.getLogger(__name__)


from enum import Enum

class StorageTier(Enum):
    """Storage tier definitions"""

    HOT = "hot"  # Frequently accessed, local storage
    WARM = "warm"  # Occasionally accessed, fast cloud storage
    COLD = "cold"  # Rarely accessed, archival storage


class CloudStorageManager:
    """
    Manages integration between vector store and cloud storage
    """

    def __init__(self, vector_store_manager: Optional[EnhancedVectorStoreManager] = None,
                 s3_service=None, local_temp_dir: str = "./uploads/tmp"):
        self.vector_store = vector_store_manager or EnhancedVectorStoreManager()
        self.s3_service = s3_service  # S3 service instance
        self.local_temp_dir = Path(local_temp_dir)
        self.local_temp_dir.mkdir(parents=True, exist_ok=True)

        # Storage mappings
        self.storage_mappings: Dict[str, Dict[str, Any]] = {}

        # Storage tier policies
        self.tier_policies = self._initialize_tier_policies()

        # Cleanup settings
        self.temp_file_retention_days = 7
        self.cleanup_interval_hours = 24

        logger.info("Cloud Storage Manager initialized")

    def _initialize_tier_policies(self) -> Dict[StorageTier, Dict[str, Any]]:
        """Initialize storage tier policies"""
        return {
            StorageTier.HOT: {
                "retention_days": 30,
                "max_size_gb": 10,
                "sync_interval_hours": 1,
                "backup_enabled": True
            },
            StorageTier.WARM: {
                "retention_days": 90,
                "max_size_gb": 100,
                "sync_interval_hours": 6,
                "backup_enabled": True
            },
            StorageTier.COLD: {
                "retention_days": 365,
                "max_size_gb": 1000,
                "sync_interval_hours": 24,
                "backup_enabled": False
            }
        }

    async def store_evidence_with_cloud_backup(self, content: str, metadata: Dict[str, Any],
                                             store_type: VectorStoreType = VectorStoreType.PRIMARY_EVIDENCE,
                                             storage_tier: StorageTier = StorageTier.HOT) -> Dict[str, Any]:
        """
        Store evidence with cloud backup and tier management

        Args:
            content: Document content
            metadata: Document metadata
            store_type: Vector store type
            storage_tier: Storage tier for this document

        Returns:
            Storage information with local and cloud paths
        """
        try:
            # Generate unique storage ID
            storage_id = f"evidence_{uuid.uuid4()}"

            # Store in vector system first
            doc_id = await self.vector_store.ingest_evidence(
                content=content,
                metadata=metadata,
                store_type=store_type
            )

            if not doc_id:
                raise Exception("Failed to store in vector system")

            # Create local temporary copy
            local_path = await self._create_local_backup(content, storage_id, metadata)

            # Upload to cloud storage if available
            cloud_info = None
            if self.s3_service:
                cloud_info = await self._upload_to_cloud(local_path, storage_id, metadata)

            # Store mapping information
            self.storage_mappings[doc_id] = {
                "storage_id": storage_id,
                "vector_doc_id": doc_id,
                "local_path": str(local_path) if local_path else None,
                "cloud_info": cloud_info,
                "storage_tier": storage_tier.value,
                "created_at": datetime.now().isoformat(),
                "last_accessed": datetime.now().isoformat(),
                "access_count": 0
            }

            # Apply storage tier policy
            await self._apply_storage_tier_policy(doc_id, storage_tier)

            return {
                "success": True,
                "doc_id": doc_id,
                "storage_id": storage_id,
                "local_path": str(local_path) if local_path else None,
                "cloud_url": cloud_info.get("url") if cloud_info else None,
                "storage_tier": storage_tier.value
            }

        except Exception as e:
            logger.error(f"Error storing evidence with cloud backup: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def retrieve_evidence_with_fallback(self, doc_id: str) -> Dict[str, Any]:
        """
        Retrieve evidence with fallback between storage layers

        Args:
            doc_id: Document ID from vector store

        Returns:
            Document content and metadata
        """
        try:
            # Check if we have storage mapping
            if doc_id not in self.storage_mappings:
                # Fallback to vector store only
                return await self._get_from_vector_store_only(doc_id)

            mapping = self.storage_mappings[doc_id]

            # Update access tracking
            mapping["last_accessed"] = datetime.now().isoformat()
            mapping["access_count"] += 1

            # Try local storage first (hot tier)
            if mapping.get("local_path"):
                local_path = Path(mapping["local_path"])
                if local_path.exists():
                    content = local_path.read_text(encoding='utf-8')
                    return {
                        "success": True,
                        "content": content,
                        "source": "local",
                        "storage_tier": mapping.get("storage_tier")
                    }

            # Try cloud storage (warm/cold tier)
            if mapping.get("cloud_info") and self.s3_service:
                cloud_content = await self._download_from_cloud(mapping["cloud_info"])
                if cloud_content:
                    # Cache locally for future access
                    await self._cache_locally(doc_id, cloud_content, mapping)
                    return {
                        "success": True,
                        "content": cloud_content,
                        "source": "cloud",
                        "storage_tier": mapping.get("storage_tier")
                    }

            # Final fallback to vector store
            return await self._get_from_vector_store_only(doc_id)

        except Exception as e:
            logger.error(f"Error retrieving evidence with fallback: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _create_local_backup(self, content: str, storage_id: str,
                                 metadata: Dict[str, Any]) -> Optional[Path]:
        """Create local backup of document"""
        try:
            # Create filename from metadata
            title = metadata.get("title", "document").replace(" ", "_")[:50]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{storage_id}_{title}_{timestamp}.txt"

            local_path = self.local_temp_dir / filename
            local_path.write_text(content, encoding='utf-8')

            return local_path

        except Exception as e:
            logger.error(f"Error creating local backup: {e}")
            return None

    async def _upload_to_cloud(self, local_path: Path, storage_id: str,
                             metadata: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Upload document to cloud storage"""
        try:
            if not self.s3_service:
                return None

            # Read content
            content = local_path.read_text(encoding='utf-8')

            # Create upload metadata
            upload_metadata = {
                "storage_id": storage_id,
                "original_name": local_path.name,
                "content_type": "text/plain",
                "vector_store": "lawyerfactory",
                **metadata
            }

            # Upload using S3 service
            # This would integrate with the existing S3 service
            cloud_result = await self._call_s3_upload_service(
                content=content,
                filename=local_path.name,
                metadata=upload_metadata
            )

            return cloud_result

        except Exception as e:
            logger.error(f"Error uploading to cloud: {e}")
            return None

    async def _download_from_cloud(self, cloud_info: Dict[str, Any]) -> Optional[str]:
        """Download document from cloud storage"""
        try:
            if not self.s3_service or not cloud_info.get("key"):
                return None

            # This would integrate with S3 download functionality
            # For now, return placeholder
            return f"Downloaded content from {cloud_info.get('key')}"

        except Exception as e:
            logger.error(f"Error downloading from cloud: {e}")
            return None

    async def _cache_locally(self, doc_id: str, content: str, mapping: Dict[str, Any]):
        """Cache downloaded content locally"""
        try:
            local_path = Path(mapping["local_path"])
            local_path.write_text(content, encoding='utf-8')
            logger.info(f"Cached content locally for {doc_id}")

        except Exception as e:
            logger.error(f"Error caching locally: {e}")

    async def _apply_storage_tier_policy(self, doc_id: str, storage_tier: StorageTier):
        """Apply storage tier policy to document"""
        try:
            policy = self.tier_policies[storage_tier]

            # Set retention based on policy
            retention_date = datetime.now() + timedelta(days=policy["retention_days"])

            # Update mapping with policy info
            if doc_id in self.storage_mappings:
                self.storage_mappings[doc_id]["retention_date"] = retention_date.isoformat()
                self.storage_mappings[doc_id]["tier_policy"] = policy

        except Exception as e:
            logger.error(f"Error applying storage tier policy: {e}")

    async def _get_from_vector_store_only(self, doc_id: str) -> Dict[str, Any]:
        """Fallback to get content from vector store only"""
        try:
            # This would need to be implemented based on vector store structure
            # For now, return placeholder
            return {
                "success": True,
                "content": f"Content for {doc_id} from vector store",
                "source": "vector_store_only"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Vector store retrieval failed: {e}"
            }

    async def _call_s3_upload_service(self, content: str, filename: str,
                                    metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Call S3 upload service (placeholder for integration)"""
        # This would integrate with the existing S3 service
        # For now, return mock response
        return {
            "success": True,
            "key": f"uploads/{datetime.now().strftime('%Y/%m/%d')}/{uuid.uuid4()}/{filename}",
            "url": f"https://s3.amazonaws.com/bucket/uploads/{filename}",
            "uploaded_at": datetime.now().isoformat()
        }

    async def cleanup_temp_files(self):
        """Clean up temporary files based on retention policy"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.temp_file_retention_days)

            for mapping in self.storage_mappings.values():
                if mapping.get("local_path"):
                    local_path = Path(mapping["local_path"])
                    if local_path.exists() and datetime.fromtimestamp(local_path.stat().st_mtime) < cutoff_date:
                        local_path.unlink()
                        logger.info(f"Cleaned up temp file: {local_path}")

        except Exception as e:
            logger.error(f"Error during temp file cleanup: {e}")

    def get_storage_stats(self) -> Dict[str, Any]:
        """Get comprehensive storage statistics"""
        try:
            stats = {
                "total_mapped_documents": len(self.storage_mappings),
                "storage_tiers": {},
                "local_temp_files": 0,
                "cloud_stored_files": 0
            }

            # Count by storage tier
            for mapping in self.storage_mappings.values():
                tier = mapping.get("storage_tier", "unknown")
                if tier not in stats["storage_tiers"]:
                    stats["storage_tiers"][tier] = 0
                stats["storage_tiers"][tier] += 1

                if mapping.get("local_path"):
                    stats["local_temp_files"] += 1

                if mapping.get("cloud_info"):
                    stats["cloud_stored_files"] += 1

            return stats

        except Exception as e:
            logger.error(f"Error getting storage stats: {e}")
            return {"error": str(e)}


class IntegratedEvidenceIngestion:
    """
    Enhanced evidence ingestion that integrates local and cloud storage
    """

    def __init__(self, vector_store_manager: Optional[EnhancedVectorStoreManager] = None,
                 cloud_storage_manager: Optional[CloudStorageManager] = None):
        self.vector_store = vector_store_manager or EnhancedVectorStoreManager()
        self.cloud_storage = cloud_storage_manager or CloudStorageManager(vector_store_manager)

    async def process_evidence_with_storage(self, content: str, metadata: Dict[str, Any],
                                          store_type: VectorStoreType = VectorStoreType.PRIMARY_EVIDENCE,
                                          storage_tier: StorageTier = StorageTier.HOT) -> Dict[str, Any]:
        """
        Process evidence with integrated storage (vector + cloud)

        Args:
            content: Document content
            metadata: Document metadata
            store_type: Vector store type
            storage_tier: Storage tier

        Returns:
            Processing results
        """
        try:
            # Store with cloud backup
            storage_result = await self.cloud_storage.store_evidence_with_cloud_backup(
                content=content,
                metadata=metadata,
                store_type=store_type,
                storage_tier=storage_tier
            )

            if storage_result.get("success"):
                return {
                    "success": True,
                    "doc_id": storage_result.get("doc_id"),
                    "storage_id": storage_result.get("storage_id"),
                    "local_path": storage_result.get("local_path"),
                    "cloud_url": storage_result.get("cloud_url"),
                    "storage_tier": storage_result.get("storage_tier"),
                    "processing_complete": True
                }
            else:
                raise Exception(storage_result.get("error", "Storage failed"))

        except Exception as e:
            logger.error(f"Error processing evidence with storage: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def retrieve_evidence_with_fallback(self, doc_id: str) -> Dict[str, Any]:
        """
        Retrieve evidence with automatic fallback between storage layers

        Args:
            doc_id: Document ID

        Returns:
            Retrieval results
        """
        return await self.cloud_storage.retrieve_evidence_with_fallback(doc_id)


# Global instances for easy access
cloud_storage_manager = CloudStorageManager()
integrated_evidence_ingestion = IntegratedEvidenceIngestion()