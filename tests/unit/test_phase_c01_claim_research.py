"""
Unit tests for phaseC01_editing.claim_research_tasks

Tests cover:
- ClaimArgumentExtractor: extracts legal claims and arguments from text
- ClaimSubstantiationAssessor: assesses claims against existing database
- ResearchTaskCreator: creates WorkflowTask-compatible research task items
- EditorClaimIntelligence: end-to-end orchestration
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from lawyerfactory.phases.phaseC01_editing.claim_research_tasks import (
    ClaimArgumentExtractor,
    ClaimAssessment,
    ClaimSubstantiationAssessor,
    EditorClaimIntelligence,
    ResearchSource,
    ResearchTaskCreator,
    ResearchTaskItem,
    SubstantiationStatus,
    analyze_document_claims,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SAMPLE_LEGAL_BRIEF = """
IN THE UNITED STATES DISTRICT COURT FOR THE NORTHERN DISTRICT OF CALIFORNIA

PLAINTIFF, v. DEFENDANT

COMPLAINT FOR DAMAGES

JURISDICTION

1. This Court has subject-matter jurisdiction pursuant to 28 U.S.C. § 1331.

STATEMENT OF FACTS

2. On or about January 15, 2023, Defendant failed to maintain safe premises.
3. Plaintiff alleges that Defendant breached the duty of care owed to all visitors.
4. Defendant knew or should have known about the hazardous condition.
5. As a proximate cause of Defendant's negligence, Plaintiff suffered damages.

CAUSE OF ACTION – NEGLIGENCE

