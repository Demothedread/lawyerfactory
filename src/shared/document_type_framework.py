"""
Modular Document Type Framework for LawyerFactory
Supports business proposals, white papers, and legal documents with extensible architecture.
Implements 1-3-1 sandwich writing model with recursive document structuring.
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime

logger = logging.getLogger(__name__)


class DocumentType(Enum):
    """Supported document types"""
    LEGAL_COMPLAINT = "legal_complaint"
    BUSINESS_PROPOSAL = "business_proposal"
    WHITE_PAPER = "white_paper"
    LEGAL_BRIEF = "legal_brief"
    CONTRACT = "contract"
    RESEARCH_REPORT = "research_report"
    TECHNICAL_SPECIFICATION = "technical_specification"
    POLICY_DOCUMENT = "policy_document"


class SectionType(Enum):
    """Types of document sections"""
    INTRODUCTION = "introduction"
    EXECUTIVE_SUMMARY = "executive_summary"
    BACKGROUND = "background"
    METHODOLOGY = "methodology"
    FINDINGS = "findings"
    ANALYSIS = "analysis"
    RECOMMENDATIONS = "recommendations"
    CONCLUSION = "conclusion"
    APPENDIX = "appendix"
    LEGAL_ARGUMENT = "legal_argument"
    FACTS = "facts"
    RELIEF_SOUGHT = "relief_sought"
    FINANCIAL_PROJECTIONS = "financial_projections"
    TECHNICAL_DETAILS = "technical_details"


class WritingStyle(Enum):
    """Writing styles for different document types"""
    FORMAL_LEGAL = "formal_legal"
    BUSINESS_PROFESSIONAL = "business_professional"
    ACADEMIC_RESEARCH = "academic_research"
    TECHNICAL_PRECISE = "technical_precise"
    PERSUASIVE = "persuasive"
    INFORMATIONAL = "informational"


@dataclass
class DocumentSection:
    """Represents a section within a document"""
    id: str
    section_type: SectionType
    title: str
    content: str = ""
    subsections: List['DocumentSection'] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    word_count_target: Optional[int] = None
    style_requirements: List[str] = field(default_factory=list)
    citations: List[str] = field(default_factory=list)
    
    def add_subsection(self, subsection: 'DocumentSection'):
        """Add a subsection"""
        self.subsections.append(subsection)
    
    def get_total_word_count(self) -> int:
        """Calculate total word count including subsections"""
        count = len(self.content.split()) if self.content else 0
        for subsection in self.subsections:
            count += subsection.get_total_word_count()
        return count
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'id': self.id,
            'section_type': self.section_type.value,
            'title': self.title,
            'content': self.content,
            'subsections': [sub.to_dict() for sub in self.subsections],
            'metadata': self.metadata,
            'word_count_target': self.word_count_target,
            'style_requirements': self.style_requirements,
            'citations': self.citations
        }


@dataclass
class DocumentStructure:
    """Represents the overall structure of a document"""
    document_type: DocumentType
    title: str
    sections: List[DocumentSection] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    style_guide: WritingStyle = WritingStyle.BUSINESS_PROFESSIONAL
    target_length: Optional[int] = None
    formatting_requirements: Dict[str, Any] = field(default_factory=dict)
    
    def add_section(self, section: DocumentSection):
        """Add a section to the document"""
        self.sections.append(section)
    
    def get_section_by_type(self, section_type: SectionType) -> Optional[DocumentSection]:
        """Get section by type"""
        for section in self.sections:
            if section.section_type == section_type:
                return section
        return None
    
    def get_total_word_count(self) -> int:
        """Calculate total document word count"""
        return sum(section.get_total_word_count() for section in self.sections)


class DocumentTemplate(ABC):
    """Abstract base class for document templates"""
    
    def __init__(self, document_type: DocumentType, style: WritingStyle):
        self.document_type = document_type
        self.style = style
        self.template_sections = []
        self.requirements = {}
        self._initialize_template()
    
    @abstractmethod
    def _initialize_template(self):
        """Initialize template-specific sections and requirements"""
        pass
    
    @abstractmethod
    def create_structure(self, context: Dict[str, Any]) -> DocumentStructure:
        """Create document structure from context"""
        pass
    
    def validate_structure(self, structure: DocumentStructure) -> List[str]:
        """Validate document structure against template requirements"""
        issues = []
        
        # Check required sections
        required_sections = self.requirements.get('required_sections', [])
        existing_types = {section.section_type for section in structure.sections}
        
        for required_type in required_sections:
            if required_type not in existing_types:
                issues.append(f"Missing required section: {required_type.value}")
        
        # Check word count requirements
        if structure.target_length:
            actual_count = structure.get_total_word_count()
            target = structure.target_length
            if actual_count < target * 0.8 or actual_count > target * 1.2:
                issues.append(f"Word count {actual_count} outside target range {target}±20%")
        
        return issues


class LegalComplaintTemplate(DocumentTemplate):
    """Template for legal complaints"""
    
    def _initialize_template(self):
        self.template_sections = [
            SectionType.INTRODUCTION,
            SectionType.FACTS,
            SectionType.LEGAL_ARGUMENT,
            SectionType.RELIEF_SOUGHT
        ]
        
        self.requirements = {
            'required_sections': self.template_sections,
            'min_word_count': 2000,
            'max_word_count': 10000,
            'citation_style': 'bluebook',
            'formatting': 'legal_standard'
        }
    
    def create_structure(self, context: Dict[str, Any]) -> DocumentStructure:
        """Create legal complaint structure"""
        case_name = context.get('case_name', 'Unknown Case')
        
        structure = DocumentStructure(
            document_type=self.document_type,
            title=f"Complaint - {case_name}",
            style_guide=WritingStyle.FORMAL_LEGAL,
            target_length=5000
        )
        
        # Introduction section
        intro = DocumentSection(
            id="intro",
            section_type=SectionType.INTRODUCTION,
            title="Introduction",
            word_count_target=500,
            style_requirements=["formal_tone", "jurisdiction_statement"]
        )
        structure.add_section(intro)
        
        # Facts section
        facts = DocumentSection(
            id="facts",
            section_type=SectionType.FACTS,
            title="Statement of Facts",
            word_count_target=2000,
            style_requirements=["chronological_order", "factual_tone"]
        )
        structure.add_section(facts)
        
        # Legal argument section
        legal_arg = DocumentSection(
            id="legal_argument",
            section_type=SectionType.LEGAL_ARGUMENT,
            title="Legal Arguments",
            word_count_target=2000,
            style_requirements=["legal_precedents", "statutory_citations"]
        )
        structure.add_section(legal_arg)
        
        # Relief sought section
        relief = DocumentSection(
            id="relief",
            section_type=SectionType.RELIEF_SOUGHT,
            title="Prayer for Relief",
            word_count_target=500,
            style_requirements=["specific_requests", "legal_remedies"]
        )
        structure.add_section(relief)
        
        return structure


class BusinessProposalTemplate(DocumentTemplate):
    """Template for business proposals"""
    
    def _initialize_template(self):
        self.template_sections = [
            SectionType.EXECUTIVE_SUMMARY,
            SectionType.BACKGROUND,
            SectionType.METHODOLOGY,
            SectionType.FINANCIAL_PROJECTIONS,
            SectionType.RECOMMENDATIONS
        ]
        
        self.requirements = {
            'required_sections': self.template_sections,
            'min_word_count': 1500,
            'max_word_count': 8000,
            'formatting': 'business_standard',
            'include_charts': True
        }
    
    def create_structure(self, context: Dict[str, Any]) -> DocumentStructure:
        """Create business proposal structure"""
        proposal_title = context.get('proposal_title', 'Business Proposal')
        
        structure = DocumentStructure(
            document_type=self.document_type,
            title=proposal_title,
            style_guide=WritingStyle.BUSINESS_PROFESSIONAL,
            target_length=4000
        )
        
        # Executive summary
        exec_summary = DocumentSection(
            id="exec_summary",
            section_type=SectionType.EXECUTIVE_SUMMARY,
            title="Executive Summary",
            word_count_target=500,
            style_requirements=["concise", "compelling", "key_points"]
        )
        structure.add_section(exec_summary)
        
        # Background
        background = DocumentSection(
            id="background",
            section_type=SectionType.BACKGROUND,
            title="Background and Opportunity",
            word_count_target=800,
            style_requirements=["market_analysis", "problem_statement"]
        )
        structure.add_section(background)
        
        # Methodology/Approach
        methodology = DocumentSection(
            id="methodology",
            section_type=SectionType.METHODOLOGY,
            title="Proposed Approach",
            word_count_target=1200,
            style_requirements=["detailed_steps", "timeline", "deliverables"]
        )
        structure.add_section(methodology)
        
        # Financial projections
        financials = DocumentSection(
            id="financials",
            section_type=SectionType.FINANCIAL_PROJECTIONS,
            title="Financial Projections",
            word_count_target=800,
            style_requirements=["budget_breakdown", "roi_analysis", "cost_benefit"]
        )
        structure.add_section(financials)
        
        # Recommendations
        recommendations = DocumentSection(
            id="recommendations",
            section_type=SectionType.RECOMMENDATIONS,
            title="Recommendations and Next Steps",
            word_count_target=700,
            style_requirements=["actionable_items", "timeline", "success_metrics"]
        )
        structure.add_section(recommendations)
        
        return structure


class WhitePaperTemplate(DocumentTemplate):
    """Template for white papers"""
    
    def _initialize_template(self):
        self.template_sections = [
            SectionType.EXECUTIVE_SUMMARY,
            SectionType.INTRODUCTION,
            SectionType.BACKGROUND,
            SectionType.ANALYSIS,
            SectionType.FINDINGS,
            SectionType.RECOMMENDATIONS,
            SectionType.CONCLUSION
        ]
        
        self.requirements = {
            'required_sections': self.template_sections,
            'min_word_count': 3000,
            'max_word_count': 15000,
            'citation_style': 'academic',
            'peer_review': True
        }
    
    def create_structure(self, context: Dict[str, Any]) -> DocumentStructure:
        """Create white paper structure"""
        paper_title = context.get('paper_title', 'White Paper')
        
        structure = DocumentStructure(
            document_type=self.document_type,
            title=paper_title,
            style_guide=WritingStyle.ACADEMIC_RESEARCH,
            target_length=8000
        )
        
        # Executive summary
        exec_summary = DocumentSection(
            id="exec_summary",
            section_type=SectionType.EXECUTIVE_SUMMARY,
            title="Executive Summary",
            word_count_target=600,
            style_requirements=["comprehensive_overview", "key_findings"]
        )
        structure.add_section(exec_summary)
        
        # Introduction
        introduction = DocumentSection(
            id="introduction",
            section_type=SectionType.INTRODUCTION,
            title="Introduction",
            word_count_target=800,
            style_requirements=["problem_definition", "scope", "objectives"]
        )
        structure.add_section(introduction)
        
        # Background
        background = DocumentSection(
            id="background",
            section_type=SectionType.BACKGROUND,
            title="Background and Context",
            word_count_target=1500,
            style_requirements=["literature_review", "current_state", "historical_context"]
        )
        structure.add_section(background)
        
        # Analysis
        analysis = DocumentSection(
            id="analysis",
            section_type=SectionType.ANALYSIS,
            title="Analysis",
            word_count_target=3000,
            style_requirements=["methodology", "data_analysis", "critical_evaluation"]
        )
        structure.add_section(analysis)
        
        # Findings
        findings = DocumentSection(
            id="findings",
            section_type=SectionType.FINDINGS,
            title="Key Findings",
            word_count_target=1500,
            style_requirements=["evidence_based", "clear_presentation", "significance"]
        )
        structure.add_section(findings)
        
        # Recommendations
        recommendations = DocumentSection(
            id="recommendations",
            section_type=SectionType.RECOMMENDATIONS,
            title="Recommendations",
            word_count_target=800,
            style_requirements=["actionable", "evidence_based", "prioritized"]
        )
        structure.add_section(recommendations)
        
        # Conclusion
        conclusion = DocumentSection(
            id="conclusion",
            section_type=SectionType.CONCLUSION,
            title="Conclusion",
            word_count_target=500,
            style_requirements=["summary", "implications", "future_research"]
        )
        structure.add_section(conclusion)
        
        return structure


class SandwichWritingModel:
    """
    Implements the 1-3-1 sandwich writing model with recursive structuring
    1 opening section, 3 main body sections, 1 closing section
    """
    
    def __init__(self):
        self.model_pattern = {
            'opening': 1,
            'body': 3,
            'closing': 1
        }
    
    def apply_model(self, structure: DocumentStructure) -> DocumentStructure:
        """Apply 1-3-1 sandwich model to document structure"""
        sections = structure.sections
        
        if len(sections) < 5:
            logger.warning("Not enough sections for 1-3-1 model, keeping original structure")
            return structure
        
        # Reorganize sections according to 1-3-1 model
        opening_sections = []
        body_sections = []
        closing_sections = []
        
        # Classify sections
        for section in sections:
            if section.section_type in [SectionType.INTRODUCTION, SectionType.EXECUTIVE_SUMMARY]:
                opening_sections.append(section)
            elif section.section_type in [SectionType.CONCLUSION, SectionType.RECOMMENDATIONS]:
                closing_sections.append(section)
            else:
                body_sections.append(section)
        
        # Apply recursive structuring to body sections
        if len(body_sections) > 3:
            body_sections = self._create_recursive_structure(body_sections)
        
        # Ensure we have exactly 3 body sections for the model
        while len(body_sections) < 3:
            # Split largest section
            largest = max(body_sections, key=lambda s: s.get_total_word_count())
            if largest.subsections:
                new_section = DocumentSection(
                    id=f"{largest.id}_split",
                    section_type=largest.section_type,
                    title=f"{largest.title} (Part 2)",
                    subsections=largest.subsections[len(largest.subsections)//2:]
                )
                largest.subsections = largest.subsections[:len(largest.subsections)//2]
                body_sections.append(new_section)
            else:
                break
        
        # Reconstruct structure
        new_structure = DocumentStructure(
            document_type=structure.document_type,
            title=structure.title,
            style_guide=structure.style_guide,
            target_length=structure.target_length,
            metadata=structure.metadata,
            formatting_requirements=structure.formatting_requirements
        )
        
        # Add sections in 1-3-1 order
        if opening_sections:
            new_structure.add_section(opening_sections[0])
        
        for i, section in enumerate(body_sections[:3]):
            new_structure.add_section(section)
        
        if closing_sections:
            new_structure.add_section(closing_sections[0])
        
        return new_structure
    
    def _create_recursive_structure(self, sections: List[DocumentSection]) -> List[DocumentSection]:
        """Create recursive 1-3-1 structure within sections"""
        if len(sections) <= 3:
            return sections
        
        # Group sections into 3 main categories
        groups = [[], [], []]
        for i, section in enumerate(sections):
            groups[i % 3].append(section)
        
        # Create 3 main sections with subsections
        main_sections = []
        for i, group in enumerate(groups):
            if not group:
                continue
                
            main_section = DocumentSection(
                id=f"main_section_{i+1}",
                section_type=group[0].section_type,
                title=f"Section {i+1}",
                subsections=group
            )
            main_sections.append(main_section)
        
        return main_sections


class DocumentTypeFramework:
    """Main framework for managing document types and generation"""
    
    def __init__(self):
        self.templates = {}
        self.sandwich_model = SandwichWritingModel()
        self._register_default_templates()
    
    def _register_default_templates(self):
        """Register default document templates"""
        self.templates[DocumentType.LEGAL_COMPLAINT] = LegalComplaintTemplate(
            DocumentType.LEGAL_COMPLAINT, WritingStyle.FORMAL_LEGAL
        )
        self.templates[DocumentType.BUSINESS_PROPOSAL] = BusinessProposalTemplate(
            DocumentType.BUSINESS_PROPOSAL, WritingStyle.BUSINESS_PROFESSIONAL
        )
        self.templates[DocumentType.WHITE_PAPER] = WhitePaperTemplate(
            DocumentType.WHITE_PAPER, WritingStyle.ACADEMIC_RESEARCH
        )
    
    def register_template(self, document_type: DocumentType, template: DocumentTemplate):
        """Register a custom document template"""
        self.templates[document_type] = template
        logger.info(f"Registered template for {document_type.value}")
    
    def create_document_structure(self, document_type: DocumentType, 
                                context: Dict[str, Any],
                                apply_sandwich_model: bool = True) -> DocumentStructure:
        """Create document structure using appropriate template"""
        if document_type not in self.templates:
            raise ValueError(f"No template registered for {document_type.value}")
        
        template = self.templates[document_type]
        structure = template.create_structure(context)
        
        if apply_sandwich_model:
            structure = self.sandwich_model.apply_model(structure)
        
        # Validate structure
        issues = template.validate_structure(structure)
        if issues:
            logger.warning(f"Structure validation issues: {issues}")
            structure.metadata['validation_issues'] = issues
        
        return structure
    
    def get_template_requirements(self, document_type: DocumentType) -> Dict[str, Any]:
        """Get requirements for a document type"""
        if document_type not in self.templates:
            return {}
        return self.templates[document_type].requirements
    
    def validate_document(self, structure: DocumentStructure) -> Dict[str, Any]:
        """Validate a complete document structure"""
        validation_result = {
            'is_valid': True,
            'issues': [],
            'warnings': [],
            'suggestions': []
        }
        
        template = self.templates.get(structure.document_type)
        if template:
            issues = template.validate_structure(structure)
            validation_result['issues'].extend(issues)
            if issues:
                validation_result['is_valid'] = False
        
        # Check 1-3-1 model compliance
        if len(structure.sections) != 5:
            validation_result['warnings'].append(
                f"Document has {len(structure.sections)} sections, 1-3-1 model recommends 5"
            )
        
        # Check word count distribution
        total_words = structure.get_total_word_count()
        if total_words > 0:
            section_distribution = []
            for section in structure.sections:
                percentage = (section.get_total_word_count() / total_words) * 100
                section_distribution.append(percentage)
            
            # Opening and closing should be ~15-20% each, body sections ~20-25% each
            if len(section_distribution) >= 5:
                if section_distribution[0] < 10 or section_distribution[0] > 30:
                    validation_result['suggestions'].append(
                        "Opening section word count may be unbalanced"
                    )
                if section_distribution[-1] < 10 or section_distribution[-1] > 30:
                    validation_result['suggestions'].append(
                        "Closing section word count may be unbalanced"
                    )
        
        return validation_result
    
    def export_structure(self, structure: DocumentStructure, format: str = 'json') -> str:
        """Export document structure to specified format"""
        if format == 'json':
            export_data = {
                'document_type': structure.document_type.value,
                'title': structure.title,
                'style_guide': structure.style_guide.value,
                'target_length': structure.target_length,
                'metadata': structure.metadata,
                'formatting_requirements': structure.formatting_requirements,
                'sections': [section.to_dict() for section in structure.sections],
                'total_word_count': structure.get_total_word_count(),
                'export_timestamp': datetime.now().isoformat()
            }
            return json.dumps(export_data, indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def import_structure(self, data: str, format: str = 'json') -> DocumentStructure:
        """Import document structure from specified format"""
        if format == 'json':
            import_data = json.loads(data)
            
            structure = DocumentStructure(
                document_type=DocumentType(import_data['document_type']),
                title=import_data['title'],
                style_guide=WritingStyle(import_data['style_guide']),
                target_length=import_data.get('target_length'),
                metadata=import_data.get('metadata', {}),
                formatting_requirements=import_data.get('formatting_requirements', {})
            )
            
            # Reconstruct sections
            for section_data in import_data.get('sections', []):
                section = self._reconstruct_section(section_data)
                structure.add_section(section)
            
            return structure
        else:
            raise ValueError(f"Unsupported import format: {format}")
    
    def _reconstruct_section(self, section_data: Dict[str, Any]) -> DocumentSection:
        """Reconstruct section from dictionary data"""
        section = DocumentSection(
            id=section_data['id'],
            section_type=SectionType(section_data['section_type']),
            title=section_data['title'],
            content=section_data.get('content', ''),
            metadata=section_data.get('metadata', {}),
            word_count_target=section_data.get('word_count_target'),
            style_requirements=section_data.get('style_requirements', []),
            citations=section_data.get('citations', [])
        )
        
        # Reconstruct subsections
        for subsection_data in section_data.get('subsections', []):
            subsection = self._reconstruct_section(subsection_data)
            section.add_subsection(subsection)
        
        return section


# Global framework instance
document_framework = DocumentTypeFramework()