"""
Vector Cluster Manager for LawyerFactory
Manages specialized vector clusters for different types of legal documents.
Provides clustering, similarity search, and validation capabilities.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .enhanced_document_categorizer import (
    DocumentAuthority,
    DocumentCluster,
    DocumentMetadata,
    DocumentType,
)

logger = logging.getLogger(__name__)


@dataclass
class VectorDocument:
    """Document with vector representation"""

    metadata: DocumentMetadata
    vector: List[float]
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ClusterAnalysis:
    """Analysis results for a document cluster"""

    cluster_id: str
    total_documents: int
    document_types: Dict[DocumentType, int]
    authority_levels: Dict[DocumentAuthority, int]
    average_similarity: float
    quality_score: float
    validation_threshold: float
    created_at: datetime = field(default_factory=datetime.now)


class VectorClusterManager:
    """
    Manages vector clusters for different types of legal documents.
    Provides specialized storage and retrieval for:
    - Case law opinions
    - Defendant-specific complaints
    - Defendant answers/motions
    - Countersuits and responses
    """

    def __init__(self, storage_path: str = "vector_clusters", embedding_service=None):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.embedding_service = embedding_service
        self.clusters: Dict[str, List[VectorDocument]] = {}
        self.cluster_metadata: Dict[str, DocumentCluster] = {}

        # Initialize standard cluster types
        self._initialize_standard_clusters()

        # Validation thresholds for different document types
        self.validation_thresholds = {
            DocumentType.PLAINTIFF_COMPLAINT: 0.6,  # 60% similarity for complaints
            DocumentType.DEFENDANT_ANSWER: 0.5,  # 50% similarity for answers
            DocumentType.JUDGE_OPINION: 0.7,  # 70% similarity for opinions
            DocumentType.BRIEF: 0.55,  # 55% similarity for briefs
        }

    def _initialize_standard_clusters(self):
        """Initialize standard cluster types"""
        standard_clusters = [
            "case_law_opinions",
            "plaintiff_complaints",
            "defendant_answers",
            "defendant_motions",
            "counterclaims",
            "expert_reports",
            "depositions",
        ]

        for cluster_id in standard_clusters:
            self.clusters[cluster_id] = []
            self.cluster_metadata[cluster_id] = DocumentCluster(
                cluster_id=cluster_id, cluster_type=cluster_id.replace("_", " ").title()
            )

    def create_defendant_cluster(self, defendant_name: str) -> str:
        """Create specialized cluster for a specific defendant"""
        cluster_id = f"{defendant_name.lower().replace(' ', '_')}_complaints"

        if cluster_id not in self.clusters:
            self.clusters[cluster_id] = []
            self.cluster_metadata[cluster_id] = DocumentCluster(
                cluster_id=cluster_id,
                cluster_type=f"{defendant_name} Complaints",
                defendant_name=defendant_name,
                typical_similarity_threshold=self.validation_thresholds[
                    DocumentType.PLAINTIFF_COMPLAINT
                ],
            )

        return cluster_id

    async def add_document(
        self,
        document: DocumentMetadata,
        text_content: str,
        cluster_id: Optional[str] = None,
    ) -> bool:
        """
        Add document to appropriate vector cluster

        Args:
            document: Document metadata
            text_content: Full text content
            cluster_id: Specific cluster ID (optional)

        Returns:
            Success status
        """
        try:
            # Generate vector embedding
            vector = await self._generate_embedding(text_content)
            if not vector:
                logger.error(
                    f"Failed to generate embedding for document {document.document_id}"
                )
                return False

            # Create vector document
            vector_doc = VectorDocument(metadata=document, vector=vector)

            # Determine appropriate cluster
            if cluster_id:
                target_cluster = cluster_id
            else:
                target_cluster = self._determine_cluster(document)

            # Create cluster if it doesn't exist
            if target_cluster not in self.clusters:
                if document.defendant_name:
                    target_cluster = self.create_defendant_cluster(
                        document.defendant_name
                    )
                else:
                    target_cluster = self._get_default_cluster(document.document_type)

            # Add to cluster
            self.clusters[target_cluster].append(vector_doc)
            document.cluster_id = target_cluster

            # Update cluster metadata
            if target_cluster in self.cluster_metadata:
                self.cluster_metadata[target_cluster].documents.append(document)

            # Save to disk
            await self._save_document(vector_doc, target_cluster)

            logger.info(
                f"Added document {document.document_id} to cluster {target_cluster}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to add document {document.document_id}: {e}")
            return False

    def _determine_cluster(self, document: DocumentMetadata) -> str:
        """Determine appropriate cluster for document"""
        # Defendant-specific complaints get their own cluster
        if (
            document.document_type == DocumentType.PLAINTIFF_COMPLAINT
            and document.defendant_name
        ):
            return self.create_defendant_cluster(document.defendant_name)

        # Map document types to clusters
        type_cluster_map = {
            DocumentType.JUDGE_OPINION: "case_law_opinions",
            DocumentType.PLAINTIFF_COMPLAINT: "plaintiff_complaints",
            DocumentType.DEFENDANT_ANSWER: "defendant_answers",
            DocumentType.DEFENDANT_MOTION: "defendant_motions",
            DocumentType.COUNTERCLAIM: "counterclaims",
            DocumentType.EXPERT_REPORT: "expert_reports",
            DocumentType.DEPOSITION: "depositions",
            DocumentType.BRIEF: "case_law_opinions",  # Briefs go with opinions
            DocumentType.COURT_ORDER: "case_law_opinions",
        }

        return type_cluster_map.get(document.document_type, "plaintiff_complaints")

    def _get_default_cluster(self, doc_type: DocumentType) -> str:
        """Get default cluster for document type"""
        defaults = {
            DocumentType.JUDGE_OPINION: "case_law_opinions",
            DocumentType.PLAINTIFF_COMPLAINT: "plaintiff_complaints",
            DocumentType.DEFENDANT_ANSWER: "defendant_answers",
            DocumentType.DEFENDANT_MOTION: "defendant_motions",
            DocumentType.COUNTERCLAIM: "counterclaims",
        }
        return defaults.get(doc_type, "plaintiff_complaints")

    async def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate vector embedding for text"""
        try:
            if self.embedding_service:
                # Use provided embedding service
                return await self.embedding_service.embed_text(text)
            else:
                # Simple fallback - return zero vector of appropriate dimension
                # In real implementation, this would use sentence-transformers or similar
                return [0.0] * 384  # Common embedding dimension

        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return None

    async def find_similar_documents(
        self,
        query_document: DocumentMetadata,
        query_text: str,
        top_k: int = 5,
        similarity_threshold: float = 0.5,
    ) -> List[Tuple[VectorDocument, float]]:
        """
        Find similar documents in the same cluster

        Args:
            query_document: Document to find similarities for
            query_text: Text content of query document
            top_k: Number of similar documents to return
            similarity_threshold: Minimum similarity score

        Returns:
            List of (document, similarity_score) tuples
        """
        try:
            if (
                not query_document.cluster_id
                or query_document.cluster_id not in self.clusters
            ):
                return []

            # Generate query vector
            query_vector = await self._generate_embedding(query_text)
            if not query_vector:
                return []

            cluster_docs = self.clusters[query_document.cluster_id]
            similarities = []

            for doc in cluster_docs:
                if doc.metadata.document_id == query_document.document_id:
                    continue

                similarity = self._calculate_cosine_similarity(query_vector, doc.vector)
                if similarity >= similarity_threshold:
                    similarities.append((doc, similarity))

            # Sort by similarity and return top_k
            similarities.sort(key=lambda x: x[1], reverse=True)
            return similarities[:top_k]

        except Exception as e:
            logger.error(f"Similarity search failed: {e}")
            return []

    def _calculate_cosine_similarity(
        self, vec1: List[float], vec2: List[float]
    ) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            import numpy as np

            vec1_np = np.array(vec1)
            vec2_np = np.array(vec2)

            dot_product = np.dot(vec1_np, vec2_np)
            norm1 = np.linalg.norm(vec1_np)
            norm2 = np.linalg.norm(vec2_np)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            return dot_product / (norm1 * norm2)

        except Exception:
            # Fallback to simple dot product similarity
            if len(vec1) != len(vec2):
                return 0.0
            return sum(a * b for a, b in zip(vec1, vec2))

    async def validate_draft_against_cluster(
        self, draft_text: str, defendant_name: str, similarity_threshold: float = 0.6
    ) -> Dict[str, Any]:
        """
        Validate a draft complaint against the defendant's complaint cluster

        Args:
            draft_text: Text of the draft complaint
            defendant_name: Name of the defendant
            similarity_threshold: Minimum similarity threshold

        Returns:
            Validation results with similarity scores and recommendations
        """
        try:
            cluster_id = f"{defendant_name.lower().replace(' ', '_')}_complaints"

            if cluster_id not in self.clusters:
                return {
                    "valid": False,
                    "reason": f"No complaint cluster found for defendant {defendant_name}",
                    "similarity_score": 0.0,
                    "recommendations": [
                        "Upload more complaints against this defendant first"
                    ],
                }

            # Generate draft vector
            draft_vector = await self._generate_embedding(draft_text)
            if not draft_vector:
                return {
                    "valid": False,
                    "reason": "Failed to generate embedding for draft",
                    "similarity_score": 0.0,
                }

            # Find most similar documents
            cluster_docs = self.clusters[cluster_id]
            similarities = []

            for doc in cluster_docs:
                similarity = self._calculate_cosine_similarity(draft_vector, doc.vector)
                similarities.append(similarity)

            if not similarities:
                return {
                    "valid": False,
                    "reason": "No documents in cluster to compare against",
                    "similarity_score": 0.0,
                }

            max_similarity = max(similarities)
            avg_similarity = sum(similarities) / len(similarities)

            # Determine validation result
            is_valid = max_similarity >= similarity_threshold

            result = {
                "valid": is_valid,
                "max_similarity": max_similarity,
                "avg_similarity": avg_similarity,
                "similarity_threshold": similarity_threshold,
                "comparison_count": len(similarities),
                "defendant": defendant_name,
                "cluster_size": len(cluster_docs),
            }

            if not is_valid:
                result["reason"] = ".2%"
                result["recommendations"] = [
                    "Review similar complaints in the cluster",
                    "Incorporate common legal elements and factual patterns",
                    "Consider adjusting the similarity threshold if appropriate",
                ]

            return result

        except Exception as e:
            logger.error(f"Draft validation failed: {e}")
            return {
                "valid": False,
                "reason": f"Validation error: {str(e)}",
                "similarity_score": 0.0,
            }

    async def get_cluster_analysis(self, cluster_id: str) -> Optional[ClusterAnalysis]:
        """Get detailed analysis of a document cluster"""
        try:
            if cluster_id not in self.clusters:
                return None

            docs = self.clusters[cluster_id]
            if not docs:
                return None

            # Analyze document types
            doc_types = {}
            authority_levels = {}

            for doc in docs:
                doc_types[doc.metadata.document_type] = (
                    doc_types.get(doc.metadata.document_type, 0) + 1
                )
                authority_levels[doc.metadata.authority_level] = (
                    authority_levels.get(doc.metadata.authority_level, 0) + 1
                )

            # Calculate average similarity (simplified)
            avg_similarity = 0.5  # Placeholder - would calculate actual similarities

            # Calculate quality score
            quality_score = self._calculate_cluster_quality(docs)

            # Get validation threshold
            threshold = self.cluster_metadata[cluster_id].typical_similarity_threshold

            return ClusterAnalysis(
                cluster_id=cluster_id,
                total_documents=len(docs),
                document_types=doc_types,
                authority_levels=authority_levels,
                average_similarity=avg_similarity,
                quality_score=quality_score,
                validation_threshold=threshold,
            )

        except Exception as e:
            logger.error(f"Cluster analysis failed: {e}")
            return None

    def _calculate_cluster_quality(self, docs: List[VectorDocument]) -> float:
        """Calculate quality score for a cluster"""
        if not docs:
            return 0.0

        # Factors for quality score
        quality_factors = []

        # Document type diversity (prefer some diversity but not too much)
        doc_types = set(doc.metadata.document_type for doc in docs)
        type_diversity = len(doc_types) / len(DocumentType)
        quality_factors.append(
            1.0 - abs(0.3 - type_diversity)
        )  # Optimal diversity around 30%

        # Authority level balance
        authority_levels = [doc.metadata.authority_level for doc in docs]
        binding_count = sum(
            1
            for auth in authority_levels
            if auth == DocumentAuthority.BINDING_PRECEDENT
        )
        authority_balance = binding_count / len(docs)
        quality_factors.append(
            min(1.0, authority_balance + 0.5)
        )  # Prefer some binding precedent

        # Average confidence score
        avg_confidence = sum(doc.metadata.confidence_score for doc in docs) / len(docs)
        quality_factors.append(avg_confidence)

        # Size factor (prefer larger clusters)
        size_score = min(1.0, len(docs) / 10.0)  # Max score at 10+ documents
        quality_factors.append(size_score)

        return sum(quality_factors) / len(quality_factors)

    async def _save_document(self, vector_doc: VectorDocument, cluster_id: str):
        """Save document to persistent storage"""
        try:
            cluster_path = self.storage_path / cluster_id
            cluster_path.mkdir(exist_ok=True)

            doc_path = cluster_path / f"{vector_doc.metadata.document_id}.json"

            doc_data = {
                "metadata": {
                    "document_id": vector_doc.metadata.document_id,
                    "document_type": vector_doc.metadata.document_type.value,
                    "authority_level": vector_doc.metadata.authority_level.value,
                    "defendant_name": vector_doc.metadata.defendant_name,
                    "plaintiff_name": vector_doc.metadata.plaintiff_name,
                    "confidence_score": vector_doc.metadata.confidence_score,
                    "extracted_entities": vector_doc.metadata.extracted_entities,
                    "key_legal_issues": vector_doc.metadata.key_legal_issues,
                    "created_at": vector_doc.metadata.created_at.isoformat(),
                },
                "vector": vector_doc.vector,
                "embedding_model": vector_doc.embedding_model,
                "cluster_id": cluster_id,
                "saved_at": datetime.now().isoformat(),
            }

            with open(doc_path, "w", encoding="utf-8") as f:
                json.dump(doc_data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.error(
                f"Failed to save document {vector_doc.metadata.document_id}: {e}"
            )

    async def load_cluster(self, cluster_id: str) -> bool:
        """Load cluster from persistent storage"""
        try:
            cluster_path = self.storage_path / cluster_id
            if not cluster_path.exists():
                return False

            self.clusters[cluster_id] = []

            for doc_file in cluster_path.glob("*.json"):
                with open(doc_file, "r", encoding="utf-8") as f:
                    doc_data = json.load(f)

                # Reconstruct metadata
                meta_data = doc_data["metadata"]
                metadata = DocumentMetadata(
                    document_id=meta_data["document_id"],
                    document_type=DocumentType(meta_data["document_type"]),
                    authority_level=DocumentAuthority(meta_data["authority_level"]),
                    defendant_name=meta_data.get("defendant_name"),
                    plaintiff_name=meta_data.get("plaintiff_name"),
                    confidence_score=meta_data.get("confidence_score", 0.0),
                    extracted_entities=meta_data.get("extracted_entities", []),
                    key_legal_issues=meta_data.get("key_legal_issues", []),
                    created_at=datetime.fromisoformat(meta_data["created_at"]),
                )

                # Create vector document
                vector_doc = VectorDocument(
                    metadata=metadata,
                    vector=doc_data["vector"],
                    embedding_model=doc_data.get("embedding_model", "unknown"),
                )

                self.clusters[cluster_id].append(vector_doc)

            logger.info(
                f"Loaded {len(self.clusters[cluster_id])} documents for cluster {cluster_id}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to load cluster {cluster_id}: {e}")
            return False
