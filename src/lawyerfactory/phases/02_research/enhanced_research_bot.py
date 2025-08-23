"""
# Script Name: enhanced_research_bot.py
# Description: Enhanced Research Bot that integrates CourtAuthorityHelper for jurisdiction-aware caselaw research with authority ranking.
# Relationships:
#   - Entity Type: Agent
#   - Directory Group: Research
#   - Group Tags: legal-research, authority-ranking
Enhanced Research Bot for LawyerFactory Research Phase.

This enhanced version integrates the CourtAuthorityHelper to provide:
- Jurisdiction-aware search optimization
- Authority level assessment (0-6 stars)
- Binding vs persuasive authority determination
- Integration with intake form data for event location context
- Enhanced evidence table integration with color-coded ratings
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from ...agents.research.court_authority_helper import CourtAuthorityHelper, JurisdictionContext
from ...agents.research.court_authority_integration import EnhancedCaselawResearcher
from ...compose.bots.caselaw_researcher import CaseLawResult
from ...compose.maestro.registry import AgentInterface, AgentCapability
from ...compose.maestro.workflow_models import WorkflowTask

logger = logging.getLogger(__name__)


@dataclass
class EnhancedResearchResult:
    """Enhanced research result with authority assessment"""
    case: CaseLawResult
    authority_level: int
    is_binding: bool
    reasoning: str
    search_priority: int
    color_code: str


class EnhancedResearchBot(AgentInterface):
    """
    Enhanced research bot that integrates court authority ranking.

    This bot extends the basic caselaw research capabilities with:
    1. Jurisdiction-aware search optimization
    2. Authority level assessment for all results
    3. Integration with intake form data
    4. Evidence table authority rating integration
    """

    def __init__(self, knowledge_graph=None):
        self.knowledge_graph = knowledge_graph
        self.capabilities = [
            AgentCapability.LEGAL_RESEARCH,
            AgentCapability.CASE_ANALYSIS,
            AgentCapability.AUTHORITY_ASSESSMENT
        ]

        # Initialize court authority helper
        self.authority_helper = CourtAuthorityHelper()
        self.enhanced_researcher = EnhancedCaselawResearcher(knowledge_graph)

        # Jurisdiction context from intake form
        self.jurisdiction_context: Optional[JurisdictionContext] = None

    def set_jurisdiction_from_intake(self, intake_form_data: Dict[str, Any]):
        """
        Set jurisdiction context from intake form data.

        Args:
            intake_form_data: Data from legal intake form containing:
                - jurisdiction: Primary jurisdiction
                - event_location: Where events occurred
                - case_type: Type of case
        """
        jurisdiction = intake_form_data.get('jurisdiction', 'federal')
        event_location = intake_form_data.get('event_location')
        case_type = intake_form_data.get('case_type', 'civil')

        # Determine question type from case type
        if 'procedural' in case_type.lower():
            question_type = 'procedural'
        else:
            question_type = 'substantive'

        # Set jurisdiction context
        self.jurisdiction_context = self.authority_helper.determine_jurisdiction_context(
            jurisdiction=jurisdiction,
            question_type=question_type,
            event_location=event_location
        )

        # Also set in enhanced researcher
        self.enhanced_researcher.set_jurisdiction_context(
            jurisdiction=jurisdiction,
            question_type=question_type,
            event_location=event_location
        )

        logger.info(f"Set jurisdiction context: {jurisdiction} ({question_type}) - Event: {event_location}")

    async def process(self, message: str) -> str:
        """Process a natural language research request with authority enhancement"""
        try:
            # Extract legal issues from message
            legal_issues = self._extract_legal_issues(message)

            # Perform enhanced search
            enhanced_results = await self.enhanced_researcher.search_caselaw_with_authority(
                legal_issues=legal_issues,
                intake_form_data=self._get_intake_form_data()
            )

            # Generate enhanced response
            response = "=== ENHANCED CASELAW RESEARCH RESULTS ===\n\n"

            # Group results by authority level
            binding_cases = [r for r in enhanced_results if r.authority_assessment.is_binding]
            persuasive_cases = [r for r in enhanced_results if not r.authority_assessment.is_binding]

            response += f"📊 **SEARCH SUMMARY**\n"
            response += f"Total Cases Found: {len(enhanced_results)}\n"
            response += f"Binding Authority: {len(binding_cases)}\n"
            response += f"Persuasive Authority: {len(persuasive_cases)}\n\n"

            if binding_cases:
                response += "🔴 **BINDING AUTHORITY CASES**\n"
                for i, result in enumerate(binding_cases[:3], 1):
                    case = result.original_case
                    auth = result.authority_assessment
                    response += f"{i}. **{case.case_name}**\n"
                    response += f"   Citation: {case.citation}\n"
                    response += f"   Court: {case.court} ({case.year})\n"
                    response += f"   Authority: {'★' * auth.star_rating} ({auth.authority_level.name})\n"
                    response += f"   Reasoning: {auth.reasoning}\n"
                    response += f"   Relevance: {result.enhanced_relevance_score:.2f}/1.0\n\n"

            if persuasive_cases:
                response += "🟠 **PERSUASIVE AUTHORITY CASES**\n"
                for i, result in enumerate(persuasive_cases[:3], 1):
                    case = result.original_case
                    auth = result.authority_assessment
                    response += f"{i}. **{case.case_name}**\n"
                    response += f"   Citation: {case.citation}\n"
                    response += f"   Court: {case.court} ({case.year})\n"
                    response += f"   Authority: {'★' * auth.star_rating} ({auth.authority_level.name})\n"
                    response += f"   Reasoning: {auth.reasoning}\n"
                    response += f"   Relevance: {result.enhanced_relevance_score:.2f}/1.0\n\n"

            # Add search recommendations if needed
            if len(enhanced_results) < 2:
                recommendations = await self.enhanced_researcher.get_search_recommendations(
                    found_cases=len(enhanced_results),
                    min_cases_needed=2
                )
                if recommendations:
                    response += "💡 **SEARCH RECOMMENDATIONS**\n"
                    response += "Consider expanding search to:\n"
                    for rec in recommendations[:3]:
                        response += f"• {rec['jurisdiction']} {rec['court']} ({rec['authority']})\n"
                    response += "\n"

            return response

        except Exception as e:
            logger.error(f"Error in enhanced research process: {e}")
            return f"Enhanced research failed: {str(e)}"

    async def execute_task(self, task: WorkflowTask, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute research task with authority enhancement"""
        try:
            # Extract legal issues from context
            legal_issues = self._extract_legal_issues_from_context(context)

            # Get intake form data from context if available
            intake_data = context.get('intake_form_data', {})

            # Perform enhanced search
            enhanced_results = await self.enhanced_researcher.search_caselaw_with_authority(
                legal_issues=legal_issues,
                intake_form_data=intake_data
            )

            # Convert to serializable format
            results_data = []
            for result in enhanced_results:
                case = result.original_case
                auth = result.authority_assessment

                results_data.append({
                    'case_name': case.case_name,
                    'citation': case.citation,
                    'court': case.court,
                    'year': case.year,
                    'jurisdiction': case.jurisdiction,
                    'relevance_score': result.enhanced_relevance_score,
                    'authority_level': auth.star_rating,
                    'authority_name': auth.authority_level.name,
                    'is_binding': auth.is_binding,
                    'reasoning': auth.reasoning,
                    'search_priority': auth.search_priority,
                    'color_code': self._get_color_code(auth.star_rating)
                })

            # Generate authority report
            authority_report = self.enhanced_researcher.generate_authority_report(enhanced_results)

            return {
                "status": "completed",
                "cases_found": len(enhanced_results),
                "binding_cases": len([r for r in enhanced_results if r.authority_assessment.is_binding]),
                "results": results_data,
                "authority_report": authority_report,
                "search_hierarchy": self._get_search_hierarchy_info()
            }

        except Exception as e:
            logger.error(f"Error executing enhanced research task: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "cases_found": 0,
                "results": [],
                "authority_report": "",
                "search_hierarchy": []
            }

    async def health_check(self) -> bool:
        """Check if the enhanced research bot is functioning"""
        try:
            # Test basic functionality
            test_issues = ["negligence"]
            enhanced_results = await self.enhanced_researcher.search_caselaw_with_authority(
                legal_issues=test_issues,
                intake_form_data={}
            )
            return True
        except Exception as e:
            logger.error(f"Enhanced research health check failed: {e}")
            return False

    async def initialize(self) -> None:
        """Initialize the enhanced research bot"""
        try:
            await self.enhanced_researcher.initialize()
            logger.info("Enhanced Research Bot initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Enhanced Research Bot: {e}")

    async def cleanup(self) -> None:
        """Clean up resources"""
        await self.enhanced_researcher.cleanup()

    async def can_handle_task(self, task: WorkflowTask) -> bool:
        """Check if this bot can handle the given task"""
        task_text = f"{task.description} {task.agent_type}".lower()
        return any(keyword in task_text for keyword in [
            "case", "precedent", "caselaw", "research", "authority", "enhanced"
        ])

    def _extract_legal_issues(self, text: str) -> List[str]:
        """Extract legal issues from text"""
        # Simple extraction - could be enhanced with NLP
        legal_keywords = [
            'negligence', 'breach', 'contract', 'tort', 'liability',
            'damages', 'injury', 'duty', 'care', 'responsibility'
        ]

        found_issues = []
        text_lower = text.lower()

        for keyword in legal_keywords:
            if keyword in text_lower:
                found_issues.append(keyword)

        return list(set(found_issues))  # Remove duplicates

    def _extract_legal_issues_from_context(self, context: Dict[str, Any]) -> List[str]:
        """Extract legal issues from workflow context"""
        # Look for legal issues in various context fields
        legal_issues = []

        # Check direct legal issues field
        if 'legal_issues' in context:
            legal_issues.extend(context['legal_issues'])

        # Check claim description
        if 'claim_description' in context:
            legal_issues.extend(self._extract_legal_issues(context['claim_description']))

        # Check selected causes
        if 'selected_causes' in context:
            legal_issues.extend(context['selected_causes'])

        return list(set(legal_issues))

    def _get_intake_form_data(self) -> Dict[str, Any]:
        """Get intake form data (placeholder - would integrate with actual form)"""
        # This would be replaced with actual intake form integration
        return {
            'jurisdiction': 'federal',
            'event_location': 'California',
            'case_type': 'civil'
        }

    def _get_color_code(self, star_rating: int) -> str:
        """Get color code for star rating"""
        if star_rating == 0:
            return "gray"
        elif star_rating <= 3:
            return "copper"
        else:
            return "jade"

    def _get_search_hierarchy_info(self) -> List[Dict[str, Any]]:
        """Get information about the current search hierarchy"""
        if not self.jurisdiction_context:
            return []

        hierarchy = self.authority_helper.get_search_hierarchy(self.jurisdiction_context)
        return hierarchy

    # Integration method for evidence table processing
    async def process_evidence_with_authority(
        self,
        evidence_table_path: str,
        intake_form_data: Dict[str, Any]
    ) -> bool:
        """
        Process evidence table and add authority ratings.

        Args:
            evidence_table_path: Path to evidence_table.json
            intake_form_data: Data from legal intake form

        Returns:
            Success status
        """
        try:
            # Set jurisdiction context
            self.set_jurisdiction_from_intake(intake_form_data)

            # Add authority ratings to evidence table
            success = await self.enhanced_researcher.add_authority_to_evidence_table(
                evidence_table_path=evidence_table_path,
                enhanced_results=[]  # Will be populated from existing evidence
            )

            return success

        except Exception as e:
            logger.error(f"Failed to process evidence with authority: {e}")
            return False


