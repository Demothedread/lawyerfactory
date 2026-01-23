"""
# Script Name: __init__.py
# Description: Post-Production Module for Legal Document Processing  This module provides comprehensive post-production capabilities for legal documents including fact verification, citation validation, and professional PDF generation.
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Core
#   - Group Tags: null
Post-Production Module for Legal Document Processing

This module provides comprehensive post-production capabilities for legal documents
including fact verification, citation validation, and professional PDF generation.
"""

from .citations import (
    BluebookValidator,
    CitationError,
    CitationReport,
    CitationStatus,
    CitationType,
    CitationValidationResult,
    get_citation_examples,
    validate_citations_quick,
)
from .pdf_generator import (
    DocumentFormat,
    DocumentMetadata,
    FormattingOptions,
    LegalPDFGenerator,
    PageSize,
    PDFGenerationResult,
    generate_complaint_pdf,
    generate_legal_pdf,
    get_formatting_presets,
)
from .verification import (
    FactChecker,
    FactStatus,
    FactVerificationResult,
    VerificationLevel,
    VerificationReport,
    verify_document_comprehensive,
    verify_document_quick,
)
from .deliverables import (
    CourtPacketArtifacts,
    CourtPacketInputs,
    PostProductionProtocol,
    build_cover_sheet_text,
    build_supplemental_evidence_index,
    build_table_of_authorities,
)

__all__ = [
    # Verification module
    "FactChecker",
    "VerificationLevel",
    "FactStatus",
    "FactVerificationResult",
    "VerificationReport",
    "verify_document_quick",
    "verify_document_comprehensive",
    # Deliverables module
    "CourtPacketArtifacts",
    "CourtPacketInputs",
    "PostProductionProtocol",
    "build_cover_sheet_text",
    "build_supplemental_evidence_index",
    "build_table_of_authorities",
    # Citations module
    "BluebookValidator",
    "CitationType",
    "CitationStatus",
    "CitationError",
    "CitationValidationResult",
    "CitationReport",
    "validate_citations_quick",
    "get_citation_examples",
    # PDF generator module
    "LegalPDFGenerator",
    "DocumentFormat",
    "PageSize",
    "DocumentMetadata",
    "FormattingOptions",
    "PDFGenerationResult",
    "generate_legal_pdf",
    "generate_complaint_pdf",
    "get_formatting_presets",
]

__version__ = "1.0.0"
__author__ = "LawyerFactory Development Team"
