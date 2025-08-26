"""
# Script Name: pdf_generator.py
# Description: Post-Production PDF Generation Module  This module provides professional PDF generation capabilities for legal documents with proper formatting, headers, footers, and legal document structure.
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Core
#   - Group Tags: null
Post-Production PDF Generation Module

This module provides professional PDF generation capabilities for legal documents
with proper formatting, headers, footers, and legal document structure.
"""

import logging
import os
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import tempfile

logger = logging.getLogger(__name__)

# Try to import PDF generation libraries
try:
    from reportlab.lib.pagesizes import letter, legal
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    from reportlab.platypus import Table, TableStyle
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
    REPORTLAB_AVAILABLE = True
except ImportError:
    logger.warning("ReportLab not available. PDF generation will use fallback method.")
    REPORTLAB_AVAILABLE = False


class DocumentFormat(Enum):
    """Legal document formats"""
    COMPLAINT = "complaint"
    MOTION = "motion"
    BRIEF = "brief"
    MEMORANDUM = "memorandum"
    ORDER = "order"
    LETTER = "letter"
    GENERAL = "general"


class PageSize(Enum):
    """Standard page sizes"""
    LETTER = "letter"
    LEGAL = "legal"
    A4 = "a4"


@dataclass
class DocumentMetadata:
    """Metadata for legal document"""
    title: str
    case_name: Optional[str] = None
    case_number: Optional[str] = None
    court: Optional[str] = None
    attorney_name: Optional[str] = None
    attorney_bar_number: Optional[str] = None
    law_firm: Optional[str] = None
    party_represented: Optional[str] = None
    date_created: Optional[str] = None
    document_type: DocumentFormat = DocumentFormat.GENERAL


@dataclass
class FormattingOptions:
    """PDF formatting options"""
    page_size: PageSize = PageSize.LETTER
    font_name: str = "Times-Roman"
    font_size: int = 12
    line_spacing: float = 1.5
    margin_top: float = 1.0
    margin_bottom: float = 1.0
    margin_left: float = 1.25
    margin_right: float = 1.0
    include_page_numbers: bool = True
    include_header: bool = True
    include_footer: bool = True
    double_space_pleadings: bool = True


@dataclass
class PDFGenerationResult:
    """Result of PDF generation"""
    success: bool
    file_path: Optional[str]
    file_size: Optional[int]
    page_count: Optional[int]
    error_message: Optional[str]
    warnings: List[str]
    generation_time: float
    metadata: DocumentMetadata


