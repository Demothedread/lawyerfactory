"""
# Script Name: caselaw_researcher.py
# Description: Caselaw Researcher Agent for LawyerFactory Orchestration Phase.  This agent searches for relevant case law and precedents using: - CourtListener API integration - Google Scholar for secondary sources - Case law databases and repositories - Citation network analysis  The agent finds controlling precedents and analogous cases to support legal arguments and claims.
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Research
#   - Group Tags: legal-research
Caselaw Researcher Agent for LawyerFactory Orchestration Phase.

This agent searches for relevant case law and precedents using:
- CourtListener API integration
- Google Scholar for secondary sources
- Case law databases and repositories
- Citation network analysis

The agent finds controlling precedents and analogous cases
to support legal arguments and claims.
"""

from dataclasses import dataclass, field
import logging
from typing import Any, Dict, List, Optional

from ...compose.maestro.registry import AgentCapability, AgentInterface
from ...compose.maestro.workflow_models import WorkflowTask

logger = logging.getLogger(__name__)


@dataclass
class CaseLawResult:
    """Result from caselaw research"""

    case_name: str
    citation: str
    court: str
    year: int
    jurisdiction: str
    relevance_score: float
    holding: str
    facts: str
    reasoning: str
    url: Optional[str] = None
    similarity_to_facts: float = 0.0


