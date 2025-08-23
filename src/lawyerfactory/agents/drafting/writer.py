"""
# Script Name: writer.py
# Description: Import AI document generation modules
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Orchestration
#   - Group Tags: null
"""

import logging
from pathlib import Path
from typing import Any, Dict, List

from jinja2 import Environment, FileSystemLoader, select_autoescape

# Import AI document generation modules
from lawyerfactory.document_generator.modules.fact_synthesis import \
    synthesize_facts
from lawyerfactory.document_generator.modules.legal_theory_mapping import (
    integrate_citations, map_facts_to_elements)

from ..agent_registry import AgentConfig, AgentInterface
from ..bot_interface import Bot
from ..workflow_models import WorkflowTask

logger = logging.getLogger(__name__)


class WriterBot(Bot, AgentInterface):
    """Enhanced writing bot for professional legal document creation using AI modules and templates"""
    
    def __init__(self, config: AgentConfig):
        # Initialize Bot interface
        Bot.__init__(self)
        # Initialize AgentInterface
        AgentInterface.__init__(self, config)
        
        # Initialize Jinja2 template environment
        template_dir = Path(__file__).parent.parent.parent / "lawyerfactory" / "document_generator" / "templates"
        if template_dir.exists():
            self.jinja_env = Environment(
                loader=FileSystemLoader(str(template_dir)),
                autoescape=select_autoescape(['html', 'xml'])
            )
            logger.info(f"WriterBot initialized with templates from: {template_dir}")
        else:
            self.jinja_env = None
            logger.warning(f"Template directory not found: {template_dir}")
        
        logger.info("WriterBot initialized with professional legal document generation capabilities")
    
    async def process(self, message: str) -> str:
        """Legacy Bot interface implementation"""
        # Use professional template for basic processing
        try:
            if self.jinja_env:
                template = self.jinja_env.get_template('complaint_body.jinja2')
                # Create a basic structure for legacy interface
                causes_of_action = [{
                    'name': 'General Claim',
                    'elements': [{
                        'name': 'Basis',
                        'fact_text': [message]
                    }]
                }]
                research = {'citations': []}
                return template.render(causes_of_action=causes_of_action, research=research)
            else:
                return f"Professional legal document based on: '{message}'"
        except Exception as e:
            logger.error(f"Template rendering failed: {e}")
            return f"Professional legal document based on: '{message}'"
    
    async def execute_task(self, task: WorkflowTask, context: Dict[str, Any]) -> Dict[str, Any]:
        """AgentInterface implementation for orchestration system"""
        logger.info(f"WriterBot executing task: {task.id}")
        
        try:
            # Extract writing parameters from task context
            content_type = context.get('content_type', 'complaint')
            case_facts = context.get('case_facts', [])
            research_findings = context.get('research_findings', {})
            case_data = context.get('case_data', {})
            
            # Execute professional writing task using AI modules
            if content_type == 'complaint':
                result = await self._write_professional_complaint(case_facts, research_findings, case_data, context)
            elif content_type == 'motion':
                result = await self._write_professional_motion(case_facts, research_findings, case_data, context)
            else:
                result = await self._write_professional_document(case_facts, research_findings, case_data, context)
            
            return {
                'status': 'completed',
                'content': result['content'],
                'content_type': content_type,
                'word_count': len(result['content'].split()) if result['content'] else 0,
                'template_used': result.get('template_used'),
                'professional_formatting': True,
                'sections_included': result.get('sections_included', [])
            }
            
        except Exception as e:
            logger.error(f"WriterBot task execution failed: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'content': None
            }
    
    async def _write_professional_complaint(self, case_facts: List[Dict], research_findings: Dict, case_data: Dict, context: Dict[str, Any]) -> Dict[str, Any]:
        """Write a professional complaint using Jinja2 templates and AI modules"""
        try:
            if not self.jinja_env:
                return {
                    'content': "Professional complaint generation requires template system",
                    'template_used': None,
                    'sections_included': []
                }
            
            # Step 1: Synthesize facts into compelling narrative
            statement_of_facts = synthesize_facts(case_facts) if case_facts else "Facts to be determined during discovery."
            
            # Step 2: Map facts to legal elements and integrate citations
            causes_of_action = context.get('causes_of_action', [])
            if causes_of_action and case_facts:
                causes_of_action = map_facts_to_elements(causes_of_action, case_facts)
                causes_of_action = integrate_citations(causes_of_action, research_findings)
            
            # Step 3: Prepare template context
            template_context = {
                'case': {
                    'case_caption': {
                        'court': case_data.get('court', 'UNITED STATES DISTRICT COURT'),
                        'district': case_data.get('district', 'NORTHERN DISTRICT OF CALIFORNIA'),
                        'plaintiff': case_data.get('plaintiff_name', 'PLAINTIFF NAME'),
                        'defendant': case_data.get('defendant_name', 'DEFENDANT NAME'),
                        'case_number': case_data.get('case_number', 'Case No. [TO BE ASSIGNED]')
                    }
                },
                'statement_of_facts': statement_of_facts,
                'causes_of_action': causes_of_action,
                'research': research_findings
            }
            
            # Step 4: Render professional complaint using template
            complaint_template = self.jinja_env.get_template('complaint.jinja2')
            professional_content = complaint_template.render(**template_context)
            
            return {
                'content': professional_content,
                'template_used': 'complaint.jinja2',
                'sections_included': ['cover_sheet', 'statement_of_facts', 'complaint_body', 'prayer_for_relief', 'bibliography']
            }
            
        except Exception as e:
            logger.error(f"Professional complaint generation failed: {e}")
            # Fallback to basic generation
            case_name = case_data.get('case_name', 'Unknown Case')
            return {
                'content': f"PROFESSIONAL COMPLAINT FOR {case_name}\n\nBased on case facts and research findings.\n\n[Professional content would be generated here]",
                'template_used': None,
                'sections_included': ['basic']
            }
    
    async def _write_professional_motion(self, case_facts: List[Dict], research_findings: Dict, case_data: Dict, context: Dict[str, Any]) -> Dict[str, Any]:
        """Write a professional motion using templates and legal theory mapping"""
        try:
            motion_type = context.get('motion_type', 'Motion for Summary Judgment')
            statement_of_facts = synthesize_facts(case_facts) if case_facts else ""
            
            # Create professional motion structure
            professional_content = f"""
{case_data.get('court', 'UNITED STATES DISTRICT COURT')}
{case_data.get('district', 'NORTHERN DISTRICT OF CALIFORNIA')}

{case_data.get('plaintiff_name', 'PLAINTIFF')},
    Plaintiff,

v.                                              Case No. {case_data.get('case_number', '[TO BE ASSIGNED]')}

{case_data.get('defendant_name', 'DEFENDANT')},
    Defendant.

{motion_type.upper()}

TO THE HONORABLE COURT:

{statement_of_facts}

LEGAL STANDARD

{self._generate_legal_standard(research_findings)}

ARGUMENT

{self._generate_argument_from_research(research_findings, case_facts)}

CONCLUSION

For the foregoing reasons, Plaintiff respectfully requests that this Court grant this motion.

Respectfully submitted,

Attorney for Plaintiff
"""
            
            return {
                'content': professional_content,
                'template_used': 'motion_template',
                'sections_included': ['header', 'facts', 'legal_standard', 'argument', 'conclusion']
            }
            
        except Exception as e:
            logger.error(f"Professional motion generation failed: {e}")
            motion_type = context.get('motion_type', 'General Motion')
            return {
                'content': f"PROFESSIONAL {motion_type.upper()}\n\nBased on case facts and legal research.\n\n[Professional motion content would be generated here]",
                'template_used': None,
                'sections_included': ['basic']
            }
    
    async def _write_professional_document(self, case_facts: List[Dict], research_findings: Dict, case_data: Dict, context: Dict[str, Any]) -> Dict[str, Any]:
        """Write a professional legal document using available templates"""
        statement_of_facts = synthesize_facts(case_facts) if case_facts else ""
        
        professional_content = f"""
PROFESSIONAL LEGAL DOCUMENT

Case: {case_data.get('case_name', 'Professional Legal Matter')}

STATEMENT OF FACTS

{statement_of_facts}

LEGAL ANALYSIS

{self._generate_argument_from_research(research_findings, case_facts)}

CONCLUSION

Based on the facts and applicable law, the following relief is appropriate.
"""
        
        return {
            'content': professional_content,
            'template_used': 'professional_document',
            'sections_included': ['facts', 'analysis', 'conclusion']
        }
    
    def _generate_legal_standard(self, research_findings: Dict) -> str:
        """Generate legal standard section from research findings"""
        citations = research_findings.get('citations', [])
        if citations:
            primary_citation = citations[0] if citations else {}
            cite_text = primary_citation.get('cite', 'Relevant legal authority')
            return f"The applicable legal standard is well-established. {cite_text}."
        return "The applicable legal standard governs this matter."
    
    def _generate_argument_from_research(self, research_findings: Dict, case_facts: List[Dict]) -> str:
        """Generate legal argument from research findings and facts"""
        argument_sections = []
        
        # Use research findings to build argument
        legal_issues = research_findings.get('legal_issues', [])
        citations = research_findings.get('citations', [])
        
        for i, issue in enumerate(legal_issues[:3]):  # Limit to top 3 issues
            section = f"Issue {i+1}: {issue}\n\n"
            if i < len(citations):
                citation = citations[i]
                section += f"As established in {citation.get('cite', 'controlling authority')}, "
                section += citation.get('summary', 'the legal principle applies to the facts of this case.')
            section += "\n"
            argument_sections.append(section)
        
        if not argument_sections:
            return "The facts and law support the relief requested."
        
        return "\n".join(argument_sections)
