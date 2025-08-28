"""
Enhanced Document Categorization System for LawyerFactory
Advanced document classification that goes beyond primary/secondary determination.
Creates specialized vector clusters for different legal document types.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class DocumentType(Enum):
    """Types of legal documents that can be categorized"""

    JUDGE_OPINION = "judge_opinion"
    PLAINTIFF_COMPLAINT = "plaintiff_complaint"
    DEFENDANT_ANSWER = "defendant_answer"
    DEFENDANT_MOTION = "defendant_motion"
    COUNTERCLAIM = "counterclaim"
    SETTLEMENT_AGREEMENT = "settlement_agreement"
    COURT_ORDER = "court_order"
    BRIEF = "brief"
    EXPERT_REPORT = "expert_report"
    DEPOSITION = "deposition"
    EVIDENCE = "evidence"
    UNKNOWN = "unknown"


class DocumentAuthority(Enum):
    """Authority level of legal documents"""

    BINDING_PRECEDENT = "binding_precedent"
    PERSUASIVE_PRECEDENT = "persuasive_precedent"
    SECONDARY_SOURCE = "secondary_source"
    FACT_EVIDENCE = "fact_evidence"
    PROCEDURAL = "procedural"


@dataclass
class DocumentMetadata:
    """Enhanced metadata for legal documents"""

    document_id: str
    document_type: DocumentType
    authority_level: DocumentAuthority
    defendant_name: Optional[str] = None
    plaintiff_name: Optional[str] = None
    case_number: Optional[str] = None
    court: Optional[str] = None
    jurisdiction: Optional[str] = None
    filing_date: Optional[str] = None
    confidence_score: float = 0.0
    extracted_entities: List[str] = field(default_factory=list)
    key_legal_issues: List[str] = field(default_factory=list)
    similarity_score: float = 0.0
    cluster_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class DocumentCluster:
    """A cluster of related legal documents"""

    cluster_id: str
    cluster_type: str  # e.g., "tesla_complaints", "negligence_opinions"
    documents: List[DocumentMetadata] = field(default_factory=list)
    centroid_vector: Optional[List[float]] = None
    defendant_name: Optional[str] = None
    typical_similarity_threshold: float = 0.6
    created_at: datetime = field(default_factory=datetime.now)


class EnhancedDocumentCategorizer:
    """
    Advanced document categorizer that creates specialized clusters
    for different types of legal documents and defendants.
    """

    def __init__(self, knowledge_graph=None):
        self.kg = knowledge_graph
        self.clusters: Dict[str, DocumentCluster] = {}

        # Document type patterns
        self.type_patterns = self._initialize_type_patterns()

        # Defendant-specific patterns (will be populated from intake form)
        self.defendant_patterns: Dict[str, List[str]] = {}

        # Authority level patterns
        self.authority_patterns = self._initialize_authority_patterns()

    def _initialize_type_patterns(self) -> Dict[DocumentType, List[str]]:
        """Initialize regex patterns for document type detection"""
        return {
            DocumentType.JUDGE_OPINION: [
                r"(?:opinion|memorandum|decision|order).*?(?:judge|court|justice)",
                r"(?:this\s+court|we\s+find|the\s+court\s+holds)",
                r"(?:affirm|reverse|remand|dismiss).*?(?:case|action|complaint)",
                r"case\s+no\.|cv-\d+|civil\s+action\s+no\.",
                r"(?:slip\s+opinion|unpublished\s+opinion|published\s+opinion)",
            ],
            DocumentType.PLAINTIFF_COMPLAINT: [
                r"complaint\s+for|complaint\s+against",
                r"plaintiff.*?(?:alleges|claims|complains)",
                r"count\s+(?:one|two|three|four|five|\d+)",
                r"(?:breach|negligence|fraud|defamation).*?(?:claim|cause|action)",
                r"wherefore.*?(?:plaintiff|petitioner).*?(?:prays|demands)",
            ],
            DocumentType.DEFENDANT_ANSWER: [
                r"answer\s+to.*?(?:complaint|petition)",
                r"defendant.*?(?:admits|denies|alleges)",
                r"affirmative\s+defenses?|defenses\s+to.*?(?:complaint|claim)",
                r"(?:general|special).*?(?:denial|denials)",
                r"come\s+now.*?(?:defendant|respondent)",
            ],
            DocumentType.DEFENDANT_MOTION: [
                r"motion\s+to.*?(?:dismiss|strike|compel|exclude)",
                r"defendant.*?(?:moves|requests).*?(?:court|judgment)",
                r"pursuant\s+to.*?(?:rule|code).*?(?:motion|request)",
                r"(?:notice|memorandum).*?(?:motion|points?\s+and\s+authorities)",
            ],
            DocumentType.COUNTERCLAIM: [
                r"counterclaim|counter-claim|cross-claim",
                r"(?:defendant|respondent).*?(?:counterclaims|alleges)",
                r"reciprocal.*?(?:claim|action)|set-off|offset",
            ],
            DocumentType.COURT_ORDER: [
                r"order\s+granting|order\s+denying|court\s+order",
                r"(?:this|the)\s+court\s+orders?|ordered.*?as\s+follows",
                r"judgment\s+entered|final\s+judgment|summary\s+judgment",
            ],
            DocumentType.BRIEF: [
                r"(?:opening|answering|reply|amicus).*?(?:brief|memorandum)",
                r"points?\s+and\s+authorities|statement\s+of\s+facts",
                r"(?:appellant|appellee|petitioner|respondent).*?(?:brief|memorandum)",
            ],
        }

    def _initialize_authority_patterns(self) -> Dict[DocumentAuthority, List[str]]:
        """Initialize patterns for determining document authority"""
        return {
            DocumentAuthority.BINDING_PRECEDENT: [
                r"(?:supreme\s+court|appellate\s+court|court\s+of\s+appeals)",
                r"published\s+opinion|official\s+reporter",
                r"(?:en\s+banc|full\s+court).*?(?:decision|opinion)",
            ],
            DocumentAuthority.PERSUASIVE_PRECEDENT: [
                r"(?:district\s+court|trial\s+court|unpublished\s+opinion)",
                r"(?:memorandum\s+opinion|slip\s+opinion)",
                r"other\s+jurisdiction|foreign\s+court",
            ],
            DocumentAuthority.SECONDARY_SOURCE: [
                r"(?:law\s+review|legal\s+commentary|annotation)",
                r"(?:treatise|hornbook|restatement)",
                r"legal\s+encyclopedia|american\s+jurisprudence",
            ],
            DocumentAuthority.FACT_EVIDENCE: [
                r"(?:deposition|affidavit|declaration)",
                r"expert\s+report|witness\s+statement",
                r"(?:exhibit|attachment|documentary\s+evidence)",
            ],
        }

    def categorize_document(
        self, text: str, filename: str = "", defendant_hint: Optional[str] = None
    ) -> DocumentMetadata:
        """
        Categorize a legal document with enhanced metadata extraction

        Args:
            text: Document text content
            filename: Original filename
            defendant_hint: Hint about defendant name from context

        Returns:
            DocumentMetadata with comprehensive classification
        """
        try:
            # Clean and normalize text
            clean_text = self._clean_text(text)

            # Detect document type
            doc_type = self._detect_document_type(clean_text, filename)

            # Detect authority level
            authority = self._detect_authority_level(clean_text, doc_type)

            # Extract entities
            entities = self._extract_entities(clean_text)

            # Extract defendant/plaintiff names
            defendant_name = self._extract_defendant_name(clean_text, defendant_hint)
            plaintiff_name = self._extract_plaintiff_name(clean_text)

            # Extract legal issues
            legal_issues = self._extract_legal_issues(clean_text)

            # Generate document ID
            doc_id = self._generate_document_id(filename, clean_text)

            # Calculate confidence
            confidence = self._calculate_confidence(clean_text, doc_type)

            return DocumentMetadata(
                document_id=doc_id,
                document_type=doc_type,
                authority_level=authority,
                defendant_name=defendant_name,
                plaintiff_name=plaintiff_name,
                confidence_score=confidence,
                extracted_entities=entities,
                key_legal_issues=legal_issues,
            )

        except Exception as e:
            logger.error(f"Document categorization failed: {e}")
            return DocumentMetadata(
                document_id=self._generate_document_id(filename, text),
                document_type=DocumentType.UNKNOWN,
                authority_level=DocumentAuthority.SECONDARY_SOURCE,
                confidence_score=0.0,
            )

    def _detect_document_type(self, text: str, filename: str = "") -> DocumentType:
        """Detect the type of legal document"""
        text_lower = text.lower()
        filename_lower = filename.lower()

        # Check filename first (often more reliable)
        filename_indicators = {
            DocumentType.PLAINTIFF_COMPLAINT: ["complaint", "claim", "petition"],
            DocumentType.DEFENDANT_ANSWER: ["answer", "response"],
            DocumentType.DEFENDANT_MOTION: ["motion", "demurrer"],
            DocumentType.COUNTERCLAIM: ["counterclaim", "crossclaim"],
            DocumentType.BRIEF: ["brief", "memorandum"],
            DocumentType.JUDGE_OPINION: ["opinion", "decision", "order"],
            DocumentType.DEPOSITION: ["deposition", "transcript"],
            DocumentType.EXPERT_REPORT: ["expert", "report"],
        }

        for doc_type, indicators in filename_indicators.items():
            if any(indicator in filename_lower for indicator in indicators):
                return doc_type

        # Check text content
        type_scores = {}
        for doc_type, patterns in self.type_patterns.items():
            score = sum(len(re.findall(pattern, text_lower)) for pattern in patterns)
            if score > 0:
                type_scores[doc_type] = score

        if type_scores:
            return max(type_scores.keys(), key=lambda x: type_scores[x])

        return DocumentType.UNKNOWN

    def _detect_authority_level(
        self, text: str, doc_type: DocumentType
    ) -> DocumentAuthority:
        """Detect the authority level of the document"""
        text_lower = text.lower()

        # Document type often determines authority
        type_authority_map = {
            DocumentType.JUDGE_OPINION: DocumentAuthority.BINDING_PRECEDENT,
            DocumentType.PLAINTIFF_COMPLAINT: DocumentAuthority.FACT_EVIDENCE,
            DocumentType.DEFENDANT_ANSWER: DocumentAuthority.FACT_EVIDENCE,
            DocumentType.BRIEF: DocumentAuthority.SECONDARY_SOURCE,
            DocumentType.EXPERT_REPORT: DocumentAuthority.FACT_EVIDENCE,
            DocumentType.DEPOSITION: DocumentAuthority.FACT_EVIDENCE,
        }

        if doc_type in type_authority_map:
            return type_authority_map[doc_type]

        # Check authority patterns
        authority_scores = {}
        for authority, patterns in self.authority_patterns.items():
            score = sum(len(re.findall(pattern, text_lower)) for pattern in patterns)
            if score > 0:
                authority_scores[authority] = score

        if authority_scores:
            return max(authority_scores.keys(), key=lambda x: authority_scores[x])

        return DocumentAuthority.SECONDARY_SOURCE

    def _extract_defendant_name(
        self, text: str, defendant_hint: Optional[str] = None
    ) -> Optional[str]:
        """Extract defendant name from document"""
        if defendant_hint:
            # If we have a hint, look for it in the text
            if defendant_hint.lower() in text.lower():
                return defendant_hint

        # Look for common defendant patterns
        patterns = [
            r"defendant\s+([A-Z][a-zA-Z\s,&]+?)(?:\s|$|,|\.)",
            r"against\s+([A-Z][a-zA-Z\s,&]+?)(?:\s|$|,|\.)",
            r"v\.?\s*([A-Z][a-zA-Z\s,&]+?)(?:\s|$|,|\.)",
            r"sued\s+([A-Z][a-zA-Z\s,&]+?)(?:\s|$|,|\.)",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                # Return the longest match (likely most complete name)
                return max(matches, key=len).strip()

        return None

    def _extract_plaintiff_name(self, text: str) -> Optional[str]:
        """Extract plaintiff name from document"""
        patterns = [
            r"plaintiff\s+([A-Z][a-zA-Z\s,&]+?)(?:\s|$|,|\.)",
            r"petitioner\s+([A-Z][a-zA-Z\s,&]+?)(?:\s|$|,|\.)",
            r"by\s+([A-Z][a-zA-Z\s,&]+?)(?:\s|$|,|\.)",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                return max(matches, key=len).strip()

        return None

    def _extract_legal_issues(self, text: str) -> List[str]:
        """Extract key legal issues from document"""
        # Common legal issue keywords
        issue_keywords = [
            "negligence",
            "breach of contract",
            "fraud",
            "defamation",
            "intentional infliction",
            "premises liability",
            "product liability",
            "professional malpractice",
            "civil rights",
            "discrimination",
            "wrongful termination",
            "harassment",
            "assault",
            "battery",
            "false imprisonment",
            "conversion",
            "trespass",
            "nuisance",
        ]

        found_issues = []
        text_lower = text.lower()

        for issue in issue_keywords:
            if issue in text_lower:
                found_issues.append(issue)

        return found_issues

    def _extract_entities(self, text: str) -> List[str]:
        """Extract named entities from document"""
        # Simple entity extraction - look for capitalized words/phrases
        entity_patterns = [
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",  # Person/Company names
            r"([A-Z][A-Z\s]+(?:Inc|Corp|Ltd|LLC|Company))",  # Company suffixes
        ]

        entities = set()
        for pattern in entity_patterns:
            matches = re.findall(pattern, text)
            entities.update(matches)

        return list(entities)

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text for processing"""
        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text)
        # Remove special characters but keep basic punctuation
        text = re.sub(r"[^\w\s.,;:!?-]", " ", text)
        return text.strip()

    def _calculate_confidence(self, text: str, doc_type: DocumentType) -> float:
        """Calculate confidence score for document classification"""
        if doc_type == DocumentType.UNKNOWN:
            return 0.0

        # Base confidence from pattern matches
        base_confidence = 0.5

        # Boost confidence based on text length and structure
        if len(text) > 1000:
            base_confidence += 0.2
        if len(text) > 5000:
            base_confidence += 0.1

        # Boost confidence for documents with clear legal structure
        legal_indicators = ["court", "judge", "law", "case", "plaintiff", "defendant"]
        indicator_count = sum(
            1 for indicator in legal_indicators if indicator in text.lower()
        )
        base_confidence += min(0.3, indicator_count * 0.05)

        return min(1.0, base_confidence)

    def _generate_document_id(self, filename: str, text: str) -> str:
        """Generate unique document ID"""
        import hashlib

        content_hash = hashlib.md5(text.encode()).hexdigest()[:8]
        filename_part = Path(filename).stem if filename else "unknown"
        return f"{filename_part}_{content_hash}"

    def create_cluster_for_defendant(self, defendant_name: str) -> DocumentCluster:
        """Create a new cluster for a specific defendant"""
        cluster_id = f"{defendant_name.lower().replace(' ', '_')}_complaints"
        cluster = DocumentCluster(
            cluster_id=cluster_id,
            cluster_type=f"{defendant_name}_complaints",
            defendant_name=defendant_name,
        )
        self.clusters[cluster_id] = cluster
        return cluster

    def add_to_cluster(self, document: DocumentMetadata, cluster_id: str) -> bool:
        """Add document to specified cluster"""
        if cluster_id not in self.clusters:
            logger.warning(f"Cluster {cluster_id} not found")
            return False

        document.cluster_id = cluster_id
        self.clusters[cluster_id].documents.append(document)
        return True

    def find_similar_documents(
        self, document: DocumentMetadata, similarity_threshold: float = 0.6
    ) -> List[DocumentMetadata]:
        """Find similar documents in the same cluster"""
        if not document.cluster_id or document.cluster_id not in self.clusters:
            return []

        cluster = self.clusters[document.cluster_id]
        similar_docs = []

        for existing_doc in cluster.documents:
            if existing_doc.document_id == document.document_id:
                continue

            # Simple similarity calculation based on shared entities and legal issues
            shared_entities = set(document.extracted_entities) & set(
                existing_doc.extracted_entities
            )
            shared_issues = set(document.key_legal_issues) & set(
                existing_doc.key_legal_issues
            )

            entity_similarity = len(shared_entities) / max(
                len(document.extracted_entities), 1
            )
            issue_similarity = len(shared_issues) / max(
                len(document.key_legal_issues), 1
            )

            overall_similarity = (entity_similarity + issue_similarity) / 2

            if overall_similarity >= similarity_threshold:
                existing_doc.similarity_score = overall_similarity
                similar_docs.append(existing_doc)

        return similar_docs