class LegalPDFGenerator:
    """
    Professional PDF generator for legal documents.
    
    Generates properly formatted PDFs with legal document standards including
    appropriate spacing, headers, footers, and court formatting requirements.
    """
    
    def __init__(self, output_directory: Optional[str] = None):
        """Initialize the PDF generator"""
        self.output_directory = output_directory or tempfile.gettempdir()
        self.style_cache = {}
        self._setup_styles()
        logger.info(f"LegalPDFGenerator initialized with output directory: {self.output_directory}")
    
    def _setup_styles(self):
        """Setup document styles"""
        if REPORTLAB_AVAILABLE:
            self.styles = getSampleStyleSheet()
            
            # Legal document specific styles
            self.styles.add(ParagraphStyle(
                name='LegalTitle',
                parent=self.styles['Heading1'],
                fontSize=14,
                spaceAfter=12,
                alignment=TA_CENTER,
                fontName='Times-Bold'
            ))
            
            self.styles.add(ParagraphStyle(
                name='LegalHeading',
                parent=self.styles['Heading2'],
                fontSize=12,
                spaceAfter=6,
                spaceBefore=12,
                alignment=TA_CENTER,
                fontName='Times-Bold'
            ))
            
            self.styles.add(ParagraphStyle(
                name='LegalBody',
                parent=self.styles['Normal'],
                fontSize=12,
                spaceAfter=12,
                spaceBefore=6,
                alignment=TA_JUSTIFY,
                fontName='Times-Roman',
                leading=18  # 1.5 line spacing
            ))
            
            self.styles.add(ParagraphStyle(
                name='LegalBodyDouble',
                parent=self.styles['LegalBody'],
                leading=24  # Double spacing for pleadings
            ))
            
            self.styles.add(ParagraphStyle(
                name='Signature',
                parent=self.styles['Normal'],
                fontSize=12,
                alignment=TA_LEFT,
                fontName='Times-Roman',
                spaceAfter=6
            ))
    
    async def generate_pdf(
        self,
        content: str,
        metadata: DocumentMetadata,
        formatting: Optional[FormattingOptions] = None,
        output_filename: Optional[str] = None
    ) -> PDFGenerationResult:
        """
        Generate a PDF from document content.
        
        Args:
            content: Document content as text
            metadata: Document metadata
            formatting: Formatting options
            output_filename: Custom output filename
            
        Returns:
            PDFGenerationResult: Result of PDF generation
        """
        start_time = datetime.now()
        logger.info(f"Starting PDF generation for document: {metadata.title}")
        
        if not REPORTLAB_AVAILABLE:
            return await self._generate_fallback_pdf(content, metadata, output_filename)
        
        formatting = formatting or FormattingOptions()
        warnings = []
        
        try:
            # Generate filename if not provided
            if not output_filename:
                safe_title = "".join(c for c in metadata.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"{safe_title}_{timestamp}.pdf"
            
            # Ensure .pdf extension
            if not output_filename.endswith('.pdf'):
                output_filename += '.pdf'
            
            file_path = os.path.join(self.output_directory, output_filename)
            
            # Create PDF document
            doc = self._create_pdf_document(file_path, formatting)
            
            # Build document content
            story = []
            
            # Add header section
            if formatting.include_header:
                story.extend(self._build_header(metadata, formatting))
            
            # Add document body
            story.extend(self._build_body(content, formatting))
            
            # Add signature block
            story.extend(self._build_signature_block(metadata))
            
            # Build the PDF
            doc.build(story, onFirstPage=self._on_first_page, onLaterPages=self._on_later_pages)
            
            # Get file info
            file_size = os.path.getsize(file_path)
            page_count = self._estimate_page_count(content, formatting)
            
            generation_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"PDF generated successfully: {file_path} ({file_size} bytes, ~{page_count} pages)")
            
            return PDFGenerationResult(
                success=True,
                file_path=file_path,
                file_size=file_size,
                page_count=page_count,
                error_message=None,
                warnings=warnings,
                generation_time=generation_time,
                metadata=metadata
            )
            
        except Exception as e:
            generation_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"PDF generation failed: {str(e)}")
            
            return PDFGenerationResult(
                success=False,
                file_path=None,
                file_size=None,
                page_count=None,
                error_message=str(e),
                warnings=warnings,
                generation_time=generation_time,
                metadata=metadata
            )
    
    def _create_pdf_document(self, file_path: str, formatting: FormattingOptions) -> SimpleDocTemplate:
        """Create PDF document with proper formatting"""
        
        # Set page size
        if formatting.page_size == PageSize.LETTER:
            page_size = letter
        elif formatting.page_size == PageSize.LEGAL:
            page_size = legal
        else:  # A4
            page_size = (595.276, 841.890)  # A4 in points
        
        # Create document
        doc = SimpleDocTemplate(
            file_path,
            pagesize=page_size,
            topMargin=formatting.margin_top * inch,
            bottomMargin=formatting.margin_bottom * inch,
            leftMargin=formatting.margin_left * inch,
            rightMargin=formatting.margin_right * inch
        )
        
        return doc
    
    def _build_header(self, metadata: DocumentMetadata, formatting: FormattingOptions) -> List:
        """Build document header section"""
        story = []
        
        # Court header for legal documents
        if metadata.court and metadata.document_type != DocumentFormat.LETTER:
            court_header = Paragraph(metadata.court.upper(), self.styles['LegalTitle'])
            story.append(court_header)
            story.append(Spacer(1, 12))
        
        # Case caption
        if metadata.case_name and metadata.case_number:
            # Create case caption table
            case_data = [
                [metadata.case_name, f"Case No. {metadata.case_number}"],
                ["", ""],
                [f"{metadata.title}", ""]
            ]
            
            case_table = Table(case_data, colWidths=[4*inch, 2*inch])
            case_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTNAME', (0, 0), (-1, -1), 'Times-Roman'),
                ('FONTSIZE', (0, 0), (-1, -1), 12),
                ('LINEBELOW', (0, 1), (0, 1), 1, colors.black),
                ('RIGHTPADDING', (1, 0), (1, -1), 0),
            ]))
            
            story.append(case_table)
            story.append(Spacer(1, 24))
        
        elif metadata.title:
            # Simple title for non-litigation documents
            title = Paragraph(metadata.title, self.styles['LegalTitle'])
            story.append(title)
            story.append(Spacer(1, 18))
        
        return story
    
    def _build_body(self, content: str, formatting: FormattingOptions) -> List:
        """Build document body content"""
        story = []
        
        # Choose appropriate style based on document type
        if formatting.double_space_pleadings:
            body_style = self.styles['LegalBodyDouble']
        else:
            body_style = self.styles['LegalBody']
        
        # Split content into paragraphs
        paragraphs = content.split('\n\n')
        
        for para_text in paragraphs:
            para_text = para_text.strip()
            if para_text:
                # Handle different paragraph types
                if para_text.isupper() and len(para_text) < 100:
                    # Likely a heading
                    para = Paragraph(para_text, self.styles['LegalHeading'])
                else:
                    # Regular body text
                    para = Paragraph(para_text, body_style)
                
                story.append(para)
                story.append(Spacer(1, 6))
        
        return story
    
    def _build_signature_block(self, metadata: DocumentMetadata) -> List:
        """Build signature block"""
        story = []
        
        if metadata.attorney_name or metadata.law_firm:
            story.append(Spacer(1, 36))  # Space before signature
            
            if metadata.attorney_name:
                story.append(Paragraph(f"Respectfully submitted,", self.styles['Signature']))
                story.append(Spacer(1, 36))  # Space for signature
                story.append(Paragraph(f"____________________________", self.styles['Signature']))
                story.append(Paragraph(metadata.attorney_name, self.styles['Signature']))
                
                if metadata.attorney_bar_number:
                    story.append(Paragraph(f"Bar No. {metadata.attorney_bar_number}", self.styles['Signature']))
            
            if metadata.law_firm:
                story.append(Paragraph(metadata.law_firm, self.styles['Signature']))
            
            if metadata.party_represented:
                story.append(Paragraph(f"Attorney for {metadata.party_represented}", self.styles['Signature']))
        
        return story
    
    def _on_first_page(self, canvas, doc):
        """First page formatting"""
        # Add any first-page specific formatting here
        pass
    
    def _on_later_pages(self, canvas, doc):
        """Later pages formatting"""
        # Add page numbers and running headers
        page_num = canvas.getPageNumber()
        text = f"Page {page_num}"
        canvas.drawRightString(doc.pagesize[0] - inch, 0.75 * inch, text)
    
    def _estimate_page_count(self, content: str, formatting: FormattingOptions) -> int:
        """Estimate number of pages"""
        # Rough estimation based on character count and formatting
        chars_per_line = 80  # Approximate
        lines_per_page = 45 if formatting.double_space_pleadings else 55
        
        total_chars = len(content)
        estimated_lines = total_chars / chars_per_line
        estimated_pages = max(1, int(estimated_lines / lines_per_page) + 1)
        
        return estimated_pages
    
    async def _generate_fallback_pdf(
        self,
        content: str,
        metadata: DocumentMetadata,
        output_filename: Optional[str] = None
    ) -> PDFGenerationResult:
        """Fallback PDF generation when ReportLab is not available"""
        start_time = datetime.now()
        
        try:
            # Generate a simple text file as fallback
            if not output_filename:
                safe_title = "".join(c for c in metadata.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"{safe_title}_{timestamp}.txt"
            
            file_path = os.path.join(self.output_directory, output_filename)
            
            # Create formatted text document
            formatted_content = self._format_text_document(content, metadata)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(formatted_content)
            
            file_size = os.path.getsize(file_path)
            generation_time = (datetime.now() - start_time).total_seconds()
            
            logger.warning(f"Generated text file (PDF library unavailable): {file_path}")
            
            return PDFGenerationResult(
                success=True,
                file_path=file_path,
                file_size=file_size,
                page_count=1,
                error_message=None,
                warnings=["PDF library not available, generated text file instead"],
                generation_time=generation_time,
                metadata=metadata
            )
            
        except Exception as e:
            generation_time = (datetime.now() - start_time).total_seconds()
            
            return PDFGenerationResult(
                success=False,
                file_path=None,
                file_size=None,
                page_count=None,
                error_message=f"Fallback generation failed: {str(e)}",
                warnings=["PDF library not available"],
                generation_time=generation_time,
                metadata=metadata
            )
    
    def _format_text_document(self, content: str, metadata: DocumentMetadata) -> str:
        """Format document as text with proper legal formatting"""
        lines = []
        
        # Header
        if metadata.court:
            lines.append(metadata.court.upper())
            lines.append("")
        
        if metadata.case_name and metadata.case_number:
            lines.append(f"{metadata.case_name}")
            lines.append(f"Case No. {metadata.case_number}")
            lines.append("")
            lines.append(metadata.title)
            lines.append("-" * 50)
        elif metadata.title:
            lines.append(metadata.title)
            lines.append("=" * len(metadata.title))
        
        lines.append("")
        lines.append("")
        
        # Content
        lines.append(content)
        
        # Signature block
        if metadata.attorney_name:
            lines.append("")
            lines.append("")
            lines.append("Respectfully submitted,")
            lines.append("")
            lines.append("")
            lines.append("____________________________")
            lines.append(metadata.attorney_name)
            
            if metadata.attorney_bar_number:
                lines.append(f"Bar No. {metadata.attorney_bar_number}")
            
            if metadata.law_firm:
                lines.append(metadata.law_firm)
            
            if metadata.party_represented:
                lines.append(f"Attorney for {metadata.party_represented}")
        
        return "\n".join(lines)


# Utility functions for external use
async def generate_legal_pdf(
    content: str,
    title: str,
    output_dir: Optional[str] = None,
    **metadata_kwargs
) -> PDFGenerationResult:
    """Quick PDF generation for legal documents"""
    metadata = DocumentMetadata(title=title, **metadata_kwargs)
    generator = LegalPDFGenerator(output_dir)
    return await generator.generate_pdf(content, metadata)


async def generate_complaint_pdf(
    content: str,
    case_name: str,
    case_number: str,
    court: str,
    attorney_name: str,
    output_dir: Optional[str] = None
) -> PDFGenerationResult:
    """Generate a formatted complaint PDF"""
    metadata = DocumentMetadata(
        title="COMPLAINT",
        case_name=case_name,
        case_number=case_number,
        court=court,
        attorney_name=attorney_name,
        document_type=DocumentFormat.COMPLAINT
    )
    
    formatting = FormattingOptions(
        double_space_pleadings=True,
        include_page_numbers=True
    )
    
    generator = LegalPDFGenerator(output_dir)
    return await generator.generate_pdf(content, metadata, formatting)


def get_formatting_presets() -> Dict[str, FormattingOptions]:
    """Get predefined formatting presets for common document types"""
    return {
        "complaint": FormattingOptions(
            double_space_pleadings=True,
            margin_left=1.5,
            include_page_numbers=True
        ),
        "motion": FormattingOptions(
            double_space_pleadings=True,
            margin_left=1.25,
            include_page_numbers=True
        ),
        "brief": FormattingOptions(
            double_space_pleadings=False,
            line_spacing=1.5,
            margin_left=1.25,
            include_page_numbers=True
        ),
        "letter": FormattingOptions(
            double_space_pleadings=False,
            line_spacing=1.0,
            margin_left=1.0,
            include_page_numbers=False,
            include_header=False
        )
    }