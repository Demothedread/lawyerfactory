"""
# Script Name: issuespotter.py
# Description: Issuespotter Agent for LawyerFactory Orchestration Phase.  This agent identifies legal issues from facts, claims, and case context. It performs issue spotting - the critical first step in legal analysis where potential causes of action are identified from the factual scenario.  The agent analyzes: - Factual patterns that suggest legal claims - Overlaps between facts and legal elements - Potential causes of action based on jurisdiction and facts
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Orchestration
#   - Group Tags: null
Issuespotter Agent for LawyerFactory Orchestration Phase.

This agent identifies legal issues from facts, claims, and case context.
It performs issue spotting - the critical first step in legal analysis where
potential causes of action are identified from the factual scenario.

The agent analyzes:
- Factual patterns that suggest legal claims
- Overlaps between facts and legal elements
- Potential causes of action based on jurisdiction and facts
"""

from dataclasses import dataclass, field
import logging
from typing import Any, Dict, List, Optional, Set

from ...compose.maestro.registry import AgentCapability, AgentInterface
from ...compose.maestro.workflow_models import WorkflowTask
from ...kg.legal_authorities import LegalAuthorityManager

logger = logging.getLogger(__name__)


@dataclass
class LegalIssue:
    """Represents a spotted legal issue"""

    title: str
    description: str
    potential_claims: List[str] = field(default_factory=list)
    relevant_facts: List[str] = field(default_factory=list)
    confidence_score: float = 0.0
    jurisdiction: Optional[str] = None
    priority: str = "medium"  # high, medium, low


