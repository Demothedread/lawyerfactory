"""
Enhanced Unified Storage API for LawyerFactory - Production Implementation

This module provides the single, unified interface for all storage operations across LawyerFactory.
Coordinates three storage tiers: S3 Raw Storage, Evidence Table, Vector Store with ObjectID tracking.
Integrates with existing evidence ingestion pipeline and claims matrix system.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import uuid

logger = logging.getLogger(__name__)

# Import existing storage components
try:
    from .cloud.cloud_storage_integration import CloudStorageManager, StorageTier
    from .evidence.table import EnhancedEvidenceTable
    from .vectors.enhanced_vector_store import (
        EnhancedVectorStoreManager,
        ValidationType,
        VectorStoreType,
    )

    STORAGE_COMPONENTS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Storage components not fully available: {e}")
    STORAGE_COMPONENTS_AVAILABLE = False


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
    Production implementation of unified storage API that coordinates all storage operations.
    Integrates with existing evidence ingestion pipeline and sophisticated storage components.
    """

    def __init__(self, storage_path: str = "data/storage"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Initialize storage tier managers
        self.vector_store_manager = None
        self.cloud_storage_manager = None
        self.evidence_table = None

        # ObjectID registry for tracking across all tiers
        self.object_registry_path = self.storage_path / "object_registry.json"
        self.object_registry = self._load_object_registry()

        # Initialize storage managers if available
        if STORAGE_COMPONENTS_AVAILABLE:
            try:
                self.vector_store_manager = EnhancedVectorStoreManager()
                self.cloud_storage_manager = CloudStorageManager(self.vector_store_manager)
                self.evidence_table = EnhancedEvidenceTable()
                logger.info("Storage components initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize storage components: {e}")

        logger.info("Enhanced Unified Storage API initialized")

    def _load_object_registry(self) -> Dict[str, Dict[str, Any]]:
        """Load the object registry from disk"""
        if self.object_registry_path.exists():
            try:
                with open(self.object_registry_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load object registry: {e}")
        return {}

    def _save_object_registry(self):
        """Save the object registry to disk"""
        try:
            with open(self.object_registry_path, "w", encoding="utf-8") as f:
                json.dump(self.object_registry, f, indent=2, ensure_ascii=False, default=str)
        except Exception as e:
            logger.error(f"Failed to save object registry: {e}")

    async def store_evidence(
        self,
        file_content: bytes,
        filename: str,
        metadata: Optional[Dict[str, Any]] = None,
        source_phase: str = "intake",
    ) -> StorageResult:
        """
        Store evidence through the unified pipeline integrating with existing components

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
                custom_metadata=metadata or {},
            )

            # Convert content to string for processing
            try:
                content_str = file_content.decode("utf-8", errors="replace")
            except:
                content_str = f"[Binary content: {filename}, {len(file_content)} bytes]"

            # Process through all storage tiers
            storage_results = {}

            # 1. Vector Store Integration
            if self.vector_store_manager:
                try:
                    vector_result = await self._store_in_vector_store(
                        content_str, evidence_metadata
                    )
                    storage_results["vector"] = vector_result
                except Exception as e:
                    logger.error(f"Vector store error: {e}")
                    storage_results["vector"] = {"error": str(e)}

            # 2. Cloud Storage Integration
            if self.cloud_storage_manager:
                try:
                    cloud_result = await self._store_in_cloud_storage(
                        file_content, evidence_metadata
                    )
                    storage_results["cloud"] = cloud_result
                except Exception as e:
                    logger.error(f"Cloud storage error: {e}")
                    storage_results["cloud"] = {"error": str(e)}

            # 3. Evidence Table Integration
            if self.evidence_table:
                try:
                    evidence_result = await self._store_in_evidence_table(
                        content_str, evidence_metadata
                    )
                    storage_results["evidence"] = evidence_result
                except Exception as e:
                    logger.error(f"Evidence table error: {e}")
                    storage_results["evidence"] = {"error": str(e)}

            # Register the object
            self.object_registry[object_id] = {
                "metadata": {
                    "object_id": object_id,
                    "original_filename": filename,
                    "content_type": evidence_metadata.content_type,
                    "file_size": evidence_metadata.file_size,
                    "upload_timestamp": evidence_metadata.upload_timestamp.isoformat(),
                    "source_phase": source_phase,
                    "custom_metadata": metadata or {},
                },
                "storage_results": storage_results,
                "created_at": datetime.now().isoformat(),
                "source_phase": source_phase,
            }
            self._save_object_registry()

            processing_time = (datetime.now() - start_time).total_seconds()

            return StorageResult(
                success=True,
                object_id=object_id,
                s3_url=storage_results.get("cloud", {}).get("url"),
                evidence_id=storage_results.get("evidence", {}).get("evidence_id"),
                vector_ids=storage_results.get("vector", {}).get("vector_ids", []),
                processing_time=processing_time,
            )

        except Exception as e:
            logger.error(f"Failed to store evidence {object_id}: {e}")
            return StorageResult(
                success=False,
                object_id=object_id,
                error=str(e),
                processing_time=(datetime.now() - start_time).total_seconds(),
            )

    async def get_evidence(
        self, object_id: str, target_tier: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieve evidence from the unified storage system

        Args:
            object_id: The ObjectID to retrieve
            target_tier: Specific tier to retrieve from ("cloud", "evidence", "vector")

        Returns:
            Evidence data from requested tier(s)
        """
        if object_id not in self.object_registry:
            return {"error": "ObjectID not found"}

        registry_entry = self.object_registry[object_id]
        storage_results = registry_entry.get("storage_results", {})

        result = {
            "object_id": object_id,
            "metadata": registry_entry.get("metadata", {}),
            "available_tiers": list(storage_results.keys()),
        }

        try:
            if target_tier == "cloud" or target_tier is None:
                if "cloud" in storage_results and self.cloud_storage_manager:
                    cloud_data = await self._get_from_cloud_storage(
                        object_id, storage_results["cloud"]
                    )
                    if cloud_data:
                        result["cloud_data"] = cloud_data

            if target_tier == "evidence" or target_tier is None:
                if "evidence" in storage_results and self.evidence_table:
                    evidence_data = await self._get_from_evidence_table(storage_results["evidence"])
                    if evidence_data:
                        result["evidence_data"] = evidence_data

            if target_tier == "vector" or target_tier is None:
                if "vector" in storage_results and self.vector_store_manager:
                    vector_data = await self._get_from_vector_store(storage_results["vector"])
                    if vector_data:
                        result["vector_data"] = vector_data

        except Exception as e:
            logger.error(f"Failed to retrieve evidence {object_id}: {e}")
            result["error"] = str(e)

        return result

    async def search_evidence(
        self, query: str, search_tier: str = "vector"
    ) -> List[Dict[str, Any]]:
        """
        Search for evidence across storage tiers

        Args:
            query: Search query
            search_tier: Which tier to search in ("vector", "evidence", "all")

        Returns:
            List of matching evidence with ObjectIDs
        """
        results = []

        try:
            if search_tier == "vector" and self.vector_store_manager:
                vector_results = await self._search_vector_store(query)
                results.extend(vector_results)

            elif search_tier == "evidence" and self.evidence_table:
                evidence_results = await self._search_evidence_table(query)
                results.extend(evidence_results)

            elif search_tier == "all":
                # Search all available tiers
                if self.vector_store_manager:
                    vector_results = await self._search_vector_store(query)
                    results.extend(vector_results)

                if self.evidence_table:
                    evidence_results = await self._search_evidence_table(query)
                    results.extend(evidence_results)

        except Exception as e:
            logger.error(f"Failed to search evidence: {e}")

        return results

    def _guess_content_type(self, filename: str) -> str:
        """Guess content type from filename"""
        import mimetypes

        content_type, _ = mimetypes.guess_type(filename)
        return content_type or "application/octet-stream"

    # Storage tier integration methods

    async def _store_in_vector_store(
        self, content: str, metadata: EvidenceMetadata
    ) -> Dict[str, Any]:
        """Store content in vector store using existing EnhancedVectorStoreManager"""
        if not self.vector_store_manager:
            return {"error": "Vector store manager not available"}

        try:
            # Determine appropriate vector store type based on content and source
            store_type = self._determine_vector_store_type(content, metadata.source_phase)

            # Determine validation types
            validation_types = self._classify_validation_types(content)

            # Store using the existing vector store manager
            doc_id = await self.vector_store_manager.ingest_evidence(
                content=content,
                metadata={
                    "object_id": metadata.object_id,
                    "filename": metadata.original_filename,
                    "source_phase": metadata.source_phase,
                    "content_type": metadata.content_type,
                    **metadata.custom_metadata,
                },
                store_type=store_type,
                validation_types=validation_types,
            )

            return {
                "success": True,
                "vector_ids": [doc_id],
                "store_type": store_type.value if hasattr(store_type, "value") else str(store_type),
                "validation_types": [
                    vt.value if hasattr(vt, "value") else str(vt) for vt in validation_types
                ],
            }

        except Exception as e:
            logger.error(f"Vector store integration error: {e}")
            return {"error": str(e)}

    async def _store_in_cloud_storage(
        self, file_content: bytes, metadata: EvidenceMetadata
    ) -> Dict[str, Any]:
        """Store file in cloud storage using existing CloudStorageManager"""
        if not self.cloud_storage_manager:
            return {"error": "Cloud storage manager not available"}

        try:
            # Use the integrated cloud storage manager
            storage_result = await self.cloud_storage_manager.store_with_tier(
                content=file_content,
                filename=metadata.original_filename,
                metadata={
                    "object_id": metadata.object_id,
                    "source_phase": metadata.source_phase,
                    "content_type": metadata.content_type,
                    **metadata.custom_metadata,
                },
                tier=StorageTier.HOT,  # Default to HOT tier for new evidence
            )

            return {
                "success": True,
                "url": storage_result.get("url"),
                "storage_id": storage_result.get("storage_id"),
                "tier": "HOT",
            }

        except Exception as e:
            logger.error(f"Cloud storage integration error: {e}")
            return {"error": str(e)}

    async def _store_in_evidence_table(
        self, content: str, metadata: EvidenceMetadata
    ) -> Dict[str, Any]:
        """Store structured data in evidence table using existing EnhancedEvidenceTable"""
        if not self.evidence_table:
            return {"error": "Evidence table not available"}

        try:
            # Create evidence entry using the enhanced evidence table
            from .evidence.table import EvidenceEntry, EvidenceType, RelevanceLevel

            # Determine evidence type and relevance
            evidence_type = self._determine_evidence_type(content, metadata.original_filename)
            relevance = self._determine_relevance(content)

            # Extract supporting facts (simplified)
            supporting_facts = self._extract_supporting_facts(content)

            evidence_entry = EvidenceEntry(
                source_document=metadata.original_filename,
                page_section="Full Document",
                evidence_type=evidence_type,
                relevance_level=relevance,
                content=content[:1000] if len(content) > 1000 else content,  # Truncate for display
                supporting_facts=supporting_facts,
                notes=f"Source: {metadata.source_phase} | ObjectID: {metadata.object_id}",
                created_by="unified_storage_api",
            )

            # Add to evidence table
            self.evidence_table.add_evidence(evidence_entry)

            return {
                "success": True,
                "evidence_id": evidence_entry.evidence_id,
                "evidence_type": (
                    evidence_type.value if hasattr(evidence_type, "value") else str(evidence_type)
                ),
                "relevance_level": (
                    relevance.value if hasattr(relevance, "value") else str(relevance)
                ),
            }

        except Exception as e:
            logger.error(f"Evidence table integration error: {e}")
            return {"error": str(e)}

    # Helper methods for classification

    def _determine_vector_store_type(self, content: str, source_phase: str):
        """Determine appropriate vector store type based on content and source"""
        if not STORAGE_COMPONENTS_AVAILABLE:
            return "PRIMARY_EVIDENCE"

        content_lower = content.lower()

        if source_phase in ["intake", "evidence"]:
            return VectorStoreType.PRIMARY_EVIDENCE
        elif "opinion" in content_lower or "court" in content_lower or "judge" in content_lower:
            return VectorStoreType.CASE_OPINIONS
        else:
            return VectorStoreType.GENERAL_RAG

    def _classify_validation_types(self, content: str) -> List:
        """Classify content for validation types"""
        if not STORAGE_COMPONENTS_AVAILABLE:
            return []

        validation_types = []
        content_lower = content.lower()

        if "tesla" in content_lower:
            validation_types.append(ValidationType.COMPLAINTS_AGAINST_TESLA)
        if "contract" in content_lower or "agreement" in content_lower:
            validation_types.append(ValidationType.CONTRACT_DISPUTES)
        if "discovery" in content_lower:
            validation_types.append(ValidationType.DISCOVERY_RESPONSES)

        return validation_types

    def _determine_evidence_type(self, content: str, filename: str):
        """Determine evidence type based on content and filename"""
        if not STORAGE_COMPONENTS_AVAILABLE:
            return "DOCUMENTARY"

        from .evidence.table import EvidenceType

        content_lower = content.lower()
        filename_lower = filename.lower()

        if "testimony" in content_lower or "deposition" in content_lower:
            return EvidenceType.TESTIMONIAL
        elif "expert" in content_lower or "opinion" in content_lower:
            return EvidenceType.EXPERT
        elif any(ext in filename_lower for ext in [".jpg", ".png", ".pdf", ".doc"]):
            return EvidenceType.DOCUMENTARY
        else:
            return EvidenceType.DOCUMENTARY

    def _determine_relevance(self, content: str):
        """Determine relevance level based on content"""
        if not STORAGE_COMPONENTS_AVAILABLE:
            return "MEDIUM"

        from .evidence.table import RelevanceLevel

        content_lower = content.lower()

        # High relevance indicators
        high_indicators = ["lawsuit", "complaint", "claim", "damages", "breach", "liability"]
        # Medium relevance indicators
        medium_indicators = ["correspondence", "email", "meeting", "discussion"]

        if any(indicator in content_lower for indicator in high_indicators):
            return RelevanceLevel.HIGH
        elif any(indicator in content_lower for indicator in medium_indicators):
            return RelevanceLevel.MEDIUM
        else:
            return RelevanceLevel.LOW

    def _extract_supporting_facts(self, content: str) -> List[str]:
        """Extract supporting facts from content"""
        facts = []

        # Simple fact extraction - look for declarative sentences
        sentences = [s.strip() for s in content.split(".") if s.strip() and len(s.strip()) > 20]

        # Take first few sentences as facts
        for sentence in sentences[:3]:
            if len(sentence) > 10:  # Minimum sentence length
                facts.append(sentence.strip())

        return facts

    # Retrieval methods for each storage tier

    async def _get_from_cloud_storage(
        self, object_id: str, cloud_result: Dict[str, Any]
    ) -> Optional[bytes]:
        """Retrieve file from cloud storage"""
        if not self.cloud_storage_manager:
            return None

        try:
            storage_id = cloud_result.get("storage_id")
            if storage_id:
                return await self.cloud_storage_manager.retrieve_by_id(storage_id)
        except Exception as e:
            logger.error(f"Cloud storage retrieval error: {e}")

        return None

    async def _get_from_evidence_table(
        self, evidence_result: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Retrieve data from evidence table"""
        if not self.evidence_table:
            return None

        try:
            evidence_id = evidence_result.get("evidence_id")
            if evidence_id:
                return self.evidence_table.get_evidence(evidence_id)
        except Exception as e:
            logger.error(f"Evidence table retrieval error: {e}")

        return None

    async def _get_from_vector_store(
        self, vector_result: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Retrieve data from vector store"""
        if not self.vector_store_manager:
            return None

        try:
            vector_ids = vector_result.get("vector_ids", [])
            if vector_ids:
                # Get first vector ID data - use direct access instead of get_document
                for store_type in self.vector_store_manager.vector_stores:
                    store = self.vector_store_manager.vector_stores[store_type]
                    if vector_ids[0] in store:
                        doc = store[vector_ids[0]]
                        return {
                            "id": doc.id,
                            "content": doc.content,
                            "metadata": doc.metadata,
                            "vector": doc.vector,
                            "store_type": store_type.value,
                        }
        except Exception as e:
            logger.error(f"Vector store retrieval error: {e}")

        return None

    # Search methods for each storage tier

    async def _search_vector_store(self, query: str) -> List[Dict[str, Any]]:
        """Search vector store and return results with ObjectIDs"""
        if not self.vector_store_manager:
            return []

        try:
            # Search using semantic_search method instead of search_similar
            search_results = await self.vector_store_manager.semantic_search(
                query=query, top_k=10, threshold=0.5
            )

            results = []
            for doc, score in search_results:
                # Find corresponding ObjectID
                vector_id = doc.id
                for obj_id, registry_entry in self.object_registry.items():
                    vector_ids = (
                        registry_entry.get("storage_results", {})
                        .get("vector", {})
                        .get("vector_ids", [])
                    )
                    if vector_id in vector_ids:
                        results.append(
                            {
                                "object_id": obj_id,
                                "metadata": registry_entry.get("metadata", {}),
                                "relevance_score": score,
                                "vector_data": {
                                    "id": doc.id,
                                    "content": doc.content,
                                    "metadata": doc.metadata,
                                },
                                "search_tier": "vector",
                            }
                        )
                        break

            return results

        except Exception as e:
            logger.error(f"Vector store search error: {e}")
            return []

    async def _search_evidence_table(self, query: str) -> List[Dict[str, Any]]:
        """Search evidence table and return results with ObjectIDs"""
        if not self.evidence_table:
            return []

        try:
            # Search using evidence table search functionality
            search_results = self.evidence_table.search_evidence(query)

            results = []
            for result in search_results:
                # Find corresponding ObjectID
                evidence_id = result.get("evidence_id")
                for obj_id, registry_entry in self.object_registry.items():
                    if (
                        registry_entry.get("storage_results", {})
                        .get("evidence", {})
                        .get("evidence_id")
                        == evidence_id
                    ):
                        results.append(
                            {
                                "object_id": obj_id,
                                "metadata": registry_entry.get("metadata", {}),
                                "evidence_data": result,
                                "search_tier": "evidence",
                            }
                        )
                        break

            return results

        except Exception as e:
            logger.error(f"Evidence table search error: {e}")
            return []


# Global instance for easy access
_enhanced_unified_storage_instance = None


def get_enhanced_unified_storage_api() -> EnhancedUnifiedStorageAPI:
    """Get the global enhanced unified storage API instance"""
    global _enhanced_unified_storage_instance
    if _enhanced_unified_storage_instance is None:
        _enhanced_unified_storage_instance = EnhancedUnifiedStorageAPI()
    return _enhanced_unified_storage_instance
