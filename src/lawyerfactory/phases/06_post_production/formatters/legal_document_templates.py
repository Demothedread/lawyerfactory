"""
# Script Name: legal_document_templates.py
# Description: Professional Legal Document Templates Provides Bluebook-compliant templates for Statement of Facts and related legal documents with proper FRCP formatting and legal writing standards.
# Relationships:
#   - Entity Type: UI Component
#   - Directory Group: Frontend
#   - Group Tags: null
Professional Legal Document Templates
Provides Bluebook-compliant templates for Statement of Facts and related legal documents
with proper FRCP formatting and legal writing standards.
"""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class DocumentType(Enum):
    """Types of legal documents supported"""
    STATEMENT_OF_FACTS = "statement_of_facts"
    MOTION_BRIEF = "motion_brief"
    COMPLAINT = "complaint"
    ANSWER = "answer"
    SUMMARY_JUDGMENT = "summary_judgment"


class CourtLevel(Enum):
    """Court levels for proper formatting"""
    FEDERAL_DISTRICT = "federal_district"
    STATE_SUPERIOR = "state_superior"
    STATE_SUPREME = "state_supreme"
    APPELLATE = "appellate"


@dataclass
class TemplateConfig:
    """Configuration for document templates"""
    court_level: CourtLevel
    jurisdiction: str
    local_rules: List[str]
    citation_format: str = "bluebook"
    line_spacing: str = "double"
    margin_size: str = "1_inch"


