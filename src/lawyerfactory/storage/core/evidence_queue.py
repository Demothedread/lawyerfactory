"""
Enhanced Evidence Classification & Queue Management

Extends evidence_ingestion.py with intelligent primary/secondary classification,
batch queue processing, and case-type-specific categorization.

Implements the critical early-stage evidence triage that feeds downstream
analysis components (ShotList, ClaimsMatrix).
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from lawyerfactory.config.case_types import (
    CaseType,
    EvidenceClass,
    PrimaryEvidenceType,
    SecondaryEvidenceType,
    classify_primary_evidence_type,
    classify_secondary_evidence_type,
    get_case_type_from_string,
    is_evidence_primary,
)

logger = logging.getLogger(__name__)


class EvidenceQueueItem:
    """Represents a single evidence item in the processing queue"""

    def __init__(
        self,
        file_path: str,
        filename: str,
        case_id: str,
        metadata: Dict[str, Any],
        case_type: CaseType,
        queue_position: int,
    ):
        self.id = str(uuid4())
        self.file_path = file_path
        self.filename = filename
        self.case_id = case_id
        self.metadata = metadata
        self.case_type = case_type
        self.queue_position = queue_position
        self.status = "queued"  # queued, processing, classified, summarized, vectorized, complete, error
        self.progress = 0
        self.evidence_class: Optional[EvidenceClass] = None
        self.evidence_type: Optional[str] = None
        self.classification_confidence: float = 0.0
        self.summary: Optional[str] = None
        self.extracted_metadata: Dict[str, Any] = {}
        self.error_message: Optional[str] = None
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "filename": self.filename,
            "case_id": self.case_id,
            "status": self.status,
            "progress": self.progress,
            "queue_position": self.queue_position,
            "evidence_class": self.evidence_class.value if self.evidence_class else None,
            "evidence_type": self.evidence_type,
            "classification_confidence": self.classification_confidence,
            "summary": self.summary,
            "extracted_metadata": self.extracted_metadata,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class EvidenceClassifier:
    """
    Intelligent evidence classifier that determines primary/secondary
    and case-type-specific subcategories
    """

    def __init__(self):
        self.primary_keywords = self._initialize_primary_keywords()
        self.secondary_keywords = self._initialize_secondary_keywords()

    def _initialize_primary_keywords(self) -> Dict[str, List[str]]:
        """Keywords indicating primary evidence"""
        return {
            "communications": [
                "email",
                "message",
                "text",
                "phone",
                "call",
                "conversation",
                "discussion",
                "meeting notes",
                "correspondence",
            ],
            "documents": [
                "contract",
                "agreement",
                "terms",
                "conditions",
                "invoice",
                "receipt",
                "purchase order",
                "warranty",
            ],
            "legal": [
                "summons",
                "complaint",
                "warrant",
                "court order",
                "deposition",
                "affidavit",
                "subpoena",
            ],
            "evidence": [
                "photo",
                "video",
                "footage",
                "recording",
                "report",
                "inspection",
                "expert",
                "damage",
            ],
            "medical": [
                "medical",
                "diagnosis",
                "treatment",
                "patient",
                "doctor",
                "hospital",
                "clinical",
                "health",
            ],
            "technical": [
                "log",
                "debug",
                "error",
                "exception",
                "traceback",
                "code",
                "software",
                "system",
                "database",
            ],
        }

    def _initialize_secondary_keywords(self) -> Dict[str, List[str]]:
        """Keywords indicating secondary evidence"""
        return {
            "case_law": [
                "held that",
                "decided",
                "opinion",
                "judgment",
                "verdict",
                "affirmed",
                "reversed",
                "syllabus",
                "headnote",
            ],
            "statutes": [
                "section",
                "subsection",
                "statute",
                "enacted",
                "amended",
                "code",
                "usc",
                "u.s.c.",
            ],
            "regulations": [
                "regulation",
                "cfr",
                "federal register",
                "administrative",
                "rule",
                "guideline",
            ],
            "academic": [
                "abstract",
                "keywords",
                "journal",
                "research",
                "study",
                "analysis",
                "literature review",
                "methodology",
            ],
        }

    def classify_evidence(
        self,
        content: str,
        filename: str,
        source_url: str = "",
        metadata: Dict[str, Any] = None,
        case_type: CaseType = CaseType.NEGLIGENCE,
    ) -> Tuple[EvidenceClass, str, float]:
        """
        Classify evidence as primary or secondary with confidence score

        Returns:
            Tuple of (EvidenceClass, evidence_type, confidence_score)
        """
        if metadata is None:
            metadata = {}

        # Check metadata hints first
        if is_evidence_primary(metadata):
            # Classify primary evidence type
            primary_type = classify_primary_evidence_type(content, filename, case_type)
            return (
                EvidenceClass.PRIMARY,
                primary_type.value,
                0.95,  # High confidence when uploaded by user
            )
        else:
            # Classify secondary evidence type
            secondary_type = classify_secondary_evidence_type(content, source_url, filename)
            return (
                EvidenceClass.SECONDARY,
                secondary_type.value,
                0.85,  # Slightly lower confidence for secondary
            )

    def calculate_confidence_score(self, evidence_class: EvidenceClass, matches: int) -> float:
        """Calculate confidence score based on keyword matches"""
        base_confidence = 0.5 + (min(matches, 5) * 0.1)  # 0.5 to 1.0
        return min(base_confidence, 0.99)


class EvidenceProcessingQueue:
    """
    Manages batch processing of evidence with ordered queue,
    status tracking, and progress callbacks
    """

    def __init__(self, max_concurrent_jobs: int = 3, case_type: CaseType = CaseType.NEGLIGENCE):
        self.max_concurrent_jobs = max_concurrent_jobs
        self.case_type = case_type
        self.queue: List[EvidenceQueueItem] = []
        self.processing: Dict[str, EvidenceQueueItem] = {}
        self.completed: List[EvidenceQueueItem] = []
        self.classifier = EvidenceClassifier()
        self.status_callbacks: List[callable] = []

    def add_to_queue(
        self,
        file_path: str,
        filename: str,
        case_id: str,
        metadata: Dict[str, Any],
    ) -> EvidenceQueueItem:
        """Add evidence item to processing queue"""
        queue_position = len(self.queue) + len(self.processing)
        item = EvidenceQueueItem(
            file_path=file_path,
            filename=filename,
            case_id=case_id,
            metadata=metadata,
            case_type=self.case_type,
            queue_position=queue_position,
        )
        self.queue.append(item)
        logger.info(f"Added to queue: {filename} (position {queue_position})")
        return item

    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status"""
        return {
            "total": len(self.queue) + len(self.processing) + len(self.completed),
            "queued": len(self.queue),
            "processing": len(self.processing),
            "completed": len(self.completed),
            "queue_items": [item.to_dict() for item in self.queue],
            "processing_items": [item.to_dict() for item in self.processing.values()],
            "completed_items": [item.to_dict() for item in self.completed[-10:]],  # Last 10
        }

    async def process_queue(self, evidence_ingestion_pipeline) -> List[EvidenceQueueItem]:
        """
        Process all queued items with concurrent job management

        Returns:
            List of processed items
        """
        processed_items = []

        while self.queue or self.processing:
            # Start new jobs if capacity available
            while len(self.processing) < self.max_concurrent_jobs and self.queue:
                item = self.queue.pop(0)
                self.processing[item.id] = item
                asyncio.create_task(
                    self._process_item(item, evidence_ingestion_pipeline)
                )

            # Wait a bit for processing
            await asyncio.sleep(0.5)

            # Check for completed items and notify
            completed_ids = [
                item_id
                for item_id, item in self.processing.items()
                if item.status == "complete" or item.status == "error"
            ]
            for item_id in completed_ids:
                item = self.processing.pop(item_id)
                self.completed.append(item)
                processed_items.append(item)
                self._notify_status_update(item)

        return processed_items

    async def _process_item(
        self, item: EvidenceQueueItem, pipeline
    ) -> None:
        """Process a single evidence item through classification and ingestion"""
        try:
            item.status = "processing"
            item.progress = 10
            self._notify_status_update(item)

            # Read file content
            item.progress = 20
            try:
                with open(item.file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except UnicodeDecodeError:
                content = "(Binary file - not text searchable)"

            item.progress = 30

            # Classify evidence
            evidence_class, evidence_type, confidence = self.classifier.classify_evidence(
                content=content,
                filename=item.filename,
                metadata=item.metadata,
                case_type=self.case_type,
            )

            item.evidence_class = evidence_class
            item.evidence_type = evidence_type
            item.classification_confidence = confidence
            item.progress = 50
            self._notify_status_update(item)

            # Extract metadata
            item.extracted_metadata = self._extract_metadata(content, item.filename)
            item.progress = 65

            # Summarize content
            if len(content) > 100:
                item.summary = self._create_summary(content, evidence_type)
            else:
                item.summary = content[:200]

            item.progress = 85
            self._notify_status_update(item)

            # Vectorize (placeholder - actual vectorization handled by ingestion pipeline)
            item.status = "complete"
            item.progress = 100
            logger.info(f"Processed: {item.filename} - {evidence_class.value}/{evidence_type}")

        except Exception as e:
            item.status = "error"
            item.error_message = str(e)
            logger.error(f"Error processing {item.filename}: {str(e)}")

        finally:
            self._notify_status_update(item)

    def _extract_metadata(self, content: str, filename: str) -> Dict[str, Any]:
        """Extract metadata from content and filename"""
        metadata = {
            "filename": filename,
            "content_length": len(content),
            "lines": content.count("\n"),
            "extraction_timestamp": datetime.utcnow().isoformat(),
        }

        # Extract key information based on content type
        if "email" in filename.lower() or "from:" in content.lower():
            # Extract email headers
            for line in content.split("\n")[:20]:
                if line.startswith("From:"):
                    metadata["from"] = line.replace("From:", "").strip()
                if line.startswith("To:"):
                    metadata["to"] = line.replace("To:", "").strip()
                if line.startswith("Date:"):
                    metadata["date"] = line.replace("Date:", "").strip()

        # Extract dates in common formats
        import re
        dates = re.findall(r"\d{1,2}/\d{1,2}/\d{2,4}", content)
        if dates:
            metadata["dates_found"] = dates[:5]

        return metadata

    def _create_summary(self, content: str, evidence_type: str) -> str:
        """Create summary of content"""
        # Simple summarization: first 200 chars + last 100 chars
        if len(content) > 300:
            return f"{content[:200]}...[{evidence_type}]...{content[-100:]}"
        return content[:200]

    def register_status_callback(self, callback: callable) -> None:
        """Register callback for status updates"""
        self.status_callbacks.append(callback)

    def _notify_status_update(self, item: EvidenceQueueItem) -> None:
        """Notify all registered callbacks of status update"""
        item.updated_at = datetime.utcnow()
        for callback in self.status_callbacks:
            try:
                callback(item)
            except Exception as e:
                logger.error(f"Error in status callback: {str(e)}")


class SecondaryEvidenceAutoGenerator:
    """
    Automatically generates secondary evidence for case type
    Fetches case law, statutes, and research materials
    """

    def __init__(self):
        self.research_sources = self._initialize_research_sources()

    def _initialize_research_sources(self) -> Dict[str, Dict[str, str]]:
        """Initialize research source URLs and APIs"""
        return {
            "case_law": {
                "courtlistener": "https://www.courtlistener.com/api/v3/search/",
                "google_scholar": "https://scholar.google.com/scholar?",
            },
            "statutes": {
                "congress": "https://www.congress.gov/",
                "uscode": "https://www.law.cornell.edu/uscode/",
            },
            "regulations": {
                "ecfr": "https://www.ecfr.gov/",
                "federal_register": "https://www.federalregister.gov/",
            },
            "journals": {
                "researchgate": "https://www.researchgate.net/",
                "ssrn": "https://papers.ssrn.com/",
            },
        }

    async def generate_secondary_evidence_for_case(
        self, case_type: CaseType, research_areas: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Auto-generate secondary evidence recommendations for case type

        Returns:
            List of secondary evidence items with source URLs
        """
        secondary_items = []

        # For each research area, generate recommendations
        for area in research_areas:
            # Placeholder: In production, would query actual legal research APIs
            items = await self._fetch_research_for_area(area)
            secondary_items.extend(items)

        return secondary_items

    async def _fetch_research_for_area(self, area: str) -> List[Dict[str, Any]]:
        """Fetch research materials for specific area"""
        # Placeholder implementation
        # In production: would make HTTP requests to legal research APIs
        return [
            {
                "title": f"Research on {area}",
                "source_url": f"https://example.com/{area}",
                "evidence_class": "secondary",
                "evidence_type": "case_law",
                "description": f"Relevant case law and authority on {area}",
            }
        ]


# Module-level queue instance (would be managed by Flask app)
_evidence_queues: Dict[str, EvidenceProcessingQueue] = {}


def get_or_create_queue(case_id: str, case_type: str) -> EvidenceProcessingQueue:
    """Get or create evidence processing queue for case"""
    if case_id not in _evidence_queues:
        case_type_enum = get_case_type_from_string(case_type)
        _evidence_queues[case_id] = EvidenceProcessingQueue(case_type=case_type_enum)
    return _evidence_queues[case_id]


def get_queue_status(case_id: str) -> Optional[Dict[str, Any]]:
    """Get status of evidence queue for case"""
    if case_id in _evidence_queues:
        return _evidence_queues[case_id].get_queue_status()
    return None