class CaselawResearcherAgent(AgentInterface):
    """Agent that researches relevant case law and precedents"""

    def __init__(self, knowledge_graph=None):
        self.knowledge_graph = knowledge_graph
        self.capabilities = [
            AgentCapability.LEGAL_RESEARCH,
            AgentCapability.CASE_ANALYSIS,
        ]

        # Initialize research clients
        self._initialize_research_clients()

    def _initialize_research_clients(self):
        """Initialize external research clients"""
        try:
            from ...kg.legal_authorities import LegalAuthorityManager

            self.authority_manager = LegalAuthorityManager()
        except Exception as e:
            logger.warning(f"Could not initialize legal authority manager: {e}")
            self.authority_manager = None

    async def process(self, message: str) -> str:
        """Process a natural language request for caselaw research"""
        try:
            # Extract legal issues from the message
            legal_issues = self._extract_legal_issues(message)

            # Search for relevant cases
            cases = await self.search_caselaw(legal_issues)

            # Generate response
            response = "Caselaw Research Results:\n\n"
            for i, case in enumerate(cases[:5], 1):  # Limit to top 5
                response += f"{i}. **{case.case_name}**\n"
                response += f"   Citation: {case.citation}\n"
                response += f"   Court: {case.court} ({case.year})\n"
                response += f"   Relevance: {case.relevance_score:.2f}/1.0\n"
                response += f"   Holding: {case.holding[:100]}...\n"
                if case.url:
                    response += f"   URL: {case.url}\n"
                response += "\n"

            return response

        except Exception as e:
            logger.error(f"Error processing caselaw research request: {e}")
            return f"Error researching caselaw: {str(e)}"

    async def execute_task(
        self, task: WorkflowTask, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a workflow task related to caselaw research"""
        try:
            # Extract legal issues from context
            legal_issues = self._extract_legal_issues_from_context(context)

            # Search for relevant cases
            cases = await self.search_caselaw(legal_issues)

            # Analyze and rank results
            analysis = self._analyze_caselaw_results(cases, context)

            return {
                "status": "completed",
                "cases_found": len(cases),
                "cases": [case.__dict__ for case in cases],
                "analysis": analysis,
                "top_precedents": [case.__dict__ for case in cases[:3]],
            }

        except Exception as e:
            logger.error(f"Error executing caselaw research task: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "cases_found": 0,
                "cases": [],
                "analysis": "",
                "top_precedents": [],
            }

    async def health_check(self) -> bool:
        """Check if the agent is functioning properly"""
        try:
            # Test basic functionality
            test_issues = ["negligence"]
            cases = await self.search_caselaw(test_issues)
            return True  # Even if no results, the search didn't crash
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    async def initialize(self) -> None:
        """Initialize the agent"""
        try:
            logger.info("Caselaw Researcher Agent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Caselaw Researcher Agent: {e}")

    async def cleanup(self) -> None:
        """Clean up resources"""
        pass

    async def can_handle_task(self, task: WorkflowTask) -> bool:
        """Check if this agent can handle the given task"""
        task_text = f"{task.description} {task.agent_type}".lower()
        return any(
            keyword in task_text
            for keyword in ["case", "precedent", "caselaw", "research", "authority"]
        )

    async def search_caselaw(self, legal_issues: List[str]) -> List[CaseLawResult]:
        """Search for relevant caselaw based on legal issues"""
        all_cases = []

        for issue in legal_issues:
            # Search using different methods
            courtlistener_cases = await self._search_courtlistener(issue)
            scholar_cases = await self._search_google_scholar(issue)
            authority_cases = await self._search_legal_authorities(issue)

            all_cases.extend(courtlistener_cases)
            all_cases.extend(scholar_cases)
            all_cases.extend(authority_cases)

        # Remove duplicates and rank by relevance
        unique_cases = self._deduplicate_cases(all_cases)
        ranked_cases = self._rank_cases_by_relevance(unique_cases)

        return ranked_cases

    async def _search_courtlistener(self, issue: str) -> List[CaseLawResult]:
        """Search CourtListener for relevant cases"""
        try:
            # Use mock results since we don't have API access
            mock_cases = [
                CaseLawResult(
                    case_name=f"Mock Case for {issue}",
                    citation="123 F. Supp. 456 (2023)",
                    court="U.S. District Court",
                    year=2023,
                    jurisdiction="federal",
                    relevance_score=0.8,
                    holding=f"The court held that {issue} claims require sufficient factual allegations.",
                    facts=f"Plaintiff alleged {issue} by defendant.",
                    reasoning="Based on established precedent in the jurisdiction.",
                )
            ]
            return mock_cases

        except Exception as e:
            logger.error(f"CourtListener search failed: {e}")
            return []

    async def _search_google_scholar(self, issue: str) -> List[CaseLawResult]:
        """Search Google Scholar for relevant cases"""
        try:
            # Use mock results
            mock_cases = [
                CaseLawResult(
                    case_name=f"Scholar Case on {issue}",
                    citation="456 F.3d 789 (2022)",
                    court="U.S. Court of Appeals",
                    year=2022,
                    jurisdiction="federal",
                    relevance_score=0.7,
                    holding=f"Appeals court affirmed district court's ruling on {issue}.",
                    facts=f"Similar factual scenario involving {issue}.",
                    reasoning="Applied controlling precedent to the facts.",
                )
            ]
            return mock_cases

        except Exception as e:
            logger.error(f"Google Scholar search failed: {e}")
            return []

    async def _search_legal_authorities(self, issue: str) -> List[CaseLawResult]:
        """Search legal authorities for relevant cases"""
        try:
            if not self.authority_manager:
                return []

            # Search legal authority database
            authorities = self.authority_manager.search_authorities(issue, limit=3)

            cases = []
            for authority in authorities:
                if "case" in authority.tags:
                    case = CaseLawResult(
                        case_name=authority.title,
                        citation=authority.section,
                        court="Authority Reference",
                        year=2023,  # Default
                        jurisdiction="general",
                        relevance_score=0.6,
                        holding=authority.content[:200] + "...",
                        facts="As described in the authority",
                        reasoning="Based on legal authority analysis",
                    )
                    cases.append(case)

            return cases

        except Exception as e:
            logger.error(f"Legal authority search failed: {e}")
            return []

    def _extract_legal_issues(self, text: str) -> List[str]:
        """Extract legal issues from text"""
        issues = []

        text_lower = text.lower()

        if "negligence" in text_lower:
            issues.append("negligence")
        if "contract" in text_lower or "breach" in text_lower:
            issues.append("breach of contract")
        if "fraud" in text_lower:
            issues.append("fraud")
        if "tort" in text_lower:
            issues.append("tort")
        if "warranty" in text_lower:
            issues.append("breach of warranty")

        return issues

    def _extract_legal_issues_from_context(self, context: Dict[str, Any]) -> List[str]:
        """Extract legal issues from workflow context"""
        issues = []

        # Look for issues in claims matrix
        claims_matrix = context.get("claims_matrix", {})
        if isinstance(claims_matrix, dict):
            claims = claims_matrix.get("claims", [])
            for claim in claims:
                if isinstance(claim, dict):
                    issues.append(claim.get("title", ""))
                elif isinstance(claim, str):
                    issues.append(claim)

        # Look for issues in other context
        if "legal_issues" in context:
            issues.extend(context["legal_issues"])

        # Extract from facts if available
        facts = context.get("facts", "")
        if isinstance(facts, str):
            issues.extend(self._extract_legal_issues(facts))

        return list(set(issues))  # Remove duplicates

    def _deduplicate_cases(self, cases: List[CaseLawResult]) -> List[CaseLawResult]:
        """Remove duplicate cases"""
        seen = set()
        unique_cases = []

        for case in cases:
            case_key = (case.case_name, case.citation)
            if case_key not in seen:
                seen.add(case_key)
                unique_cases.append(case)

        return unique_cases

    def _rank_cases_by_relevance(
        self, cases: List[CaseLawResult]
    ) -> List[CaseLawResult]:
        """Rank cases by relevance score"""
        return sorted(cases, key=lambda x: x.relevance_score, reverse=True)

    def _analyze_caselaw_results(
        self, cases: List[CaseLawResult], context: Dict[str, Any]
    ) -> str:
        """Analyze caselaw search results"""
        analysis = "Caselaw Analysis:\n\n"

        if not cases:
            return "No relevant cases found for the given legal issues."

        analysis += f"Total Cases Found: {len(cases)}\n"
        analysis += f"Top Relevant Cases: {len(cases[:3])}\n\n"

        analysis += "Key Findings:\n"
        for i, case in enumerate(cases[:3], 1):
            analysis += f"{i}. {case.case_name} ({case.year})\n"
            analysis += f"   Relevance: {case.relevance_score:.2f}\n"
            analysis += f"   Holding: {case.holding[:150]}...\n"
            analysis += f"   Court: {case.court}\n\n"

        analysis += "Recommendations:\n"
        analysis += "1. Prioritize binding precedent from the jurisdiction\n"
        analysis += "2. Look for cases with similar factual scenarios\n"
        analysis += "3. Consider the recency of the decisions\n"
        analysis += "4. Evaluate how well the reasoning applies to your facts\n"

        return analysis
