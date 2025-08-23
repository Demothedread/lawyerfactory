# Script Name: test_statement_of_facts_normalizer.py
# Description: Unit tests for StatementOfFactsGenerator normalizer and enhanced methods  Tests the normalizer's ability to handle various input formats and the robust error handling in legal fact processing.
# Relationships:
#   - Entity Type: Test
#   - Directory Group: Core
#   - Group Tags: testing
Unit tests for StatementOfFactsGenerator normalizer and enhanced methods

Tests the normalizer's ability to handle various input formats and the
robust error handling in legal fact processing.
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from src.lawyerfactory.compose.strategies.statement_of_facts import (
    StatementOfFactsGenerator, 
    FactCategory, 
    LegalFact
)


class TestStatementOfFactsNormalizer:
    """Test suite for StatementOfFactsGenerator normalizer and enhanced methods"""

    def setup_method(self):
        """Set up test fixtures"""
        self.generator = StatementOfFactsGenerator()

    def test_normalize_facts_matrix_complete_data(self):
        """Test normalizer with complete facts matrix"""
        facts_matrix = {
            "undisputed_facts": ["Fact 1", "Fact 2"],
            "disputed_facts": ["Disputed fact"],
            "procedural_facts": ["Procedural fact"],
            "case_metadata": {"case_number": "123"},
            "evidence_references": {"fact1": ["doc1.pdf"]},
            "key_events": ["Event 1"],
            "background_context": ["Background info"],
            "damages_claims": ["Damages claim"]
        }
        
        result = self.generator._normalize_facts_matrix(facts_matrix)
        
        assert isinstance(result, dict)
        assert len(result["undisputed_facts"]) == 2
        assert len(result["disputed_facts"]) == 1
        assert len(result["procedural_facts"]) == 1
        assert len(result["key_events"]) == 1
        assert len(result["background_context"]) == 1
        assert len(result["damages_claims"]) == 1

    def test_normalize_facts_matrix_empty_input(self):
        """Test normalizer with empty dict"""
        facts_matrix = {}
        
        result = self.generator._normalize_facts_matrix(facts_matrix)
        
        assert isinstance(result, dict)
        assert result["undisputed_facts"] == []
        assert result["disputed_facts"] == []
        assert result["procedural_facts"] == []
        assert result["case_metadata"] == {}
        assert result["evidence_references"] == {}

    def test_normalize_facts_matrix_invalid_input(self):
        """Test normalizer with non-dict input"""
        with patch('src.lawyerfactory.compose.strategies.statement_of_facts.logger') as mock_logger:
            result = self.generator._normalize_facts_matrix("not a dict")
            
            assert isinstance(result, dict)
            assert result["undisputed_facts"] == []
            mock_logger.warning.assert_called()

    def test_normalize_facts_matrix_string_facts(self):
        """Test normalizer converting string facts to lists"""
        facts_matrix = {
            "undisputed_facts": "single fact string",
            "disputed_facts": ["list fact"],
        }
        
        result = self.generator._normalize_facts_matrix(facts_matrix)
        
        assert result["undisputed_facts"] == ["single fact string"]
        assert result["disputed_facts"] == ["list fact"]

    def test_normalize_facts_matrix_wrong_types(self):
        """Test normalizer handling wrong data types"""
        facts_matrix = {
            "undisputed_facts": 123,  # Should be list
            "case_metadata": "should be dict",  # Should be dict
        }
        
        with patch('src.lawyerfactory.compose.strategies.statement_of_facts.logger') as mock_logger:
            result = self.generator._normalize_facts_matrix(facts_matrix)
            
            assert result["undisputed_facts"] == ["123"]  # Converted to string list
            assert result["case_metadata"] == {}  # Reset to empty dict
            mock_logger.warning.assert_called()

    def test_create_legal_fact_valid_dict(self):
        """Test _create_legal_fact with valid dictionary input"""
        fact_data = {
            "text": "Test fact text",
            "confidence": 0.9,
            "source_documents": ["doc1.pdf"],
            "date": "2024-01-01",
            "legal_significance": "important"
        }
        
        result = self.generator._create_legal_fact(
            fact_data, 1, FactCategory.MATERIAL
        )
        
        assert isinstance(result, LegalFact)
        assert result.id == "fact_001"
        assert result.text == "Test fact text."  # Should add period
        assert result.confidence == 0.9
        assert result.category == FactCategory.MATERIAL

    def test_create_legal_fact_string_input(self):
        """Test _create_legal_fact with string input"""
        fact_data = "Simple fact text"
        
        result = self.generator._create_legal_fact(
            fact_data, 2, FactCategory.BACKGROUND
        )
        
        assert isinstance(result, LegalFact)
        assert result.id == "fact_002"
        assert result.text == "Simple fact text."
        assert result.confidence == 0.8  # Default confidence
        assert result.category == FactCategory.BACKGROUND

    def test_create_legal_fact_none_input(self):
        """Test _create_legal_fact with None input"""
        result = self.generator._create_legal_fact(
            None, 3, FactCategory.DISPUTED
        )
        
        assert result is None

    def test_create_legal_fact_empty_text(self):
        """Test _create_legal_fact with empty text"""
        fact_data = {"text": "   "}  # Empty/whitespace text
        
        result = self.generator._create_legal_fact(
            fact_data, 4, FactCategory.MATERIAL
        )
        
        assert result is None

    def test_create_legal_fact_invalid_confidence(self):
        """Test _create_legal_fact with invalid confidence values"""
        fact_data = {
            "text": "Test fact",
            "confidence": 1.5  # Invalid confidence > 1
        }
        
        with patch('src.lawyerfactory.compose.strategies.statement_of_facts.logger') as mock_logger:
            result = self.generator._create_legal_fact(
                fact_data, 5, FactCategory.MATERIAL, default_confidence=0.7
            )
            
            assert result.confidence == 0.7  # Should use default
            mock_logger.warning.assert_called()

    def test_create_legal_fact_non_list_documents(self):
        """Test _create_legal_fact with non-list source documents"""
        fact_data = {
            "text": "Test fact",
            "source_documents": "single_doc.pdf"  # Should be list
        }
        
        result = self.generator._create_legal_fact(
            fact_data, 6, FactCategory.MATERIAL
        )
        
        assert result.source_documents == ["single_doc.pdf"]

    def test_populate_case_data_with_defaults_complete(self):
        """Test _populate_case_data_with_defaults with complete data"""
        case_data = {
            "plaintiff_name": "John Doe",
            "defendant_name": "Acme Corp",
            "case_number": "2024-CV-001",
            "court": "Superior Court"
        }
        
        result = self.generator._populate_case_data_with_defaults(case_data)
        
        assert result["plaintiff_name"] == "John Doe"
        assert result["defendant_name"] == "Acme Corp"
        assert result["case_number"] == "2024-CV-001"
        assert result["court"] == "Superior Court"
        # Should still have defaults for missing fields
        assert "attorney_name" in result
        assert "bar_number" in result

    def test_populate_case_data_with_defaults_empty(self):
        """Test _populate_case_data_with_defaults with empty data"""
        case_data = {}
        
        with patch('src.lawyerfactory.compose.strategies.statement_of_facts.logger') as mock_logger:
            result = self.generator._populate_case_data_with_defaults(case_data)
            
            assert "[Plaintiff Name - Please Update]" in result["plaintiff_name"]
            assert "[Defendant Name - Please Update]" in result["defendant_name"]
            assert "case_title" in result
            mock_logger.warning.assert_called()

    def test_populate_case_data_auto_generate_title(self):
        """Test auto-generation of case title"""
        case_data = {
            "plaintiff_name": "Smith Industries",
            "defendant_name": "Jones LLC"
        }
        
        result = self.generator._populate_case_data_with_defaults(case_data)
        
        assert result["case_title"] == "Smith Industries v. Jones LLC"

    def test_structure_legal_facts_error_handling(self):
        """Test _structure_legal_facts with error conditions"""
        facts_matrix = {
            "undisputed_facts": [
                "Valid fact",
                None,  # Should cause error
                {"text": "Dict fact"},  # Should work
                ""  # Empty fact should be filtered
            ]
        }
        
        with patch('src.lawyerfactory.compose.strategies.statement_of_facts.logger') as mock_logger:
            result = self.generator._structure_legal_facts(facts_matrix)
            
            assert isinstance(result, list)
            # Should have processed valid facts and skipped invalid ones
            assert len(result) >= 1  # At least the valid facts
            mock_logger.error.assert_called()  # Should log errors

    def test_structure_legal_facts_comprehensive(self):
        """Test _structure_legal_facts with all fact types"""
        facts_matrix = {
            "undisputed_facts": ["Undisputed fact 1"],
            "disputed_facts": ["Disputed fact 1"],
            "procedural_facts": ["Procedural fact 1"],
            "key_events": ["Key event 1"],
            "background_context": ["Background 1"],
            "damages_claims": [{"text": "Damages claim 1", "is_disputed": True}]
        }
        
        result = self.generator._structure_legal_facts(facts_matrix)
        
        assert isinstance(result, list)
        assert len(result) == 6  # One fact from each category
        
        # Check that categories are correctly assigned
        categories = [fact.category for fact in result]
        assert FactCategory.MATERIAL in categories
        assert FactCategory.DISPUTED in categories
        assert FactCategory.PROCEDURAL in categories
        assert FactCategory.BACKGROUND in categories
        assert FactCategory.DAMAGES in categories

    def test_format_case_caption_with_defaults(self):
        """Test _format_case_caption using populated defaults"""
        case_data = {"plaintiff_name": "Test Plaintiff"}
        
        result = self.generator._format_case_caption(case_data)
        
        assert "Test Plaintiff" in result
        assert "Plaintiff," in result
        assert "v." in result
        assert "Case No." in result

    def test_generate_parties_introduction_enhanced(self):
        """Test _generate_parties_introduction with enhanced features"""
        case_data = {
            "plaintiff_name": "ABC Corp",
            "defendant_name": "XYZ Inc",
            "case_type": "breach of contract",
            "jurisdiction_basis": "diversity of citizenship"
        }
        
        result = self.generator._generate_parties_introduction(case_data)
        
        assert "ABC Corp" in result
        assert "XYZ Inc" in result
        assert "breach of contract" in result
        assert "diversity of citizenship" in result
        assert "following facts establish" in result

    @patch('src.lawyerfactory.compose.strategies.statement_of_facts.logger')
    def test_error_logging_throughout(self, mock_logger):
        """Test that errors are properly logged throughout the system"""
        # Test with problematic data that should trigger logging
        facts_matrix = {
            "undisputed_facts": [None, "", "  ", "valid fact"]
        }
        
        result = self.generator._structure_legal_facts(facts_matrix)
        
        # Should have logged warnings/errors for invalid facts
        assert mock_logger.error.called or mock_logger.warning.called
        # Should still process valid facts
        assert len(result) >= 1

    def test_resilience_with_missing_optional_fields(self):
        """Test system resilience when optional fields are missing"""
        fact_data = {"text": "Minimal fact"}  # Only required field
        
        result = self.generator._create_legal_fact(
            fact_data, 1, FactCategory.MATERIAL
        )
        
        assert isinstance(result, LegalFact)
        assert result.text == "Minimal fact."
        assert result.source_documents == []  # Should default to empty list
        assert result.supporting_evidence == []
        assert result.date is None
        assert result.citation == ""

    def test_confidence_validation_edge_cases(self):
        """Test confidence validation with edge cases"""
        test_cases = [
            (0, 0),      # Minimum valid
            (1, 1),      # Maximum valid
            (-0.1, 0.8), # Below minimum, should use default
            (1.1, 0.8),  # Above maximum, should use default
            ("0.5", 0.8), # String, should use default
            (None, 0.8)   # None, should use default
        ]
        
        for confidence_input, expected in test_cases:
            fact_data = {
                "text": "Test fact",
                "confidence": confidence_input
            }
            
            result = self.generator._create_legal_fact(
                fact_data, 1, FactCategory.MATERIAL, default_confidence=0.8
            )
            
            assert result.confidence == expected


if __name__ == "__main__":
    pytest.main([__file__])