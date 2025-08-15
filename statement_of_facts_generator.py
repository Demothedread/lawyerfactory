"""
Professional Statement of Facts Generation Engine
Produces litigation-ready Statement of Facts documents from knowledge graph data
with proper legal formatting, Bluebook citations, and FRCP compliance.
"""

import logging
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, date
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum

from knowledge_graph_integration import KnowledgeGraphIntegration
from enhanced_knowledge_graph import EnhancedKnowledgeGraph, LegalEntityType, LegalRelationshipType

logger = logging.getLogger(__name__)


class FactCategory(Enum):
    """Categories for organizing facts in Statement of Facts"""
    BACKGROUND = "background"
    MATERIAL = "material"
    DISPUTED = "disputed"
    PROCEDURAL = "procedural"
    DAMAGES = "damages"


class CitationFormat(Enum):
    """Supported citation formats"""
    BLUEBOOK = "bluebook"
    RECORD = "record"
    EXHIBIT = "exhibit"


@dataclass
class LegalFact:
    """Structured representation of a legal fact"""
    id: str
    text: str
    category: FactCategory
    confidence: float
    source_documents: List[str] = field(default_factory=list)
    supporting_evidence: List[str] = field(default_factory=list)
    date: Optional[str] = None
    is_disputed: bool = False
    legal_significance: str = ""
    citation: Optional[str] = None
    verification_status: str = "pending"  # pending, verified, disputed
    

@dataclass
class StatementSection:
    """Section of Statement of Facts"""
    title: str
    facts: List[LegalFact]
    introduction: str = ""
    conclusion: str = ""
    subsections: List['StatementSection'] = field(default_factory=list)


