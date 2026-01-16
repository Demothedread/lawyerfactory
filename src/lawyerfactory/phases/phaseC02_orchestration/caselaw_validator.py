"""
# Script Name: caselaw_validator.py
# Description: Caselaw Validation Agent for LawyerFactory Orchestration Phase  This agent monitors document generation and validates legal citations for: - Jurisdiction appropriateness - Authority precedence (binding vs persuasive) - Currency of law (superseded cases) - Citation formatting and consistency  It integrates with the writer bot to provide real-time feedback and corrections.
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Workflow
#   - Group Tags: null
Caselaw Validation Agent for LawyerFactory Orchestration Phase

This agent monitors document generation and validates legal citations for:
- Jurisdiction appropriateness
- Authority precedence (binding vs persuasive)
- Currency of law (superseded cases)
- Citation formatting and consistency

It integrates with the writer bot to provide real-time feedback and corrections.
"""

from dataclasses import dataclass, field
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from ...compose.maestro.registry import AgentCapability, AgentInterface
from ...compose.maestro.workflow_models import WorkflowTask
from ...kg.legal_authorities import AuthorityCitationManager, LegalAuthorityManager

logger = logging.getLogger(__name__)


@dataclass
class CitationIssue:
    """Represents a citation issue found in a document"""

    original_citation: str
    issue_type: str  # "obsolete", "non_binding", "wrong_jurisdiction", "formatting"
    description: str
    suggested_replacement: Optional[str] = None
    context: str = ""  # Surrounding text for replacement
    start_position: int = 0
    end_position: int = 0


@dataclass
class ValidationReport:
    """Report of citation validation results"""

    total_citations: int = 0
    valid_citations: int = 0
    issues: List[CitationIssue] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    citation_table: str = ""


