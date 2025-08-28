"""
# Script Name: rules_of_law.py
# Description: Rules of Law Agent for LawyerFactory Orchestration Phase.  This agent extracts and applies legal rules from authoritative sources including: - Restatements of Torts and Contracts - UCC provisions - Black's Law Dictionary - Other legal authorities  It provides rule-based analysis for claims and helps ensure legal accuracy.
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Orchestration
#   - Group Tags: null
Rules of Law Agent for LawyerFactory Orchestration Phase.

This agent extracts and applies legal rules from authoritative sources including:
- Restatements of Torts and Contracts
- UCC provisions
- Black's Law Dictionary
- Other legal authorities

It provides rule-based analysis for claims and helps ensure legal accuracy.
"""

from dataclasses import dataclass, field
import logging
from typing import Any, Dict, List, Optional

from ...compose.maestro.registry import AgentCapability, AgentInterface
from ...compose.maestro.workflow_models import WorkflowTask
from ...kg.legal_authorities import LegalAuthority, LegalAuthorityManager

logger = logging.getLogger(__name__)


@dataclass
class LegalRule:
    """Represents a legal rule extracted from authorities"""

    rule_text: str
    source: str
    section: str
    category: str
    jurisdiction: Optional[str] = None
    conditions: List[str] = field(default_factory=list)
    exceptions: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)


