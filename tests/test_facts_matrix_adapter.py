# Script Name: test_facts_matrix_adapter.py
# Description: Unit tests for FactsMatrixAdapter  Tests the adapter's ability to transform raw ingestion data into canonical facts_matrix format with proper error handling and validation.
# Relationships:
#   - Entity Type: Test
#   - Directory Group: Core
#   - Group Tags: testing
Unit tests for FactsMatrixAdapter

Tests the adapter's ability to transform raw ingestion data into canonical
facts_matrix format with proper error handling and validation.
"""

import pytest
from unittest.mock import patch, MagicMock
from src.lawyerfactory.ingest.adapters.facts_matrix_adapter import FactsMatrixAdapter


class TestFactsMatrixAdapter:
    """Test suite for FactsMatrixAdapter"""

    def test_transform_to_facts_matrix_basic(self):
        """Test basic transformation with complete data"""
        raw_data = {
            "undisputed_facts": ["Fact 1", "Fact 2"],
            "disputed_facts": ["Disputed fact 1"],
            "procedural_facts": ["Procedural fact 1"],
            "case_metadata": {"case_number": "123", "court": "Superior Court"},
            "evidence_references": {"fact1": ["doc1.pdf"]}
        }
        
        result = FactsMatrixAdapter.transform_to_facts_matrix(raw_data)
        
        assert isinstance(result, dict)
        assert "undisputed_facts" in result
        assert "disputed_facts" in result
        assert "procedural_facts" in result
        assert "case_metadata" in result
        assert "evidence_references" in result
        assert len(result["undisputed_facts"]) == 2
        assert len(result["disputed_facts"]) == 1

    def test_transform_to_facts_matrix_empty_input(self):
        """Test transformation with empty input"""
        raw_data = {}
        
        result = FactsMatrixAdapter.transform_to_facts_matrix(raw_data)
        
        assert isinstance(result, dict)
        assert result["undisputed_facts"] == []
        assert result["disputed_facts"] == []
        assert result["procedural_facts"] == []
        assert result["case_metadata"] == {}
        assert result["evidence_references"] == {}

    def test_transform_to_facts_matrix_none_input(self):
        """Test transformation with None input"""
        with patch('src.lawyerfactory.ingest.adapters.facts_matrix_adapter.logger') as mock_logger:
            result = FactsMatrixAdapter.transform_to_facts_matrix(None)
            
            assert isinstance(result, dict)
            assert result["undisputed_facts"] == []
            mock_logger.warning.assert_called()

    def test_extract_facts_list_input(self):
        """Test _extract_facts with list input"""
        raw_data = {"test_facts": ["fact1", "fact2", "fact3"]}
        possible_keys = ["test_facts"]
        
        result = FactsMatrixAdapter._extract_facts(raw_data, possible_keys)
        
        assert result == ["fact1", "fact2", "fact3"]

    def test_extract_facts_string_input(self):
        """Test _extract_facts with string input"""
        raw_data = {"test_facts": "single fact"}
        possible_keys = ["test_facts"]
        
        result = FactsMatrixAdapter._extract_facts(raw_data, possible_keys)
        
        assert result == ["single fact"]

    def test_extract_facts_dict_input(self):
        """Test _extract_facts with nested dictionary input"""
        raw_data = {
            "test_facts": {
                "category1": ["fact1", "fact2"],
                "category2": "fact3"
            }
        }
        possible_keys = ["test_facts"]
        
        result = FactsMatrixAdapter._extract_facts(raw_data, possible_keys)
        
        assert "fact1" in result
        assert "fact2" in result
        assert "fact3" in result

    def test_extract_facts_missing_key(self):
        """Test _extract_facts with missing key"""
        raw_data = {"other_key": ["fact1"]}
        possible_keys = ["missing_key"]
        
        result = FactsMatrixAdapter._extract_facts(raw_data, possible_keys)
        
        assert result == []

    def test_extract_case_metadata_direct(self):
        """Test _extract_case_metadata with direct metadata"""
        raw_data = {
            "case_metadata": {
                "case_number": "123",
                "court": "Superior Court",
                "judge": "Judge Smith"
            }
        }
        
        result = FactsMatrixAdapter._extract_case_metadata(raw_data)
        
        assert result["case_number"] == "123"
        assert result["court"] == "Superior Court"
        assert result["judge"] == "Judge Smith"

    def test_extract_case_metadata_top_level(self):
        """Test _extract_case_metadata with top-level fields"""
        raw_data = {
            "case_number": "456",
            "plaintiff": "John Doe",
            "defendant": "Jane Corp"
        }
        
        result = FactsMatrixAdapter._extract_case_metadata(raw_data)
        
        assert result["case_number"] == "456"
        assert result["plaintiff"] == "John Doe"
        assert result["defendant"] == "Jane Corp"

    def test_extract_evidence_references(self):
        """Test _extract_evidence_references"""
        raw_data = {
            "evidence_references": {
                "fact1": ["doc1.pdf", "doc2.pdf"],
                "fact2": ["doc3.pdf"]
            }
        }
        
        result = FactsMatrixAdapter._extract_evidence_references(raw_data)
        
        assert "fact1" in result
        assert "fact2" in result
        assert len(result["fact1"]) == 2

    def test_validate_facts_matrix_valid(self):
        """Test validate_facts_matrix with valid input"""
        facts_matrix = {
            "undisputed_facts": ["fact1"],
            "disputed_facts": ["fact2"],
            "procedural_facts": [],
            "case_metadata": {"case_number": "123"},
            "evidence_references": {}
        }
        
        result = FactsMatrixAdapter.validate_facts_matrix(facts_matrix)
        
        assert result is True

    def test_validate_facts_matrix_invalid_type(self):
        """Test validate_facts_matrix with invalid type"""
        with patch('src.lawyerfactory.ingest.adapters.facts_matrix_adapter.logger') as mock_logger:
            result = FactsMatrixAdapter.validate_facts_matrix("not a dict")
            
            assert result is False
            mock_logger.error.assert_called()

    def test_validate_facts_matrix_missing_key(self):
        """Test validate_facts_matrix with missing required key"""
        facts_matrix = {
            "undisputed_facts": ["fact1"],
            # Missing other required keys
        }
        
        with patch('src.lawyerfactory.ingest.adapters.facts_matrix_adapter.logger') as mock_logger:
            result = FactsMatrixAdapter.validate_facts_matrix(facts_matrix)
            
            assert result is False
            mock_logger.error.assert_called()

    def test_validate_facts_matrix_wrong_type_for_list_field(self):
        """Test validate_facts_matrix with wrong type for list field"""
        facts_matrix = {
            "undisputed_facts": "should be list",  # Wrong type
            "disputed_facts": [],
            "procedural_facts": [],
            "case_metadata": {},
            "evidence_references": {}
        }
        
        with patch('src.lawyerfactory.ingest.adapters.facts_matrix_adapter.logger') as mock_logger:
            result = FactsMatrixAdapter.validate_facts_matrix(facts_matrix)
            
            assert result is False
            mock_logger.error.assert_called()

    def test_flatten_fact_dict_nested(self):
        """Test _flatten_fact_dict with nested structure"""
        fact_dict = {
            "level1": {
                "level2": ["fact1", "fact2"],
                "level2b": "fact3"
            },
            "direct": ["fact4"]
        }
        
        result = FactsMatrixAdapter._flatten_fact_dict(fact_dict)
        
        assert "fact1" in result
        assert "fact2" in result
        assert "fact3" in result
        assert "fact4" in result

    def test_flatten_fact_dict_empty(self):
        """Test _flatten_fact_dict with empty dict"""
        result = FactsMatrixAdapter._flatten_fact_dict({})
        
        assert result == []

    @patch('src.lawyerfactory.ingest.adapters.facts_matrix_adapter.logger')
    def test_transform_error_handling(self, mock_logger):
        """Test error handling during transformation"""
        # Create raw_data that will cause an exception during processing
        raw_data = MagicMock()
        raw_data.get.side_effect = Exception("Test exception")
        
        result = FactsMatrixAdapter.transform_to_facts_matrix(raw_data)
        
        # Should return safe defaults even on error
        assert isinstance(result, dict)
        assert "undisputed_facts" in result
        mock_logger.error.assert_called()

    def test_alternative_key_names(self):
        """Test extraction with alternative key names"""
        raw_data = {
            "agreed_facts": ["fact1", "fact2"],  # Alternative to undisputed_facts
            "contested_facts": ["fact3"],        # Alternative to disputed_facts
        }
        
        result = FactsMatrixAdapter.transform_to_facts_matrix(raw_data)
        
        assert len(result["undisputed_facts"]) == 2
        assert len(result["disputed_facts"]) == 1

    def test_empty_string_facts_filtered(self):
        """Test that empty string facts are filtered out"""
        raw_data = {
            "undisputed_facts": ["valid fact", "", "  ", "another valid fact", None]
        }
        
        result = FactsMatrixAdapter.transform_to_facts_matrix(raw_data)
        
        # Should only have 2 valid facts (empty strings and None filtered out)
        assert len(result["undisputed_facts"]) == 2
        assert "valid fact" in result["undisputed_facts"]
        assert "another valid fact" in result["undisputed_facts"]


if __name__ == "__main__":
    pytest.main([__file__])