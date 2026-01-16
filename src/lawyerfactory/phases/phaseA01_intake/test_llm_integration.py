"""
Integration Tests for LLM-powered Evidence Processing Functions

This module tests the LLM integration functions in assessor.py,
including fallback mechanisms and error handling.
"""

import json
from pathlib import Path
import tempfile
from unittest.mock import MagicMock, patch

import pytest

# Import the functions to test
from .assessor import (
    LLM_INTEGRATION_AVAILABLE,
    llm_classify_evidence,
    llm_extract_metadata,
    llm_summarize_text,
    simple_categorize,
)
from .enhanced_evidence_assessor import (
    llm_categorize_document,
    llm_extract_document_metadata,
    llm_generate_summary,
)


class TestSimpleCategorize:
    """Test the enhanced simple_categorize function with keyword arrays."""

    def test_contract_keywords(self):
        """Test that contract-related keywords trigger contract category."""
        contract_texts = [
            "This contract agreement between parties",
            "Terms and conditions shall apply",
            "The parties hereby agree to the following provisions",
            "Breach of contract terms",
            "Contract amendment and modification",
        ]
        for text in contract_texts:
            assert simple_categorize(text) == "contract"

    def test_litigation_keywords(self):
        """Test that litigation-related keywords trigger litigation category."""
        litigation_texts = [
            "Plaintiff files complaint against defendant",
            "Motion for summary judgment",
            "Discovery deposition scheduled",
            "Trial court jurisdiction",
            "Appeal of the verdict",
        ]
        for text in litigation_texts:
            assert simple_categorize(text) == "litigation"

    def test_financial_keywords(self):
        """Test that financial keywords trigger financial category."""
        financial_texts = [
            "Invoice for services rendered",
            "Payment receipt acknowledged",
            "Financial statement balance",
            "Tax audit compliance",
            "Accounting ledger entries",
        ]
        for text in financial_texts:
            assert simple_categorize(text) == "financial"

    def test_correspondence_keywords(self):
        """Test that correspondence keywords trigger correspondence category."""
        correspondence_texts = [
            "Email correspondence regarding the matter",
            "Official memorandum issued",
            "Press release announcement",
            "Business letter communication",
        ]
        for text in correspondence_texts:
            assert simple_categorize(text) == "correspondence"

    def test_regulatory_keywords(self):
        """Test that regulatory keywords trigger regulatory category."""
        regulatory_texts = [
            "Compliance with regulations required",
            "Policy and procedure guidelines",
            "Legal requirements mandate",
            "Statutory compliance standards",
        ]
        for text in regulatory_texts:
            assert simple_categorize(text) == "regulatory"

    def test_employment_keywords(self):
        """Test that employment keywords trigger employment category."""
        employment_texts = [
            "Employment contract terms",
            "Employee handbook policies",
            "Job position requirements",
            "Salary compensation package",
        ]
        for text in employment_texts:
            assert simple_categorize(text) == "employment"

    def test_real_estate_keywords(self):
        """Test that real estate keywords trigger real_estate category."""
        real_estate_texts = [
            "Property lease agreement",
            "Real estate transaction",
            "Mortgage deed recorded",
            "Tenant landlord relationship",
        ]
        for text in real_estate_texts:
            assert simple_categorize(text) == "real_estate"

    def test_ip_keywords(self):
        """Test that IP keywords trigger intellectual_property category."""
        ip_texts = [
            "Patent application filed",
            "Trademark registration",
            "Copyright infringement claim",
            "Non-disclosure agreement",
        ]
        for text in ip_texts:
            assert simple_categorize(text) == "intellectual_property"

    def test_medical_keywords(self):
        """Test that medical keywords trigger medical category."""
        medical_texts = [
            "Medical treatment records",
            "Patient health information",
            "Hospital medical charts",
            "Insurance claim processing",
        ]
        for text in medical_texts:
            assert simple_categorize(text) == "medical"

    def test_general_fallback(self):
        """Test that non-matching text falls back to general category."""
        general_texts = [
            "This is a general document",
            "Some random content here",
            "",
            "No specific legal keywords",
        ]
        for text in general_texts:
            assert simple_categorize(text) == "general"

    def test_empty_input(self):
        """Test handling of empty or None input."""
        assert simple_categorize("") == "general"
        assert simple_categorize(None) == "general"