class LegalDocumentTemplates:
    """Professional legal document template system"""
    
    def __init__(self, config: Optional[TemplateConfig] = None):
        self.config = config or self._get_default_config()
        self.templates = self._initialize_templates()
        
    def _get_default_config(self) -> TemplateConfig:
        """Get default template configuration"""
        return TemplateConfig(
            court_level=CourtLevel.STATE_SUPERIOR,
            jurisdiction="California",
            local_rules=["Local Rule 3-101", "Local Rule 3-102"]
        )
    
    def _initialize_templates(self) -> Dict[str, Dict[str, str]]:
        """Initialize all document templates"""
        return {
            DocumentType.STATEMENT_OF_FACTS.value: {
                'header': self._get_statement_header_template(),
                'section': self._get_statement_section_template(),
                'fact_paragraph': self._get_fact_paragraph_template(),
                'disputed_fact': self._get_disputed_fact_template(),
                'conclusion': self._get_statement_conclusion_template(),
                'signature_block': self._get_signature_block_template()
            },
            DocumentType.MOTION_BRIEF.value: {
                'header': self._get_motion_header_template(),
                'introduction': self._get_motion_introduction_template(),
                'argument': self._get_motion_argument_template(),
                'conclusion': self._get_motion_conclusion_template()
            },
            DocumentType.COMPLAINT.value: {
                'header': self._get_complaint_header_template(),
                'jurisdiction': self._get_jurisdiction_template(),
                'parties': self._get_parties_template(),
                'facts': self._get_facts_template(),
                'causes_of_action': self._get_causes_template(),
                'prayer': self._get_prayer_template()
            }
        }
    
    def _get_statement_header_template(self) -> str:
        """Statement of Facts header template"""
        return """STATEMENT OF FACTS

{case_caption}

TO THE HONORABLE COURT:

{moving_party}, by and through undersigned counsel, respectfully submits this Statement of Facts {document_purpose}.

{compliance_statement}

"""
    
    def _get_statement_section_template(self) -> str:
        """Section header template for Statement of Facts"""
        return """
{section_number}. {section_title}

{section_introduction}

"""
    
    def _get_fact_paragraph_template(self) -> str:
        """Individual fact paragraph template"""
        return """{paragraph_number}. {fact_text}{citation}"""
    
    def _get_disputed_fact_template(self) -> str:
        """Disputed fact paragraph template"""
        return """{paragraph_number}. {fact_text}{citation} {opposing_party} {dispute_qualifier} {dispute_description}."""
    
    def _get_statement_conclusion_template(self) -> str:
        """Statement of Facts conclusion template"""
        return """
CONCLUSION

Based on the foregoing facts, {conclusion_statement}

{prayer_for_relief}

Respectfully submitted,

{signature_block}

"""
    
    def _get_signature_block_template(self) -> str:
        """Professional signature block template"""
        return """_________________________
{attorney_name}
{attorney_title}
{bar_number}
{law_firm}
{address_line_1}
{address_line_2}
{phone}
{email}
Attorney for {client_name}

"""
    
    def _get_motion_header_template(self) -> str:
        """Motion brief header template"""
        return """{motion_title}

{case_caption}

TO THE HONORABLE COURT:

{moving_party}, by and through undersigned counsel, respectfully moves this Court {motion_request}.

This motion is made {basis_statement} and is supported by the attached memorandum of points and authorities, the declaration of {declarant}, and the evidence submitted herewith.

"""
    
    def _get_motion_introduction_template(self) -> str:
        """Motion introduction template"""
        return """
INTRODUCTION

{case_overview}

{motion_summary}

{relief_requested}

"""
    
    def _get_motion_argument_template(self) -> str:
        """Motion argument section template"""
        return """
ARGUMENT

{argument_number}. {argument_heading}

{legal_standard}

{factual_application}

{conclusion_paragraph}

"""
    
    def _get_motion_conclusion_template(self) -> str:
        """Motion conclusion template"""
        return """
CONCLUSION

For the foregoing reasons, {moving_party} respectfully requests that this Court {specific_relief}.

{additional_relief}

Respectfully submitted,

{signature_block}

"""
    
    def _get_complaint_header_template(self) -> str:
        """Complaint header template"""
        return """{complaint_title}

{case_caption}

{filing_information}

TO DEFENDANT {defendant_name}:

YOU ARE BEING SUED BY PLAINTIFF {plaintiff_name}.

{service_notice}

"""
    
    def _get_jurisdiction_template(self) -> str:
        """Jurisdiction and venue template"""
        return """
JURISDICTION AND VENUE

{jurisdiction_paragraph}. This Court has jurisdiction over this action because {jurisdiction_basis}.

{venue_paragraph}. Venue is proper in this Court because {venue_basis}.

"""
    
    def _get_parties_template(self) -> str:
        """Parties section template"""
        return """
PARTIES

{plaintiff_paragraph}. Plaintiff {plaintiff_name} {plaintiff_description}.

{defendant_paragraph}. Defendant {defendant_name} {defendant_description}.

{additional_parties}

"""
    
    def _get_facts_template(self) -> str:
        """Facts section template for complaints"""
        return """
STATEMENT OF FACTS

{facts_introduction}

{facts_paragraphs}

"""
    
    def _get_causes_template(self) -> str:
        """Causes of action template"""
        return """
{cause_number}

({cause_title})

{incorporation_paragraph}. Plaintiff incorporates by reference paragraphs {paragraph_range} as though fully set forth herein.

{cause_elements}

{prayer_paragraph}. WHEREFORE, Plaintiff prays for judgment against Defendant as set forth below.

"""
    
    def _get_prayer_template(self) -> str:
        """Prayer for relief template"""
        return """
PRAYER FOR RELIEF

WHEREFORE, Plaintiff respectfully requests that this Court enter judgment in favor of Plaintiff and against Defendant as follows:

{relief_items}

{general_relief}

{attorneys_fees}

{costs}

{additional_relief}

Respectfully submitted,

{signature_block}

"""
    
    def get_case_caption_template(self, court_level: CourtLevel) -> str:
        """Get appropriate case caption based on court level"""
        if court_level == CourtLevel.FEDERAL_DISTRICT:
            return """{plaintiff_name},
                        Plaintiff,
v.                                      Case No. {case_number}

{defendant_name},
                        Defendant.

UNITED STATES DISTRICT COURT
{district}"""
        
        elif court_level == CourtLevel.STATE_SUPERIOR:
            return """{plaintiff_name},
                        Plaintiff,
v.                                      Case No. {case_number}

{defendant_name},
                        Defendant.

SUPERIOR COURT OF {state}
{county}"""
        
        else:  # Default template
            return """{plaintiff_name},
                        Plaintiff,
v.                                      Case No. {case_number}

{defendant_name},
                        Defendant.

{court_name}"""
    
    def get_bluebook_citation_formats(self) -> Dict[str, str]:
        """Get Bluebook citation format templates"""
        return {
            'case_citation': "{case_name}, {volume} {reporter} {page} ({court} {year})",
            'statute_citation': "{title} U.S.C. § {section} ({year})",
            'regulation_citation': "{title} C.F.R. § {section} ({year})",
            'record_citation': "({document_type} {page})",
            'exhibit_citation': "(Ex. {exhibit_number})",
            'deposition_citation': "({deponent_name} Dep. {page}:{line})",
            'declaration_citation': "({declarant_name} Decl. ¶ {paragraph})",
            'multiple_citations': "{primary_citation}; {secondary_citation}",
            'parenthetical': "{citation} ({parenthetical_text})",
            'string_citation': "{citation_1}; {citation_2}; {citation_3}"
        }
    
    def get_legal_writing_standards(self) -> Dict[str, List[str]]:
        """Get legal writing standards and best practices"""
        return {
            'fact_writing': [
                "Use past tense for completed actions",
                "Maintain objective, neutral tone",
                "Include specific dates, times, and locations",
                "Provide proper citations for all assertions",
                "Use active voice when possible",
                "Avoid legal conclusions in fact statements",
                "Present facts chronologically within sections",
                "Include only relevant, material facts"
            ],
            'citation_requirements': [
                "Cite all factual assertions to record evidence",
                "Use proper Bluebook format for all citations",
                "Include pincites for specific information",
                "Place citations at end of sentences",
                "Use short form citations after full citation",
                "Include parenthetical explanations when helpful"
            ],
            'document_structure': [
                "Begin with proper case caption",
                "Include clear section headings",
                "Number all factual paragraphs consecutively",
                "Use Roman numerals for major sections",
                "End with proper signature block",
                "Include certificate of service if required"
            ],
            'professional_tone': [
                "Use formal, respectful language",
                "Avoid inflammatory or argumentative language",
                "Present disputed facts objectively",
                "Use appropriate legal terminology",
                "Maintain consistency in party designations",
                "Follow court's local rules for formatting"
            ]
        }
    
    def get_frcp_compliance_checklist(self) -> Dict[str, List[str]]:
        """Get FRCP compliance checklist for documents"""
        return {
            'rule_8_pleadings': [
                "Include short and plain statement of claim",
                "Show court has jurisdiction",
                "Include demand for relief",
                "Use separate paragraphs for separate allegations",
                "Number paragraphs consecutively"
            ],
            'rule_10_form': [
                "Include case caption with case number",
                "Include title of document",
                "Use proper signature block",
                "Include attorney information",
                "Follow local court formatting rules"
            ],
            'rule_11_good_faith': [
                "Ensure factual contentions have evidentiary support",
                "Verify legal contentions are warranted by law",
                "Confirm document not filed for improper purpose",
                "Attorney signature certifies compliance"
            ],
            'rule_56_summary_judgment': [
                "Include statement of undisputed facts",
                "Cite specific record evidence",
                "Identify disputed facts requiring trial",
                "Support all factual assertions with citations"
            ]
        }
    
    def format_document(self, document_type: DocumentType, content: Dict[str, Any]) -> str:
        """Format complete document using appropriate template"""
        template_set = self.templates.get(document_type.value, {})
        
        if document_type == DocumentType.STATEMENT_OF_FACTS:
            return self._format_statement_of_facts(template_set, content)
        elif document_type == DocumentType.MOTION_BRIEF:
            return self._format_motion_brief(template_set, content)
        elif document_type == DocumentType.COMPLAINT:
            return self._format_complaint(template_set, content)
        else:
            raise ValueError(f"Unsupported document type: {document_type}")
    
    def _format_statement_of_facts(self, templates: Dict[str, str], content: Dict[str, Any]) -> str:
        """Format Statement of Facts document"""
        document_parts = []
        
        # Header
        case_caption = self.get_case_caption_template(self.config.court_level).format(**content.get('case_info', {}))
        header = templates['header'].format(
            case_caption=case_caption,
            moving_party=content.get('moving_party', 'Plaintiff'),
            document_purpose=content.get('document_purpose', 'in support of the pending motion'),
            compliance_statement=self._get_compliance_statement()
        )
        document_parts.append(header)
        
        # Sections
        for section in content.get('sections', []):
            section_header = templates['section'].format(**section)
            document_parts.append(section_header)
            
            # Facts within section
            for i, fact in enumerate(section.get('facts', []), 1):
                if fact.get('is_disputed', False):
                    fact_para = templates['disputed_fact'].format(
                        paragraph_number=fact['paragraph_number'],
                        fact_text=fact['text'],
                        citation=fact.get('citation', ''),
                        opposing_party=content.get('opposing_party', 'Defendant'),
                        dispute_qualifier='disputes that',
                        dispute_description=fact.get('dispute_description', 'this allegation is accurate')
                    )
                else:
                    fact_para = templates['fact_paragraph'].format(**fact)
                
                document_parts.append(fact_para)
        
        # Conclusion
        conclusion = templates['conclusion'].format(
            conclusion_statement=content.get('conclusion_statement', 'the facts support the relief requested'),
            prayer_for_relief=content.get('prayer_for_relief', ''),
            signature_block=templates['signature_block'].format(**content.get('attorney_info', {}))
        )
        document_parts.append(conclusion)
        
        return '\n'.join(document_parts)
    
    def _format_motion_brief(self, templates: Dict[str, str], content: Dict[str, Any]) -> str:
        """Format motion brief document"""
        # Implementation for motion brief formatting
        return "Motion brief formatting not yet implemented"
    
    def _format_complaint(self, templates: Dict[str, str], content: Dict[str, Any]) -> str:
        """Format complaint document"""
        # Implementation for complaint formatting
        return "Complaint formatting not yet implemented"
    
    def _get_compliance_statement(self) -> str:
        """Get compliance statement for local rules"""
        rules = ', '.join(self.config.local_rules)
        return f"This Statement is submitted in compliance with {rules}."
    
    def validate_citation_format(self, citation: str, citation_type: str) -> Dict[str, Any]:
        """Validate citation format against Bluebook standards"""
        citation_formats = self.get_bluebook_citation_formats()
        
        # Basic validation (can be enhanced with more sophisticated checking)
        is_valid = True
        errors = []
        
        if citation_type == 'case_citation':
            # Check for required elements
            if not re.search(r'\d+\s+\w+\s+\d+', citation):
                is_valid = False
                errors.append("Missing volume, reporter, or page number")
            
            if not re.search(r'\(\w+\s+\d{4}\)', citation):
                is_valid = False
                errors.append("Missing or malformed court and year")
        
        elif citation_type == 'record_citation':
            if not citation.startswith('(') or not citation.endswith(')'):
                is_valid = False
                errors.append("Record citations must be in parentheses")
        
        return {
            'is_valid': is_valid,
            'errors': errors,
            'suggestions': self._get_citation_suggestions(citation, citation_type)
        }
    
    def _get_citation_suggestions(self, citation: str, citation_type: str) -> List[str]:
        """Get suggestions for improving citation format"""
        suggestions = []
        
        if citation_type == 'case_citation':
            suggestions.append("Ensure format: Case Name, Vol. Reporter Page (Court Year)")
            suggestions.append("Use proper abbreviations from Bluebook Table T1")
        elif citation_type == 'record_citation':
            suggestions.append("Use format: (Doc. [number], p. [page])")
            suggestions.append("Include pincites for specific information")
        
        return suggestions