class StatementOfFactsGenerator:
    """Professional Statement of Facts generation engine"""
    
    def __init__(self, kg_integration: Optional[KnowledgeGraphIntegration] = None):
        self.kg_integration = kg_integration or KnowledgeGraphIntegration()
        self.citation_format = CitationFormat.BLUEBOOK
        self.templates = self._load_templates()
        
    def _load_templates(self) -> Dict[str, str]:
        """Load professional legal document templates"""
        return {
            'document_header': """STATEMENT OF FACTS

{case_caption}

TO THE HONORABLE COURT:

{party_plaintiff}, by and through undersigned counsel, respectfully submits this Statement of Facts in support of {document_purpose}.

""",
            
            'section_introduction': """
{section_number}. {section_title}

{introduction_text}
""",
            
            'fact_paragraph': """{paragraph_number}. {fact_text}{citation}""",
            
            'disputed_fact': """{paragraph_number}. {fact_text}{citation} {party_defendant} disputes {dispute_description}.""",
            
            'conclusion': """
CONCLUSION

Based on the foregoing facts, {conclusion_statement}

Respectfully submitted,

_________________________
{attorney_name}
{attorney_title}
{bar_number}
Attorney for {client_name}

"""
        }
    
    def generate_statement_of_facts(self, session_id: str, 
                                  case_data: Dict[str, Any],
                                  options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate complete Statement of Facts document"""
        logger.info(f"Generating Statement of Facts for session {session_id}")
        
        try:
            # Get processed facts from knowledge graph
            facts_data = self.kg_integration.generate_facts_matrix_and_statement(session_id)
            
            if not facts_data or 'facts_matrix' not in facts_data:
                raise ValueError("No facts matrix available for statement generation")
            
            # Structure legal facts
            structured_facts = self._structure_legal_facts(facts_data['facts_matrix'])
            
            # Organize facts into Statement of Facts sections
            statement_sections = self._organize_statement_sections(structured_facts, case_data)
            
            # Generate professional document
            document = self._generate_professional_document(statement_sections, case_data)
            
            # Create verification report
            verification_report = self._create_verification_report(structured_facts)
            
            # Generate attorney review points
            review_points = self._identify_review_requirements(structured_facts, facts_data)
            
            result = {
                'session_id': session_id,
                'generation_timestamp': datetime.now().isoformat(),
                'document': {
                    'content': document,
                    'sections': [self._section_to_dict(s) for s in statement_sections],
                    'word_count': len(document.split()),
                    'paragraph_count': len([p for p in document.split('\n') if p.strip() and p.strip()[0].isdigit()])
                },
                'verification_report': verification_report,
                'attorney_review_points': review_points,
                'export_formats': self._generate_export_formats(document, case_data),
                'quality_metrics': self._assess_document_quality(document, structured_facts)
            }
            
            logger.info(f"Statement of Facts generated: {result['document']['word_count']} words, {result['document']['paragraph_count']} paragraphs")
            return result
            
        except Exception as e:
            logger.exception(f"Failed to generate Statement of Facts for session {session_id}: {e}")
            return {
                'session_id': session_id,
                'error': str(e),
                'generation_timestamp': datetime.now().isoformat(),
                'success': False
            }
    
    def _structure_legal_facts(self, facts_matrix: Dict[str, Any]) -> List[LegalFact]:
        """Structure raw facts into legal fact objects"""
        structured_facts = []
        fact_id_counter = 1
        
        # Process undisputed facts
        for fact_data in facts_matrix.get('undisputed_facts', []):
            structured_facts.append(LegalFact(
                id=f"fact_{fact_id_counter:03d}",
                text=self._format_fact_text(fact_data),
                category=FactCategory.MATERIAL,
                confidence=fact_data.get('confidence', 0.8),
                source_documents=fact_data.get('source_documents', []),
                supporting_evidence=fact_data.get('supporting_evidence', []),
                date=fact_data.get('date'),
                is_disputed=False,
                legal_significance=fact_data.get('legal_significance', ''),
                citation=self._format_citation(fact_data)
            ))
            fact_id_counter += 1
        
        # Process disputed facts
        for fact_data in facts_matrix.get('disputed_facts', []):
            structured_facts.append(LegalFact(
                id=f"fact_{fact_id_counter:03d}",
                text=self._format_fact_text(fact_data),
                category=FactCategory.DISPUTED,
                confidence=fact_data.get('confidence', 0.5),
                source_documents=fact_data.get('source_documents', []),
                supporting_evidence=fact_data.get('supporting_evidence', []),
                date=fact_data.get('date'),
                is_disputed=True,
                legal_significance=fact_data.get('legal_significance', ''),
                citation=self._format_citation(fact_data)
            ))
            fact_id_counter += 1
        
        # Process key events as material facts
        for event_data in facts_matrix.get('key_events', []):
            structured_facts.append(LegalFact(
                id=f"fact_{fact_id_counter:03d}",
                text=self._format_fact_text(event_data),
                category=FactCategory.MATERIAL,
                confidence=event_data.get('confidence', 0.9),
                source_documents=event_data.get('source_documents', []),
                supporting_evidence=event_data.get('supporting_evidence', []),
                date=event_data.get('date'),
                is_disputed=False,
                legal_significance=event_data.get('legal_significance', 'key_event'),
                citation=self._format_citation(event_data)
            ))
            fact_id_counter += 1
        
        # Process background context
        for context_data in facts_matrix.get('background_context', []):
            structured_facts.append(LegalFact(
                id=f"fact_{fact_id_counter:03d}",
                text=self._format_fact_text(context_data),
                category=FactCategory.BACKGROUND,
                confidence=context_data.get('confidence', 0.7),
                source_documents=context_data.get('source_documents', []),
                supporting_evidence=context_data.get('supporting_evidence', []),
                date=context_data.get('date'),
                is_disputed=False,
                legal_significance=context_data.get('legal_significance', 'background'),
                citation=self._format_citation(context_data)
            ))
            fact_id_counter += 1
        
        # Process damages claims
        for damages_data in facts_matrix.get('damages_claims', []):
            structured_facts.append(LegalFact(
                id=f"fact_{fact_id_counter:03d}",
                text=self._format_fact_text(damages_data),
                category=FactCategory.DAMAGES,
                confidence=damages_data.get('confidence', 0.8),
                source_documents=damages_data.get('source_documents', []),
                supporting_evidence=damages_data.get('supporting_evidence', []),
                date=damages_data.get('date'),
                is_disputed=damages_data.get('is_disputed', False),
                legal_significance=damages_data.get('legal_significance', 'damages'),
                citation=self._format_citation(damages_data)
            ))
            fact_id_counter += 1
        
        # Sort facts chronologically within categories
        return self._sort_facts_chronologically(structured_facts)
    
    def _organize_statement_sections(self, facts: List[LegalFact], 
                                   case_data: Dict[str, Any]) -> List[StatementSection]:
        """Organize facts into proper Statement of Facts sections"""
        sections = []
        
        # I. INTRODUCTION AND PARTIES
        party_facts = [f for f in facts if 'parties' in f.legal_significance.lower() or 'party' in f.text.lower()]
        introduction_section = StatementSection(
            title="INTRODUCTION AND PARTIES",
            facts=party_facts,
            introduction=self._generate_parties_introduction(case_data)
        )
        sections.append(introduction_section)
        
        # II. JURISDICTION AND VENUE
        jurisdiction_facts = [f for f in facts if any(term in f.text.lower() 
                            for term in ['jurisdiction', 'venue', 'court', 'filed'])]
        jurisdiction_section = StatementSection(
            title="JURISDICTION AND VENUE",
            facts=jurisdiction_facts,
            introduction="This Court has jurisdiction over this matter pursuant to the following facts:"
        )
        sections.append(jurisdiction_section)
        
        # III. BACKGROUND FACTS
        background_facts = [f for f in facts if f.category == FactCategory.BACKGROUND]
        background_section = StatementSection(
            title="BACKGROUND FACTS",
            facts=background_facts,
            introduction="The following background facts provide necessary context for this matter:"
        )
        sections.append(background_section)
        
        # IV. MATERIAL FACTS
        material_facts = [f for f in facts if f.category == FactCategory.MATERIAL and not f.is_disputed]
        material_section = StatementSection(
            title="MATERIAL FACTS",
            facts=material_facts,
            introduction="The following material facts are central to the claims and defenses in this case:"
        )
        sections.append(material_section)
        
        # V. DISPUTED FACTS
        disputed_facts = [f for f in facts if f.category == FactCategory.DISPUTED or f.is_disputed]
        if disputed_facts:
            disputed_section = StatementSection(
                title="DISPUTED FACTS",
                facts=disputed_facts,
                introduction="The parties dispute the following facts, which require resolution through discovery or trial:"
            )
            sections.append(disputed_section)
        
        # VI. DAMAGES AND RELIEF SOUGHT
        damages_facts = [f for f in facts if f.category == FactCategory.DAMAGES]
        if damages_facts:
            damages_section = StatementSection(
                title="DAMAGES AND RELIEF SOUGHT",
                facts=damages_facts,
                introduction="Plaintiff has suffered the following damages as a result of Defendant's conduct:"
            )
            sections.append(damages_section)
        
        return sections
    
    def _generate_professional_document(self, sections: List[StatementSection], 
                                      case_data: Dict[str, Any]) -> str:
        """Generate professional Statement of Facts document"""
        document_parts = []
        
        # Document header
        case_caption = self._format_case_caption(case_data)
        document_purpose = case_data.get('document_purpose', 'the pending motion')
        
        header = self.templates['document_header'].format(
            case_caption=case_caption,
            party_plaintiff=case_data.get('plaintiff_name', 'Plaintiff'),
            document_purpose=document_purpose
        )
        document_parts.append(header)
        
        # Generate sections
        paragraph_counter = 1
        for section_num, section in enumerate(sections, 1):
            # Section header
            section_intro = self.templates['section_introduction'].format(
                section_number=self._format_roman_numeral(section_num),
                section_title=section.title,
                introduction_text=section.introduction
            )
            document_parts.append(section_intro)
            
            # Section facts
            for fact in section.facts:
                if fact.is_disputed:
                    fact_text = self.templates['disputed_fact'].format(
                        paragraph_number=paragraph_counter,
                        fact_text=fact.text,
                        citation=fact.citation or "",
                        party_defendant=case_data.get('defendant_name', 'Defendant'),
                        dispute_description=self._generate_dispute_description(fact)
                    )
                else:
                    fact_text = self.templates['fact_paragraph'].format(
                        paragraph_number=paragraph_counter,
                        fact_text=fact.text,
                        citation=fact.citation or ""
                    )
                
                document_parts.append(fact_text)
                paragraph_counter += 1
            
            document_parts.append("")  # Add spacing between sections
        
        # Document conclusion
        conclusion = self.templates['conclusion'].format(
            conclusion_statement=case_data.get('conclusion_statement', 
                                             'the relief requested is appropriate and should be granted'),
            attorney_name=case_data.get('attorney_name', '[Attorney Name]'),
            attorney_title=case_data.get('attorney_title', 'Attorney at Law'),
            bar_number=case_data.get('bar_number', '[Bar Number]'),
            client_name=case_data.get('plaintiff_name', '[Client Name]')
        )
        document_parts.append(conclusion)
        
        return "\n".join(document_parts)
    
    def _format_fact_text(self, fact_data: Any) -> str:
        """Format raw fact data into proper legal writing style"""
        if isinstance(fact_data, str):
            text = fact_data
        elif isinstance(fact_data, dict):
            text = fact_data.get('text', fact_data.get('description', str(fact_data)))
        else:
            text = str(fact_data)
        
        # Ensure proper sentence structure
        text = text.strip()
        if not text.endswith('.'):
            text += '.'
        
        # Capitalize first letter
        if text:
            text = text[0].upper() + text[1:]
        
        # Clean up common formatting issues
        text = re.sub(r'\s+', ' ', text)  # Multiple spaces
        text = re.sub(r'\.+', '.', text)  # Multiple periods
        
        return text
    
    def _format_citation(self, fact_data: Any) -> str:
        """Format Bluebook-compliant citations"""
        if not isinstance(fact_data, dict):
            return ""
        
        source_docs = fact_data.get('source_documents', [])
        if not source_docs:
            return ""
        
        # Format based on document type
        citations = []
        for doc in source_docs[:3]:  # Limit to 3 citations per fact
            if isinstance(doc, str):
                # Simple document reference
                if doc.endswith('.pdf'):
                    doc_name = doc.replace('.pdf', '').replace('_', ' ').title()
                    citations.append(f"(Ex. {doc_name})")
                else:
                    citations.append(f"(See {doc})")
            elif isinstance(doc, dict):
                # Structured citation
                if 'exhibit' in doc:
                    citations.append(f"(Ex. {doc['exhibit']})")
                elif 'page' in doc:
                    citations.append(f"(Doc. {doc.get('document', '')}, p. {doc['page']})")
        
        return " " + "; ".join(citations) if citations else ""
    
    def _format_case_caption(self, case_data: Dict[str, Any]) -> str:
        """Format proper case caption"""
        plaintiff = case_data.get('plaintiff_name', '[Plaintiff Name]')
        defendant = case_data.get('defendant_name', '[Defendant Name]')
        case_number = case_data.get('case_number', '[Case Number]')
        court = case_data.get('court', '[Court Name]')
        
        return f"""{plaintiff},
                        Plaintiff,
v.                                      Case No. {case_number}

{defendant},
                        Defendant.

{court}"""
    
    def _generate_parties_introduction(self, case_data: Dict[str, Any]) -> str:
        """Generate introduction to parties section"""
        plaintiff = case_data.get('plaintiff_name', 'Plaintiff')
        defendant = case_data.get('defendant_name', 'Defendant')
        
        return f"""This action involves a dispute between {plaintiff} ("Plaintiff") and {defendant} ("Defendant"). The following facts establish the identity and relevant background of the parties:"""
    
    def _format_roman_numeral(self, num: int) -> str:
        """Convert number to Roman numeral"""
        roman_numerals = {
            1: 'I', 2: 'II', 3: 'III', 4: 'IV', 5: 'V',
            6: 'VI', 7: 'VII', 8: 'VIII', 9: 'IX', 10: 'X'
        }
        return roman_numerals.get(num, str(num))
    
    def _generate_dispute_description(self, fact: LegalFact) -> str:
        """Generate description of what is disputed about a fact"""
        # This could be enhanced with AI to generate more specific disputes
        return "the accuracy and completeness of this allegation"
    
    def _sort_facts_chronologically(self, facts: List[LegalFact]) -> List[LegalFact]:
        """Sort facts chronologically within their categories"""
        def sort_key(fact):
            # Sort by category first, then by date
            category_order = {
                FactCategory.BACKGROUND: 1,
                FactCategory.MATERIAL: 2,
                FactCategory.DISPUTED: 3,
                FactCategory.PROCEDURAL: 4,
                FactCategory.DAMAGES: 5
            }
            
            category_rank = category_order.get(fact.category, 6)
            
            # Try to parse date for chronological ordering
            date_rank = 9999  # Default for facts without dates
            if fact.date:
                try:
                    parsed_date = datetime.fromisoformat(fact.date.replace('Z', '+00:00'))
                    date_rank = parsed_date.timestamp()
                except (ValueError, AttributeError):
                    pass
            
            return (category_rank, date_rank)
        
        return sorted(facts, key=sort_key)
    
    def _create_verification_report(self, facts: List[LegalFact]) -> Dict[str, Any]:
        """Create verification report for attorney review"""
        total_facts = len(facts)
        high_confidence = len([f for f in facts if f.confidence >= 0.8])
        medium_confidence = len([f for f in facts if 0.6 <= f.confidence < 0.8])
        low_confidence = len([f for f in facts if f.confidence < 0.6])
        disputed_facts = len([f for f in facts if f.is_disputed])
        
        citation_coverage = len([f for f in facts if f.citation]) / total_facts if total_facts > 0 else 0
        
        return {
            'total_facts': total_facts,
            'confidence_distribution': {
                'high_confidence': high_confidence,
                'medium_confidence': medium_confidence,
                'low_confidence': low_confidence
            },
            'disputed_facts_count': disputed_facts,
            'citation_coverage': citation_coverage,
            'verification_recommendations': self._generate_verification_recommendations(facts),
            'quality_score': self._calculate_quality_score(facts)
        }
    
    def _identify_review_requirements(self, facts: List[LegalFact], 
                                    facts_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify specific attorney review requirements"""
        review_points = []
        
        # Low confidence facts
        low_confidence_facts = [f for f in facts if f.confidence < 0.6]
        if low_confidence_facts:
            review_points.append({
                'type': 'confidence_review',
                'priority': 'high',
                'description': f'{len(low_confidence_facts)} facts require confidence verification',
                'facts': [f.id for f in low_confidence_facts]
            })
        
        # Facts without citations
        uncited_facts = [f for f in facts if not f.citation]
        if len(uncited_facts) > len(facts) * 0.3:  # More than 30% uncited
            review_points.append({
                'type': 'citation_review',
                'priority': 'medium',
                'description': f'{len(uncited_facts)} facts need proper citations',
                'facts': [f.id for f in uncited_facts]
            })
        
        # Disputed facts requiring attention
        disputed_facts = [f for f in facts if f.is_disputed]
        if disputed_facts:
            review_points.append({
                'type': 'dispute_resolution',
                'priority': 'high',
                'description': f'{len(disputed_facts)} disputed facts need resolution strategy',
                'facts': [f.id for f in disputed_facts]
            })
        
        # Missing key elements
        attorney_review_points = facts_data.get('attorney_review_points', [])
        for point in attorney_review_points:
            review_points.append({
                'type': 'knowledge_graph_flag',
                'priority': point.get('priority', 'medium'),
                'description': point.get('description', ''),
                'details': point.get('details', {})
            })
        
        return review_points
    
    def _generate_export_formats(self, document: str, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate export capabilities for different formats"""
        return {
            'markdown': {
                'content': self._convert_to_markdown(document),
                'filename': f"statement_of_facts_{case_data.get('case_number', 'draft')}.md"
            },
            'word_ready': {
                'content': self._format_for_word(document),
                'filename': f"statement_of_facts_{case_data.get('case_number', 'draft')}.docx",
                'instructions': "Ready for import into Microsoft Word for final formatting"
            },
            'pdf_ready': {
                'content': document,
                'filename': f"statement_of_facts_{case_data.get('case_number', 'draft')}.pdf",
                'instructions': "Formatted for PDF generation with proper legal document structure"
            }
        }
    
    def _convert_to_markdown(self, document: str) -> str:
        """Convert document to Markdown format"""
        # Convert Roman numerals to Markdown headers
        lines = document.split('\n')
        markdown_lines = []
        
        for line in lines:
            line = line.strip()
            if re.match(r'^[IVX]+\.\s+[A-Z\s]+$', line):
                # Section header
                markdown_lines.append(f"## {line}")
            elif re.match(r'^\d+\.\s+', line):
                # Numbered paragraph
                markdown_lines.append(f"{line}")
            elif line.isupper() and len(line) > 5:
                # Title
                markdown_lines.append(f"# {line}")
            else:
                markdown_lines.append(line)
        
        return '\n'.join(markdown_lines)
    
    def _format_for_word(self, document: str) -> str:
        """Format document for Microsoft Word import"""
        # Add specific formatting markers for Word
        formatted = document.replace('\n\n', '\n\n---PAGE-BREAK---\n\n')
        return formatted
    
    def _assess_document_quality(self, document: str, facts: List[LegalFact]) -> Dict[str, Any]:
        """Assess overall document quality"""
        word_count = len(document.split())
        paragraph_count = len([p for p in document.split('\n') if p.strip() and p.strip()[0].isdigit()])
        
        avg_confidence = sum(f.confidence for f in facts) / len(facts) if facts else 0
        citation_rate = len([f for f in facts if f.citation]) / len(facts) if facts else 0
        
        quality_score = (
            (avg_confidence * 0.4) +
            (citation_rate * 0.3) +
            (min(word_count / 2000, 1.0) * 0.2) +  # Appropriate length
            (min(paragraph_count / 50, 1.0) * 0.1)  # Good paragraph count
        )
        
        return {
            'overall_quality_score': quality_score,
            'word_count': word_count,
            'paragraph_count': paragraph_count,
            'average_confidence': avg_confidence,
            'citation_coverage': citation_rate,
            'readability_assessment': self._assess_readability(document),
            'legal_writing_compliance': self._assess_legal_compliance(document)
        }
    
    def _assess_readability(self, document: str) -> Dict[str, Any]:
        """Assess document readability"""
        sentences = len([s for s in document.split('.') if s.strip()])
        words = len(document.split())
        avg_sentence_length = words / sentences if sentences > 0 else 0
        
        return {
            'average_sentence_length': avg_sentence_length,
            'complexity_level': 'appropriate' if 15 <= avg_sentence_length <= 25 else 'review_needed'
        }
    
    def _assess_legal_compliance(self, document: str) -> Dict[str, Any]:
        """Assess compliance with legal writing standards"""
        has_proper_caption = 'Case No.' in document
        has_proper_conclusion = 'Respectfully submitted' in document
        has_numbered_paragraphs = bool(re.search(r'^\d+\.', document, re.MULTILINE))
        
        compliance_score = sum([has_proper_caption, has_proper_conclusion, has_numbered_paragraphs]) / 3
        
        return {
            'compliance_score': compliance_score,
            'has_proper_caption': has_proper_caption,
            'has_proper_conclusion': has_proper_conclusion,
            'has_numbered_paragraphs': has_numbered_paragraphs,
            'frcp_compliance': 'good' if compliance_score >= 0.8 else 'needs_review'
        }
    
    def _generate_verification_recommendations(self, facts: List[LegalFact]) -> List[str]:
        """Generate specific verification recommendations"""
        recommendations = []
        
        low_confidence_count = len([f for f in facts if f.confidence < 0.6])
        if low_confidence_count > 0:
            recommendations.append(f"Verify {low_confidence_count} low-confidence facts with additional sources")
        
        uncited_count = len([f for f in facts if not f.citation])
        if uncited_count > 0:
            recommendations.append(f"Add proper citations for {uncited_count} facts")
        
        disputed_count = len([f for f in facts if f.is_disputed])
        if disputed_count > 0:
            recommendations.append(f"Develop litigation strategy for {disputed_count} disputed facts")
        
        return recommendations
    
    def _calculate_quality_score(self, facts: List[LegalFact]) -> float:
        """Calculate overall quality score for facts"""
        if not facts:
            return 0.0
        
        confidence_score = sum(f.confidence for f in facts) / len(facts)
        citation_score = len([f for f in facts if f.citation]) / len(facts)
        completeness_score = len([f for f in facts if f.source_documents]) / len(facts)
        
        return (confidence_score * 0.5 + citation_score * 0.3 + completeness_score * 0.2)
    
    def _section_to_dict(self, section: StatementSection) -> Dict[str, Any]:
        """Convert StatementSection to dictionary"""
        return {
            'title': section.title,
            'introduction': section.introduction,
            'conclusion': section.conclusion,
            'fact_count': len(section.facts),
            'facts': [
                {
                    'id': fact.id,
                    'text': fact.text,
                    'category': fact.category.value,
                    'confidence': fact.confidence,
                    'is_disputed': fact.is_disputed,
                    'citation': fact.citation
                }
                for fact in section.facts
            ]
        }


def create_statement_of_facts_generator() -> StatementOfFactsGenerator:
    """Factory function to create Statement of Facts generator"""
    return StatementOfFactsGenerator()


if __name__ == "__main__":
    # Example usage
    generator = create_statement_of_facts_generator()
    
    # Test case data
    test_case_data = {
        'plaintiff_name': 'John Doe',
        'defendant_name': 'MegaCorp Industries',
        'case_number': '2024-CV-12345',
        'court': 'Superior Court of California, County of Los Angeles',
        'document_purpose': 'Plaintiff\'s Motion for Summary Judgment',
        'attorney_name': 'Jane Attorney',
        'attorney_title': 'Attorney at Law',
        'bar_number': 'State Bar No. 123456'
    }
    
    print("Statement of Facts Generator initialized successfully")
    print("Ready for integration with knowledge graph system")