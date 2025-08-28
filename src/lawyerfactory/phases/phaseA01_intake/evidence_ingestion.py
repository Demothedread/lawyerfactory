"""
Evidence Ingestion Pipeline for LawyerFactory

This module provides automated evidence ingestion with vector tokenization,
integrating with the intake processor to automatically store evidence in
specialized vector stores for later retrieval and analysis.

Features:
- Automatic document processing and vectorization
- Integration with existing intake workflow
- Research rounds accumulation
- Metadata extraction and tagging
- Validation type classification
"""

import asyncio
from datetime import datetime
import logging
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Set

from .cloud_storage_integration import (
    CloudStorageManager,
    IntegratedEvidenceIngestion,
    StorageTier,
)
from .enhanced_vector_store import (
    EnhancedVectorStoreManager,
    ValidationType,
    VectorStoreType,
)

logger = logging.getLogger(__name__)


class EvidenceIngestionPipeline:
    """
    Automated pipeline for ingesting evidence and storing as vectors
    """

    def __init__(
        self, vector_store_manager: Optional[EnhancedVectorStoreManager] = None
    ):
        self.vector_store = vector_store_manager or EnhancedVectorStoreManager()
        self.cloud_storage = CloudStorageManager(vector_store_manager)
        self.integrated_ingestion = IntegratedEvidenceIngestion(
            vector_store_manager, self.cloud_storage
        )

        # Document type patterns for classification
        self.document_patterns = self._initialize_document_patterns()

        # Validation type keywords
        self.validation_keywords = self._initialize_validation_keywords()

        # Processing statistics
        self.stats = {
            "documents_processed": 0,
            "vectors_created": 0,
            "errors": 0,
            "processing_time": 0,
        }

    def _initialize_document_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize patterns for document type classification"""
        return {
            "complaint": {
                "patterns": [
                    r"complaint",
                    r"petition",
                    r"claim",
                    r"lawsuit",
                    r"plaintiff.*v.*defendant",
                    r"case.*no\.",
                ],
                "store_type": VectorStoreType.PRIMARY_EVIDENCE,
                "validation_types": [ValidationType.COMPLAINTS_AGAINST_TESLA],
            },
            "contract": {
                "patterns": [
                    r"contract",
                    r"agreement",
                    r"terms",
                    r"conditions",
                    r"parties",
                    r"hereby",
                    r"whereas",
                    r"shall",
                ],
                "store_type": VectorStoreType.PRIMARY_EVIDENCE,
                "validation_types": [ValidationType.CONTRACT_DISPUTES],
            },
            "case_opinion": {
                "patterns": [
                    r"opinion",
                    r"holding",
                    r"precedent",
                    r"court.*opinion",
                    r"appellate",
                    r"supreme",
                    r"district.*court",
                ],
                "store_type": VectorStoreType.CASE_OPINIONS,
                "validation_types": [],
            },
            "deposition": {
                "patterns": [
                    r"deposition",
                    r"testimony",
                    r"witness",
                    r"transcript",
                    r"q\.",
                    r"a\.",
                    r"examination",
                ],
                "store_type": VectorStoreType.PRIMARY_EVIDENCE,
                "validation_types": [],
            },
            "expert_report": {
                "patterns": [
                    r"expert.*report",
                    r"analysis",
                    r"findings",
                    r"conclusion",
                    r"methodology",
                    r"credentials",
                ],
                "store_type": VectorStoreType.PRIMARY_EVIDENCE,
                "validation_types": [],
            },
        }

    def _initialize_validation_keywords(self) -> Dict[ValidationType, List[str]]:
        """Initialize keywords for validation type classification"""
        return {
            ValidationType.COMPLAINTS_AGAINST_TESLA: [
                "tesla",
                "elon musk",
                "autonomous vehicle",
                "self-driving",
                "electric vehicle",
                "automotive",
                "vehicle defect",
            ],
            ValidationType.CONTRACT_DISPUTES: [
                "breach",
                "contract",
                "agreement",
                "terms",
                "violation",
                "performance",
                "obligation",
                "consideration",
            ],
            ValidationType.PERSONAL_INJURY: [
                "injury",
                "accident",
                "negligence",
                "damages",
                "pain",
                "suffering",
                "medical",
                "treatment",
            ],
            ValidationType.EMPLOYMENT_CLAIMS: [
                "employment",
                "wrongful termination",
                "discrimination",
                "harassment",
                "wage",
                "overtime",
                "retaliation",
            ],
            ValidationType.INTELLECTUAL_PROPERTY: [
                "patent",
                "copyright",
                "trademark",
                "trade secret",
                "infringement",
                "license",
                "intellectual property",
            ],
        }

    async def process_intake_form(self, intake_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process intake form data and extract evidence for vectorization

        Args:
            intake_data: Intake form data from legal intake form

        Returns:
            Processing results with vector store information
        """
        try:
            start_time = datetime.now()

            # Extract case information
            case_info = {
                "case_name": intake_data.get("claim_description", "Unknown Case"),
                "plaintiff_name": intake_data.get("user_name", "Unknown Plaintiff"),
                "defendant_name": intake_data.get(
                    "opposing_party_names", "Unknown Defendant"
                ),
                "case_number": intake_data.get("case_number", ""),
                "jurisdiction": intake_data.get("jurisdiction", "general"),
                "claim_amount": intake_data.get("claim_amount", 0),
                "events_location": intake_data.get("events_location", ""),
                "events_date": intake_data.get("events_date", ""),
            }

            # Create comprehensive case description
            case_description = self._create_case_description(intake_data, case_info)

            # Classify and store in appropriate vector stores
            doc_id = await self.vector_store.ingest_evidence(
                content=case_description,
                metadata={
                    **case_info,
                    "source": "intake_form",
                    "content_type": "case_summary",
                    "processing_stage": "intake",
                },
                store_type=VectorStoreType.PRIMARY_EVIDENCE,
                validation_types=self._classify_validation_types(case_description),
            )

            processing_time = (datetime.now() - start_time).total_seconds()
            self.stats["documents_processed"] += 1
            self.stats["processing_time"] += processing_time

            return {
                "success": True,
                "document_id": doc_id,
                "case_info": case_info,
                "processing_time": processing_time,
                "vector_stores_updated": ["primary_evidence", "general_rag"],
            }

        except Exception as e:
            logger.error(f"Error processing intake form: {e}")
            self.stats["errors"] += 1
            return {"success": False, "error": str(e), "case_info": {}}

    async def process_document_evidence(
        self,
        file_path: str,
        metadata: Dict[str, Any],
        storage_tier: StorageTier = StorageTier.HOT,
    ) -> Dict[str, Any]:
        """
        Process document evidence with integrated cloud storage

        Args:
            file_path: Path to the document file
            metadata: Document metadata
            storage_tier: Storage tier for this document

        Returns:
            Processing results with storage information
        """
        try:
            start_time = datetime.now()

            # Read document content (simplified - in production would use proper document parsers)
            content = await self._read_document_content(file_path)

            if not content:
                return {"success": False, "error": "Could not read document content"}

            # Classify document type
            doc_type_info = self._classify_document_type(content)

            # Extract additional metadata
            enhanced_metadata = {
                **metadata,
                "file_path": file_path,
                "document_type": doc_type_info["type"],
                "source": "document_evidence",
                "processing_stage": "evidence_ingestion",
                "word_count": len(content.split()),
                "character_count": len(content),
                "storage_tier": storage_tier.value,
            }

            # Store with integrated cloud storage
            storage_result = (
                await self.integrated_ingestion.process_evidence_with_storage(
                    content=content,
                    metadata=enhanced_metadata,
                    store_type=doc_type_info["store_type"],
                    storage_tier=storage_tier,
                )
            )

            processing_time = (datetime.now() - start_time).total_seconds()
            self.stats["documents_processed"] += 1
            self.stats["vectors_created"] += 1
            self.stats["processing_time"] += processing_time

            if storage_result.get("success"):
                return {
                    "success": True,
                    "document_id": storage_result.get("doc_id"),
                    "storage_id": storage_result.get("storage_id"),
                    "document_type": doc_type_info["type"],
                    "vector_store": doc_type_info["store_type"].value,
                    "validation_types": [
                        vt.value for vt in doc_type_info["validation_types"]
                    ],
                    "local_path": storage_result.get("local_path"),
                    "cloud_url": storage_result.get("cloud_url"),
                    "storage_tier": storage_result.get("storage_tier"),
                    "processing_time": processing_time,
                }
            else:
                raise Exception(storage_result.get("error", "Storage failed"))

        except Exception as e:
            logger.error(f"Error processing document evidence: {e}")
            self.stats["errors"] += 1
            return {"success": False, "error": str(e)}

    async def process_research_round(
        self, research_content: str, round_number: int, case_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process research round content and accumulate in vector stores

        Args:
            research_content: Research findings and analysis
            round_number: Research round number
            case_context: Case context information

        Returns:
            Processing results
        """
        try:
            start_time = datetime.now()

            # Add research round to vector store
            doc_id = await self.vector_store.add_research_round(
                research_content=research_content,
                metadata={
                    **case_context,
                    "research_round": round_number,
                    "content_type": "research_findings",
                    "processing_stage": "research",
                },
                round_number=round_number,
            )

            processing_time = (datetime.now() - start_time).total_seconds()
            self.stats["documents_processed"] += 1
            self.stats["processing_time"] += processing_time

            return {
                "success": True,
                "document_id": doc_id,
                "research_round": round_number,
                "processing_time": processing_time,
            }

        except Exception as e:
            logger.error(f"Error processing research round: {e}")
            self.stats["errors"] += 1
            return {"success": False, "error": str(e)}

    async def batch_process_evidence(
        self, evidence_list: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Batch process multiple evidence items

        Args:
            evidence_list: List of evidence items with content and metadata

        Returns:
            Batch processing results
        """
        try:
            start_time = datetime.now()
            results = []

            # Process each evidence item
            for evidence in evidence_list:
                if evidence.get("type") == "intake_form":
                    result = await self.process_intake_form(evidence.get("data", {}))
                elif evidence.get("type") == "document":
                    result = await self.process_document_evidence(
                        evidence.get("file_path", ""), evidence.get("metadata", {})
                    )
                elif evidence.get("type") == "research":
                    result = await self.process_research_round(
                        evidence.get("content", ""),
                        evidence.get("round_number", 1),
                        evidence.get("case_context", {}),
                    )
                else:
                    result = {
                        "success": False,
                        "error": f"Unknown evidence type: {evidence.get('type')}",
                    }

                results.append(result)

            processing_time = (datetime.now() - start_time).total_seconds()

            # Calculate batch statistics
            successful = sum(1 for r in results if r.get("success", False))
            failed = len(results) - successful

            return {
                "success": True,
                "total_processed": len(results),
                "successful": successful,
                "failed": failed,
                "results": results,
                "batch_processing_time": processing_time,
            }

        except Exception as e:
            logger.error(f"Error in batch processing: {e}")
            return {
                "success": False,
                "error": str(e),
                "total_processed": 0,
                "successful": 0,
                "failed": 0,
            }

    def _create_case_description(
        self, intake_data: Dict[str, Any], case_info: Dict[str, Any]
    ) -> str:
        """Create comprehensive case description from intake data"""
        description_parts = []

        # Basic case information
        description_parts.append(f"Case: {case_info['case_name']}")
        description_parts.append(f"Plaintiff: {case_info['plaintiff_name']}")
        description_parts.append(f"Defendant: {case_info['defendant_name']}")

        if case_info.get("case_number"):
            description_parts.append(f"Case Number: {case_info['case_number']}")

        # Claim details
        claim_description = intake_data.get("claim_description", "")
        if claim_description:
            description_parts.append(f"Claim Description: {claim_description}")

        if case_info.get("claim_amount"):
            description_parts.append(f"Claim Amount: ${case_info['claim_amount']:,}")

        # Location and timing
        if case_info.get("events_location"):
            description_parts.append(f"Location: {case_info['events_location']}")

        if case_info.get("events_date"):
            description_parts.append(f"Date of Events: {case_info['events_date']}")

        # Jurisdiction
        if case_info.get("jurisdiction"):
            description_parts.append(f"Jurisdiction: {case_info['jurisdiction']}")

        # Additional details
        agreement_type = intake_data.get("agreement_type", "")
        if agreement_type:
            description_parts.append(f"Agreement Type: {agreement_type}")

        other_party_name = intake_data.get("other_party_name", "")
        if other_party_name:
            description_parts.append(f"Other Party: {other_party_name}")

        return "\n".join(description_parts)

    def _classify_document_type(self, content: str) -> Dict[str, Any]:
        """Classify document type based on content patterns"""
        content_lower = content.lower()

        for doc_type, info in self.document_patterns.items():
            for pattern in info["patterns"]:
                if re.search(pattern, content_lower, re.IGNORECASE):
                    return {
                        "type": doc_type,
                        "store_type": info["store_type"],
                        "validation_types": info["validation_types"],
                    }

        # Default classification
        return {
            "type": "general_document",
            "store_type": VectorStoreType.GENERAL_RAG,
            "validation_types": [],
        }

    def _classify_validation_types(self, content: str) -> List[ValidationType]:
        """Classify content for validation types based on keywords"""
        content_lower = content.lower()
        validation_types = []

        for validation_type, keywords in self.validation_keywords.items():
            keyword_matches = sum(1 for keyword in keywords if keyword in content_lower)
            if keyword_matches > 0:
                validation_types.append(validation_type)

        return validation_types

    async def _read_document_content(self, file_path: str) -> str:
        """Read document content (simplified implementation)"""
        try:
            path = Path(file_path)
            if path.exists():
                # In production, this would use proper document parsers
                # (PDF, DOCX, TXT, etc.)
                if path.suffix.lower() in [".txt", ".md"]:
                    return path.read_text(encoding="utf-8")
                else:
                    # Placeholder for binary document processing
                    return f"Document content from {path.name} (binary file - needs parser)"
            else:
                return ""
        except Exception as e:
            logger.error(f"Error reading document {file_path}: {e}")
            return ""

    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        return {
            **self.stats,
            "average_processing_time": (
                self.stats["processing_time"]
                / max(self.stats["documents_processed"], 1)
            ),
        }

    async def cleanup_processing_artifacts(self):
        """Clean up temporary processing artifacts"""
        try:
            # In production, this would clean up temporary files
            # created during document processing
            logger.info("Processing artifacts cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


# Integration function for existing intake processor
async def integrate_with_intake_processor(
    intake_data: Dict[str, Any],
    vector_store_manager: Optional[EnhancedVectorStoreManager] = None,
) -> Dict[str, Any]:
    """
    Integration function to add vector ingestion to existing intake processing

    Args:
        intake_data: Intake form data
        vector_store_manager: Optional vector store manager instance

    Returns:
        Processing results
    """
    try:
        pipeline = EvidenceIngestionPipeline(vector_store_manager)
        return await pipeline.process_intake_form(intake_data)
    except Exception as e:
        logger.error(f"Error integrating with intake processor: {e}")
        return {"success": False, "error": str(e)}


# Global pipeline instance
evidence_pipeline = EvidenceIngestionPipeline()