class CaselawValidationAgent(AgentInterface):
    """Agent that validates caselaw citations in generated documents"""

    def __init__(self, knowledge_graph=None):
        self.knowledge_graph = knowledge_graph
        self.capabilities = [
            AgentCapability.LEGAL_RESEARCH,
            AgentCapability.CASE_ANALYSIS,
            AgentCapability.DOCUMENT_REVIEW,
        ]

        # Initialize authority managers
        self.authority_manager = LegalAuthorityManager()
        self.citation_manager = AuthorityCitationManager(self.authority_manager)

        # Citation tracking
        self.citations_found: Dict[str, List[str]] = {}  # doc_id -> citations

    async def process(self, message: str) -> str:
        """Process a natural language request for citation validation"""
        try:
            if "validate" in message.lower():
                # Extract document content from message
                doc_content = self._extract_document_content(message)
                if doc_content:
                    report = await self.validate_document_citations(
                        doc_content, "california"
                    )
                    return self._format_validation_report(report)
                else:
                    return "Please provide document content to validate."

            return (
                "Caselaw Validation Agent ready. Send 'validate' with document content."
            )

        except Exception as e:
            logger.error(f"Error processing validation request: {e}")
            return f"Error processing request: {str(e)}"

    async def execute_task(
        self, task: WorkflowTask, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a workflow task related to citation validation"""
        try:
            document_content = context.get("document_content", "")
            jurisdiction = context.get("jurisdiction", "california")

            if not document_content:
                return {
                    "status": "failed",
                    "error": "No document content provided for validation",
                }

            # Validate citations
            validation_report = await self.validate_document_citations(
                document_content, jurisdiction
            )

            # Generate corrections if needed
            corrections = []
            if validation_report.issues:
                corrections = await self.generate_corrections(
                    validation_report, document_content
                )

            return {
                "status": "completed",
                "validation_report": validation_report.__dict__,
                "corrections": corrections,
                "citation_table": validation_report.citation_table,
                "needs_correction": len(validation_report.issues) > 0,
            }

        except Exception as e:
            logger.error(f"Error executing validation task: {e}")
            return {"status": "failed", "error": str(e)}

    async def health_check(self) -> bool:
        """Check if the agent is functioning properly"""
        try:
            # Test with a simple validation
            test_doc = "According to Smith v. Jones, 123 Cal.App.4th 456 (2005), the rule is clear."
            report = await self.validate_document_citations(test_doc, "california")
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    async def initialize(self) -> None:
        """Initialize the agent"""
        try:
            logger.info("Caselaw Validation Agent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Caselaw Validation Agent: {e}")

    async def cleanup(self) -> None:
        """Clean up resources"""
        pass

    async def can_handle_task(self, task: WorkflowTask) -> bool:
        """Check if this agent can handle the given task"""
        task_text = f"{task.description} {task.agent_type}".lower()
        return any(
            keyword in task_text
            for keyword in ["citation", "validate", "authority", "caselaw", "precedent"]
        )

    async def validate_document_citations(
        self, document_content: str, jurisdiction: str
    ) -> ValidationReport:
        """Validate all citations in a document"""
        report = ValidationReport()

        # Extract citations using regex patterns
        citations = self._extract_citations(document_content)
        report.total_citations = len(citations)

        # Validate each citation
        for citation in citations:
            validation = self.authority_manager.validate_citation_for_jurisdiction(
                citation, jurisdiction
            )

            if validation["valid"]:
                report.valid_citations += 1
            else:
                # Create issue
                issue = CitationIssue(
                    original_citation=citation,
                    issue_type=self._determine_issue_type(validation),
                    description=validation.get("reason", "Citation issue"),
                    suggested_replacement=(
                        validation.get("suggested_alternatives", [None])[0]
                        if validation.get("suggested_alternatives")
                        else None
                    ),
                )
                report.issues.append(issue)

        # Generate recommendations
        report.recommendations = self._generate_recommendations(report.issues)

        # Generate citation table
        report.citation_table = self.citation_manager.generate_citation_table(
            citations, jurisdiction
        )

        return report

    def _extract_citations(self, text: str) -> List[str]:
        """Extract legal citations from text using regex patterns"""
        citations = []

        # Common citation patterns
        patterns = [
            r"\d+\s+[A-Za-z\.]+\s+\d+",  # 123 Cal.App.4th 456
            r"\d+\s+[A-Za-z\.]+\s+\d+\s*\([^)]*\)",  # 123 Cal.App.4th 456 (2005)
            r"\d+\s+[USF]\.? Supp\.?\s+\d+",  # 123 F.Supp. 456
            r"\d+\s+[USF]\.?3d\s+\d+",  # 123 F.3d 456
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text)
            citations.extend(matches)

        # Remove duplicates while preserving order
        seen = set()
        unique_citations = []
        for citation in citations:
            if citation not in seen:
                seen.add(citation)
                unique_citations.append(citation)

        return unique_citations

    def _determine_issue_type(self, validation: Dict[str, Any]) -> str:
        """Determine the type of citation issue"""
        if validation.get("authority_type") == "obsolete":
            return "obsolete"
        elif not validation.get("valid", False):
            return "non_binding"
        else:
            return "other"

    def _generate_recommendations(self, issues: List[CitationIssue]) -> List[str]:
        """Generate recommendations based on citation issues"""
        recommendations = []

        if not issues:
            recommendations.append(
                "All citations appear to be valid for the jurisdiction."
            )
            return recommendations

        obsolete_count = sum(1 for issue in issues if issue.issue_type == "obsolete")
        non_binding_count = sum(
            1 for issue in issues if issue.issue_type == "non_binding"
        )

        if obsolete_count > 0:
            recommendations.append(
                f"Update {obsolete_count} obsolete citations with current authority"
            )

        if non_binding_count > 0:
            recommendations.append(
                f"Replace {non_binding_count} non-binding citations with jurisdiction-appropriate authority"
            )

        if len(issues) > 0:
            recommendations.append(
                "Consider adding a Table of Authorities to document all citations"
            )

        return recommendations

    async def generate_corrections(
        self, report: ValidationReport, original_document: str
    ) -> List[Dict[str, Any]]:
        """Generate correction suggestions for citation issues"""
        corrections = []

        for issue in report.issues:
            if issue.suggested_replacement:
                # Find context around the citation
                context = self._find_citation_context(
                    original_document, issue.original_citation
                )

                correction = {
                    "original_citation": issue.original_citation,
                    "suggested_replacement": issue.suggested_replacement,
                    "context": context,
                    "issue_type": issue.issue_type,
                    "description": issue.description,
                }
                corrections.append(correction)

        return corrections

    def _find_citation_context(
        self, document: str, citation: str, context_chars: int = 100
    ) -> str:
        """Find the context around a citation in the document"""
        try:
            index = document.find(citation)
            if index == -1:
                return ""

            start = max(0, index - context_chars)
            end = min(len(document), index + len(citation) + context_chars)

            context = document[start:end]
            return f"...{context}..."

        except Exception:
            return ""

    def _extract_document_content(self, message: str) -> Optional[str]:
        """Extract document content from a message"""
        # Simple extraction - look for document content after keywords
        keywords = ["document:", "content:", "validate this:"]
        for keyword in keywords:
            if keyword in message.lower():
                return message[message.lower().find(keyword) + len(keyword) :].strip()

        # If no keywords found, assume the entire message is document content
        if len(message) > 50:  # Arbitrary threshold
            return message

        return None

    def _format_validation_report(self, report: ValidationReport) -> str:
        """Format validation report for display"""
        lines = []
        lines.append("📋 CASELAW VALIDATION REPORT")
        lines.append("=" * 40)
        lines.append(f"Total Citations Found: {report.total_citations}")
        lines.append(f"Valid Citations: {report.valid_citations}")
        lines.append(f"Issues Found: {len(report.issues)}")
        lines.append("")

        if report.issues:
            lines.append("⚠️  ISSUES:")
            for i, issue in enumerate(report.issues, 1):
                lines.append(f"{i}. {issue.original_citation}")
                lines.append(f"   Issue: {issue.issue_type}")
                lines.append(f"   Description: {issue.description}")
                if issue.suggested_replacement:
                    lines.append(f"   Suggested: {issue.suggested_replacement}")
                lines.append("")
        else:
            lines.append("✅ No citation issues found!")

        if report.recommendations:
            lines.append("💡 RECOMMENDATIONS:")
            for rec in report.recommendations:
                lines.append(f"• {rec}")

        return "\n".join(lines)

    async def monitor_document_generation(
        self, document_content: str, jurisdiction: str
    ) -> Dict[str, Any]:
        """Monitor document generation and provide real-time validation feedback"""
        # This would be called by the writer bot during document generation
        report = await self.validate_document_citations(document_content, jurisdiction)

        # Track citations for this document
        doc_id = f"doc_{len(self.citations_found)}"
        citations = self._extract_citations(document_content)
        self.citations_found[doc_id] = citations

        return {
            "validation_report": report.__dict__,
            "needs_immediate_attention": len(report.issues) > 0,
            "corrections_available": len(
                [i for i in report.issues if i.suggested_replacement]
            )
            > 0,
        }

    def get_citation_table_of_contents(self, doc_id: str, jurisdiction: str) -> str:
        """Generate a Table of Contents for all citations in a document"""
        if doc_id not in self.citations_found:
            return "No citations tracked for this document."

        citations = self.citations_found[doc_id]
        return self.citation_manager.generate_citation_table(citations, jurisdiction)
