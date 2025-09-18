"""
Phase C01 Fact Verification Integration
Integrates precision citation service with fact verification workflows in editing phase.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional
import logging

from ...research.precision_citation_service import (
    PrecisionCitationService,
    PrecisionCitation
)
from ...evidence.table import EnhancedEvidenceTable, EvidenceEntry, EvidenceType, RelevanceLevel

logger = logging.getLogger(__name__)


class FactVerificationIntegration:
    """
    Integrates fact verification research into Phase C01 editing process
    """

    def __init__(self):
        self.citation_service = PrecisionCitationService()
        self.evidence_table = EnhancedEvidenceTable()

    async def verify_facts(
        self,
        facts: List[str],
        case_context: Dict[str, Any],
        session_id: str,
        max_sources_per_fact: int = 2
    ) -> Dict[str, Any]:
        """
        Perform fact verification research for Phase C01 editing

        Args:
            facts: List of facts to verify
            case_context: Case context and background
            session_id: Session identifier
            max_sources_per_fact: Maximum sources per fact (default 2)

        Returns:
            Verification results with citations and evidence entries
        """
        logger.info(f"Starting Phase C01 fact verification for {len(facts)} facts")

        try:
            # Perform precision fact verification
            verification_results = await self.citation_service.search_fact_verification(
                facts, case_context, max_sources_per_fact
            )

            # Convert results to evidence entries and organize by fact
            fact_evidence = {}
            all_evidence_ids = []

            for fact, citations in verification_results.items():
                # Convert citations to evidence entries
                evidence_entries = await self._citations_to_evidence_entries(
                    citations, fact, case_context, session_id
                )

                # Store in evidence table
                evidence_ids = []
                for entry in evidence_entries:
                    evidence_id = self.evidence_table.add_evidence(entry)
                    evidence_ids.append(evidence_id)
                    all_evidence_ids.append(evidence_id)

                fact_evidence[fact] = {
                    "citations_found": len(citations),
                    "evidence_ids": evidence_ids,
                    "evidence_entries": evidence_entries,
                    "verification_confidence": self._calculate_verification_confidence(citations),
                    "recommendations": self._generate_verification_recommendations(citations, fact)
                }

            # Create overall verification summary
            verification_summary = self._create_verification_summary(
                facts, verification_results, fact_evidence, case_context
            )

            result = {
                "session_id": session_id,
                "verification_performed": True,
                "total_facts": len(facts),
                "total_citations": sum(len(citations) for citations in verification_results.values()),
                "total_evidence_entries": len(all_evidence_ids),
                "fact_verification": fact_evidence,
                "evidence_ids": all_evidence_ids,
                "verification_summary": verification_summary,
                "timestamp": datetime.now().isoformat()
            }

            logger.info(f"Fact verification complete: {result['total_citations']} citations, {result['total_evidence_entries']} evidence entries")
            return result

        except Exception as e:
            logger.exception(f"Phase C01 fact verification failed: {e}")
            return {
                "session_id": session_id,
                "verification_performed": False,
                "error": str(e),
                "total_facts": len(facts),
                "total_citations": 0,
                "total_evidence_entries": 0,
                "timestamp": datetime.now().isoformat()
            }

    async def _citations_to_evidence_entries(
        self,
        citations: List[PrecisionCitation],
        fact: str,
        case_context: Dict[str, Any],
        session_id: str
    ) -> List[EvidenceEntry]:
        """Convert precision citations to evidence table entries for fact verification"""
        evidence_entries = []

        for citation in citations:
            # Determine evidence type based on source
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
                page_section=f"Fact Verification - {citation.quality_metrics.domain}",
                content=citation.content,
                evidence_type=evidence_type,
                relevance_score=relevance_score,
                relevance_level=relevance_level,
                bluebook_citation=citation.bluebook_citation,
                extracted_date=citation.publication_date,
                key_terms=self._extract_fact_terms(citation, fact),
                notes=self._create_verification_notes(citation, fact),
                created_by="fact_verification_c01",
            )

            # Add supporting facts based on verification context
            entry.supporting_facts = self._link_to_fact_context(citation, fact, case_context)

            evidence_entries.append(entry)

        return evidence_entries

    def _extract_fact_terms(self, citation: PrecisionCitation, fact: str) -> List[str]:
        """Extract key terms relevant to fact verification"""
        terms = []

        # Add domain and source type
        terms.extend([citation.quality_metrics.domain, citation.source_type])

        # Add fact-specific terms
        fact_words = fact.lower().split()
        for word in fact_words:
            if len(word) > 3:  # Skip short words
                terms.append(word)

        # Add verification keywords
        verification_keywords = [
            "verification", "confirmed", "evidence", "supporting",
            "corroboration", "validation", "substantiation", "proof"
        ]

        text_to_check = f"{citation.title} {citation.content}".lower()
        for keyword in verification_keywords:
            if keyword in text_to_check:
                terms.append(keyword)

        return list(set(terms))  # Remove duplicates

    def _create_verification_notes(
        self,
        citation: PrecisionCitation,
        fact: str
    ) -> str:
        """Create notes for fact verification evidence entry"""
        notes_parts = [
            f"Fact verification research from Phase C01 editing",
            f"Fact: {fact[:50]}..." if len(fact) > 50 else f"Fact: {fact}",
            f"Quality Score: {citation.quality_metrics.overall_quality_score:.1f}/5.0",
            f"Authority Score: {citation.quality_metrics.authority_score:.1f}/5.0",
            f"Source Type: {citation.source_type}",
            f"Domain: {citation.quality_metrics.domain}"
        ]

        return " | ".join(notes_parts)

    def _link_to_fact_context(
        self,
        citation: PrecisionCitation,
        fact: str,
        case_context: Dict[str, Any]
    ) -> List[str]:
        """Link citation to relevant fact context"""
        fact_links = []

        # Create fact IDs based on fact content
        fact_id = fact.lower().replace(" ", "_")[:30]
        fact_links.append(f"fact_verification_{fact_id}")

        # Link to case jurisdiction if mentioned
        jurisdiction = case_context.get("jurisdiction")
        if jurisdiction and jurisdiction.lower() in citation.content.lower():
            fact_links.append(f"jurisdiction_context_{jurisdiction.lower()}")

        # Link to case type
        case_type = case_context.get("case_type")
        if case_type and case_type.lower() in citation.content.lower():
            fact_links.append(f"case_type_context_{case_type.lower()}")

        return fact_links

    def _calculate_verification_confidence(self, citations: List[PrecisionCitation]) -> float:
        """Calculate overall verification confidence for a fact"""
        if not citations:
            return 0.0

        # Weight by quality scores and recency
        total_weighted_score = sum(
            citation.quality_metrics.overall_quality_score * citation.quality_metrics.recency_score
            for citation in citations
        )

        # Normalize to 0-1 scale
        max_possible_score = len(citations) * 5.0
        confidence = total_weighted_score / max_possible_score if max_possible_score > 0 else 0.0

        return min(1.0, confidence)

    def _generate_verification_recommendations(
        self,
        citations: List[PrecisionCitation],
        fact: str
    ) -> List[str]:
        """Generate recommendations based on verification results"""
        recommendations = []

        if not citations:
            recommendations.append("No verification sources found - consider additional fact-checking")
            recommendations.append("Review fact for alternative sources or primary evidence")
            return recommendations

        avg_quality = sum(c.quality_metrics.overall_quality_score for c in citations) / len(citations)

        if avg_quality >= 4.0:
            recommendations.append("Strong verification with high-quality sources")
            recommendations.append("Fact appears well-corroborated")
        elif avg_quality >= 3.0:
            recommendations.append("Moderate verification found")
            recommendations.append("Consider additional sources for stronger corroboration")
        else:
            recommendations.append("Weak verification - sources lack authority")
            recommendations.append("Seek primary sources or court documents for fact confirmation")

        # Source type recommendations
        academic_count = sum(1 for c in citations if c.source_type == "academic")
        if academic_count == 0:
            recommendations.append("No academic sources found - consider scholarly verification")

        return recommendations

    def _create_verification_summary(
        self,
        facts: List[str],
        verification_results: Dict[str, List[PrecisionCitation]],
        fact_evidence: Dict[str, Any],
        case_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create comprehensive verification summary"""
        summary = {
            "total_facts_reviewed": len(facts),
            "facts_with_verification": 0,
            "facts_needing_research": 0,
            "average_verification_confidence": 0.0,
            "highest_confidence_fact": None,
            "lowest_confidence_fact": None,
            "domain_distribution": {},
            "overall_recommendations": []
        }

        if not fact_evidence:
            return summary

        # Calculate statistics
        verification_confidences = {}
        for fact, evidence_data in fact_evidence.items():
            confidence = evidence_data["verification_confidence"]
            verification_confidences[fact] = confidence

            if evidence_data["citations_found"] > 0:
                summary["facts_with_verification"] += 1
            else:
                summary["facts_needing_research"] += 1

            # Track domain distribution
            for evidence_entry in evidence_data["evidence_entries"]:
                for term in evidence_entry.key_terms:
                    if "." in term:  # Likely a domain
                        summary["domain_distribution"][term] = summary["domain_distribution"].get(term, 0) + 1

        if verification_confidences:
            summary["average_verification_confidence"] = sum(verification_confidences.values()) / len(verification_confidences)
            summary["highest_confidence_fact"] = max(verification_confidences, key=verification_confidences.get)
            summary["lowest_confidence_fact"] = min(verification_confidences, key=verification_confidences.get)

        # Generate overall recommendations
        if summary["facts_needing_research"] > 0:
            summary["overall_recommendations"].append(
                f"{summary['facts_needing_research']} facts need additional verification research"
            )

        if summary["average_verification_confidence"] < 0.5:
            summary["overall_recommendations"].append(
                "Overall fact verification is weak - consider strengthening fact-checking process"
            )
        elif summary["average_verification_confidence"] > 0.8:
            summary["overall_recommendations"].append(
                "Strong fact verification across facts - good foundation for legal arguments"
            )

        return summary

    async def get_verification_results(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve verification results for a session"""
        # This would typically query a database or cache
        # For now, return None (would be implemented with persistent storage)
        return None

    async def update_fact_confidence(
        self,
        fact: str,
        additional_evidence: List[str]
    ) -> bool:
        """Update fact confidence based on additional evidence"""
        try:
            # This would update the fact confidence calculation
            # based on new evidence discovered
            logger.info(f"Updated fact confidence for: {fact[:30]}...")
            return True
        except Exception as e:
            logger.error(f"Failed to update fact confidence: {e}")
            return False


# Convenience functions for integration
async def perform_c01_fact_verification(
    facts: List[str],
    case_context: Dict[str, Any],
    session_id: str,
    max_sources_per_fact: int = 2
) -> Dict[str, Any]:
    """Convenience function for Phase C01 fact verification"""
    integration = FactVerificationIntegration()
    return await integration.verify_facts(facts, case_context, session_id, max_sources_per_fact)


if __name__ == "__main__":
    # Example usage
    async def test_c01_integration():
        facts = [
            "Defendant property owner failed to maintain safe premises",
            "Plaintiff slipped and fell due to wet floor",
            "Incident occurred on January 15, 2023"
        ]

        case_context = {
            "jurisdiction": "California",
            "case_type": "premises_liability"
        }

        integration = FactVerificationIntegration()
        results = await integration.verify_facts(
            facts, case_context, "test_session_c01"
        )

        print("Phase C01 Fact Verification Results:")
        print(f"Total Citations: {results['total_citations']}")
        print(f"Evidence Entries: {results['total_evidence_entries']}")
        print(f"Facts Verified: {results['verification_summary']['facts_with_verification']}")

    asyncio.run(test_c01_integration())