class TestLLMIntegration:
    """Test LLM integration functions and fallback mechanisms."""

    def test_llm_categorize_fallback(self):
        """Test that llm_categorize_document falls back when LLM unavailable."""
        if not LLM_INTEGRATION_AVAILABLE:
            # Test fallback behavior
            result = llm_categorize_document(
                "This is a contract document", "contract.txt", "John Doe"
            )
            assert "document_type" in result
            assert result["document_type"] == "contract"

    def test_llm_extract_metadata_fallback(self):
        """Test that llm_extract_document_metadata falls back when LLM unavailable."""
        if not LLM_INTEGRATION_AVAILABLE:
            result = llm_extract_document_metadata(
                "Sample document content", "sample.txt"
            )
            assert "title" in result
            assert "summary" in result
            assert result["title"] == "sample.txt"

    def test_llm_generate_summary_fallback(self):
        """Test that llm_generate_summary falls back when LLM unavailable."""
        if not LLM_INTEGRATION_AVAILABLE:
            result = llm_generate_summary(
                "This is a long document with multiple sentences. It contains important information."
            )
            assert isinstance(result, str)
            assert len(result) > 0

    @patch("src.lawyerfactory.phases.01_intake.llm_integration.llm_classify_evidence")
    def test_llm_categorize_with_mock(self, mock_classify):
        """Test llm_categorize_document with mocked LLM service."""
        mock_classify.return_value = {
            "success": True,
            "classification": {
                "evidence_type": "PRIMARY",
                "specific_category": "Witness Statement",
                "confidence_score": 0.95,
                "reasoning": "Document contains witness testimony",
                "key_characteristics": ["First-hand account", "Detailed testimony"],
            },
        }

        result = llm_categorize_document(
            "Witness testimony content", "witness.txt", "Jane Smith"
        )

        assert result["document_type"] == "Witness Statement"
        assert result["authority_level"] == "primary"
        assert result["confidence_score"] == 0.95
        assert result["evidence_type"] == "PRIMARY"

    @patch("src.lawyerfactory.phases.01_intake.llm_integration.llm_extract_metadata")
    def test_llm_extract_metadata_with_mock(self, mock_extract):
        """Test llm_extract_document_metadata with mocked LLM service."""
        mock_extract.return_value = {
            "title": "Legal Brief",
            "author": "Attorney Smith",
            "date": "2024-01-15",
            "parties_involved": ["Plaintiff Corp", "Defendant LLC"],
            "key_issues": ["Breach of contract", "Damages"],
            "summary": "This brief argues for breach of contract damages.",
            "relevance_score": 0.9,
            "legal_context": "Commercial litigation",
        }

        result = llm_extract_document_metadata("Legal brief content", "brief.pdf")

        assert result["title"] == "Legal Brief"
        assert result["author"] == "Attorney Smith"
        assert "Plaintiff Corp" in result["parties_involved"]
        assert result["relevance_score"] == 0.9


class TestFileProcessing:
    """Test file processing functions."""

    def test_ingest_files_with_temp_files(self):
        """Test llm_enhanced_ingest_files with temporary files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            test_files = []

            # Contract file
            contract_file = Path(temp_dir) / "contract.txt"
            contract_file.write_text(
                "This is a contract agreement between the parties. Terms and conditions apply."
            )
            test_files.append(str(contract_file))

            # Litigation file
            litigation_file = Path(temp_dir) / "complaint.txt"
            litigation_file.write_text(
                "Plaintiff files complaint against defendant in court."
            )
            test_files.append(str(litigation_file))

            # General file
            general_file = Path(temp_dir) / "general.txt"
            general_file.write_text(
                "This is a general document with no specific legal keywords."
            )
            test_files.append(str(general_file))

            # Test file processing
            results = llm_enhanced_ingest_files(test_files)

            assert len(results) == 3

            # Check contract file
            contract_result = next(
                r for r in results if r["filename"] == "contract.txt"
            )
            assert contract_result["categorization"]["document_type"] == "contract"

            # Check litigation file
            litigation_result = next(
                r for r in results if r["filename"] == "complaint.txt"
            )
            assert litigation_result["categorization"]["document_type"] == "litigation"

            # Check general file
            general_result = next(r for r in results if r["filename"] == "general.txt")
            assert general_result["categorization"]["document_type"] == "general"

    def test_ingest_files_nonexistent(self):
        """Test llm_enhanced_ingest_files with nonexistent files."""
        nonexistent_files = ["/nonexistent/file1.txt", "/nonexistent/file2.txt"]
        results = llm_enhanced_ingest_files(nonexistent_files)
        assert len(results) == 0  # Should handle errors gracefully


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_malformed_content(self):
        """Test handling of malformed or unusual content."""
        malformed_texts = [
            "!!!@#$%^&*()",
            "\n\n\n\n\n",
            "a" * 10000,  # Very long text
            "合同",  # Non-English text
            "🤖🚀💼",  # Emojis
        ]

        for text in malformed_texts:
            result = simple_categorize(text)
            assert isinstance(result, str)
            assert result in [
                "general",
                "contract",
                "litigation",
                "financial",
                "correspondence",
                "regulatory",
                "employment",
                "real_estate",
                "intellectual_property",
                "medical",
            ]

    def test_unicode_handling(self):
        """Test handling of Unicode characters."""
        unicode_text = "This is a contract with special characters: àáâãäå"
        result = simple_categorize(unicode_text)
        assert result == "contract"  # Should still detect contract keyword


if __name__ == "__main__":
    # Run basic tests
    test_instance = TestSimpleCategorize()

    print("Running simple_categorize tests...")

    test_instance.test_contract_keywords()
    print("✓ Contract keywords test passed")

    test_instance.test_litigation_keywords()
    print("✓ Litigation keywords test passed")

    test_instance.test_financial_keywords()
    print("✓ Financial keywords test passed")

    test_instance.test_correspondence_keywords()
    print("✓ Correspondence keywords test passed")

    test_instance.test_regulatory_keywords()
    print("✓ Regulatory keywords test passed")

    test_instance.test_employment_keywords()
    print("✓ Employment keywords test passed")

    test_instance.test_real_estate_keywords()
    print("✓ Real estate keywords test passed")

    test_instance.test_ip_keywords()
    print("✓ IP keywords test passed")

    test_instance.test_medical_keywords()
    print("✓ Medical keywords test passed")

    test_instance.test_general_fallback()
    print("✓ General fallback test passed")

    test_instance.test_empty_input()
    print("✓ Empty input test passed")

    print("\nAll simple_categorize tests passed! ✅")

    # Test LLM integration availability
    print(f"\nLLM Integration Available: {LLM_INTEGRATION_AVAILABLE}")

    if LLM_INTEGRATION_AVAILABLE:
        print("LLM functions are available for enhanced processing")
    else:
        print("Using fallback mechanisms - LLM functions not available")
