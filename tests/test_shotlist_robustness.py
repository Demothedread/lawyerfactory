# Script Name: test_shotlist_robustness.py
# Description: Unit tests for enhanced shotlist functionality  Tests the robust error handling and missing field tolerance in the evidence shotlist builder.
# Relationships:
#   - Entity Type: Test
#   - Directory Group: Core
#   - Group Tags: testing
Unit tests for enhanced shotlist functionality

Tests the robust error handling and missing field tolerance in 
the evidence shotlist builder.
"""

import pytest
import tempfile
import csv
from pathlib import Path
from unittest.mock import patch
from src.lawyerfactory.evidence.shotlist import (
    build_shot_list, 
    validate_evidence_rows, 
    _process_evidence_row,
    _log_processing_stats
)


class TestShotlistRobustness:
    """Test suite for enhanced shotlist functionality"""

    def test_build_shot_list_complete_data(self):
        """Test build_shot_list with complete, well-formed data"""
        evidence_rows = [
            {
                "fact_id": "fact_001",
                "source_id": "doc_123",
                "timestamp": "2024-01-01T10:00:00Z",
                "summary": "Important fact summary",
                "entities": ["Person A", "Company B"],
                "citations": ["Doc 1, p. 5", "Exhibit A"]
            },
            {
                "fact_id": "fact_002", 
                "source_id": "doc_124",
                "timestamp": "2024-01-02T11:00:00Z",
                "summary": "Another fact summary",
                "entities": ["Person C"],
                "citations": ["Doc 2, p. 10"]
            }
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            out_path = Path(temp_dir) / "test_shotlist.csv"
            result_path = build_shot_list(evidence_rows, out_path)
            
            assert result_path.exists()
            
            # Verify CSV content
            with open(result_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
            assert len(rows) == 2
            assert rows[0]["fact_id"] == "fact_001"
            assert rows[0]["entities"] == "Person A|Company B"
            assert rows[1]["citations"] == "Doc 2, p. 10"

    def test_build_shot_list_missing_fields(self):
        """Test build_shot_list with missing fields"""
        evidence_rows = [
            {
                "fact_id": "fact_001",
                # Missing source_id, timestamp, summary
                "entities": ["Person A"],
                "citations": []
            },
            {
                # Missing fact_id
                "source_id": "doc_124",
                "summary": "Summary only",
                # Missing entities, citations
            },
            {}  # Completely empty row
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            out_path = Path(temp_dir) / "test_shotlist_missing.csv"
            
            with patch('src.lawyerfactory.evidence.shotlist.logger') as mock_logger:
                result_path = build_shot_list(evidence_rows, out_path)
                
            assert result_path.exists()
            
            # Verify CSV was created with fallback values
            with open(result_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
            assert len(rows) == 3
            # First row should have fact_id but missing fields filled
            assert rows[0]["fact_id"] == "fact_001"
            assert rows[0]["source_id"] == "unknown_source"
            
            # Second row should have generated fact_id
            assert rows[1]["fact_id"] == "fact_2"  # Generated
            assert rows[1]["summary"] == "Summary only"
            
            # Third row should be completely filled with defaults
            assert rows[2]["fact_id"] == "fact_3"
            assert rows[2]["summary"] == "[No summary available]"
            
            # Should have logged warnings about missing fields
            assert mock_logger.debug.called or mock_logger.warning.called

    def test_build_shot_list_wrong_data_types(self):
        """Test build_shot_list with wrong data types"""
        evidence_rows = [
            {
                "fact_id": 123,  # Should be string
                "source_id": None,
                "entities": "single_entity_string",  # Should be list
                "citations": 456,  # Should be list
                "summary": ["list", "instead", "of", "string"]  # Should be string
            },
            "not_a_dict",  # Entire row is wrong type
            None  # Null row
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            out_path = Path(temp_dir) / "test_shotlist_types.csv"
            
            with patch('src.lawyerfactory.evidence.shotlist.logger') as mock_logger:
                result_path = build_shot_list(evidence_rows, out_path)
                
            assert result_path.exists()
            
            with open(result_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
            assert len(rows) == 3
            # Should have converted types appropriately
            assert rows[0]["fact_id"] == "123"
            assert rows[0]["entities"] == "single_entity_string"
            
            # Error rows should have fallback values
            assert "error" in rows[1]["fact_id"].lower() or rows[1]["fact_id"] == "fact_2"

    def test_process_evidence_row_comprehensive(self):
        """Test _process_evidence_row with various edge cases"""
        stats = {
            "missing_fact_id": 0,
            "missing_source_id": 0,
            "missing_timestamp": 0,
            "missing_summary": 0,
            "missing_entities": 0,
            "missing_citations": 0
        }
        
        # Test with mixed data types and missing fields
        row = {
            "fact_id": "",  # Empty string
            "source_id": None,
            "entities": ["Entity 1", None, "", "Entity 2"],  # Mixed valid/invalid
            "citations": "single citation string",  # String instead of list
            "summary": None,
            "timestamp": 123456  # Number instead of string
        }
        
        result = _process_evidence_row(row, 5, stats)
        
        assert result["fact_id"] == "fact_5"  # Generated due to empty string
        assert result["source_id"] == "unknown_source"  # None converted
        assert result["entities"] == "Entity 1|Entity 2"  # Filtered and joined
        assert result["citations"] == "single citation string"  # Converted from string
        assert result["summary"] == "[No summary available]"  # None converted
        assert result["timestamp"] == "123456"  # Number converted to string
        
        # Check that stats were updated
        assert stats["missing_fact_id"] == 1
        assert stats["missing_source_id"] == 1
        assert stats["missing_summary"] == 1

    def test_validate_evidence_rows_complete(self):
        """Test validate_evidence_rows with complete data"""
        evidence_rows = [
            {
                "fact_id": "fact_001",
                "source_id": "doc_123",
                "timestamp": "2024-01-01",
                "summary": "Complete summary",
                "entities": ["Entity 1"],
                "citations": ["Citation 1"]
            }
        ]
        
        result = validate_evidence_rows(evidence_rows)
        
        assert result["valid"] is True
        assert result["total_rows"] == 1
        assert len(result["quality_issues"]) == 0
        assert all(
            field_info["completeness_percentage"] == 100.0 
            for field_info in result["field_completeness"].values()
        )

    def test_validate_evidence_rows_incomplete(self):
        """Test validate_evidence_rows with incomplete data"""
        evidence_rows = [
            {"fact_id": "fact_001", "summary": "Has summary"},  # Missing other fields
            {"source_id": "doc_123"},  # Missing most fields
            {},  # Empty row
            "not_a_dict"  # Wrong type
        ]
        
        result = validate_evidence_rows(evidence_rows)
        
        assert result["valid"] is True  # Still valid, just with issues
        assert result["total_rows"] == 4
        assert len(result["quality_issues"]) > 0
        assert len(result["recommendations"]) > 0
        
        # Check completeness percentages
        fact_id_completeness = result["field_completeness"]["fact_id"]["completeness_percentage"]
        assert fact_id_completeness == 25.0  # Only 1 out of 4 rows has fact_id

    def test_validate_evidence_rows_edge_cases(self):
        """Test validate_evidence_rows with edge cases"""
        # Test with empty list
        result_empty = validate_evidence_rows([])
        assert "No evidence rows provided" in result_empty["quality_issues"]
        
        # Test with non-list input
        result_invalid = validate_evidence_rows("not a list")
        assert result_invalid["valid"] is False
        assert "must be a list" in result_invalid["error"]

    def test_build_shot_list_error_recovery(self):
        """Test that build_shot_list recovers from individual row errors"""
        evidence_rows = [
            {"fact_id": "good_fact", "summary": "Good row"},
            None,  # This will cause an error
            {"fact_id": "another_good", "summary": "Another good row"}
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            out_path = Path(temp_dir) / "test_error_recovery.csv"
            
            with patch('src.lawyerfactory.evidence.shotlist.logger') as mock_logger:
                result_path = build_shot_list(evidence_rows, out_path)
                
            assert result_path.exists()
            
            with open(result_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
            # Should have 3 rows: 2 good + 1 error fallback
            assert len(rows) == 3
            assert rows[0]["fact_id"] == "good_fact"
            assert rows[2]["fact_id"] == "another_good"
            # Middle row should be error fallback
            assert "error" in rows[1]["fact_id"].lower()
            
            # Should have logged the error
            mock_logger.error.assert_called()

    def test_empty_list_handling(self):
        """Test handling of empty lists in entities and citations"""
        evidence_rows = [
            {
                "fact_id": "fact_001",
                "entities": [],
                "citations": [],
                "summary": "Valid summary"
            }
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            out_path = Path(temp_dir) / "test_empty_lists.csv"
            result_path = build_shot_list(evidence_rows, out_path)
            
            with open(result_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
            assert len(rows) == 1
            assert rows[0]["entities"] == ""  # Empty string for empty list
            assert rows[0]["citations"] == ""  # Empty string for empty list

    def test_log_processing_stats(self):
        """Test _log_processing_stats function"""
        stats = {
            "total_rows": 10,
            "errors": 2,
            "missing_fact_id": 3,
            "missing_summary": 1,
            "missing_entities": 0
        }
        
        with patch('src.lawyerfactory.evidence.shotlist.logger') as mock_logger:
            _log_processing_stats(stats, Path("test.csv"))
            
            # Should log total rows and errors
            assert mock_logger.info.called
            # Should log missing field warnings
            assert mock_logger.warning.called

    def test_large_dataset_handling(self):
        """Test handling of larger datasets"""
        # Create a larger dataset with mixed quality
        evidence_rows = []
        for i in range(100):
            row = {"fact_id": f"fact_{i:03d}"}
            
            # Add some missing fields randomly
            if i % 3 == 0:
                row["summary"] = f"Summary {i}"
            if i % 2 == 0:
                row["entities"] = [f"Entity_{i}"]
            if i % 5 == 0:
                row["citations"] = [f"Citation_{i}"]
                
            evidence_rows.append(row)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            out_path = Path(temp_dir) / "test_large.csv"
            result_path = build_shot_list(evidence_rows, out_path)
            
            assert result_path.exists()
            
            with open(result_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
            assert len(rows) == 100
            # All rows should have fact_id (either original or generated)
            assert all(row["fact_id"] for row in rows)


if __name__ == "__main__":
    pytest.main([__file__])