def create_legal_templates(config: Optional[TemplateConfig] = None) -> LegalDocumentTemplates:
    """Factory function to create legal document templates"""
    return LegalDocumentTemplates(config)


# Example usage and testing
if __name__ == "__main__":
    # Create template system
    templates = create_legal_templates()
    
    # Test Statement of Facts formatting
    test_content = {
        'case_info': {
            'plaintiff_name': 'John Doe',
            'defendant_name': 'MegaCorp Industries',
            'case_number': '2024-CV-12345',
            'state': 'CALIFORNIA',
            'county': 'COUNTY OF LOS ANGELES'
        },
        'moving_party': 'Plaintiff',
        'document_purpose': 'in support of Plaintiff\'s Motion for Summary Judgment',
        'sections': [
            {
                'section_number': 'I',
                'section_title': 'PARTIES',
                'section_introduction': 'The following facts establish the identity of the parties:',
                'facts': [
                    {
                        'paragraph_number': 1,
                        'text': 'Plaintiff John Doe is an individual residing in Los Angeles County, California.',
                        'citation': ' (Doe Decl. ¶ 1.)'
                    }
                ]
            }
        ],
        'attorney_info': {
            'attorney_name': 'Jane Attorney',
            'attorney_title': 'Attorney at Law',
            'bar_number': 'State Bar No. 123456',
            'law_firm': 'Law Firm LLP',
            'address_line_1': '123 Legal Street',
            'address_line_2': 'Los Angeles, CA 90210',
            'phone': '(555) 123-4567',
            'email': 'jattorney@lawfirm.com',
            'client_name': 'John Doe'
        }
    }
    
    print("Legal Document Templates initialized successfully")
    print("Ready for professional document generation")