"""
Phase A01 Background Research Integration

This module integrates precision citation service with Phase A01 intake processing
to perform background research using intake form data and existing evidence.
"""

import asyncio
from datetime import datetime
import logging
from typing import Any, Dict, List, Optional

from ...evidence.table import EnhancedEvidenceTable
from ...research.precision_citation_service import PrecisionCitation, PrecisionCitationService
from ...storage.enhanced_unified_storage_api import get_enhanced_unified_storage_api

logger = logging.getLogger(__name__)


class BackgroundResearchIntegration:
    """
    Integrates background research into Phase A01 intake processing
    """

    def __init__(self):
        self.citation_service = PrecisionCitationService()
        self.evidence_table = EnhancedEvidenceTable()
        self.unified_storage = None

        # Initialize unified storage if available
        try:
            self.unified_storage = get_enhanced_unified_storage_api()
        except Exception as e:
            logger.warning(f"Unified storage not available: {e}")

    async def perform_background_research(
        self,
        intake_data: Dict[str, Any],
        session_id: str,
        existing_evidence: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Perform background research for Phase A01 intake

        Args:
            intake_data: Intake form data
            session_id: Session identifier
            existing_evidence: Existing evidence from evidence table

        Returns:
            Research results with citations and evidence entries
        """
        logger.info(f"Starting Phase A01 background research for session {session_id}")

        try:
            # Perform precision research
            citations = await self.citation_service.search_background_research(
                intake_data, existing_evidence, max_sources=4
            )

            # Convert citations to evidence entries
            evidence_entries = await self._citations_to_evidence_entries(
                citations, intake_data, session_id
            )

            # Store in evidence table
            stored_entries = []
            for entry in evidence_entries:
                evidence_id = self.evidence_table.add_evidence(entry)
                stored_entries.append(evidence_id)

            # Create research summary
            research_summary = self._create_research_summary(
                citations, evidence_entries, intake_data
            )

            result = {
                "session_id": session_id,
                "research_performed": True,
                "citations_found": len(citations),
                "evidence_entries_created": len(evidence_entries),
                "evidence_ids": stored_entries,
                "research_summary": research_summary,
                "citations": [self._citation_to_dict(c) for c in citations],
                "timestamp": datetime.now().isoformat(),
            }

            logger.info(
                f"Phase A01 background research complete: {len(citations)} citations, {len(evidence_entries)} evidence entries"
            )
            return result

        except Exception as e:
            logger.exception(f"Phase A01 background research failed: {e}")
            return {
                "session_id": session_id,
                "research_performed": False,
                "error": str(e),
                "citations_found": 0,
                "evidence_entries_created": 0,
                "timestamp": datetime.now().isoformat(),
            }

    async def _citations_to_evidence_entries(
        self, citations: List[PrecisionCitation], intake_data: Dict[str, Any], session_id: str
    ) -> List[Any]:
        """
        Convert precision citations to evidence table entries
        """
        from ...evidence.table import EvidenceEntry, EvidenceType, RelevanceLevel

        evidence_entries = []

        for citation in citations:
            # Determine evidence type
            if citation.source_type == "academic":
                evidence_type = EvidenceType.DOCUMENTARY
                relevance_level = RelevanceLevel.HIGH
            elif citation.source_type == "news":
                evidence_type = EvidenceType.DIGITAL
                relevance_level = RelevanceLevel.MEDIUM
            else:
                evidence_type = EvidenceType.DIGITAL
                relevance_level = RelevanceLevel.MEDIUM

            # Calculate relevance score from quality metrics
            relevance_score = min(1.0, citation.quality_metrics.overall_quality_score / 5.0)

            # Create evidence entry
            entry = EvidenceEntry(
                source_document=citation.title,
                page_section=f"Background Research - {citation.quality_metrics.domain}",
                content=citation.content,
                evidence_type=evidence_type,
                relevance_score=relevance_score,
                relevance_level=relevance_level,
                bluebook_citation=citation.bluebook_citation,
                extracted_date=citation.publication_date,
                key_terms=self._extract_key_terms(citation),
                notes=self._create_evidence_notes(citation, intake_data),
                created_by="background_research_a01",
            )

            # Add supporting facts based on intake data
            entry.supporting_facts = self._link_to_intake_facts(citation, intake_data)

            evidence_entries.append(entry)

        return evidence_entries

    def _extract_key_terms(self, citation: PrecisionCitation) -> List[str]:
        """Extract key terms from citation for indexing"""
        terms = []

        # Add domain
        terms.append(citation.quality_metrics.domain)

        # Add source type
        terms.append(citation.source_type)

        # Extract legal keywords from title and content
        legal_keywords = [
            "negligence",
            "breach",
            "contract",
            "tort",
            "damages",
            "liability",
            "duty",
            "care",
            "injury",
            "property",
            "jurisdiction",
            "venue",
            "case law",
            "precedent",
        ]

        text_to_check = f"{citation.title} {citation.content}".lower()
        for keyword in legal_keywords:
            if keyword in text_to_check:
                terms.append(keyword)

        return list(set(terms))  # Remove duplicates

    def _create_evidence_notes(
        self, citation: PrecisionCitation, intake_data: Dict[str, Any]
    ) -> str:
        """Create notes for evidence entry"""
        notes_parts = [
            f"Background research citation from Phase A01 intake processing",
            f"Quality Score: {citation.quality_metrics.overall_quality_score:.1f}/5.0",
            f"Authority Score: {citation.quality_metrics.authority_score:.1f}/5.0",
            f"Source Type: {citation.source_type}",
            f"Domain: {citation.quality_metrics.domain}",
        ]

        # Add jurisdiction context if available
        jurisdiction = intake_data.get("jurisdiction")
        if jurisdiction:
            notes_parts.append(f"Jurisdiction Context: {jurisdiction}")

        # Add cause of action context
        causes_of_action = intake_data.get("causes_of_action", [])
        if causes_of_action:
            coa_str = ", ".join(str(coa) for coa in causes_of_action[:3])
            notes_parts.append(f"Related Causes of Action: {coa_str}")

        return " | ".join(notes_parts)

    def _link_to_intake_facts(
        self, citation: PrecisionCitation, intake_data: Dict[str, Any]
    ) -> List[str]:
        """Link citation to relevant intake facts"""
        fact_links = []

        # Create fact IDs based on intake data elements
        jurisdiction = intake_data.get("jurisdiction")
        if jurisdiction and jurisdiction.lower() in citation.content.lower():
            fact_links.append(f"intake_jurisdiction_{jurisdiction.lower()}")

        causes_of_action = intake_data.get("causes_of_action", [])
        for coa in causes_of_action:
            coa_str = str(coa).lower().replace(" ", "_")
            if coa_str in citation.content.lower() or coa_str in citation.title.lower():
                fact_links.append(f"intake_coa_{coa_str}")

        claim_description = intake_data.get("claim_description", "")
        if claim_description:
            # Simple keyword matching for claim linkage
            claim_words = set(claim_description.lower().split()[:5])  # First 5 words
            citation_words = set(citation.content.lower().split()[:20])  # First 20 words
            overlap = claim_words.intersection(citation_words)
            if overlap:
                fact_links.append(f"intake_claim_description_{len(overlap)}_overlap")

        return fact_links

    def _create_research_summary(
        self,
        citations: List[PrecisionCitation],
        evidence_entries: List[Any],
        intake_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create comprehensive research summary"""
        summary = {
            "total_citations": len(citations),
            "total_evidence_entries": len(evidence_entries),
            "quality_distribution": {},
            "domain_distribution": {},
            "source_type_distribution": {},
            "average_quality_score": 0.0,
            "highest_quality_source": None,
            "research_scope": self._determine_research_scope(intake_data),
            "key_findings": [],
        }

        if citations:
            # Calculate distributions
            quality_scores = []
            for citation in citations:
                quality = citation.quality_metrics.overall_quality_score
                quality_scores.append(quality)

                # Quality distribution
                quality_bucket = f"{int(quality)}-{int(quality) + 1}"
                summary["quality_distribution"][quality_bucket] = (
                    summary["quality_distribution"].get(quality_bucket, 0) + 1
                )

                # Domain distribution
                domain = citation.quality_metrics.domain
                summary["domain_distribution"][domain] = (
                    summary["domain_distribution"].get(domain, 0) + 1
                )

                # Source type distribution
                source_type = citation.source_type
                summary["source_type_distribution"][source_type] = (
                    summary["source_type_distribution"].get(source_type, 0) + 1
                )

            # Average quality
            summary["average_quality_score"] = sum(quality_scores) / len(quality_scores)

            # Highest quality source
            best_citation = max(citations, key=lambda c: c.quality_metrics.overall_quality_score)
            summary["highest_quality_source"] = {
                "title": best_citation.title,
                "domain": best_citation.quality_metrics.domain,
                "quality_score": best_citation.quality_metrics.overall_quality_score,
            }

            # Key findings (simplified)
            summary["key_findings"] = [
                f"Found {len(citations)} relevant sources across {len(summary['domain_distribution'])} domains",
                f"Average quality score: {summary['average_quality_score']:.1f}/5.0",
                f"Primary domains: {', '.join(list(summary['domain_distribution'].keys())[:3])}",
            ]

        return summary

    def _determine_research_scope(self, intake_data: Dict[str, Any]) -> str:
        """Determine the scope of research performed"""
        scope_parts = []

        jurisdiction = intake_data.get("jurisdiction")
        if jurisdiction:
            scope_parts.append(f"{jurisdiction} jurisdiction")

        causes_of_action = intake_data.get("causes_of_action", [])
        if causes_of_action:
            coa_count = len(causes_of_action)
            scope_parts.append(f"{coa_count} cause(s) of action")

        events_location = intake_data.get("events_location")
        if events_location:
            scope_parts.append(f"{events_location} location context")

        if not scope_parts:
            return "General legal research"

        return " | ".join(scope_parts)

    def _citation_to_dict(self, citation: PrecisionCitation) -> Dict[str, Any]:
        """Convert citation to dictionary for API responses"""
        return {
            "title": citation.title,
            "url": citation.url,
            "content": citation.content,
            "source_type": citation.source_type,
            "quality_metrics": {
                "domain": citation.quality_metrics.domain,
                "authority_score": citation.quality_metrics.authority_score,
                "citation_count_weight": citation.quality_metrics.citation_count_weight,
                "q_score_weight": citation.quality_metrics.q_score_weight,
                "recency_score": citation.quality_metrics.recency_score,
                "overall_quality_score": citation.quality_metrics.overall_quality_score,
            },
            "citation_count": citation.citation_count,
            "author_q_score": citation.author_q_score,
            "publication_date": citation.publication_date,
            "bluebook_citation": citation.bluebook_citation,
        }

    async def get_research_results(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve research results for a session
        """
        # This would typically query a database or cache
        # For now, return None (would be implemented with persistent storage)
        return None

    async def link_evidence_to_claims(self, evidence_ids: List[str], claim_ids: List[str]) -> bool:
        """
        Link research evidence to specific claims for later reference
        """
        try:
            for evidence_id in evidence_ids:
                for claim_id in claim_ids:
                    # This would create relationships in the knowledge graph
                    # For now, just log the linkage
                    logger.info(f"Linked evidence {evidence_id} to claim {claim_id}")

            return True
        except Exception as e:
            logger.error(f"Failed to link evidence to claims: {e}")
            return False


# Convenience functions for integration
async def perform_a01_background_research(
    intake_data: Dict[str, Any], session_id: str, existing_evidence: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Convenience function for Phase A01 background research"""
    integration = BackgroundResearchIntegration()
    return await integration.perform_background_research(intake_data, session_id, existing_evidence)


if __name__ == "__main__":
    # Example usage
    async def test_a01_integration():
        intake_data = {
            "jurisdiction": "California",
            "causes_of_action": ["negligence", "premises_liability"],
            "claim_description": "Defendant property owner failed to maintain safe premises causing plaintiff slip and fall injury",
            "events_location": "Los Angeles, California",
            "events_date": "January 2023",
            "client_name": "John Doe",
            "opposing_party_names": ["MegaCorp Properties"],
        }

        integration = BackgroundResearchIntegration()
        results = await integration.perform_background_research(intake_data, "test_session_001")

        print("Phase A01 Background Research Results:")
        print(f"Citations Found: {results['citations_found']}")
        print(f"Evidence Entries: {results['evidence_entries_created']}")
        print(f"Research Summary: {results['research_summary']}")

    asyncio.run(test_a01_integration())
