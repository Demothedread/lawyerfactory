"""
Phase B01 Claim Substantiation Integration
Integrates precision citation service with claim validation and substantiation workflows.
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


class ClaimSubstantiationIntegration:
    """
    Integrates claim substantiation research into Phase B01 review process
    """

    def __init__(self):
        self.citation_service = PrecisionCitationService()
        self.evidence_table = EnhancedEvidenceTable()

    async def substantiate_claims(
        self,
        claims: List[str],
        jurisdiction: str,
        case_context: Dict[str, Any],
        session_id: str,
        max_sources_per_claim: int = 3
    ) -> Dict[str, Any]:
        """
        Perform claim substantiation research for Phase B01

        Args:
            claims: List of legal claims to substantiate
            jurisdiction: Legal jurisdiction
            case_context: Case context and background
            session_id: Session identifier
            max_sources_per_claim: Maximum sources per claim (default 3)

        Returns:
            Substantiation results with citations and evidence entries
        """
        logger.info(f"Starting Phase B01 claim substantiation for {len(claims)} claims")

        try:
            # Perform precision claim substantiation
            substantiation_results = await self.citation_service.search_claim_substantiation(
                claims, jurisdiction, max_sources_per_claim
            )

            # Convert results to evidence entries and organize by claim
            claim_evidence = {}
            all_evidence_ids = []

            for claim, citations in substantiation_results.items():
                # Convert citations to evidence entries
                evidence_entries = await self._citations_to_evidence_entries(
                    citations, claim, jurisdiction, case_context, session_id
                )

                # Store in evidence table
                evidence_ids = []
                for entry in evidence_entries:
                    evidence_id = self.evidence_table.add_evidence(entry)
                    evidence_ids.append(evidence_id)
                    all_evidence_ids.append(evidence_id)

                claim_evidence[claim] = {
                    "citations_found": len(citations),
                    "evidence_ids": evidence_ids,
                    "evidence_entries": evidence_entries,
                    "substantiation_strength": self._calculate_substantiation_strength(citations),
                    "recommendations": self._generate_substantiation_recommendations(citations, claim)
                }

            # Create overall substantiation summary
            substantiation_summary = self._create_substantiation_summary(
                claims, substantiation_results, claim_evidence, case_context
            )

            result = {
                "session_id": session_id,
                "substantiation_performed": True,
                "total_claims": len(claims),
                "total_citations": sum(len(citations) for citations in substantiation_results.values()),
                "total_evidence_entries": len(all_evidence_ids),
                "claim_substantiation": claim_evidence,
                "evidence_ids": all_evidence_ids,
                "substantiation_summary": substantiation_summary,
                "timestamp": datetime.now().isoformat()
            }

            logger.info(f"Claim substantiation complete: {result['total_citations']} citations, {result['total_evidence_entries']} evidence entries")
            return result

        except Exception as e:
            logger.exception(f"Phase B01 claim substantiation failed: {e}")
            return {
                "session_id": session_id,
                "substantiation_performed": False,
                "error": str(e),
                "total_claims": len(claims),
                "total_citations": 0,
                "total_evidence_entries": 0,
                "timestamp": datetime.now().isoformat()
            }

    async def _citations_to_evidence_entries(
        self,
        citations: List[PrecisionCitation],
        claim: str,
        jurisdiction: str,
        case_context: Dict[str, Any],
        session_id: str
    ) -> List[EvidenceEntry]:
        """Convert precision citations to evidence table entries for claim substantiation"""
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
                page_section=f"Claim Substantiation - {citation.quality_metrics.domain}",
                content=citation.content,
                evidence_type=evidence_type,
                relevance_score=relevance_score,
                relevance_level=relevance_level,
                bluebook_citation=citation.bluebook_citation,
                extracted_date=citation.publication_date,
                key_terms=self._extract_claim_terms(citation, claim),
                notes=self._create_substantiation_notes(citation, claim, jurisdiction),
                created_by="claim_substantiation_b01",
            )

            # Add supporting facts based on claim and jurisdiction
            entry.supporting_facts = self._link_to_claim_facts(citation, claim, jurisdiction, case_context)

            evidence_entries.append(entry)

        return evidence_entries

    def _extract_claim_terms(self, citation: PrecisionCitation, claim: str) -> List[str]:
        """Extract key terms relevant to claim substantiation"""
        terms = []

        # Add domain and source type
        terms.extend([citation.quality_metrics.domain, citation.source_type])

        # Add claim-specific terms
        claim_words = claim.lower().split()
        for word in claim_words:
            if len(word) > 3:  # Skip short words
                terms.append(word)

        # Add legal substantiation keywords
        substantiation_keywords = [
            "precedent", "case law", "legal authority", "court ruling",
            "judicial decision", "legal standard", "burden of proof",
            "elements", "substantiation", "evidence required"
        ]

        text_to_check = f"{citation.title} {citation.content}".lower()
        for keyword in substantiation_keywords:
            if keyword in text_to_check:
                terms.append(keyword.replace(" ", "_"))

        return list(set(terms))  # Remove duplicates

    def _create_substantiation_notes(
        self,
        citation: PrecisionCitation,
        claim: str,
        jurisdiction: str
    ) -> str:
        """Create notes for claim substantiation evidence entry"""
        notes_parts = [
            f"Claim substantiation research from Phase B01 review",
            f"Claim: {claim[:50]}..." if len(claim) > 50 else f"Claim: {claim}",
            f"Quality Score: {citation.quality_metrics.overall_quality_score:.1f}/5.0",
            f"Authority Score: {citation.quality_metrics.authority_score:.1f}/5.0",
            f"Source Type: {citation.source_type}",
            f"Domain: {citation.quality_metrics.domain}",
            f"Jurisdiction: {jurisdiction}"
        ]

        return " | ".join(notes_parts)

    def _link_to_claim_facts(
        self,
        citation: PrecisionCitation,
        claim: str,
        jurisdiction: str,
        case_context: Dict[str, Any]
    ) -> List[str]:
        """Link citation to relevant claim facts"""
        fact_links = []

        # Create fact IDs based on claim elements
        if jurisdiction.lower() in citation.content.lower():
            fact_links.append(f"claim_jurisdiction_{jurisdiction.lower()}")

        # Link to specific claim
        claim_id = claim.lower().replace(" ", "_")[:30]
        fact_links.append(f"claim_substantiation_{claim_id}")

        # Check for legal element matches
        legal_elements = [
            "duty", "breach", "causation", "damages", "negligence",
            "contract", "tort", "liability", "standard of care"
        ]

        content_lower = citation.content.lower()
        for element in legal_elements:
            if element in content_lower and element in claim.lower():
                fact_links.append(f"legal_element_{element}")

        return fact_links

    def _calculate_substantiation_strength(self, citations: List[PrecisionCitation]) -> float:
        """Calculate overall substantiation strength for a claim"""
        if not citations:
            return 0.0

        # Weight by quality scores
        total_weighted_score = sum(
            citation.quality_metrics.overall_quality_score for citation in citations
        )

        # Normalize to 0-1 scale
        max_possible_score = len(citations) * 5.0
        strength = total_weighted_score / max_possible_score if max_possible_score > 0 else 0.0

        return min(1.0, strength)

    def _generate_substantiation_recommendations(
        self,
        citations: List[PrecisionCitation],
        claim: str
    ) -> List[str]:
        """Generate recommendations based on substantiation results"""
        recommendations = []

        if not citations:
            recommendations.append("No substantiating sources found - consider additional research")
            recommendations.append("Review claim elements for alternative legal theories")
            return recommendations

        avg_quality = sum(c.quality_metrics.overall_quality_score for c in citations) / len(citations)

        if avg_quality >= 4.0:
            recommendations.append("Strong substantiation with high-quality sources")
            recommendations.append("Consider citing these sources in legal brief")
        elif avg_quality >= 3.0:
            recommendations.append("Moderate substantiation found")
            recommendations.append("May benefit from additional authoritative sources")
        else:
            recommendations.append("Weak substantiation - sources lack authority")
            recommendations.append("Seek primary legal authorities and case law")

        # Source type recommendations
        academic_count = sum(1 for c in citations if c.source_type == "academic")
        if academic_count == 0:
            recommendations.append("No academic sources found - consider law review research")

        return recommendations

    def _create_substantiation_summary(
        self,
        claims: List[str],
        substantiation_results: Dict[str, List[PrecisionCitation]],
        claim_evidence: Dict[str, Any],
        case_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create comprehensive substantiation summary"""
        summary = {
            "total_claims_reviewed": len(claims),
            "claims_with_substantiation": 0,
            "claims_needing_research": 0,
            "average_substantiation_strength": 0.0,
            "strongest_claim": None,
            "weakest_claim": None,
            "domain_distribution": {},
            "overall_recommendations": []
        }

        if not claim_evidence:
            return summary

        # Calculate statistics
        substantiation_strengths = {}
        for claim, evidence_data in claim_evidence.items():
            strength = evidence_data["substantiation_strength"]
            substantiation_strengths[claim] = strength

            if evidence_data["citations_found"] > 0:
                summary["claims_with_substantiation"] += 1
            else:
                summary["claims_needing_research"] += 1

            # Track domain distribution
            for evidence_entry in evidence_data["evidence_entries"]:
                for term in evidence_entry.key_terms:
                    if "." in term:  # Likely a domain
                        summary["domain_distribution"][term] = summary["domain_distribution"].get(term, 0) + 1

        if substantiation_strengths:
            summary["average_substantiation_strength"] = sum(substantiation_strengths.values()) / len(substantiation_strengths)
            summary["strongest_claim"] = max(substantiation_strengths, key=substantiation_strengths.get)
            summary["weakest_claim"] = min(substantiation_strengths, key=substantiation_strengths.get)

        # Generate overall recommendations
        if summary["claims_needing_research"] > 0:
            summary["overall_recommendations"].append(
                f"{summary['claims_needing_research']} claims need additional research"
            )

        if summary["average_substantiation_strength"] < 0.5:
            summary["overall_recommendations"].append(
                "Overall substantiation is weak - consider strengthening legal research"
            )
        elif summary["average_substantiation_strength"] > 0.8:
            summary["overall_recommendations"].append(
                "Strong substantiation across claims - good foundation for legal arguments"
            )

        return summary

    async def get_substantiation_results(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve substantiation results for a session"""
        # This would typically query a database or cache
        # For now, return None (would be implemented with persistent storage)
        return None

    async def update_claim_strength(
        self,
        claim: str,
        additional_evidence: List[str]
    ) -> bool:
        """Update claim strength based on additional evidence"""
        try:
            # This would update the claim strength calculation
            # based on new evidence discovered
            logger.info(f"Updated claim strength for: {claim[:30]}...")
            return True
        except Exception as e:
            logger.error(f"Failed to update claim strength: {e}")
            return False


# Convenience functions for integration
async def perform_b01_claim_substantiation(
    claims: List[str],
    jurisdiction: str,
    case_context: Dict[str, Any],
    session_id: str,
    max_sources_per_claim: int = 3
) -> Dict[str, Any]:
    """Convenience function for Phase B01 claim substantiation"""
    integration = ClaimSubstantiationIntegration()
    return await integration.substantiate_claims(
        claims, jurisdiction, case_context, session_id, max_sources_per_claim
    )


if __name__ == "__main__":
    # Example usage
    async def test_b01_integration():
        claims = [
            "negligence per se violation of safety regulations",
            "breach of duty of care in premises maintenance",
            "failure to warn of known hazards"
        ]

        integration = ClaimSubstantiationIntegration()
        results = await integration.substantiate_claims(
            claims, "California", {"case_type": "premises_liability"}, "test_session_b01"
        )

        print("Phase B01 Claim Substantiation Results:")
        print(f"Total Citations: {results['total_citations']}")
        print(f"Evidence Entries: {results['total_evidence_entries']}")
        print(f"Claims Substantiated: {results['substantiation_summary']['claims_with_substantiation']}")

    asyncio.run(test_b01_integration())