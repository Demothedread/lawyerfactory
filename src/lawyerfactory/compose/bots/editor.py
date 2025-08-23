"""
# Script Name: editor.py
# Description: Import AI compliance and review modules
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Orchestration
#   - Group Tags: null
"""

import logging
from typing import Any, Dict, List

# Import AI compliance and review modules
from lawyerfactory.document_generator.modules.compliance_checker import (
    check_rule_12b6, flag_for_review, validate_citations)

from ..agent_registry import AgentConfig, AgentInterface
from ..bot_interface import Bot
from ..workflow_models import WorkflowTask

logger = logging.getLogger(__name__)


class LegalEditorBot(Bot, AgentInterface):
    """Enhanced legal editor bot for professional document review and compliance checking"""
    
    def __init__(self, config: AgentConfig):
        # Initialize Bot interface
        Bot.__init__(self)
        # Initialize AgentInterface
        AgentInterface.__init__(self, config)
        
        logger.info("LegalEditorBot initialized with professional compliance checking capabilities")
    
    async def process(self, message: str) -> str:
        """Legacy Bot interface implementation with compliance checking"""
        try:
            # Basic compliance review for legacy interface
            issues = []
            
            # Check for basic legal document structure
            if "cause of action" in message.lower():
                # Simulate basic compliance check
                issues.append("Verify all legal elements are supported by facts")
            
            if issues:
                return flag_for_review(f"Professional review feedback for: '{message}'", issues)
            else:
                return f"Professional compliance review completed for: '{message}' - No issues found"
                
        except Exception as e:
            logger.error(f"Legacy compliance review failed: {e}")
            return f"Professional feedback for '{message}'"
    
    async def execute_task(self, task: WorkflowTask, context: Dict[str, Any]) -> Dict[str, Any]:
        """AgentInterface implementation for orchestration system with full compliance checking"""
        logger.info(f"LegalEditorBot executing task: {task.id}")
        
        try:
            # Extract editing parameters from task context
            document_content = context.get('document_content', '')
            content = context.get('content', document_content)  # Alternative key
            review_type = context.get('review_type', 'compliance')
            causes_of_action = context.get('causes_of_action', [])
            research_findings = context.get('research_findings', {})
            
            # Execute professional compliance review
            if review_type == 'compliance' or review_type == 'rule_12b6':
                result = await self._professional_compliance_review(content, causes_of_action, research_findings, context)
            elif review_type == 'citation_review':
                result = await self._professional_citation_review(content, research_findings, context)
            elif review_type == 'legal_brief':
                result = await self._professional_legal_brief_review(content, causes_of_action, research_findings, context)
            elif review_type == 'formatting':
                result = await self._professional_format_review(content, context)
            else:
                result = await self._comprehensive_professional_review(content, causes_of_action, research_findings, context)
            
            return {
                'status': 'completed',
                'reviewed_content': result['content'],
                'feedback': result['feedback'],
                'compliance_issues': result.get('compliance_issues', []),
                'citation_issues': result.get('citation_issues', []),
                'review_type': review_type,
                'changes_made': result.get('changes_made', 0),
                'ready_for_filing': result.get('ready_for_filing', False),
                'attorney_review_required': result.get('attorney_review_required', False)
            }
            
        except Exception as e:
            logger.error(f"LegalEditorBot task execution failed: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'reviewed_content': None,
                'feedback': None
            }
    
    async def _professional_compliance_review(self, content: str, causes_of_action: List[Dict], research_findings: Dict, context: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive Rule 12(b)(6) compliance review using AI modules"""
        try:
            compliance_issues = []
            citation_issues = []
            
            # Rule 12(b)(6) compliance check
            if causes_of_action:
                logger.info("Performing Rule 12(b)(6) compliance check")
                rule_12b6_issues = check_rule_12b6(causes_of_action)
                compliance_issues.extend(rule_12b6_issues)
            
            # Citation validation
            if research_findings:
                logger.info("Validating citation formatting")
                citation_format_issues = validate_citations(research_findings)
                citation_issues.extend(citation_format_issues)
            
            # Additional professional review checks
            content_issues = self._check_document_structure(content)
            compliance_issues.extend(content_issues)
            
            # Determine if attorney review is required
            all_issues = compliance_issues + citation_issues
            attorney_review_required = len(all_issues) > 0
            
            # Apply review flags if needed
            reviewed_content = flag_for_review(content, all_issues) if all_issues else content
            
            # Generate comprehensive feedback
            feedback_sections = []
            
            if compliance_issues:
                feedback_sections.append("**COMPLIANCE ISSUES:**")
                for issue in compliance_issues:
                    feedback_sections.append(f"• {issue}")
                feedback_sections.append("")
            
            if citation_issues:
                feedback_sections.append("**CITATION ISSUES:**")
                for issue in citation_issues:
                    feedback_sections.append(f"• {issue}")
                feedback_sections.append("")
            
            if not all_issues:
                feedback_sections.append("**COMPLIANCE STATUS:** Document meets Rule 12(b)(6) requirements and citation standards.")
            
            feedback_sections.append(f"**REVIEW SUMMARY:** {len(compliance_issues)} compliance issues, {len(citation_issues)} citation issues found.")
            
            return {
                'content': reviewed_content,
                'feedback': "\n".join(feedback_sections),
                'compliance_issues': compliance_issues,
                'citation_issues': citation_issues,
                'changes_made': len(all_issues),
                'ready_for_filing': len(all_issues) == 0,
                'attorney_review_required': attorney_review_required
            }
            
        except Exception as e:
            logger.error(f"Professional compliance review failed: {e}")
            return {
                'content': content,
                'feedback': f"Compliance review encountered an error: {str(e)}",
                'compliance_issues': [f"Review system error: {str(e)}"],
                'citation_issues': [],
                'changes_made': 0,
                'ready_for_filing': False,
                'attorney_review_required': True
            }
    
    async def _professional_citation_review(self, content: str, research_findings: Dict, context: Dict[str, Any]) -> Dict[str, Any]:
        """Focused citation review using validation modules"""
        try:
            citation_issues = validate_citations(research_findings) if research_findings else []
            
            # Additional citation checks
            content_citation_issues = self._check_inline_citations(content)
            citation_issues.extend(content_citation_issues)
            
            # Generate citation-specific feedback
            if citation_issues:
                feedback = "**CITATION REVIEW:**\n" + "\n".join(f"• {issue}" for issue in citation_issues)
                reviewed_content = flag_for_review(content, citation_issues)
            else:
                feedback = "**CITATION REVIEW:** All citations properly formatted and complete."
                reviewed_content = content
            
            return {
                'content': reviewed_content,
                'feedback': feedback,
                'citation_issues': citation_issues,
                'changes_made': len(citation_issues),
                'ready_for_filing': len(citation_issues) == 0,
                'attorney_review_required': len(citation_issues) > 0
            }
            
        except Exception as e:
            logger.error(f"Citation review failed: {e}")
            return {
                'content': content,
                'feedback': f"Citation review error: {str(e)}",
                'citation_issues': [f"Citation review system error: {str(e)}"],
                'changes_made': 0,
                'ready_for_filing': False,
                'attorney_review_required': True
            }
    
    async def _professional_legal_brief_review(self, content: str, causes_of_action: List[Dict], research_findings: Dict, context: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive legal brief review combining compliance and quality checks"""
        # Perform compliance review first
        compliance_result = await self._professional_compliance_review(content, causes_of_action, research_findings, context)
        
        # Add legal brief specific checks
        brief_issues = []
        
        # Check for essential brief components
        if "STATEMENT OF FACTS" not in content.upper():
            brief_issues.append("Missing Statement of Facts section")
        
        if "LEGAL STANDARD" not in content.upper() and "STANDARD OF REVIEW" not in content.upper():
            brief_issues.append("Missing Legal Standard section")
        
        if "ARGUMENT" not in content.upper():
            brief_issues.append("Missing Argument section")
        
        if "CONCLUSION" not in content.upper():
            brief_issues.append("Missing Conclusion section")
        
        # Combine all issues
        all_issues = compliance_result.get('compliance_issues', []) + compliance_result.get('citation_issues', []) + brief_issues
        
        # Update feedback
        feedback_sections = [compliance_result.get('feedback', '')]
        if brief_issues:
            feedback_sections.append("**BRIEF STRUCTURE ISSUES:**")
            for issue in brief_issues:
                feedback_sections.append(f"• {issue}")
        
        return {
            'content': compliance_result['content'],
            'feedback': "\n".join(feedback_sections),
            'compliance_issues': compliance_result.get('compliance_issues', []),
            'citation_issues': compliance_result.get('citation_issues', []),
            'brief_issues': brief_issues,
            'changes_made': len(all_issues),
            'ready_for_filing': len(all_issues) == 0,
            'attorney_review_required': len(all_issues) > 0
        }
    
    async def _professional_format_review(self, content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Professional document formatting review"""
        formatting_issues = []
        formatted_content = content
        
        # Check and fix common formatting issues
        if "\n\n\n" in content:
            formatted_content = formatted_content.replace("\n\n\n", "\n\n")
            formatting_issues.append("Fixed excessive line spacing")
        
        if "  " in content:
            formatted_content = formatted_content.replace("  ", " ")
            formatting_issues.append("Fixed multiple spaces")
        
        formatted_content = formatted_content.strip()
        
        # Check for proper legal formatting
        if not any(court_indicator in content.upper() for court_indicator in ["UNITED STATES DISTRICT COURT", "SUPERIOR COURT", "COURT"]):
            formatting_issues.append("Missing court designation in header")
        
        feedback = "**FORMATTING REVIEW:**\n"
        if formatting_issues:
            feedback += "\n".join(f"• {issue}" for issue in formatting_issues)
        else:
            feedback += "Document formatting meets professional standards."
        
        return {
            'content': formatted_content,
            'feedback': feedback,
            'formatting_issues': formatting_issues,
            'changes_made': len(formatting_issues),
            'ready_for_filing': True,  # Formatting issues don't prevent filing
            'attorney_review_required': False
        }
    
    async def _comprehensive_professional_review(self, content: str, causes_of_action: List[Dict], research_findings: Dict, context: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive review combining all professional checks"""
        # Perform all types of professional review
        compliance_result = await self._professional_compliance_review(content, causes_of_action, research_findings, context)
        format_result = await self._professional_format_review(compliance_result['content'], context)
        
        # Combine results
        all_issues = (compliance_result.get('compliance_issues', []) +
                     compliance_result.get('citation_issues', []) +
                     format_result.get('formatting_issues', []))
        
        comprehensive_feedback = f"""**COMPREHENSIVE PROFESSIONAL REVIEW**

{compliance_result.get('feedback', '')}

{format_result.get('feedback', '')}

**OVERALL STATUS:** {len(all_issues)} total issues found.
"""
        
        return {
            'content': format_result['content'],
            'feedback': comprehensive_feedback,
            'compliance_issues': compliance_result.get('compliance_issues', []),
            'citation_issues': compliance_result.get('citation_issues', []),
            'formatting_issues': format_result.get('formatting_issues', []),
            'changes_made': len(all_issues),
            'ready_for_filing': len(compliance_result.get('compliance_issues', []) + compliance_result.get('citation_issues', [])) == 0,
            'attorney_review_required': len(compliance_result.get('compliance_issues', []) + compliance_result.get('citation_issues', [])) > 0
        }
    
    def _check_document_structure(self, content: str) -> List[str]:
        """Check basic document structure requirements"""
        issues = []
        
        # Check for basic legal document elements
        if not any(section in content.upper() for section in ["PLAINTIFF", "DEFENDANT", "PETITIONER", "RESPONDENT"]):
            issues.append("Missing party identification")
        
        if "JURISDICTION" not in content.upper():
            issues.append("Missing jurisdiction statement")
        
        if not any(damages in content.upper() for damages in ["DAMAGES", "RELIEF", "PRAYER"]):
            issues.append("Missing damages or relief request")
        
        return issues
    
    def _check_inline_citations(self, content: str) -> List[str]:
        """Check for proper inline citation formatting"""
        issues = []
        
        # Basic citation format checks
        import re

        # Look for incomplete citations (basic patterns)
        if "see " in content.lower() and not re.search(r'\d+\s+U\.S\.\s+\d+', content):
            issues.append("Incomplete case citations found")
        
        if "§" in content and not re.search(r'\d+\s+U\.S\.C\.\s+§\s+\d+', content):
            issues.append("Incomplete statutory citations found")
        
        return issues