class RulesOfLawAgent(AgentInterface):
    """Agent that extracts and applies legal rules from authoritative sources"""

    def __init__(self, knowledge_graph=None):
        self.knowledge_graph = knowledge_graph
        self.authority_manager = LegalAuthorityManager()
        self.capabilities = [
            AgentCapability.LEGAL_RESEARCH,
            AgentCapability.CASE_ANALYSIS,
        ]

    async def process(self, message: str) -> str:
        """Process a natural language request for legal rules"""
        try:
            # Parse the request to understand what rules are needed
            rules = await self.find_relevant_rules(message)

            if not rules:
                return "No relevant legal rules found for the given query."

            # Format the response
            response = (
                "Based on authoritative legal sources, here are the relevant rules:\n\n"
            )
            for i, rule in enumerate(rules, 1):
                response += f"{i}. **{rule.rule_text}**\n"
                response += f"   - Source: {rule.source} {rule.section}\n"
                if rule.conditions:
                    response += f"   - Conditions: {', '.join(rule.conditions)}\n"
                if rule.exceptions:
                    response += f"   - Exceptions: {', '.join(rule.exceptions)}\n"
                response += "\n"

            return response

        except Exception as e:
            logger.error(f"Error processing rules request: {e}")
            return f"Error retrieving legal rules: {str(e)}"

    async def execute_task(
        self, task: WorkflowTask, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a workflow task related to legal rules"""
        try:
            # Extract legal issues from the task
            legal_issues = self._extract_legal_issues(task, context)

            # Find relevant rules
            all_rules = []
            for issue in legal_issues:
                rules = await self.find_relevant_rules(issue)
                all_rules.extend(rules)

            # Remove duplicates
            unique_rules = self._deduplicate_rules(all_rules)

            # Apply rules to generate analysis
            analysis = await self._apply_rules_to_facts(unique_rules, context)

            return {
                "status": "completed",
                "rules_found": len(unique_rules),
                "rules": [rule.__dict__ for rule in unique_rules],
                "analysis": analysis,
                "legal_issues_identified": legal_issues,
            }

        except Exception as e:
            logger.error(f"Error executing rules task: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "rules_found": 0,
                "rules": [],
                "analysis": "",
                "legal_issues_identified": [],
            }

    async def health_check(self) -> bool:
        """Check if the legal authority database is accessible"""
        try:
            # Try to access the authority manager
            authorities = self.authority_manager.search_authorities("test", limit=1)
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    async def initialize(self) -> None:
        """Initialize the agent and load legal authorities"""
        try:
            # Ensure the legal authority database is populated
            from ...kg.legal_authorities import populate_default_authorities

            populate_default_authorities(self.authority_manager)
            logger.info("Rules of Law Agent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Rules of Law Agent: {e}")

    async def cleanup(self) -> None:
        """Clean up resources"""
        # Save any pending changes
        self.authority_manager.save_authorities()

    async def can_handle_task(self, task: WorkflowTask) -> bool:
        """Check if this agent can handle the given task"""
        # Can handle tasks related to legal rules, analysis, or authority research
        task_text = f"{task.description} {task.agent_type}".lower()
        return any(
            keyword in task_text
            for keyword in ["rule", "law", "authority", "legal", "analysis", "irac"]
        )

    async def find_relevant_rules(self, query: str) -> List[LegalRule]:
        """Find legal rules relevant to the given query"""
        try:
            # Search the legal authority database
            authorities = self.authority_manager.search_authorities(query, limit=10)

            rules = []
            for authority in authorities:
                # Extract rules from the authority content
                extracted_rules = self._extract_rules_from_authority(authority, query)
                rules.extend(extracted_rules)

            return rules

        except Exception as e:
            logger.error(f"Error finding relevant rules: {e}")
            return []

    def _extract_legal_issues(
        self, task: WorkflowTask, context: Dict[str, Any]
    ) -> List[str]:
        """Extract legal issues from task and context"""
        issues = []

        # Look for legal issues in task description
        description = task.description.lower()
        if "negligence" in description:
            issues.append("negligence")
        if "contract" in description or "breach" in description:
            issues.append("breach of contract")
        if "warranty" in description:
            issues.append("warranty")
        if "tort" in description:
            issues.append("tort")

        # Look for issues in context
        claims_matrix = context.get("claims_matrix", {})
        if claims_matrix:
            for claim in claims_matrix.get("claims", []):
                if isinstance(claim, dict):
                    issues.append(claim.get("title", ""))
                elif isinstance(claim, str):
                    issues.append(claim)

        return list(set(issues))  # Remove duplicates

    def _extract_rules_from_authority(
        self, authority: LegalAuthority, query: str
    ) -> List[LegalRule]:
        """Extract specific rules from a legal authority"""
        rules = []

        # Simple rule extraction - in practice, this would be more sophisticated
        content = authority.content

        # Look for rule-like patterns
        if "is" in content and (
            "shall" in content or "must" in content or "may" in content
        ):
            rule = LegalRule(
                rule_text=content[:500] + "..." if len(content) > 500 else content,
                source=authority.source,
                section=authority.section,
                category=authority.category,
                jurisdiction=authority.jurisdiction,
            )
            rules.append(rule)

        return rules

    def _deduplicate_rules(self, rules: List[LegalRule]) -> List[LegalRule]:
        """Remove duplicate rules"""
        seen = set()
        unique_rules = []

        for rule in rules:
            rule_key = (rule.rule_text[:100], rule.source, rule.section)
            if rule_key not in seen:
                seen.add(rule_key)
                unique_rules.append(rule)

        return unique_rules

    async def _apply_rules_to_facts(
        self, rules: List[LegalRule], context: Dict[str, Any]
    ) -> str:
        """Apply legal rules to the facts in context"""
        analysis = "Legal Rule Analysis:\n\n"

        facts = context.get("facts", [])
        if not facts:
            return "No facts available for rule application analysis."

        analysis += "Facts Present:\n"
        for i, fact in enumerate(facts[:5], 1):  # Limit to first 5 facts
            analysis += f"{i}. {fact}\n"
        analysis += "\n"

        analysis += "Applicable Rules:\n"
        for i, rule in enumerate(rules[:3], 1):  # Limit to first 3 rules
            analysis += (
                f"{i}. {rule.source} {rule.section}: {rule.rule_text[:200]}...\n"
            )
            analysis += f"   Category: {rule.category}\n"
            if rule.conditions:
                analysis += f"   Conditions: {', '.join(rule.conditions[:2])}\n"
            analysis += "\n"

        analysis += "Preliminary Analysis:\n"
        analysis += "The above rules may apply to the facts depending on jurisdiction and specific circumstances. "
        analysis += (
            "Further analysis would be required to determine exact application.\n"
        )

        return analysis