class IssuespotterAgent(AgentInterface):
    """Agent that identifies legal issues from facts and context"""

    def __init__(self, knowledge_graph=None):
        self.knowledge_graph = knowledge_graph
        self.authority_manager = LegalAuthorityManager()
        self.capabilities = [
            AgentCapability.LEGAL_RESEARCH,
            AgentCapability.CASE_ANALYSIS,
        ]

        # Common legal patterns for issue spotting
        self._load_issue_patterns()

    def _load_issue_patterns(self):
        """Load common legal issue patterns"""
        self.issue_patterns = {
            "negligence": {
                "keywords": ["duty", "breach", "care", "reasonable", "harm", "injury"],
                "claims": ["negligence", "negligent infliction of emotional distress"],
                "elements": ["duty of care", "breach", "causation", "damages"],
            },
            "contract_breach": {
                "keywords": [
                    "contract",
                    "agreement",
                    "breach",
                    "promise",
                    "obligation",
                ],
                "claims": ["breach of contract", "specific performance", "restitution"],
                "elements": [
                    "offer",
                    "acceptance",
                    "consideration",
                    "breach",
                    "damages",
                ],
            },
            "warranty": {
                "keywords": [
                    "warranty",
                    "merchantable",
                    "fitness",
                    "quality",
                    "defect",
                ],
                "claims": [
                    "breach of warranty",
                    "implied warranty",
                    "express warranty",
                ],
                "elements": ["warranty", "breach", "reliance", "damages"],
            },
            "products_liability": {
                "keywords": ["product", "defect", "design", "manufacturing", "warning"],
                "claims": ["strict liability", "negligence", "breach of warranty"],
                "elements": ["defect", "causation", "damages"],
            },
            "fraud": {
                "keywords": [
                    "misrepresentation",
                    "fraud",
                    "deceit",
                    "false",
                    "material",
                ],
                "claims": [
                    "fraudulent misrepresentation",
                    "negligent misrepresentation",
                ],
                "elements": ["misrepresentation", "materiality", "reliance", "damages"],
            },
        }

    async def process(self, message: str) -> str:
        """Process a natural language request for issue spotting"""
        try:
            # Extract facts from the message
            facts = self._extract_facts_from_text(message)

            # Spot issues based on facts
            issues = await self.spot_issues(facts, {"jurisdiction": "general"})

            if not issues:
                return "No clear legal issues identified from the provided facts."

            # Format the response
            response = "Legal Issues Identified:\n\n"
            for i, issue in enumerate(issues, 1):
                response += f"{i}. **{issue.title}**\n"
                response += f"   {issue.description}\n"
                response += (
                    f"   Potential Claims: {', '.join(issue.potential_claims)}\n"
                )
                response += f"   Confidence: {issue.confidence_score:.2f}\n"
                response += f"   Priority: {issue.priority}\n\n"

            return response

        except Exception as e:
            logger.error(f"Error processing issue spotting request: {e}")
            return f"Error identifying legal issues: {str(e)}"

    async def execute_task(
        self, task: WorkflowTask, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a workflow task related to issue spotting"""
        try:
            # Extract facts from context
            facts = self._extract_facts_from_context(context)

            # Get jurisdiction and other context
            jurisdiction = context.get("jurisdiction", "general")

            # Spot issues
            issues = await self.spot_issues(facts, {"jurisdiction": jurisdiction})

            # Generate analysis
            analysis = self._generate_issue_analysis(issues, facts)

            return {
                "status": "completed",
                "issues_found": len(issues),
                "issues": [issue.__dict__ for issue in issues],
                "analysis": analysis,
                "facts_analyzed": len(facts),
            }

        except Exception as e:
            logger.error(f"Error executing issue spotting task: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "issues_found": 0,
                "issues": [],
                "analysis": "",
                "facts_analyzed": 0,
            }

    async def health_check(self) -> bool:
        """Check if the agent is functioning properly"""
        try:
            # Test basic functionality
            test_facts = ["The driver was speeding", "The car crashed into a tree"]
            issues = await self.spot_issues(test_facts, {"jurisdiction": "general"})
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    async def initialize(self) -> None:
        """Initialize the agent"""
        try:
            logger.info("Issuespotter Agent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Issuespotter Agent: {e}")

    async def cleanup(self) -> None:
        """Clean up resources"""
        pass

    async def can_handle_task(self, task: WorkflowTask) -> bool:
        """Check if this agent can handle the given task"""
        task_text = f"{task.description} {task.agent_type}".lower()
        return any(
            keyword in task_text
            for keyword in ["issue", "spot", "identify", "legal", "claim", "analysis"]
        )

    async def spot_issues(
        self, facts: List[str], context: Dict[str, Any]
    ) -> List[LegalIssue]:
        """Main issue spotting logic"""
        issues = []

        # Analyze each fact for legal patterns
        for fact in facts:
            fact_issues = self._analyze_fact_for_issues(fact, context)
            issues.extend(fact_issues)

        # Look for patterns across multiple facts
        cross_fact_issues = self._analyze_cross_fact_patterns(facts, context)
        issues.extend(cross_fact_issues)

        # Remove duplicates and rank by confidence
        unique_issues = self._deduplicate_issues(issues)
        ranked_issues = self._rank_issues_by_confidence(unique_issues)

        return ranked_issues

    def _extract_facts_from_text(self, text: str) -> List[str]:
        """Extract facts from natural language text"""
        # Simple sentence-based extraction
        sentences = text.replace("?", ".").replace("!", ".").split(".")
        facts = [s.strip() for s in sentences if len(s.strip()) > 10]
        return facts

    def _extract_facts_from_context(self, context: Dict[str, Any]) -> List[str]:
        """Extract facts from workflow context"""
        facts = []

        # Look for facts in various context fields
        if "facts" in context:
            facts.extend(context["facts"])
        if "evidence_table" in context:
            for evidence in context["evidence_table"]:
                if isinstance(evidence, dict):
                    facts.append(evidence.get("title", str(evidence)))
                else:
                    facts.append(str(evidence))
        if "fact_matrix" in context:
            # Add facts from fact matrix
            fact_matrix = context["fact_matrix"]
            if isinstance(fact_matrix, dict):
                undisputed_facts = fact_matrix.get("undisputed_facts", [])
                facts.extend(undisputed_facts)

        return list(set(facts))  # Remove duplicates

    def _analyze_fact_for_issues(
        self, fact: str, context: Dict[str, Any]
    ) -> List[LegalIssue]:
        """Analyze a single fact for potential legal issues"""
        issues = []
        fact_lower = fact.lower()

        for pattern_name, pattern in self.issue_patterns.items():
            confidence = 0.0
            matching_keywords = []

            # Check for keyword matches
            for keyword in pattern["keywords"]:
                if keyword in fact_lower:
                    confidence += 0.2
                    matching_keywords.append(keyword)

            if confidence > 0.3:  # Threshold for considering an issue
                issue = LegalIssue(
                    title=f"Potential {pattern_name.replace('_', ' ').title()} Issue",
                    description=f"Fact suggests possible {pattern_name.replace('_', ' ')} based on: {', '.join(matching_keywords)}",
                    potential_claims=pattern["claims"],
                    relevant_facts=[fact],
                    confidence_score=min(confidence, 1.0),
                    jurisdiction=context.get("jurisdiction"),
                    priority="high" if confidence > 0.7 else "medium",
                )
                issues.append(issue)

        return issues

    def _analyze_cross_fact_patterns(
        self, facts: List[str], context: Dict[str, Any]
    ) -> List[LegalIssue]:
        """Analyze patterns across multiple facts"""
        issues = []

        # Look for combinations that suggest specific claims
        fact_text = " ".join(facts).lower()

        # Check for product liability patterns
        if ("product" in fact_text or "defect" in fact_text) and (
            "injury" in fact_text or "harm" in fact_text
        ):
            issues.append(
                LegalIssue(
                    title="Potential Products Liability Issue",
                    description="Multiple facts suggest product defect causing harm",
                    potential_claims=[
                        "strict liability",
                        "negligence",
                        "breach of warranty",
                    ],
                    relevant_facts=facts,
                    confidence_score=0.8,
                    jurisdiction=context.get("jurisdiction"),
                    priority="high",
                )
            )

        # Check for contract patterns
        if ("contract" in fact_text or "agreement" in fact_text) and (
            "breach" in fact_text or "fail" in fact_text
        ):
            issues.append(
                LegalIssue(
                    title="Potential Breach of Contract Issue",
                    description="Facts indicate contractual relationship and failure to perform",
                    potential_claims=["breach of contract", "specific performance"],
                    relevant_facts=facts,
                    confidence_score=0.7,
                    jurisdiction=context.get("jurisdiction"),
                    priority="high",
                )
            )

        return issues

    def _deduplicate_issues(self, issues: List[LegalIssue]) -> List[LegalIssue]:
        """Remove duplicate issues"""
        seen = set()
        unique_issues = []

        for issue in issues:
            # Create a key based on title and claims
            key = (issue.title, tuple(sorted(issue.potential_claims)))
            if key not in seen:
                seen.add(key)
                unique_issues.append(issue)

        return unique_issues

    def _rank_issues_by_confidence(self, issues: List[LegalIssue]) -> List[LegalIssue]:
        """Rank issues by confidence score"""
        return sorted(issues, key=lambda x: x.confidence_score, reverse=True)

    def _generate_issue_analysis(
        self, issues: List[LegalIssue], facts: List[str]
    ) -> str:
        """Generate analysis of spotted issues"""
        analysis = "Issue Spotting Analysis:\n\n"

        if not issues:
            return "No significant legal issues identified from the provided facts."

        analysis += f"Total Issues Identified: {len(issues)}\n"
        analysis += f"Facts Analyzed: {len(facts)}\n\n"

        analysis += "Issues by Priority:\n"
        high_priority = [i for i in issues if i.priority == "high"]
        medium_priority = [i for i in issues if i.priority == "medium"]

        if high_priority:
            analysis += f"High Priority ({len(high_priority)}):\n"
            for issue in high_priority:
                analysis += (
                    f"  - {issue.title} (Confidence: {issue.confidence_score:.2f})\n"
                )

        if medium_priority:
            analysis += f"Medium Priority ({len(medium_priority)}):\n"
            for issue in medium_priority:
                analysis += (
                    f"  - {issue.title} (Confidence: {issue.confidence_score:.2f})\n"
                )

        analysis += "\nRecommendations:\n"
        analysis += (
            "1. Prioritize high-confidence issues for immediate legal analysis\n"
        )
        analysis += "2. Consider jurisdiction-specific rules and precedents\n"
        analysis += "3. Evaluate potential counterarguments and defenses\n"
        analysis += "4. Assess damages and remedies for each potential claim\n"

        return analysis
