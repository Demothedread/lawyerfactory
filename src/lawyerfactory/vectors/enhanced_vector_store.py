"""
Enhanced Multi-Purpose Vector Store Manager for LawyerFactory

This module provides a comprehensive vector storage system with multiple specialized stores:
- Primary Evidence Store: For Statement of Facts construction
- Case Opinions Store: For knowledge graph integration
- General RAG Store: For semantic search and LLM augmentation
- Validation Sub-Vectors: Filtered collections for validation

Features:
- Evidence ingestion pipeline with vector tokenization
- Research rounds integration with vector storage
- LLM RAG functionality integration
- Validation type filtering and sub-vector creation
- Real-time vector store status and metrics
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Set, Tuple, runtime_checkable
import uuid

import numpy as np

try:
    import boto3  # optional; only used if S3 is configured
    from botocore.exceptions import ClientError
except Exception:  # keep optional
    boto3 = None
    ClientError = Exception

from .memory_compression import MCPMemoryManager, MemoryType

logger = logging.getLogger(__name__)


class VectorStoreType(Enum):
    """Types of specialized vector stores"""

    PRIMARY_EVIDENCE = "primary_evidence"
    CASE_OPINIONS = "case_opinions"
    GENERAL_RAG = "general_rag"
    VALIDATION_SUB_VECTORS = "validation_sub_vectors"


class ValidationType(Enum):
    """Types of validation that can be performed"""

    COMPLAINTS_AGAINST_TESLA = "complaints_against_tesla"
    CONTRACT_DISPUTES = "contract_disputes"
    PERSONAL_INJURY = "personal_injury"
    EMPLOYMENT_CLAIMS = "employment_claims"
    INTELLECTUAL_PROPERTY = "intellectual_property"
    CUSTOM_FILTER = "custom_filter"


@dataclass
class VectorDocument:
    """Enhanced vector document with metadata"""

    id: str
    content: str
    vector: List[float]
    metadata: Dict[str, Any]
    store_type: VectorStoreType
    validation_types: List[ValidationType] = field(default_factory=list)
    embedding_model: str = "text-embedding-3-small"
    created_at: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    relevance_score: float = 1.0


@dataclass
class VectorStoreMetrics:
    """Metrics for vector store performance and usage"""

    total_documents: int = 0
    total_vectors: int = 0
    storage_size_mb: float = 0.0
    average_query_time: float = 0.0
    cache_hit_rate: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class ValidationSubVector:
    """Filtered sub-vector for specific validation types"""

    id: str
    validation_type: ValidationType
    document_ids: Set[str] = field(default_factory=set)
    similarity_threshold: float = 0.6
    created_at: datetime = field(default_factory=datetime.now)
    quality_score: float = 0.0


# --- Blob/object storage abstractions ---
@runtime_checkable
class BlobStore(Protocol):
    def put_bytes(
        self, key: str, data: bytes, content_type: Optional[str] = None
    ) -> str:
        """Store bytes at key. Return a URL or file path for retrieval."""
        ...

    def get_url(self, key: str, expires_in: int = 3600) -> str:
        """Return a retrievable URL or path (may be presigned for remote stores)."""
        ...


class LocalDirBlobStore:
    """Directory-based blob store for single-user/dev use."""

    def __init__(self, base_path: Path = Path("uploads")):
        self.base_path = base_path
        self.base_path.mkdir(parents=True, exist_ok=True)

    def put_bytes(
        self, key: str, data: bytes, content_type: Optional[str] = None
    ) -> str:
        # Ensure directory structure
        full_path = self.base_path / key
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, "wb") as f:
            f.write(data)
        # Return a file:// URL for local use
        return full_path.resolve().as_uri()

    def get_url(self, key: str, expires_in: int = 3600) -> str:
        return (self.base_path / key).resolve().as_uri()


class S3BlobStore:
    """S3-backed blob store with directory-like prefixes via keys."""

    def __init__(
        self,
        bucket: str,
        region: Optional[str] = None,
        base_prefix: str = "",
        client: Any = None,
    ):
        if boto3 is None:
            raise RuntimeError("boto3 not available; install boto3 to use S3BlobStore")
        self.bucket = bucket
        self.base_prefix = base_prefix.strip("/")
        self.client = client or boto3.client("s3", region_name=region)

    def _full_key(self, key: str) -> str:
        key = key.lstrip("/")
        return f"{self.base_prefix}/{key}" if self.base_prefix else key

    def put_bytes(
        self, key: str, data: bytes, content_type: Optional[str] = None
    ) -> str:
        extra_args = {"ContentType": content_type} if content_type else {}
        self.client.put_object(
            Bucket=self.bucket, Key=self._full_key(key), Body=data, **extra_args
        )
        # Return an s3:// URL as stable locator; public URL/presign via get_url
        return f"s3://{self.bucket}/{self._full_key(key)}"

    def get_url(self, key: str, expires_in: int = 3600) -> str:
        try:
            return self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": self._full_key(key)},
                ExpiresIn=expires_in,
            )
        except ClientError:
            # Fallback to s3:// if presign fails
            return f"s3://{self.bucket}/{self._full_key(key)}"


import hashlib


class EnhancedVectorStoreManager:
    """
    Enhanced vector store manager with multiple specialized stores
    and advanced RAG capabilities for legal document processing.
    """

    def __init__(
        self,
        storage_path: str = "enhanced_vector_stores",
        embedding_service: Any = None,
        memory_manager: Optional[MCPMemoryManager] = None,
        blob_store: Optional[BlobStore] = None,
    ):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Embedding dimension normalization target
        self.embedding_dim: int = int(os.getenv("EMBED_DIM", "1536"))

        # Blob/object storage for uploaded evidence files
        s3_bucket = os.getenv("LF_S3_BUCKET")
        s3_region = os.getenv("LF_S3_REGION")
        s3_prefix = os.getenv("LF_S3_PREFIX", "lawyerfactory")
        if blob_store is not None:
            self.blob_store: BlobStore = blob_store
        elif s3_bucket:
            self.blob_store = S3BlobStore(
                bucket=s3_bucket, region=s3_region, base_prefix=s3_prefix
            )
        else:
            local_dir = Path(os.getenv("LF_LOCAL_UPLOAD_DIR", "uploads"))
            self.blob_store = LocalDirBlobStore(base_path=local_dir)

        self.embedding_service = embedding_service
        self.memory_manager: MCPMemoryManager = memory_manager or MCPMemoryManager()

        # Initialize specialized vector stores (simple in-memory maps)
        self.vector_stores: Dict[VectorStoreType, Dict[str, VectorDocument]] = {
            store_type: {} for store_type in VectorStoreType
        }

        # Validation sub-vectors
        self.validation_sub_vectors: Dict[str, ValidationSubVector] = {}

        # Store metrics
        self.store_metrics: Dict[VectorStoreType, VectorStoreMetrics] = {
            store_type: VectorStoreMetrics() for store_type in VectorStoreType
        }

        # Cache for frequently accessed vectors
        self.vector_cache: Dict[str, List[float]] = {}
        self.cache_max_size = 1000

        # Default validation type
        self.default_validation_type = ValidationType.COMPLAINTS_AGAINST_TESLA

        logger.info("Enhanced Vector Store Manager initialized")

    # -------------
    # Core helpers
    # -------------

    def _build_object_key(
        self, filename: str, store_type: VectorStoreType, metadata: Dict[str, Any]
    ) -> str:
        """Create a directory-like key: {store_type}/{case_id|unknown}/{YYYY}/{MM}/{uuid}_{filename}"""
        today = datetime.now()
        case_id = str(metadata.get("case_id") or metadata.get("matter_id") or "unknown")
        safe_name = filename.replace(os.sep, "_")
        return f"{store_type.value}/{case_id}/{today.year:04d}/{today.month:02d}/{uuid.uuid4()}_{safe_name}"

    def _normalize_vector(self, vector: List[float]) -> List[float]:
        """Normalize any vector to the target embedding dimension deterministically."""
        if not vector:
            return [0.0] * self.embedding_dim
        if len(vector) == self.embedding_dim:
            return [float(x) for x in vector]
        # repeat / truncate as needed
        reps = (self.embedding_dim + len(vector) - 1) // len(vector)
        normed = (list(vector) * reps)[: self.embedding_dim]
        return [float(x) for x in normed]

    async def _generate_embedding(self, text: str) -> List[float]:
        """Robust embedding generation with multiple fallbacks."""
        if not text:
            return [0.0] * self.embedding_dim

        # Try user-provided embedding service (sync/async; several common method names)
        svc = self.embedding_service
        if svc is not None:
            try:
                if hasattr(svc, "embed"):  # async or sync
                    maybe = svc.embed(text)
                    if asyncio.iscoroutine(maybe):
                        vec = await maybe
                    else:
                        vec = maybe
                    return self._normalize_vector(list(vec))
                if hasattr(svc, "embed_documents"):
                    vec = svc.embed_documents([text])[0]
                    return self._normalize_vector(list(vec))
                if hasattr(svc, "get_embedding"):
                    vec = svc.get_embedding(text)
                    return self._normalize_vector(list(vec))
                # OpenAI-style client: client.embeddings.create(...)
                embeddings_api = getattr(svc, "embeddings", None)
                if embeddings_api is not None and hasattr(embeddings_api, "create"):

                    def _call():
                        resp = embeddings_api.create(
                            model="text-embedding-3-small", input=text
                        )
                        data = getattr(resp, "data", None) or (
                            resp.get("data") if isinstance(resp, dict) else None
                        )
                        first = data[0]
                        return getattr(first, "embedding", None) or first.get(
                            "embedding"
                        )

                    vec = await asyncio.to_thread(_call)
                    return self._normalize_vector(list(vec))
            except Exception as exc:
                logger.warning("Custom embedding_service failed; falling back. %s", exc)

        # Deterministic fallback from SHA256 digest -> floats in [-1,1]
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        raw = [((b / 255.0) * 2.0) - 1.0 for b in digest]
        return self._normalize_vector(raw)

    @staticmethod
    def _calculate_cosine_similarity(a: List[float], b: List[float]) -> float:
        va = np.array(a, dtype=np.float32)
        vb = np.array(b, dtype=np.float32)
        denom = np.linalg.norm(va) * np.linalg.norm(vb)
        if denom == 0.0:
            return 0.0
        return float(np.dot(va, vb) / denom)

    async def _update_validation_sub_vectors(
        self, vector_doc: VectorDocument, validation_types: List[ValidationType]
    ) -> None:
        """Ensure sub-vector indexes exist and include this document id."""
        for vtype in validation_types:
            key = f"{vtype.value}_sub_vector"
            sub = self.validation_sub_vectors.get(key)
            if sub is None:
                sub = ValidationSubVector(id=key, validation_type=vtype)
                self.validation_sub_vectors[key] = sub
            sub.document_ids.add(vector_doc.id)
            # naive quality score heuristic
            sub.quality_score = min(1.0, sub.quality_score + 0.01)

    async def _store_in_memory_system(self, vector_doc: VectorDocument) -> None:
        """Persist a compact memory of this document if a memory manager is available."""
        try:
            mm = self.memory_manager
            if not mm:
                return
            payload = {
                "id": vector_doc.id,
                "store_type": vector_doc.store_type.value,
                "meta": vector_doc.metadata,
                "created_at": vector_doc.created_at.isoformat(),
            }
            # Try common APIs
            for meth in ("store", "add", "save", "append"):
                fn = getattr(mm, meth, None)
                if fn:
                    # Some APIs may expect (type, text, meta) or a dict
                    try:
                        fn(
                            (
                                MemoryType.DOCUMENT
                                if "DOCUMENT" in dir(MemoryType)
                                else "DOCUMENT"
                            ),
                            vector_doc.content,
                            payload,
                        )
                        return
                    except TypeError:
                        fn(payload)
                        return
        except Exception as exc:
            logger.debug("Memory store skipped: %s", exc)

    def _classify_research_content(self, research_content: str) -> VectorStoreType:
        """Very simple heuristic to route research content to a store."""
        txt = (research_content or "").lower()
        if any(k in txt for k in ("opinion", "holding", "case ", " v. ", "court of")):
            return VectorStoreType.CASE_OPINIONS
        if any(k in txt for k in ("analysis", "report", "memo", "notes", "research")):
            return VectorStoreType.GENERAL_RAG
        return VectorStoreType.PRIMARY_EVIDENCE

    # -------------
    # Public API
    # -------------

    async def ingest_evidence(
        self,
        content: str,
        metadata: Dict[str, Any],
        store_type: VectorStoreType = VectorStoreType.PRIMARY_EVIDENCE,
        validation_types: Optional[List[ValidationType]] = None,
    ) -> str:
        """
        Ingest evidence *text* and store as vectors; pairs with ingest_file for blobs.

        Args:
            content: Text content to vectorize
            metadata: Document metadata
            store_type: Primary store type for this content
            validation_types: Applicable validation types

        Returns:
            Document ID for later retrieval
        """
        try:
            doc_id = f"{store_type.value}_{uuid.uuid4()}"
            vector = await self._generate_embedding(content)

            vector_doc = VectorDocument(
                id=doc_id,
                content=content,
                vector=vector,
                metadata=dict(metadata),
                store_type=store_type,
                validation_types=validation_types or [],
            )

            # Put into primary store
            self.vector_stores[store_type][doc_id] = vector_doc

            # Also into GENERAL_RAG for broad search
            if store_type != VectorStoreType.GENERAL_RAG:
                rag_id = f"rag_{doc_id}"
                self.vector_stores[VectorStoreType.GENERAL_RAG][rag_id] = (
                    VectorDocument(
                        id=rag_id,
                        content=content,
                        vector=vector,
                        metadata={**metadata, "source_store": store_type.value},
                        store_type=VectorStoreType.GENERAL_RAG,
                        validation_types=validation_types or [],
                    )
                )

            # Update validation sub-vectors
            if validation_types:
                await self._update_validation_sub_vectors(vector_doc, validation_types)

            # Metrics
            self.store_metrics[store_type].total_documents += 1
            self.store_metrics[store_type].total_vectors += 1
            self.store_metrics[store_type].last_updated = datetime.now()

            # Memory system (best-effort)
            await self._store_in_memory_system(vector_doc)

            logger.info("Ingested evidence %s into %s", doc_id, store_type.value)
            return doc_id
        except Exception as exc:
            logger.error("Error ingesting evidence: %s", exc)
            return ""

    async def ingest_file(
        self,
        file_bytes: bytes,
        filename: str,
        metadata: Dict[str, Any],
        store_type: VectorStoreType = VectorStoreType.PRIMARY_EVIDENCE,
        validation_types: Optional[List[ValidationType]] = None,
        content_text: Optional[str] = None,
        content_type: Optional[str] = None,
    ) -> str:
        """
        Store a user-uploaded file in the configured blob store (local dir or S3),
        then vectorize either provided `content_text` (preferred) or a placeholder.
        Returns a document ID.
        """
        try:
            key = self._build_object_key(filename, store_type, metadata)
            locator = self.blob_store.put_bytes(
                key, file_bytes, content_type=content_type
            )
            enriched_meta = {
                **metadata,
                "blob_key": key,
                "blob_locator": locator,
                "filename": filename,
            }

            # Prefer extracted/parsed text for embedding; else a lightweight placeholder
            text_for_embed = (
                content_text
                if content_text
                else f"Uploaded file: {filename}\nMeta: {json.dumps({k: v for k, v in enriched_meta.items() if k != 'file_bytes'})}"
            )

            return await self.ingest_evidence(
                content=text_for_embed,
                metadata=enriched_meta,
                store_type=store_type,
                validation_types=validation_types,
            )
        except Exception as e:
            logger.error(f"Error ingesting file {filename}: {e}")
            return ""

    async def add_research_round(
        self, research_content: str, metadata: Dict[str, Any], round_number: int
    ) -> str:
        """
        Add research content from a research round to vector stores
        """
        enhanced_metadata = {
            **metadata,
            "research_round": round_number,
            "content_type": "research_findings",
            "timestamp": datetime.now().isoformat(),
        }
        store_type = self._classify_research_content(research_content)
        return await self.ingest_evidence(
            content=research_content,
            metadata=enhanced_metadata,
            store_type=store_type,
            validation_types=[ValidationType.CUSTOM_FILTER],
        )

    async def semantic_search(
        self,
        query: str,
        store_type: Optional[VectorStoreType] = None,
        top_k: int = 10,
        threshold: float = 0.5,
    ) -> List[Tuple[VectorDocument, float]]:
        """
        Perform semantic search across vector stores
        """
        try:
            query_vector = await self._generate_embedding(query)
            results: List[Tuple[VectorDocument, float]] = []

            stores_to_search = [store_type] if store_type else list(VectorStoreType)
            for store in stores_to_search:
                if store not in self.vector_stores:
                    continue
                for doc in self.vector_stores[store].values():
                    sim = self._calculate_cosine_similarity(query_vector, doc.vector)
                    if sim >= threshold:
                        results.append((doc, sim))

            results.sort(key=lambda x: x[1], reverse=True)
            return results[:top_k]
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []

    async def _create_validation_sub_vector(
        self, validation_type: ValidationType
    ) -> None:
        """Create a sub-vector index for a validation type by scanning existing docs."""
        key = f"{validation_type.value}_sub_vector"
        sub = ValidationSubVector(id=key, validation_type=validation_type)
        # include all docs that already carry this validation tag
        for store in self.vector_stores.values():
            for doc in store.values():
                if validation_type in (doc.validation_types or []):
                    sub.document_ids.add(doc.id)
        self.validation_sub_vectors[key] = sub

    async def get_validation_sub_vector(
        self, validation_type: ValidationType, min_quality_score: float = 0.5
    ) -> List[VectorDocument]:
        """
        Get filtered sub-vector for specific validation type
        """
        try:
            sub_vector_key = f"{validation_type.value}_sub_vector"
            if sub_vector_key not in self.validation_sub_vectors:
                await self._create_validation_sub_vector(validation_type)

            sub_vector = self.validation_sub_vectors.get(sub_vector_key)
            if not sub_vector or sub_vector.quality_score < min_quality_score:
                return []

            # Gather actual documents
            docs: List[VectorDocument] = []
            for store in self.vector_stores.values():
                for doc_id, doc in store.items():
                    if doc_id in sub_vector.document_ids:
                        docs.append(doc)
            return docs
        except Exception as e:
            logger.error(f"Error getting validation sub-vector: {e}")
            return []

    def _extract_relevant_context(
        self, content: str, query: str, max_length: int
    ) -> str:
        """Extract relevant context window from content based on query"""
        # Simple implementation: return first max_length characters
        # In production, this would use more sophisticated text segmentation
        return content[:max_length] if len(content) > max_length else content

    async def rag_retrieve_context(
        self, query: str, max_contexts: int = 5, context_window: int = 1000
    ) -> List[str]:
        """
        Retrieve relevant context for LLM augmentation using RAG

        Args:
            query: Query to find relevant context for
            max_contexts: Maximum number of context chunks to return
            context_window: Maximum characters per context chunk

        Returns:
            List of relevant context strings
        """
        try:
            # Search general RAG store for relevant content
            search_results = await self.semantic_search(
                query=query,
                store_type=VectorStoreType.GENERAL_RAG,
                top_k=max_contexts * 2,  # Get more to filter
                threshold=0.3,  # Lower threshold for broader context
            )

            contexts = []
            for doc, similarity in search_results[:max_contexts]:
                # Extract relevant context window around the content
                context = self._extract_relevant_context(
                    doc.content, query, context_window
                )
                if context:
                    contexts.append(context)

            return contexts

        except Exception as e:
            logger.error(f"Error in RAG context retrieval: {e}")
            return []

    async def get_store_metrics(self) -> Dict[str, Any]:
        """Get comprehensive metrics for all vector stores"""
        metrics = {
            "overall": {
                "total_documents": sum(
                    m.total_documents for m in self.store_metrics.values()
                ),
                "total_vectors": sum(
                    m.total_vectors for m in self.store_metrics.values()
                ),
                "cache_size": len(self.vector_cache),
                "validation_sub_vectors": len(self.validation_sub_vectors),
                "blob_store": type(self.blob_store).__name__,
            },
            "stores": {},
        }

        for store_type, store_metric in self.store_metrics.items():
            metrics["stores"][store_type.value] = {
                "documents": store_metric.total_documents,
                "vectors": store_metric.total_vectors,
                "storage_mb": store_metric.storage_size_mb,
                "last_updated": store_metric.last_updated.isoformat(),
            }

        return metrics



# Global instance for easy access
enhanced_vector_store = EnhancedVectorStoreManager()