# Integration function for the research phase
async def integrate_enhanced_research_phase(
    legal_issues: List[str],
    intake_form_data: Dict[str, Any],
    evidence_table_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Main integration function for the enhanced research phase.

    Args:
        legal_issues: List of legal issues to research
        intake_form_data: Data from legal intake form
        evidence_table_path: Optional path to evidence table for authority rating

    Returns:
        Comprehensive research results with authority assessments
    """

    # Initialize enhanced research bot
    research_bot = EnhancedResearchBot()

    # Set jurisdiction context from intake form
    research_bot.set_jurisdiction_from_intake(intake_form_data)

    # Perform enhanced research
    enhanced_results = await research_bot.enhanced_researcher.search_caselaw_with_authority(
        legal_issues=legal_issues,
        intake_form_data=intake_form_data
    )

    # Process evidence table if provided
    evidence_success = False
    if evidence_table_path:
        evidence_success = await research_bot.process_evidence_with_authority(
            evidence_table_path=evidence_table_path,
            intake_form_data=intake_form_data
        )

    # Generate comprehensive report
    authority_report = research_bot.enhanced_researcher.generate_authority_report(enhanced_results)

    return {
        'success': True,
        'cases_found': len(enhanced_results),
        'binding_cases': len([r for r in enhanced_results if r.authority_assessment.is_binding]),
        'enhanced_results': enhanced_results,
        'authority_report': authority_report,
        'evidence_processing_success': evidence_success,
        'jurisdiction_context': {
            'primary_jurisdiction': research_bot.jurisdiction_context.primary_jurisdiction if research_bot.jurisdiction_context else None,
            'court_type': research_bot.jurisdiction_context.court_type if research_bot.jurisdiction_context else None,
            'event_location': research_bot.jurisdiction_context.event_location if research_bot.jurisdiction_context else None,
            'question_type': research_bot.jurisdiction_context.question_type.value if research_bot.jurisdiction_context else None
        }
    }