6. Plaintiff contends that Defendant violated the applicable standard of care.
7. Defendant's breach of duty directly caused Plaintiff's injuries.
8. Under California law, a property owner owes a duty of care to invitees.
"""


# ---------------------------------------------------------------------------
# ClaimArgumentExtractor tests
# ---------------------------------------------------------------------------


class TestClaimArgumentExtractor:
    def setup_method(self):
        self.extractor = ClaimArgumentExtractor()

    def test_extract_returns_list(self):
        claims = self.extractor.extract_claims(SAMPLE_LEGAL_BRIEF)
        assert isinstance(claims, list)

    def test_extract_finds_legal_arguments(self):
        claims = self.extractor.extract_claims(SAMPLE_LEGAL_BRIEF)
        claim_types = [c["type"] for c in claims]
        assert "legal_argument" in claim_types

    def test_extract_finds_factual_assertions(self):
        claims = self.extractor.extract_claims(SAMPLE_LEGAL_BRIEF)
        claim_types = [c["type"] for c in claims]
        assert "factual_assertion" in claim_types

    def test_each_claim_has_required_keys(self):
        claims = self.extractor.extract_claims(SAMPLE_LEGAL_BRIEF)
        for claim in claims:
            assert "id" in claim
            assert "text" in claim
            assert "type" in claim
            assert "sentence_index" in claim

    def test_claim_ids_are_unique(self):
        claims = self.extractor.extract_claims(SAMPLE_LEGAL_BRIEF)
        ids = [c["id"] for c in claims]
        assert len(ids) == len(set(ids))

    def test_empty_document_returns_empty_list(self):
        claims = self.extractor.extract_claims("")
        assert claims == []

    def test_short_sentences_are_skipped(self):
        # Sentences shorter than 20 chars should not be returned
        claims = self.extractor.extract_claims("Short. Also short.")
        assert all(len(c["text"]) >= 20 for c in claims)

    def test_non_claim_text_returns_empty(self):
        claims = self.extractor.extract_claims(
            "The quick brown fox jumped over the lazy dog. "
            "This sentence has no legal signals whatsoever. "
            "Absolutely nothing relevant to legal proceedings here."
        )
        assert claims == []


# ---------------------------------------------------------------------------
# ClaimSubstantiationAssessor tests
# ---------------------------------------------------------------------------


class TestClaimSubstantiationAssessor:
    def _make_claim(self, text="Defendant breached the duty of care."):
        return {
            "id": "claim_test_001",
            "text": text,
            "type": "legal_argument",
            "sentence_index": 0,
        }

    def test_no_storage_returns_unsubstantiated(self):
        """Without any storage backend, claims should be unsubstantiated."""
        assessor = ClaimSubstantiationAssessor()
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(
                assessor.assess_claim(self._make_claim(), {})
            )
        finally:
            loop.close()
        assert isinstance(result, ClaimAssessment)
        assert result.status == SubstantiationStatus.UNSUBSTANTIATED
        assert result.needs_research is True
        assert result.confidence_score < 0.3

    def test_with_storage_returning_evidence_substantiates_claim(self):
        """With strong DB evidence, claim should be substantiated."""
        mock_storage = MagicMock()
        mock_storage.search_evidence = AsyncMock(
            return_value=[
                {"content": "Case law on negligence.", "relevance_score": 0.9},
                {"content": "Duty of care standard.", "relevance_score": 0.85},
            ]
        )
        assessor = ClaimSubstantiationAssessor(storage_api=mock_storage)
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(
                assessor.assess_claim(self._make_claim(), {"jurisdiction": "CA"})
            )
        finally:
            loop.close()
        assert result.status == SubstantiationStatus.SUBSTANTIATED
        assert result.needs_research is False
        assert result.confidence_score > 0.5

    def test_with_single_weak_evidence_is_partial(self):
        """Single low-relevance DB result → partially substantiated."""
        mock_storage = MagicMock()
        mock_storage.search_evidence = AsyncMock(
            return_value=[{"content": "Some content.", "relevance_score": 0.4}]
        )
        assessor = ClaimSubstantiationAssessor(storage_api=mock_storage)
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(
                assessor.assess_claim(self._make_claim(), {})
            )
        finally:
            loop.close()
        assert result.status in (
            SubstantiationStatus.PARTIALLY_SUBSTANTIATED,
            SubstantiationStatus.UNSUBSTANTIATED,
        )

    def test_research_questions_generated_for_unsubstantiated(self):
        assessor = ClaimSubstantiationAssessor()
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(
                assessor.assess_claim(
                    self._make_claim(),
                    {"jurisdiction": "California", "case_type": "negligence"},
                )
            )
        finally:
            loop.close()
        assert len(result.research_questions) > 0

    def test_source_tiers_searched_recorded(self):
        assessor = ClaimSubstantiationAssessor()
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(
                assessor.assess_claim(self._make_claim(), {})
            )
        finally:
            loop.close()
        assert ResearchSource.EXISTING_DATABASE in result.source_tiers_searched

    def test_storage_exception_gracefully_handled(self):
        """Storage failure should not raise; claim remains unsubstantiated."""
        mock_storage = MagicMock()
        mock_storage.search_evidence = AsyncMock(side_effect=RuntimeError("DB down"))
        assessor = ClaimSubstantiationAssessor(storage_api=mock_storage)
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(
                assessor.assess_claim(self._make_claim(), {})
            )
        finally:
            loop.close()
        assert result.status == SubstantiationStatus.UNSUBSTANTIATED


# ---------------------------------------------------------------------------
# ResearchTaskCreator tests
# ---------------------------------------------------------------------------


class TestResearchTaskCreator:
    def _make_assessment(self, status=SubstantiationStatus.UNSUBSTANTIATED):
        return ClaimAssessment(
            claim_id="claim_001",
            claim_text="Defendant breached the duty of care.",
            claim_type="legal_argument",
            status=status,
            confidence_score=0.0,
            needs_research=True,
            research_questions=[
                "What California case law supports duty of care breach?",
                "Precedent for premises liability negligence CA?",
            ],
        )

    def test_create_research_task_returns_task_item(self):
        creator = ResearchTaskCreator()
        task = creator.create_research_task(self._make_assessment(), {"jurisdiction": "CA"})
        assert isinstance(task, ResearchTaskItem)

    def test_task_has_claim_reference(self):
        creator = ResearchTaskCreator()
        task = creator.create_research_task(self._make_assessment(), {})
        assert task.claim_id == "claim_001"
        assert "duty of care" in task.claim_text

    def test_unsubstantiated_claim_gets_critical_priority(self):
        creator = ResearchTaskCreator()
        task = creator.create_research_task(
            self._make_assessment(SubstantiationStatus.UNSUBSTANTIATED), {}
        )
        assert task.priority == "critical"

    def test_partially_substantiated_gets_high_priority(self):
        creator = ResearchTaskCreator()
        task = creator.create_research_task(
            self._make_assessment(SubstantiationStatus.PARTIALLY_SUBSTANTIATED), {}
        )
        assert task.priority == "high"

    def test_to_workflow_task_targets_research_phase(self):
        creator = ResearchTaskCreator()
        task = creator.create_research_task(self._make_assessment(), {})
        wf_task = task.to_workflow_task()
        assert wf_task["phase"] == "research"
        assert wf_task["research_needed"] is True
        assert wf_task["research_context"]["origin"] == "phaseC01_editing"

    def test_courtlistener_search_called_when_client_available(self):
        mock_cl = MagicMock()
        mock_cl.search_opinions = AsyncMock(
            return_value=[
                {"case_name": "Smith v Jones", "citation": "100 F.3d 200", "excerpt": "..."}
            ]
        )
        creator = ResearchTaskCreator(courtlistener_client=mock_cl)
        assessment = self._make_assessment()
        task = creator.create_research_task(assessment, {"jurisdiction": "CA"})

        loop = asyncio.new_event_loop()
        try:
            results = loop.run_until_complete(creator.execute_tiered_research(task))
        finally:
            loop.close()

        assert any(r["source"] == ResearchSource.COURT_LISTENER.value for r in results)
        assert mock_cl.search_opinions.called

    def test_web_search_called_when_no_courtlistener_results(self):
        """With no CourtListener client, falls through to web/citation search."""
        mock_citations = MagicMock()
        mock_citations.search_claim_substantiation = AsyncMock(
            return_value={
                "What California case law supports duty of care breach?": [
                    MagicMock(
                        title="Legal Analysis",
                        url="https://example.com",
                        content="...",
                        bluebook_citation="",
                        quality_metrics=MagicMock(overall_quality_score=3.5),
                    )
                ]
            }
        )
        creator = ResearchTaskCreator(citation_service=mock_citations)
        assessment = self._make_assessment()
        task = creator.create_research_task(assessment, {"jurisdiction": "CA"})

        loop = asyncio.new_event_loop()
        try:
            results = loop.run_until_complete(creator.execute_tiered_research(task))
        finally:
            loop.close()

        assert any(r["source"] == ResearchSource.WEB_SEARCH.value for r in results)

    def test_ingest_findings_without_pipeline_assigns_ids(self):
        """Without a real pipeline, evidence IDs are still assigned."""
        creator = ResearchTaskCreator()
        assessment = self._make_assessment()
        task = creator.create_research_task(assessment, {})
        task.search_results = [
            {"content": "Some content", "source": "web_search", "title": "Article"},
        ]

        loop = asyncio.new_event_loop()
        try:
            ids = loop.run_until_complete(creator.ingest_findings(task, "case_001"))
        finally:
            loop.close()

        assert len(ids) == 1
        assert task.ingested_evidence_ids == ids

    def test_ingest_empty_results_returns_empty_list(self):
        creator = ResearchTaskCreator()
        assessment = self._make_assessment()
        task = creator.create_research_task(assessment, {})
        # No search results set → nothing to ingest

        loop = asyncio.new_event_loop()
        try:
            ids = loop.run_until_complete(creator.ingest_findings(task, "case_001"))
        finally:
            loop.close()

        assert ids == []


# ---------------------------------------------------------------------------
# EditorClaimIntelligence end-to-end tests
# ---------------------------------------------------------------------------


class TestEditorClaimIntelligence:
    def test_analyze_document_returns_expected_keys(self):
        intel = EditorClaimIntelligence()
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(
                intel.analyze_document(
                    SAMPLE_LEGAL_BRIEF,
                    {"jurisdiction": "California", "case_type": "negligence"},
                    "session_001",
                )
            )
        finally:
            loop.close()

        required_keys = {
            "session_id",
            "analysis_performed",
            "total_claims_found",
            "substantiated_claims",
            "partially_substantiated_claims",
            "unsubstantiated_claims",
            "research_tasks_created",
            "new_evidence_ingested",
            "claim_assessments",
            "research_tasks",
            "overall_substantiation_score",
            "timestamp",
        }
        assert required_keys.issubset(result.keys())

    def test_sample_brief_finds_claims(self):
        intel = EditorClaimIntelligence()
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(
                intel.analyze_document(SAMPLE_LEGAL_BRIEF, {}, "session_002")
            )
        finally:
            loop.close()
        assert result["total_claims_found"] > 0

    def test_unsubstantiated_claims_generate_research_tasks(self):
        """Without storage backend every claim is unsubstantiated → tasks created."""
        intel = EditorClaimIntelligence()
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(
                intel.analyze_document(SAMPLE_LEGAL_BRIEF, {}, "session_003")
            )
        finally:
            loop.close()
        assert result["research_tasks_created"] == result["unsubstantiated_claims"]

    def test_research_tasks_reference_correct_phase(self):
        intel = EditorClaimIntelligence()
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(
                intel.analyze_document(SAMPLE_LEGAL_BRIEF, {}, "session_004")
            )
        finally:
            loop.close()
        for task in result["research_tasks"]:
            assert task["phase"] == "research"

    def test_overall_score_zero_when_no_storage(self):
        """Without DB, nothing is substantiated → score should be 0."""
        intel = EditorClaimIntelligence()
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(
                intel.analyze_document(SAMPLE_LEGAL_BRIEF, {}, "session_005")
            )
        finally:
            loop.close()
        assert result["overall_substantiation_score"] == 0.0

    def test_score_improves_with_storage_hits(self):
        """When all DB searches return strong evidence, score improves."""
        mock_storage = MagicMock()
        mock_storage.search_evidence = AsyncMock(
            return_value=[
                {"content": "Strong precedent.", "relevance_score": 0.9},
                {"content": "Supporting case law.", "relevance_score": 0.85},
            ]
        )
        intel = EditorClaimIntelligence(storage_api=mock_storage)
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(
                intel.analyze_document(
                    SAMPLE_LEGAL_BRIEF,
                    {"jurisdiction": "CA"},
                    "session_006",
                )
            )
        finally:
            loop.close()
        assert result["overall_substantiation_score"] > 0.0

    def test_no_research_tasks_when_fully_substantiated(self):
        """When all claims are substantiated, no research tasks should be created."""
        mock_storage = MagicMock()
        mock_storage.search_evidence = AsyncMock(
            return_value=[
                {"content": "Strong precedent.", "relevance_score": 0.95},
                {"content": "Supporting case law.", "relevance_score": 0.9},
                {"content": "More authority.", "relevance_score": 0.88},
            ]
        )
        intel = EditorClaimIntelligence(storage_api=mock_storage)
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(
                intel.analyze_document(SAMPLE_LEGAL_BRIEF, {}, "session_007")
            )
        finally:
            loop.close()
        assert result["research_tasks_created"] == 0

    def test_empty_document_produces_no_claims_or_tasks(self):
        intel = EditorClaimIntelligence()
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(
                intel.analyze_document("", {}, "session_008")
            )
        finally:
            loop.close()
        assert result["total_claims_found"] == 0
        assert result["research_tasks_created"] == 0

    def test_analyze_document_claims_convenience_wrapper(self):
        """The module-level convenience function should return the same structure."""
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(
                analyze_document_claims(
                    SAMPLE_LEGAL_BRIEF, {"jurisdiction": "CA"}, "session_009"
                )
            )
        finally:
            loop.close()
        assert result["analysis_performed"] is True
        assert "claim_assessments" in result
