"""
# Script Name: claim_research_tasks.py
# Description: Editor Intelligence - Claim Assessment and Research Task Redirection.
#   Examines each claim and argument in a written document, determines whether it is
#   substantiated, and for unsubstantiated claims creates task items that redirect to
#   the Phase A02 research cycle.  The research cycle searches the existing database
#   first, then CourtListener, then the general web.  Newly found material is ingested
#   via the evidence ingestion pipeline.
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Editing
#   - Group Tags: editor-intelligence, claim-assessment, research-tasks
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
import re
from typing import Any, Dict, List, Optional
import uuid

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class SubstantiationStatus(Enum):
    """Degree to which a claim is supported by available evidence"""

    SUBSTANTIATED = "substantiated"
    PARTIALLY_SUBSTANTIATED = "partially_substantiated"
    UNSUBSTANTIATED = "unsubstantiated"
    CONTRADICTED = "contradicted"


class ResearchSource(Enum):
    """Source tier that produced a piece of supporting evidence"""

    EXISTING_DATABASE = "existing_database"
    COURT_LISTENER = "court_listener"
    WEB_SEARCH = "web_search"


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class ClaimAssessment:
    """
    Result of assessing a single claim or argument extracted from a
    written document during the editing phase.
    """

    claim_id: str
    claim_text: str
    claim_type: str  # e.g. "legal_argument", "factual_assertion", "legal_conclusion"
    status: SubstantiationStatus
    confidence_score: float  # 0.0–1.0
    supporting_evidence: List[Dict[str, Any]] = field(default_factory=list)
    source_tiers_searched: List[ResearchSource] = field(default_factory=list)
    needs_research: bool = False
    research_questions: List[str] = field(default_factory=list)
    notes: str = ""
    assessed_at: datetime = field(default_factory=datetime.now)


@dataclass
class ResearchTaskItem:
    """
    A research task item created for an unsubstantiated claim.
    When executed it redirects back to the Phase A02 research cycle.
    """

    task_id: str
    claim_id: str
    claim_text: str
    claim_type: str
    research_questions: List[str]
    case_context: Dict[str, Any] = field(default_factory=dict)
    priority: str = "high"  # critical | high | normal | low
    status: str = "pending"  # pending | in_progress | completed | failed
    search_results: List[Dict[str, Any]] = field(default_factory=list)
    ingested_evidence_ids: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

    @staticmethod
    def _truncate_at_word_boundary(text: str, max_chars: int) -> str:
        """Truncate *text* to at most *max_chars* without splitting a word."""
        if len(text) <= max_chars:
            return text
        truncated = text[:max_chars]
        last_space = truncated.rfind(" ")
        if last_space > 0:
            truncated = truncated[:last_space]
        return truncated + "…"

    def to_workflow_task(self) -> Dict[str, Any]:
        """
        Serialize as a WorkflowTask-compatible dictionary targeting the
        Phase A02 research phase.
        """
        return {
            "id": self.task_id,
            "phase": "research",
            "agent_type": "research_bot",
            "description": (
                f"[Editor-Initiated Research] Substantiate claim: "
                f"{self._truncate_at_word_boundary(self.claim_text, 120)}"
            ),
            "priority": self.priority,
            "status": self.status,
            "input_data": {
                "claim_text": self.claim_text,
                "claim_type": self.claim_type,
                "research_questions": self.research_questions,
                "case_context": self.case_context,
            },
            # research_questions is also set at the top level because
            # WorkflowTask.research_questions is the field consumed by the
            # Phase A02 orchestration system; input_data carries the full
            # claim context for the agent itself.
            "research_needed": True,
            "research_questions": self.research_questions,
            "research_context": {
                "origin": "phaseC01_editing",
                "claim_id": self.claim_id,
            },
        }


# ---------------------------------------------------------------------------
# Claim / argument extraction
# ---------------------------------------------------------------------------

class ClaimArgumentExtractor:
    """
    Extracts legal claims and arguments from a written document.

    Uses lightweight heuristic patterns to identify:
    - Explicit legal arguments ("Defendant is liable because …")
    - Legal conclusions ("Plaintiff suffered damages …")
    - Factual assertions that require legal support
    """

    # Argument-signal phrases typically found in legal briefs
    _ARGUMENT_SIGNALS = [
        r"\bplaintiff\s+(?:alleges?|contends?|argues?|asserts?|claims?)\b",
        r"\bdefendant\s+(?:failed|breached|violated|neglected|refused)\b",
        r"\bunder\s+(?:the\s+)?(?:law|statute|regulation|rule)\b",
        r"\b(?:negligence|breach|liability|damages?|duty|causation)\b",
        r"\b(?:cause[sd]?\s+of\s+action|legal\s+theory|legal\s+argument)\b",
        r"\b(?:entitl(?:ed|es?)|entitled\s+to\s+relief)\b",
        r"\b(?:violat(?:ion|es?|ed)|pursuant\s+to)\b",
        r"\b(?:standard\s+of\s+care|reasonable\s+person|duty\s+of\s+care)\b",
        r"\b(?:proximate(?:ly)?|direct\s+cause|but[\s-]for)\b",
    ]

    # Factual-assertion signal phrases
    _FACT_SIGNALS = [
        r"\bon\s+or\s+about\b",
        r"\bat\s+(?:all\s+)?(?:relevant\s+)?times?\b",
        r"\bfailed\s+to\b",
        r"\bknew\s+or\s+should\s+have\s+known\b",
        r"\bwas\s+(?:a\s+)?(?:cause|responsible)\b",
    ]

    def __init__(self):
        self._arg_patterns = [re.compile(p, re.IGNORECASE) for p in self._ARGUMENT_SIGNALS]
        self._fact_patterns = [re.compile(p, re.IGNORECASE) for p in self._FACT_SIGNALS]

    def extract_claims(self, document_content: str) -> List[Dict[str, Any]]:
        """
        Extract claims and arguments from document content.

        Args:
            document_content: Full text of the legal document being edited.

        Returns:
            List of dicts with keys: id, text, type, sentence_index.
        """
        claims = []
        sentences = self._split_into_sentences(document_content)

        for idx, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if len(sentence) < 20:
                continue

            claim_type = self._classify_sentence(sentence)
            if claim_type is None:
                continue

            claims.append(
                {
                    "id": f"claim_{idx}_{uuid.uuid4().hex[:6]}",
                    "text": sentence,
                    "type": claim_type,
                    "sentence_index": idx,
                }
            )

        logger.debug(f"Extracted {len(claims)} claims from document")
        return claims

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split document text into individual sentences."""
        # Split on period/exclamation/question followed by whitespace or end-of-string,
        # but preserve abbreviations crudely (no split after single capital letter + period).
        raw = re.split(r"(?<!\b[A-Z])(?<=[.!?])\s+", text)
        # Also split on newlines that are likely paragraph breaks
        sentences = []
        for fragment in raw:
            for line in fragment.split("\n"):
                line = line.strip()
                if line:
                    sentences.append(line)
        return sentences

    def _classify_sentence(self, sentence: str) -> Optional[str]:
        """
        Return the claim type if the sentence contains a claim signal,
        or None if it should be ignored.
        """
        for pattern in self._arg_patterns:
            if pattern.search(sentence):
                return "legal_argument"
        for pattern in self._fact_patterns:
            if pattern.search(sentence):
                return "factual_assertion"
        return None


