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
from dataclasses import dataclass, field
import logging
from typing import Any, Dict, List, Optional

from ...agents.research.court_authority_helper import CourtAuthorityHelper, JurisdictionContext
from ...agents.research.court_authority_integration import EnhancedCaselawResearcher
from ...compose.bots.caselaw_researcher import CaseLawResult
from ...compose.maestro.registry import AgentCapability, AgentInterface
from ...compose.maestro.workflow_models import WorkflowTask
from ...storage.enhanced_unified_storage_api import get_enhanced_unified_storage_api

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
            AgentCapability.AUTHORITY_ASSESSMENT,
        ]

        # Initialize court authority helper
        self.authority_helper = CourtAuthorityHelper()
        self.enhanced_researcher = EnhancedCaselawResearcher(knowledge_graph)

        # Initialize unified storage API
        self.unified_storage = get_unified_storage_api()

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
        jurisdiction = intake_form_data.get("jurisdiction", "federal")
        event_location = intake_form_data.get("event_location")
        case_type = intake_form_data.get("case_type", "civil")

        # Determine question type from case type
        if "procedural" in case_type.lower():
            question_type = "procedural"
        else:
            question_type = "substantive"

        # Set jurisdiction context
        self.jurisdiction_context = self.authority_helper.determine_jurisdiction_context(
            jurisdiction=jurisdiction,
            question_type=question_type,
            event_location=event_location,
        )

        # Also set in enhanced researcher
        self.enhanced_researcher.set_jurisdiction_context(
            jurisdiction=jurisdiction,
            question_type=question_type,
            event_location=event_location,
        )

        logger.info(
            f"Set jurisdiction context: {jurisdiction} ({question_type}) - Event: {event_location}"
        )

    async def process(self, message: str) -> str:
        """Process a natural language research request with authority enhancement"""
        try:
            # Extract legal issues from message
            legal_issues = self._extract_legal_issues(message)

            # Perform enhanced search
            enhanced_results = await self.enhanced_researcher.search_caselaw_with_authority(
                legal_issues=legal_issues,
                intake_form_data=self._get_intake_form_data(),
            )

            # Generate enhanced response
            response = "=== ENHANCED CASELAW RESEARCH RESULTS ===\n\n"

            # Group results by authority level
            binding_cases = [r for r in enhanced_results if r.authority_assessment.is_binding]
            persuasive_cases = [
                r for r in enhanced_results if not r.authority_assessment.is_binding
            ]

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
                    response += (
                        f"   Authority: {'★' * auth.star_rating} ({auth.authority_level.name})\n"
                    )
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
                    response += (
                        f"   Authority: {'★' * auth.star_rating} ({auth.authority_level.name})\n"
                    )
                    response += f"   Reasoning: {auth.reasoning}\n"
                    response += f"   Relevance: {result.enhanced_relevance_score:.2f}/1.0\n\n"

            # Add search recommendations if needed
            if len(enhanced_results) < 2:
                recommendations = await self.enhanced_researcher.get_search_recommendations(
                    found_cases=len(enhanced_results), min_cases_needed=2
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
        """Execute research task with authority enhancement and unified storage integration"""
        try:
            # Extract legal issues from context
            legal_issues = self._extract_legal_issues_from_context(context)

            # Get intake form data from context if available
            intake_data = context.get("intake_form_data", {})
            case_id = context.get("case_id", "unknown_case")

            # Set jurisdiction context from intake data
            if intake_data:
                self.set_jurisdiction_from_intake(intake_data)

            # Perform enhanced search
            enhanced_results = await self.enhanced_researcher.search_caselaw_with_authority(
                legal_issues=legal_issues, intake_form_data=intake_data
            )

            # Convert to EnhancedResearchResult format for unified storage
            research_results = []
            for result in enhanced_results:
                case = result.original_case
                auth = result.authority_assessment

                research_result = EnhancedResearchResult(
                    case=case,
                    authority_level=auth.star_rating,
                    is_binding=auth.is_binding,
                    reasoning=auth.reasoning,
                    search_priority=auth.search_priority,
                    color_code=self._get_color_code(auth.star_rating),
                )
                research_results.append(research_result)

            # Store research results through unified storage pipeline
            storage_metadata = {
                "task_id": task.id,
                "workflow_phase": "research",
                "legal_issues": legal_issues,
                "jurisdiction_context": (
                    {
                        "primary_jurisdiction": (
                            self.jurisdiction_context.primary_jurisdiction
                            if self.jurisdiction_context
                            else None
                        ),
                        "court_type": (
                            self.jurisdiction_context.court_type
                            if self.jurisdiction_context
                            else None
                        ),
                        "event_location": (
                            self.jurisdiction_context.event_location
                            if self.jurisdiction_context
                            else None
                        ),
                    }
                    if self.jurisdiction_context
                    else None
                ),
            }

            storage_result = await self.store_research_results(
                research_results, case_id, storage_metadata
            )

            # Convert to serializable format
            results_data = []
            for result, storage_info in zip(enhanced_results, storage_result.get("results", [])):
                case = result.original_case
                auth = result.authority_assessment

                results_data.append(
                    {
                        "case_name": case.case_name,
                        "citation": case.citation,
                        "court": case.court,
                        "year": case.year,
                        "jurisdiction": case.jurisdiction,
                        "relevance_score": result.enhanced_relevance_score,
                        "authority_level": auth.star_rating,
                        "authority_name": auth.authority_level.name,
                        "is_binding": auth.is_binding,
                        "reasoning": auth.reasoning,
                        "search_priority": auth.search_priority,
                        "color_code": self._get_color_code(auth.star_rating),
                        "object_id": storage_info.get("object_id"),  # Add ObjectID
                        "storage_urls": storage_info.get("storage_urls", {}),  # Add storage URLs
                    }
                )

            # Generate authority report
            authority_report = self.enhanced_researcher.generate_authority_report(enhanced_results)

            return {
                "status": "completed",
                "cases_found": len(enhanced_results),
                "binding_cases": len(
                    [r for r in enhanced_results if r.authority_assessment.is_binding]
                ),
                "results": results_data,
                "authority_report": authority_report,
                "search_hierarchy": self._get_search_hierarchy_info(),
                "storage_result": storage_result,  # Include storage results
                "object_ids": storage_result.get("object_ids", []),  # Include ObjectIDs
            }

        except Exception as e:
            logger.error(f"Error executing enhanced research task: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "cases_found": 0,
                "results": [],
                "authority_report": "",
                "search_hierarchy": [],
                "storage_result": {"success": False, "error": str(e)},
                "object_ids": [],
            }

    async def health_check(self) -> bool:
        """Check if the enhanced research bot is functioning"""
        try:
            # Test basic functionality
            test_issues = ["negligence"]
            enhanced_results = await self.enhanced_researcher.search_caselaw_with_authority(
                legal_issues=test_issues, intake_form_data={}
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
        return any(
            keyword in task_text
            for keyword in [
                "case",
                "precedent",
                "caselaw",
                "research",
                "authority",
                "enhanced",
            ]
        )

    def _extract_legal_issues(self, text: str) -> List[str]:
        """Extract legal issues from text"""
        # Simple extraction - could be enhanced with NLP
        legal_keywords = [
            "negligence",
            "breach",
            "contract",
            "tort",
            "liability",
            "damages",
            "injury",
            "duty",
            "care",
            "responsibility",
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
        if "legal_issues" in context:
            legal_issues.extend(context["legal_issues"])

        # Check claim description
        if "claim_description" in context:
            legal_issues.extend(self._extract_legal_issues(context["claim_description"]))

        # Check selected causes
        if "selected_causes" in context:
            legal_issues.extend(context["selected_causes"])

        return list(set(legal_issues))

    def _get_intake_form_data(self) -> Dict[str, Any]:
        """Get intake form data (placeholder - would integrate with actual form)"""
        # This would be replaced with actual intake form integration
        return {
            "jurisdiction": "federal",
            "event_location": "California",
            "case_type": "civil",
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
        self, evidence_table_path: str, intake_form_data: Dict[str, Any]
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
                enhanced_results=[],  # Will be populated from existing evidence
            )

            return success

        except Exception as e:
            logger.error(f"Failed to process evidence with authority: {e}")
            return False

    # Unified Storage Integration Methods
    async def store_research_results(
        self,
        research_results: List[EnhancedResearchResult],
        case_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Store research results through unified storage pipeline.

        Args:
            research_results: List of enhanced research results
            case_id: Associated case identifier
            metadata: Additional metadata for storage

        Returns:
            Storage results with ObjectIDs
        """
        try:
            stored_results = []
            object_ids = []

            for result in research_results:
                # Convert research result to storable format
                research_content = self._format_research_result_for_storage(result)

                # Store through unified storage
                storage_result = await self.unified_storage.store_evidence(
                    file_content=research_content.encode("utf-8"),
                    filename=f"research_{result.case.citation.replace('/', '_')}.txt",
                    metadata={
                        "case_id": case_id,
                        "citation": result.case.citation,
                        "court": result.case.court,
                        "year": result.case.year,
                        "authority_level": result.authority_level,
                        "is_binding": result.is_binding,
                        "research_phase": "caselaw_research",
                        "jurisdiction": (
                            self.jurisdiction_context.primary_jurisdiction
                            if self.jurisdiction_context
                            else None
                        ),
                        **(metadata or {}),
                    },
                    source_phase="research",
                )

                if storage_result.success:
                    object_ids.append(storage_result.object_id)
                    stored_results.append(
                        {
                            "object_id": storage_result.object_id,
                            "citation": result.case.citation,
                            "authority_level": result.authority_level,
                            "storage_urls": {
                                "s3": storage_result.s3_url,
                                "evidence": storage_result.evidence_id,
                                "vector": storage_result.vector_ids,
                            },
                        }
                    )
                else:
                    logger.warning(
                        f"Failed to store research result {result.case.citation}: {storage_result.error}"
                    )

            return {
                "success": True,
                "stored_count": len(stored_results),
                "object_ids": object_ids,
                "results": stored_results,
            }

        except Exception as e:
            logger.error(f"Failed to store research results: {e}")
            return {
                "success": False,
                "error": str(e),
                "stored_count": 0,
                "object_ids": [],
                "results": [],
            }

    async def retrieve_research_by_object_id(self, object_id: str) -> Dict[str, Any]:
        """
        Retrieve research results using ObjectID.

        Args:
            object_id: The ObjectID to retrieve

        Returns:
            Research data from unified storage
        """
        try:
            evidence_data = await self.unified_storage.get_evidence(object_id)

            if "error" in evidence_data:
                return evidence_data

            # Enhance with research-specific data
            metadata = evidence_data.get("metadata", {})
            research_data = {
                "object_id": object_id,
                "citation": metadata.get("citation"),
                "court": metadata.get("court"),
                "year": metadata.get("year"),
                "authority_level": metadata.get("authority_level"),
                "is_binding": metadata.get("is_binding"),
                "jurisdiction": metadata.get("jurisdiction"),
                "available_tiers": evidence_data.get("available_tiers", []),
                "content": None,
                "evidence_data": evidence_data.get("evidence_data"),
                "vector_data": evidence_data.get("vector_data"),
            }

            # Try to get content from S3 if available
            if "s3" in evidence_data.get("available_tiers", []):
                s3_content = evidence_data.get("s3_data")
                if s3_content and isinstance(s3_content, bytes):
                    try:
                        research_data["content"] = s3_content.decode("utf-8")
                    except UnicodeDecodeError:
                        research_data["content"] = f"[Binary content: {len(s3_content)} bytes]"

            return research_data

        except Exception as e:
            logger.error(f"Failed to retrieve research by ObjectID {object_id}: {e}")
            return {"error": str(e)}

    async def search_research_evidence(
        self, query: str, case_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search research evidence using unified storage.

        Args:
            query: Search query
            case_id: Optional case ID to filter results

        Returns:
            List of matching research evidence
        """
        try:
            search_results = await self.unified_storage.search_evidence(query, search_tier="vector")

            # Filter by case_id if provided
            if case_id:
                search_results = [
                    result
                    for result in search_results
                    if result.get("metadata", {}).get("case_id") == case_id
                ]

            # Enhance results with research-specific data
            enhanced_results = []
            for result in search_results:
                metadata = result.get("metadata", {})
                enhanced_results.append(
                    {
                        "object_id": result.get("object_id"),
                        "citation": metadata.get("citation"),
                        "court": metadata.get("court"),
                        "year": metadata.get("year"),
                        "authority_level": metadata.get("authority_level"),
                        "is_binding": metadata.get("is_binding"),
                        "relevance_score": result.get("relevance_score", 0.0),
                        "jurisdiction": metadata.get("jurisdiction"),
                    }
                )

            return enhanced_results

        except Exception as e:
            logger.error(f"Failed to search research evidence: {e}")
            return []

    def _format_research_result_for_storage(self, result: EnhancedResearchResult) -> str:
        """
        Format research result for storage as text content.

        Args:
            result: Enhanced research result

        Returns:
            Formatted text content
        """
        case = result.case

        content = f"""
CASELAW RESEARCH RESULT
======================

Citation: {case.citation}
Case Name: {case.case_name}
Court: {case.court}
Year: {case.year}
Jurisdiction: {case.jurisdiction}

AUTHORITY ASSESSMENT
===================
Authority Level: {result.authority_level} stars
Is Binding: {result.is_binding}
Reasoning: {result.reasoning}
Search Priority: {result.search_priority}
Color Code: {result.color_code}

CASE DETAILS
============
{case.case_name} ({case.year})

Court: {case.court}
Jurisdiction: {case.jurisdiction}

Full Citation: {case.citation}

RESEARCH CONTEXT
================
Source: Enhanced Caselaw Research
Research Phase: Authority Assessment
Processing Date: {asyncio.get_event_loop().time()}

AUTHORITY ANALYSIS
==================
{result.reasoning}

Search Priority: {result.search_priority}
Color Code: {result.color_code}
Stars: {result.authority_level}
Binding Authority: {result.is_binding}
"""

        return content.strip()


# Integration function for the research phase
async def integrate_enhanced_research_phase(
    legal_issues: List[str],
    intake_form_data: Dict[str, Any],
    evidence_table_path: Optional[str] = None,
    case_id: str = "research_case",
) -> Dict[str, Any]:
    """
    Main integration function for the enhanced research phase with unified storage.

    Args:
        legal_issues: List of legal issues to research
        intake_form_data: Data from legal intake form
        evidence_table_path: Optional path to evidence table for authority rating
        case_id: Case identifier for unified storage tracking

    Returns:
        Comprehensive research results with authority assessments and storage info
    """

    # Initialize enhanced research bot
    research_bot = EnhancedResearchBot()

    # Set jurisdiction context from intake form
    research_bot.set_jurisdiction_from_intake(intake_form_data)

    # Perform enhanced research
    enhanced_results = await research_bot.enhanced_researcher.search_caselaw_with_authority(
        legal_issues=legal_issues, intake_form_data=intake_form_data
    )

    # Convert to EnhancedResearchResult format for unified storage
    research_results = []
    for result in enhanced_results:
        case = result.original_case
        auth = result.authority_assessment

        research_result = EnhancedResearchResult(
            case=case,
            authority_level=auth.star_rating,
            is_binding=auth.is_binding,
            reasoning=auth.reasoning,
            search_priority=auth.search_priority,
            color_code=research_bot._get_color_code(auth.star_rating),
        )
        research_results.append(research_result)

    # Store research results through unified storage pipeline
    storage_metadata = {
        "integration_function": "integrate_enhanced_research_phase",
        "legal_issues": legal_issues,
        "jurisdiction_context": (
            {
                "primary_jurisdiction": (
                    research_bot.jurisdiction_context.primary_jurisdiction
                    if research_bot.jurisdiction_context
                    else None
                ),
                "court_type": (
                    research_bot.jurisdiction_context.court_type
                    if research_bot.jurisdiction_context
                    else None
                ),
                "event_location": (
                    research_bot.jurisdiction_context.event_location
                    if research_bot.jurisdiction_context
                    else None
                ),
                "question_type": (
                    research_bot.jurisdiction_context.question_type.value
                    if research_bot.jurisdiction_context
                    else None
                ),
            }
            if research_bot.jurisdiction_context
            else None
        ),
    }

    storage_result = await research_bot.store_research_results(
        research_results, case_id, storage_metadata
    )

    # Process evidence table if provided
    evidence_success = False
    if evidence_table_path:
        evidence_success = await research_bot.process_evidence_with_authority(
            evidence_table_path=evidence_table_path, intake_form_data=intake_form_data
        )

    # Generate comprehensive report
    authority_report = research_bot.enhanced_researcher.generate_authority_report(enhanced_results)

    return {
        "success": True,
        "cases_found": len(enhanced_results),
        "binding_cases": len([r for r in enhanced_results if r.authority_assessment.is_binding]),
        "enhanced_results": enhanced_results,
        "authority_report": authority_report,
        "evidence_processing_success": evidence_success,
        "storage_result": storage_result,  # Include unified storage results
        "object_ids": storage_result.get("object_ids", []),  # Include ObjectIDs
        "jurisdiction_context": {
            "primary_jurisdiction": (
                research_bot.jurisdiction_context.primary_jurisdiction
                if research_bot.jurisdiction_context
                else None
            ),
            "court_type": (
                research_bot.jurisdiction_context.court_type
                if research_bot.jurisdiction_context
                else None
            ),
            "event_location": (
                research_bot.jurisdiction_context.event_location
                if research_bot.jurisdiction_context
                else None
            ),
            "question_type": (
                research_bot.jurisdiction_context.question_type.value
                if research_bot.jurisdiction_context
                else None
            ),
        },
    }
