"""
# Script Name: court_authority_integration.py
# Description: Integration layer between CourtAuthorityHelper and CaselawResearcher for enhanced legal research with authority ranking.
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Research
#   - Group Tags: legal-research, authority-ranking
Integration layer between CourtAuthorityHelper and CaselawResearcher.

This module provides enhanced caselaw research capabilities by integrating
the Court Authority Helper's jurisdiction-aware search optimization with
the Caselaw Researcher's search capabilities.
"""

from dataclasses import dataclass, field
import logging
from typing import Any, Dict, List, Optional

from ...compose.bots.caselaw_researcher import CaselawResearcherAgent, CaseLawResult
from .court_authority_helper import (
    CaselawAuthority,
    CourtAuthorityHelper,
    JurisdictionContext,
)

logger = logging.getLogger(__name__)


@dataclass
class EnhancedCaselawResult:
    """Enhanced caselaw result with authority rating"""

    original_case: CaseLawResult
    authority_assessment: CaselawAuthority
    enhanced_relevance_score: float
    search_priority: int


class EnhancedCaselawResearcher:
    """
    Enhanced caselaw researcher that integrates authority ranking.

    This class wraps the existing CaselawResearcherAgent and enhances it with:
    1. Jurisdiction-aware search optimization
    2. Authority level assessment for all results
    3. Priority-based search expansion
    4. Integration with intake form data for event location context
    """

    def __init__(self, knowledge_graph=None):
        self.base_researcher = CaselawResearcherAgent(knowledge_graph)
        self.authority_helper = CourtAuthorityHelper()
        self.jurisdiction_context: Optional[JurisdictionContext] = None

    def set_jurisdiction_context(
        self,
        jurisdiction: str,
        question_type: str = "substantive",
        event_location: Optional[str] = None,
        venue: Optional[str] = None,
    ):
        """
        Set jurisdiction context for authority-aware searching.

        Args:
            jurisdiction: Primary jurisdiction (federal, state name, etc.)
            question_type: Type of legal question (procedural/substantive)
            event_location: Where events occurred (from intake form)
            venue: Court where case is filed
        """
        self.jurisdiction_context = (
            self.authority_helper.determine_jurisdiction_context(
                jurisdiction=jurisdiction,
                question_type=question_type,
                event_location=event_location,
                venue=venue,
            )
        )

        logger.info(f"Set jurisdiction context: {self.jurisdiction_context}")

    async def search_caselaw_with_authority(
        self, legal_issues: List[str], intake_form_data: Optional[Dict[str, Any]] = None
    ) -> List[EnhancedCaselawResult]:
        """
        Enhanced caselaw search with authority ranking.

        Args:
            legal_issues: List of legal issues to search for
            intake_form_data: Data from legal intake form for jurisdiction context

        Returns:
            List of enhanced caselaw results with authority ratings
        """

        # Set jurisdiction context from intake form if available
        if intake_form_data and not self.jurisdiction_context:
            jurisdiction = intake_form_data.get("jurisdiction", "federal")
            event_location = intake_form_data.get("event_location")
            self.set_jurisdiction_context(
                jurisdiction=jurisdiction, event_location=event_location
            )

        # Get search hierarchy for optimization
        search_hierarchy = []
        if self.jurisdiction_context:
            search_hierarchy = self.authority_helper.get_search_hierarchy(
                self.jurisdiction_context
            )
            logger.info(f"Using search hierarchy with {len(search_hierarchy)} levels")

        # Perform base search
        base_results = await self.base_researcher.search_caselaw(legal_issues)

        # Enhance results with authority assessment
        enhanced_results = []
        for case in base_results:
            if self.jurisdiction_context:
                # Assess authority level
                authority = self.authority_helper.assess_caselaw_authority(
                    case_citation=case.citation,
                    case_court=case.court,
                    case_jurisdiction=case.jurisdiction,
                    context=self.jurisdiction_context,
                )

                # Calculate enhanced relevance score
                enhanced_score = self._calculate_enhanced_relevance(
                    case.relevance_score, authority.star_rating
                )

                enhanced_result = EnhancedCaselawResult(
                    original_case=case,
                    authority_assessment=authority,
                    enhanced_relevance_score=enhanced_score,
                    search_priority=authority.search_priority,
                )

                enhanced_results.append(enhanced_result)
            else:
                # Fallback without jurisdiction context
                fallback_authority = CaselawAuthority(
                    case_name=case.case_name,
                    citation=case.citation,
                    court=case.court,
                    jurisdiction=case.jurisdiction,
                    authority_level=self.authority_helper._calculate_authority_level(
                        case.court,
                        case.jurisdiction,
                        JurisdictionContext(primary_jurisdiction="federal"),
                    ),
                    star_rating=1,  # Conservative fallback
                    is_binding=False,
                    reasoning="No jurisdiction context available",
                    search_priority=5,
                )

                enhanced_result = EnhancedCaselawResult(
                    original_case=case,
                    authority_assessment=fallback_authority,
                    enhanced_relevance_score=case.relevance_score,
                    search_priority=fallback_authority.search_priority,
                )

                enhanced_results.append(enhanced_result)

        # Sort by enhanced relevance and authority level
        enhanced_results.sort(
            key=lambda x: (
                x.enhanced_relevance_score,
                x.authority_assessment.star_rating,
            ),
            reverse=True,
        )

        logger.info(
            f"Enhanced search completed: {len(enhanced_results)} results with authority ratings"
        )
        return enhanced_results

    def _calculate_enhanced_relevance(
        self, base_relevance: float, authority_stars: int
    ) -> float:
        """
        Calculate enhanced relevance score combining base relevance with authority level.

        Args:
            base_relevance: Original relevance score (0-1)
            authority_stars: Authority level (0-6)

        Returns:
            Enhanced relevance score (0-1)
        """
        # Authority weight: higher authority increases relevance
        authority_weight = min(authority_stars / 6.0, 1.0)  # 0-1 scale

        # Combine base relevance with authority weight
        # Authority gets 30% weight, base relevance gets 70%
        enhanced_score = (base_relevance * 0.7) + (authority_weight * 0.3)

        return min(enhanced_score, 1.0)  # Cap at 1.0

    async def get_search_recommendations(
        self, found_cases: int, min_cases_needed: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Get search recommendations based on results.

        Args:
            found_cases: Number of cases found so far
            min_cases_needed: Minimum number of cases needed

        Returns:
            List of recommended search parameters
        """

        if not self.jurisdiction_context:
            return []

        return self.authority_helper.optimize_search_parameters(
            context=self.jurisdiction_context,
            found_cases=found_cases,
            min_cases_needed=min_cases_needed,
        )

    def generate_authority_report(
        self, enhanced_results: List[EnhancedCaselawResult]
    ) -> str:
        """
        Generate a report on the authority levels of found cases.

        Args:
            enhanced_results: List of enhanced caselaw results

        Returns:
            Formatted authority report
        """

        if not enhanced_results:
            return "No cases found for authority analysis."

        report = "=== CASELAW AUTHORITY ANALYSIS ===\n\n"

        # Group by authority level
        binding_cases = [
            r for r in enhanced_results if r.authority_assessment.is_binding
        ]
        persuasive_cases = [
            r for r in enhanced_results if not r.authority_assessment.is_binding
        ]

        report += f"TOTAL CASES FOUND: {len(enhanced_results)}\n"
        report += f"BINDING AUTHORITY: {len(binding_cases)}\n"
        report += f"PERSUASIVE AUTHORITY: {len(persuasive_cases)}\n\n"

        if binding_cases:
            report += "📋 BINDING CASES (★4-6):\n"
            for i, result in enumerate(binding_cases[:5], 1):
                case = result.original_case
                auth = result.authority_assessment
                report += f"{i}. {case.case_name}\n"
                report += f"   Citation: {case.citation}\n"
                report += f"   Authority: {'★' * auth.star_rating} ({auth.authority_level.name})\n"
                report += f"   Reasoning: {auth.reasoning}\n\n"

        if persuasive_cases:
            report += "💭 PERSUASIVE CASES (★1-3):\n"
            for i, result in enumerate(persuasive_cases[:5], 1):
                case = result.original_case
                auth = result.authority_assessment
                report += f"{i}. {case.case_name}\n"
                report += f"   Citation: {case.citation}\n"
                report += f"   Authority: {'★' * auth.star_rating} ({auth.authority_level.name})\n"
                report += f"   Reasoning: {auth.reasoning}\n\n"

        return report

    async def add_authority_to_evidence_table(
        self, evidence_table_path: str, enhanced_results: List[EnhancedCaselawResult]
    ) -> bool:
        """
        Add authority ratings to evidence table entries.

        Args:
            evidence_table_path: Path to evidence_table.json
            enhanced_results: Enhanced caselaw results with authority data

        Returns:
            Success status
        """

        try:
            # Load evidence table
            with open(evidence_table_path, "r", encoding="utf-8") as f:
                table_data = json.load(f)

            # Create mapping from citations to authority data
            authority_map = {}
            for result in enhanced_results:
                citation = result.original_case.citation
                authority_map[citation] = {
                    "stars": result.authority_assessment.star_rating,
                    "level": result.authority_assessment.authority_level.name,
                    "is_binding": result.authority_assessment.is_binding,
                    "reasoning": result.authority_assessment.reasoning,
                    "color_code": self._get_color_code(
                        result.authority_assessment.star_rating
                    ),
                }

            # Update evidence entries with authority data
            updated_count = 0
            for entry in table_data.get("evidence_entries", []):
                citation = entry.get("bluebook_citation", "")
                if citation in authority_map:
                    entry["authority_rating"] = authority_map[citation]
                    updated_count += 1

            # Save updated table
            with open(evidence_table_path, "w", encoding="utf-8") as f:
                json.dump(table_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Added authority ratings to {updated_count} evidence entries")
            return True

        except Exception as e:
            logger.error(f"Failed to add authority ratings to evidence table: {e}")
            return False

    def _get_color_code(self, star_rating: int) -> str:
        """Get color code for star rating display"""
        if star_rating == 0:
            return "gray"  # No authority
        elif star_rating <= 3:
            return "copper"  # Persuasive (least to most)
        else:
            return "jade"  # Binding (least to most)

    # Delegate other methods to base researcher
    async def process(self, message: str) -> str:
        return await self.base_researcher.process(message)

    async def execute_task(self, task, context: Dict[str, Any]) -> Dict[str, Any]:
        return await self.base_researcher.execute_task(task, context)

    async def health_check(self) -> bool:
        return await self.base_researcher.health_check()

    async def initialize(self) -> None:
        await self.base_researcher.initialize()

    async def cleanup(self) -> None:
        await self.base_researcher.cleanup()

    async def can_handle_task(self, task) -> bool:
        return await self.base_researcher.can_handle_task(task)


# Integration example for evidence table processing
async def process_evidence_with_authority(
    evidence_table_path: str, intake_form_data: Dict[str, Any], legal_issues: List[str]
) -> Dict[str, Any]:
    """
    Complete workflow for processing evidence with authority ratings.

    This function demonstrates how to integrate the enhanced caselaw researcher
    with the evidence table processing workflow.
    """

    # Initialize enhanced researcher
    researcher = EnhancedCaselawResearcher()

    # Set jurisdiction context from intake form
    researcher.set_jurisdiction_context(
        jurisdiction=intake_form_data.get("jurisdiction", "federal"),
        event_location=intake_form_data.get("event_location"),
        question_type="substantive",  # Could be determined from context
    )

    # Search for caselaw with authority enhancement
    enhanced_results = await researcher.search_caselaw_with_authority(
        legal_issues=legal_issues, intake_form_data=intake_form_data
    )

    # Add authority ratings to evidence table
    success = await researcher.add_authority_to_evidence_table(
        evidence_table_path=evidence_table_path, enhanced_results=enhanced_results
    )

    # Generate authority report
    report = researcher.generate_authority_report(enhanced_results)

    return {
        "success": success,
        "results_count": len(enhanced_results),
        "binding_cases": len(
            [r for r in enhanced_results if r.authority_assessment.is_binding]
        ),
        "authority_report": report,
        "enhanced_results": [r.__dict__ for r in enhanced_results],
    }


if __name__ == "__main__":
    # Example usage
    import asyncio

    async def main():
        researcher = EnhancedCaselawResearcher()

        # Example: Federal substantive question
        researcher.set_jurisdiction_context(
            jurisdiction="federal",
            question_type="substantive",
            event_location="California",  # From intake form
        )

        # Search with authority enhancement
        results = await researcher.search_caselaw_with_authority(
            legal_issues=["negligence", "duty of care"],
            intake_form_data={
                "jurisdiction": "federal",
                "event_location": "California",
            },
        )

        # Print results with authority ratings
        for result in results[:3]:
            case = result.original_case
            auth = result.authority_assessment
            print(f"Case: {case.case_name}")
            print(f"Citation: {case.citation}")
            print(f"Authority: {'★' * auth.star_rating} ({auth.authority_level.name})")
            print(f"Binding: {auth.is_binding}")
            print(f"Reasoning: {auth.reasoning}")
            print("---")

    asyncio.run(main())