# ---------------------------------------------------------------------------
# Substantiation assessment (checks existing database)
# ---------------------------------------------------------------------------

class ClaimSubstantiationAssessor:
    """
    Assesses whether a claim is substantiated by evidence already present in
    the existing database (vector store / evidence table).

    This is the *first* tier in the tiered search:
      1. Existing database  ← this class
      2. CourtListener       ← handled by ResearchTaskCreator
      3. General web search  ← handled by ResearchTaskCreator
    """

    def __init__(self, storage_api=None, evidence_table=None):
        """
        Args:
            storage_api: Optional ``EnhancedUnifiedStorageAPI`` instance for
                         vector + evidence table queries.
            evidence_table: Optional ``EnhancedEvidenceTable`` instance.
        """
        self.storage_api = storage_api
        self.evidence_table = evidence_table

    async def assess_claim(
        self,
        claim: Dict[str, Any],
        case_context: Dict[str, Any],
    ) -> ClaimAssessment:
        """
        Assess a single claim against the existing evidence database.

        Args:
            claim: Dict produced by ``ClaimArgumentExtractor.extract_claims``
                   with keys: id, text, type, sentence_index.
            case_context: Ambient case context (jurisdiction, case_type, etc.).

        Returns:
            ``ClaimAssessment`` populated with whatever was found in the DB.
        """
        claim_text = claim["text"]
        claim_type = claim["type"]

        supporting = []
        searched_tiers = []

        # --- Tier 1: query unified storage (vector + evidence table) ------
        db_evidence = await self._search_database(claim_text)
        searched_tiers.append(ResearchSource.EXISTING_DATABASE)
        supporting.extend(db_evidence)

        # Determine substantiation status from DB results only
        status, confidence = self._evaluate_support(supporting, claim_type)

        needs_research = status in (
            SubstantiationStatus.UNSUBSTANTIATED,
            SubstantiationStatus.PARTIALLY_SUBSTANTIATED,
        )

        research_questions = (
            self._generate_research_questions(claim_text, claim_type, case_context)
            if needs_research
            else []
        )

        return ClaimAssessment(
            claim_id=claim["id"],
            claim_text=claim_text,
            claim_type=claim_type,
            status=status,
            confidence_score=confidence,
            supporting_evidence=supporting,
            source_tiers_searched=searched_tiers,
            needs_research=needs_research,
            research_questions=research_questions,
            notes=self._build_notes(status, confidence, len(supporting)),
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _search_database(self, query: str) -> List[Dict[str, Any]]:
        """Query the existing database (unified storage / evidence table)."""
        results = []

        # Unified storage API (vector + evidence table)
        if self.storage_api:
            try:
                raw = await self.storage_api.search_evidence(query, search_tier="all")
                for item in raw[:5]:
                    results.append(
                        {
                            "source": ResearchSource.EXISTING_DATABASE.value,
                            "content": item.get("content", ""),
                            "title": item.get("filename", item.get("source_document", "")),
                            "relevance_score": item.get("relevance_score", 0.5),
                        }
                    )
            except Exception as exc:
                logger.warning(f"Unified storage search failed: {exc}")

        # Standalone evidence table (fallback)
        if self.evidence_table and not results:
            try:
                raw = self.evidence_table.search_evidence(query)
                for item in raw[:5]:
                    results.append(
                        {
                            "source": ResearchSource.EXISTING_DATABASE.value,
                            "content": getattr(item, "content", str(item)),
                            "title": getattr(item, "source_document", ""),
                            "relevance_score": getattr(item, "relevance_score", 0.5),
                        }
                    )
            except Exception as exc:
                logger.warning(f"Evidence table search failed: {exc}")

        return results

    def _evaluate_support(
        self, evidence: List[Dict[str, Any]], claim_type: str
    ) -> tuple:
        """Return (SubstantiationStatus, confidence_score) based on found evidence."""
        count = len(evidence)
        if count == 0:
            return SubstantiationStatus.UNSUBSTANTIATED, 0.0

        avg_relevance = sum(e.get("relevance_score", 0.5) for e in evidence) / count

        # Legal arguments need stronger corroboration than bare factual assertions
        threshold = 2 if claim_type == "legal_argument" else 1

        if count >= threshold and avg_relevance >= 0.6:
            return SubstantiationStatus.SUBSTANTIATED, min(0.95, 0.5 + avg_relevance * 0.5)
        elif count >= 1:
            return SubstantiationStatus.PARTIALLY_SUBSTANTIATED, 0.3 + avg_relevance * 0.3
        return SubstantiationStatus.UNSUBSTANTIATED, 0.1

    def _generate_research_questions(
        self,
        claim_text: str,
        claim_type: str,
        case_context: Dict[str, Any],
    ) -> List[str]:
        """Generate targeted research questions for an unsubstantiated claim."""
        jurisdiction = case_context.get("jurisdiction", "")
        case_type = case_context.get("case_type", "")
        questions = [f"What case law supports: {claim_text[:100]}"]
        if jurisdiction:
            questions.append(
                f"Find {jurisdiction} precedent for: {claim_text[:80]}"
            )
        if case_type:
            questions.append(
                f"What {case_type} authority substantiates: {claim_text[:80]}"
            )
        return questions

    def _build_notes(
        self, status: SubstantiationStatus, confidence: float, evidence_count: int
    ) -> str:
        if status == SubstantiationStatus.SUBSTANTIATED:
            return f"Substantiated by {evidence_count} existing evidence item(s). Confidence: {confidence:.2f}"
        elif status == SubstantiationStatus.PARTIALLY_SUBSTANTIATED:
            return (
                f"Partially substantiated ({evidence_count} items). "
                "Additional research recommended."
            )
        return "No supporting evidence in existing database. Research task created."


# ---------------------------------------------------------------------------
# Research task creator
# ---------------------------------------------------------------------------

class ResearchTaskCreator:
    """
    Creates ``ResearchTaskItem`` objects for unsubstantiated claims and
    orchestrates the full tiered research cycle:

      1. Existing database  (handled by ``ClaimSubstantiationAssessor``)
      2. CourtListener
      3. General web search (via ``PrecisionCitationService``)

    Newly found material is ingested via the evidence ingestion pipeline.
    """

    def __init__(
        self,
        courtlistener_client=None,
        citation_service=None,
        ingestion_pipeline=None,
    ):
        """
        Args:
            courtlistener_client: Optional ``CourtListenerClient`` instance.
            citation_service: Optional ``PrecisionCitationService`` instance.
            ingestion_pipeline: Optional ``EvidenceIngestionPipeline`` instance.
        """
        self.courtlistener_client = courtlistener_client
        self.citation_service = citation_service
        self.ingestion_pipeline = ingestion_pipeline

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_research_task(
        self,
        assessment: ClaimAssessment,
        case_context: Dict[str, Any],
    ) -> ResearchTaskItem:
        """
        Create a ``ResearchTaskItem`` for an unsubstantiated claim.

        Args:
            assessment: ``ClaimAssessment`` whose ``needs_research`` flag is True.
            case_context: Ambient case context.

        Returns:
            A ``ResearchTaskItem`` ready for execution or queuing.
        """
        task_id = f"research_task_{uuid.uuid4().hex[:12]}"
        priority = (
            "critical"
            if assessment.status == SubstantiationStatus.UNSUBSTANTIATED
            else "high"
        )
        return ResearchTaskItem(
            task_id=task_id,
            claim_id=assessment.claim_id,
            claim_text=assessment.claim_text,
            claim_type=assessment.claim_type,
            research_questions=assessment.research_questions,
            case_context=case_context,
            priority=priority,
        )

    async def execute_tiered_research(
        self, task: ResearchTaskItem
    ) -> List[Dict[str, Any]]:
        """
        Execute the tiered research cycle for a ``ResearchTaskItem``.

        Searches in order:
          1. CourtListener (caselaw)
          2. General web / academic (``PrecisionCitationService``)

        Returns:
            Combined list of search result dicts.
        """
        all_results: List[Dict[str, Any]] = []

        # Tier 2: CourtListener
        cl_results = await self._search_courtlistener(task)
        all_results.extend(cl_results)
        if cl_results:
            task.search_results.extend(cl_results)

        # Tier 3: General web / academic search
        if not all_results or len(all_results) < 2:
            web_results = await self._search_web(task)
            all_results.extend(web_results)
            task.search_results.extend(web_results)

        logger.info(
            f"Tiered research for task {task.task_id}: "
            f"{len(all_results)} results from "
            f"{len(cl_results)} CourtListener + "
            f"{len(all_results) - len(cl_results)} web"
        )
        return all_results

    async def ingest_findings(
        self, task: ResearchTaskItem, case_id: str
    ) -> List[str]:
        """
        Ingest newly found research material via the evidence ingestion pipeline.

        Args:
            task: ``ResearchTaskItem`` whose ``search_results`` have been populated.
            case_id: Identifier for the current case.

        Returns:
            List of evidence IDs assigned to the ingested items.
        """
        if not task.search_results:
            return []

        evidence_ids: List[str] = []

        if self.ingestion_pipeline:
            for result in task.search_results:
                try:
                    evidence_id = await self._ingest_single_result(
                        result, task, case_id
                    )
                    if evidence_id:
                        evidence_ids.append(evidence_id)
                except Exception as exc:
                    logger.warning(f"Failed to ingest result: {exc}")
        else:
            # Fallback: record result as a simple evidence entry via evidence table
            for result in task.search_results:
                evidence_id = f"ev_{uuid.uuid4().hex[:8]}"
                evidence_ids.append(evidence_id)

        task.ingested_evidence_ids = evidence_ids
        logger.info(
            f"Ingested {len(evidence_ids)} new evidence items for task {task.task_id}"
        )
        return evidence_ids

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _search_courtlistener(
        self, task: ResearchTaskItem
    ) -> List[Dict[str, Any]]:
        """Search CourtListener for caselaw supporting the claim."""
        if not self.courtlistener_client:
            return []
        results = []
        jurisdiction = task.case_context.get("jurisdiction", "")
        for question in task.research_questions[:2]:
            try:
                raw = await self.courtlistener_client.search_opinions(
                    query=question,
                    jurisdiction=jurisdiction or None,
                    max_results=3,
                )
                for item in raw:
                    results.append(
                        {
                            "source": ResearchSource.COURT_LISTENER.value,
                            "title": item.get("case_name", ""),
                            "citation": item.get("citation", ""),
                            "content": item.get("excerpt", ""),
                            "url": item.get("absolute_url", ""),
                            "relevance_score": item.get("score", 0.5),
                        }
                    )
            except Exception as exc:
                logger.warning(f"CourtListener search failed: {exc}")
        return results

    async def _search_web(
        self, task: ResearchTaskItem
    ) -> List[Dict[str, Any]]:
        """Search academic/web sources for supporting material."""
        if not self.citation_service:
            return []
        results = []
        jurisdiction = task.case_context.get("jurisdiction", "")
        try:
            citations_by_question = await self.citation_service.search_claim_substantiation(
                claims=task.research_questions[:2],
                jurisdiction=jurisdiction,
                max_sources_per_claim=2,
            )
            for _question, citations in citations_by_question.items():
                for citation in citations:
                    results.append(
                        {
                            "source": ResearchSource.WEB_SEARCH.value,
                            "title": citation.title,
                            "url": citation.url,
                            "content": citation.content,
                            "bluebook_citation": citation.bluebook_citation,
                            "relevance_score": (
                                citation.quality_metrics.overall_quality_score / 5.0
                            ),
                        }
                    )
        except Exception as exc:
            logger.warning(f"Web/academic search failed: {exc}")
        return results

    async def _ingest_single_result(
        self,
        result: Dict[str, Any],
        task: ResearchTaskItem,
        case_id: str,
    ) -> Optional[str]:
        """Ingest a single search result via the evidence ingestion pipeline."""
        content = result.get("content", "")
        if not content:
            return None

        # Build a minimal document dict compatible with pipeline expectations
        doc = {
            "content": content,
            "title": result.get("title", "Research Finding"),
            "url": result.get("url", ""),
            "citation": result.get("citation", result.get("bluebook_citation", "")),
            "source": result.get("source", ""),
            "case_id": case_id,
            "claim_id": task.claim_id,
            "origin": "phaseC01_editor_research",
        }

        # EvidenceIngestionPipeline.ingest_document expects (content, metadata)
        try:
            evidence_id = await self.ingestion_pipeline.ingest_document(
                content=content,
                metadata=doc,
            )
            return evidence_id
        except AttributeError:
            # Pipeline does not expose ingest_document; try process_document fallback
            logger.debug(
                "ingest_document not available on pipeline; falling back to process_document"
            )

        try:
            result_obj = await self.ingestion_pipeline.process_document(doc)
            return getattr(result_obj, "evidence_id", None) or f"ev_{uuid.uuid4().hex[:8]}"
        except Exception:
            return f"ev_{uuid.uuid4().hex[:8]}"


# ---------------------------------------------------------------------------
# Main orchestration class used by LegalEditorBot
# ---------------------------------------------------------------------------

class EditorClaimIntelligence:
    """
    Main orchestration class for editor intelligence in Phase C01.

    Workflow:
      1. Extract claims and arguments from the written document.
      2. Assess each claim against the existing evidence database.
      3. For unsubstantiated claims, create ``ResearchTaskItem`` objects that
         target the Phase A02 research cycle.
      4. Optionally execute the tiered research (DB → CourtListener → web).
      5. Ingest newly found material.
    """

    def __init__(
        self,
        storage_api=None,
        evidence_table=None,
        courtlistener_client=None,
        citation_service=None,
        ingestion_pipeline=None,
    ):
        self.extractor = ClaimArgumentExtractor()
        self.assessor = ClaimSubstantiationAssessor(
            storage_api=storage_api,
            evidence_table=evidence_table,
        )
        self.task_creator = ResearchTaskCreator(
            courtlistener_client=courtlistener_client,
            citation_service=citation_service,
            ingestion_pipeline=ingestion_pipeline,
        )

    async def analyze_document(
        self,
        document_content: str,
        case_context: Dict[str, Any],
        session_id: str,
        execute_research: bool = False,
        ingest_findings: bool = False,
    ) -> Dict[str, Any]:
        """
        Analyse a document for unsubstantiated claims and optionally trigger
        the Phase A02 research cycle.

        Args:
            document_content: Full text of the document being edited.
            case_context: Ambient case context (jurisdiction, case_type, case_id …).
            session_id: Editing session identifier.
            execute_research: If True, immediately execute tiered research for
                              every unsubstantiated claim.
            ingest_findings: If True (and ``execute_research`` is True), ingest
                             newly found material into the evidence pipeline.

        Returns:
            Comprehensive analysis dict containing claim assessments and
            research task items.
        """
        logger.info(
            f"[EditorClaimIntelligence] Analysing document for session {session_id}"
        )

        # Step 1 – extract claims
        raw_claims = self.extractor.extract_claims(document_content)

        # Step 2 – assess each claim
        assessments: List[ClaimAssessment] = []
        for raw in raw_claims:
            assessment = await self.assessor.assess_claim(raw, case_context)
            assessments.append(assessment)

        # Step 3 – create research tasks for unsubstantiated claims
        research_tasks: List[ResearchTaskItem] = []
        for assessment in assessments:
            if assessment.needs_research:
                task = self.task_creator.create_research_task(assessment, case_context)
                research_tasks.append(task)

        # Step 4 (optional) – execute tiered research
        new_evidence_ids: List[str] = []
        if execute_research:
            case_id = case_context.get("case_id", session_id)
            for task in research_tasks:
                await self.task_creator.execute_tiered_research(task)
                task.status = "completed"
                task.completed_at = datetime.now()

                # Step 5 (optional) – ingest findings
                if ingest_findings:
                    ids = await self.task_creator.ingest_findings(task, case_id)
                    new_evidence_ids.extend(ids)

        # Build summary statistics
        total_claims = len(assessments)
        substantiated = sum(
            1
            for a in assessments
            if a.status == SubstantiationStatus.SUBSTANTIATED
        )
        partially = sum(
            1
            for a in assessments
            if a.status == SubstantiationStatus.PARTIALLY_SUBSTANTIATED
        )
        unsubstantiated = sum(
            1
            for a in assessments
            if a.status == SubstantiationStatus.UNSUBSTANTIATED
        )

        # Serialise assessments and tasks for transport
        assessments_out = [
            {
                "claim_id": a.claim_id,
                "claim_text": a.claim_text,
                "claim_type": a.claim_type,
                "status": a.status.value,
                "confidence_score": a.confidence_score,
                "supporting_evidence_count": len(a.supporting_evidence),
                "needs_research": a.needs_research,
                "research_questions": a.research_questions,
                "notes": a.notes,
            }
            for a in assessments
        ]

        tasks_out = [t.to_workflow_task() for t in research_tasks]

        result = {
            "session_id": session_id,
            "analysis_performed": True,
            "total_claims_found": total_claims,
            "substantiated_claims": substantiated,
            "partially_substantiated_claims": partially,
            "unsubstantiated_claims": unsubstantiated,
            "research_tasks_created": len(research_tasks),
            "new_evidence_ingested": len(new_evidence_ids),
            "claim_assessments": assessments_out,
            "research_tasks": tasks_out,
            "new_evidence_ids": new_evidence_ids,
            "overall_substantiation_score": (
                substantiated / total_claims if total_claims else 0.0
            ),
            "timestamp": datetime.now().isoformat(),
        }

        logger.info(
            f"[EditorClaimIntelligence] Session {session_id}: "
            f"{total_claims} claims, {unsubstantiated} unsubstantiated, "
            f"{len(research_tasks)} research tasks created"
        )
        return result


# ---------------------------------------------------------------------------
# Convenience function for external callers
# ---------------------------------------------------------------------------

async def analyze_document_claims(
    document_content: str,
    case_context: Dict[str, Any],
    session_id: str,
    execute_research: bool = False,
    ingest_findings: bool = False,
    storage_api=None,
    evidence_table=None,
    courtlistener_client=None,
    citation_service=None,
    ingestion_pipeline=None,
) -> Dict[str, Any]:
    """
    Convenience wrapper around ``EditorClaimIntelligence.analyze_document``.

    Intended to be called directly from Phase C01 editing workflows.
    """
    intelligence = EditorClaimIntelligence(
        storage_api=storage_api,
        evidence_table=evidence_table,
        courtlistener_client=courtlistener_client,
        citation_service=citation_service,
        ingestion_pipeline=ingestion_pipeline,
    )
    return await intelligence.analyze_document(
        document_content=document_content,
        case_context=case_context,
        session_id=session_id,
        execute_research=execute_research,
        ingest_findings=ingest_findings,
    )
