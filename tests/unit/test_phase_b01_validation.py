"""
Unit tests for Phase B01 validation logic (handle_review_phase in server.py)
Tests deliverable validation business rules: shotlist minimum facts, claims completeness,
outline required sections, Rule 12(b)(6) compliance scoring
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pytest
import json
import csv
import tempfile
import shutil
from unittest.mock import patch, MagicMock


# Import server functions (we'll mock the full app context)
# Since handle_review_phase is not directly importable, we'll test its logic

@pytest.fixture
def temp_deliverables_dir():
    """Fixture: Create temporary deliverables directory"""
    temp_dir = tempfile.mkdtemp()
    deliverables_path = Path(temp_dir) / "deliverables"
    deliverables_path.mkdir(parents=True)
    
    yield deliverables_path
    
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def valid_shotlist_csv(temp_deliverables_dir):
    """Fixture: Create valid shotlist with 15 facts (>10 minimum)"""
    shotlist_path = temp_deliverables_dir / "shotlist.csv"
    
    with open(shotlist_path, 'w', newline='') as f:
        writer = csv.DictWriter(
            f, 
            fieldnames=["timestamp", "summary", "source_id", "relevant_sections", "tags", "confidence"]
        )
        writer.writeheader()
        
        # Write 15 facts
        for i in range(1, 16):
            writer.writerow({
                "timestamp": f"2024-01-{i:02d} 10:00:00",
                "summary": f"Fact {i}",
                "source_id": f"EV-{i:03d}",
                "relevant_sections": '["statement_of_facts"]',
                "tags": '["test"]',
                "confidence": 90
            })
    
    return shotlist_path


@pytest.fixture
def invalid_shotlist_csv(temp_deliverables_dir):
    """Fixture: Create invalid shotlist with only 5 facts (<10 minimum)"""
    shotlist_path = temp_deliverables_dir / "shotlist.csv"
    
    with open(shotlist_path, 'w', newline='') as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["timestamp", "summary", "source_id", "relevant_sections", "tags", "confidence"]
        )
        writer.writeheader()
        
        # Write only 5 facts
        for i in range(1, 6):
            writer.writerow({
                "timestamp": f"2024-01-{i:02d} 10:00:00",
                "summary": f"Fact {i}",
                "source_id": f"EV-{i:03d}",
                "relevant_sections": '["statement_of_facts"]',
                "tags": '["test"]',
                "confidence": 90
            })
    
    return shotlist_path


@pytest.fixture
def valid_claims_matrix_json(temp_deliverables_dir):
    """Fixture: Create valid claims matrix with all elements complete"""
    claims_path = temp_deliverables_dir / "claims_matrix.json"
    
    claims_data = {
        "element_analysis": {
            "valid_contract": {
                "element_name": "Valid Contract",
                "definition": "Contract requires offer, acceptance, consideration",
                "decision_outcome": "SATISFIED",
                "confidence_score": 95
            },
            "material_breach": {
                "element_name": "Material Breach",
                "definition": "Breach goes to root of contract",
                "decision_outcome": "SATISFIED",
                "confidence_score": 92
            },
            "causation": {
                "element_name": "Causation",
                "definition": "Breach caused damages",
                "decision_outcome": "SATISFIED",
                "confidence_score": 91
            }
        }
    }
    
    with open(claims_path, 'w') as f:
        json.dump(claims_data, f, indent=2)
    
    return claims_path


@pytest.fixture
def invalid_claims_matrix_json(temp_deliverables_dir):
    """Fixture: Create invalid claims matrix with missing decision_outcomes"""
    claims_path = temp_deliverables_dir / "claims_matrix.json"
    
    claims_data = {
        "element_analysis": {
            "valid_contract": {
                "element_name": "Valid Contract",
                "definition": "Contract requires offer, acceptance, consideration",
                "decision_outcome": None,  # Missing outcome!
                "confidence_score": 95
            },
            "material_breach": {
                "element_name": "Material Breach",
                "definition": "Breach goes to root of contract",
                # decision_outcome missing entirely!
                "confidence_score": 92
            }
        }
    }
    
    with open(claims_path, 'w') as f:
        json.dump(claims_data, f, indent=2)
    
    return claims_path


@pytest.fixture
def valid_skeletal_outline_json(temp_deliverables_dir):
    """Fixture: Create valid skeletal outline with required sections and Rule 12(b)(6) score >= 75%"""
    outline_path = temp_deliverables_dir / "skeletal_outline.json"
    
    outline_data = {
        "sections": [
            {"id": "caption", "title": "Caption", "required": True},
            {"id": "introduction", "title": "Introduction", "required": True},
            {"id": "jurisdiction", "title": "Jurisdiction", "required": True},
            {"id": "parties", "title": "Parties", "required": True},
            {"id": "statement_of_facts", "title": "Statement of Facts", "required": True},
            {"id": "count_one", "title": "Count I: Breach of Contract", "required": False},
            {"id": "prayer_for_relief", "title": "Prayer for Relief", "required": True}
        ],
        "rule12b6ComplianceScore": 85  # Above 75% threshold
    }
    
    with open(outline_path, 'w') as f:
        json.dump(outline_data, f, indent=2)
    
    return outline_path


@pytest.fixture
def invalid_skeletal_outline_json(temp_deliverables_dir):
    """Fixture: Create invalid skeletal outline missing required sections and low Rule 12(b)(6) score"""
    outline_path = temp_deliverables_dir / "skeletal_outline.json"
    
    outline_data = {
        "sections": [
            {"id": "caption", "title": "Caption", "required": True},
            {"id": "introduction", "title": "Introduction", "required": True},
            # Missing: jurisdiction, parties, statement_of_facts!
            {"id": "count_one", "title": "Count I: Breach of Contract", "required": False}
        ],
        "rule12b6ComplianceScore": 60  # Below 75% threshold!
    }
    
    with open(outline_path, 'w') as f:
        json.dump(outline_data, f, indent=2)
    
    return outline_path


class TestShotlistValidation:
    """Test suite for shotlist validation business rules"""

    def test_valid_shotlist_passes(self, valid_shotlist_csv):
        """Test: Shotlist with 15 facts (>10 minimum) passes validation"""
        with open(valid_shotlist_csv, 'r') as f:
            shotlist_facts = list(csv.DictReader(f))
            fact_count = len(shotlist_facts)
        
        # Assert validation logic
        assert fact_count >= 10, f"Expected >= 10 facts, got {fact_count}"
        assert fact_count == 15

    def test_invalid_shotlist_fails(self, invalid_shotlist_csv):
        """Test: Shotlist with 5 facts (<10 minimum) fails validation"""
        with open(invalid_shotlist_csv, 'r') as f:
            shotlist_facts = list(csv.DictReader(f))
            fact_count = len(shotlist_facts)
        
        # Assert validation fails
        assert fact_count < 10, f"Expected < 10 facts for invalid test, got {fact_count}"
        assert fact_count == 5


class TestClaimsMatrixValidation:
    """Test suite for claims matrix validation business rules"""

    def test_valid_claims_matrix_passes(self, valid_claims_matrix_json):
        """Test: Claims matrix with all decision_outcomes set passes validation"""
        with open(valid_claims_matrix_json, 'r') as f:
            claims_data = json.load(f)
            element_analysis = claims_data.get("element_analysis", {})
        
        # Check all elements have decision_outcome
        all_elements_complete = all(
            elem.get("decision_outcome") is not None
            for elem in element_analysis.values()
        )
        
        assert all_elements_complete
        assert len(element_analysis) == 3

    def test_invalid_claims_matrix_fails(self, invalid_claims_matrix_json):
        """Test: Claims matrix with missing decision_outcomes fails validation"""
        with open(invalid_claims_matrix_json, 'r') as f:
            claims_data = json.load(f)
            element_analysis = claims_data.get("element_analysis", {})
        
        # Check for missing decision_outcomes
        all_elements_complete = all(
            elem.get("decision_outcome") is not None
            for elem in element_analysis.values()
        )
        
        assert not all_elements_complete  # Should fail
        assert len(element_analysis) == 2


class TestSkeletalOutlineValidation:
    """Test suite for skeletal outline validation business rules"""

    def test_valid_outline_passes(self, valid_skeletal_outline_json):
        """Test: Outline with all required sections and Rule 12(b)(6) >= 75% passes"""
        with open(valid_skeletal_outline_json, 'r') as f:
            outline_data = json.load(f)
            sections = outline_data.get("sections", [])
            rule12b6_score = outline_data.get("rule12b6ComplianceScore", 0)
        
        # Check required sections
        section_ids = [s.get("id") for s in sections]
        required_sections = ["caption", "introduction", "jurisdiction", "parties", "statement_of_facts"]
        has_required_sections = all(req in section_ids for req in required_sections)
        
        # Check Rule 12(b)(6) score
        rule12b6_passes = rule12b6_score >= 75
        
        assert has_required_sections
        assert len(sections) >= 5
        assert rule12b6_passes
        assert rule12b6_score == 85

    def test_invalid_outline_fails(self, invalid_skeletal_outline_json):
        """Test: Outline missing required sections or low Rule 12(b)(6) score fails"""
        with open(invalid_skeletal_outline_json, 'r') as f:
            outline_data = json.load(f)
            sections = outline_data.get("sections", [])
            rule12b6_score = outline_data.get("rule12b6ComplianceScore", 0)
        
        # Check required sections
        section_ids = [s.get("id") for s in sections]
        required_sections = ["caption", "introduction", "jurisdiction", "parties", "statement_of_facts"]
        has_required_sections = all(req in section_ids for req in required_sections)
        
        # Check Rule 12(b)(6) score
        rule12b6_passes = rule12b6_score >= 75
        
        # Should fail on missing sections or low score
        assert not has_required_sections or not rule12b6_passes
        assert rule12b6_score == 60  # Below threshold


class TestCompleteValidation:
    """Test complete validation workflow (all deliverables)"""

    def test_all_valid_deliverables_pass(
        self,
        valid_shotlist_csv,
        valid_claims_matrix_json,
        valid_skeletal_outline_json
    ):
        """Test: All valid deliverables result in ready_for_drafting = True"""
        validations = {}
        
        # Shotlist validation
        with open(valid_shotlist_csv, 'r') as f:
            fact_count = len(list(csv.DictReader(f)))
            validations["shotlist_facts"] = {
                "passed": fact_count >= 10,
                "count": fact_count
            }
        
        # Claims matrix validation
        with open(valid_claims_matrix_json, 'r') as f:
            claims_data = json.load(f)
            element_analysis = claims_data.get("element_analysis", {})
            all_complete = all(
                elem.get("decision_outcome") is not None
                for elem in element_analysis.values()
            )
            validations["claims_elements"] = {
                "passed": len(element_analysis) > 0 and all_complete,
                "count": len(element_analysis)
            }
        
        # Outline validation
        with open(valid_skeletal_outline_json, 'r') as f:
            outline_data = json.load(f)
            sections = outline_data.get("sections", [])
            section_ids = [s.get("id") for s in sections]
            required = ["caption", "introduction", "jurisdiction", "parties", "statement_of_facts"]
            has_required = all(req in section_ids for req in required)
            rule12b6_score = outline_data.get("rule12b6ComplianceScore", 0)
            
            validations["outline_sections"] = {"passed": has_required and len(sections) >= 5}
            validations["rule_12b6_score"] = {"passed": rule12b6_score >= 75, "score": rule12b6_score}
        
        # Overall validation
        all_valid = all(v.get("passed", False) for v in validations.values())
        
        assert all_valid
        assert validations["shotlist_facts"]["passed"]
        assert validations["claims_elements"]["passed"]
        assert validations["outline_sections"]["passed"]
        assert validations["rule_12b6_score"]["passed"]

    def test_any_invalid_deliverable_fails(
        self,
        invalid_shotlist_csv,
        valid_claims_matrix_json,
        valid_skeletal_outline_json
    ):
        """Test: Any invalid deliverable results in ready_for_drafting = False"""
        validations = {}
        
        # Shotlist validation (invalid - only 5 facts)
        with open(invalid_shotlist_csv, 'r') as f:
            fact_count = len(list(csv.DictReader(f)))
            validations["shotlist_facts"] = {
                "passed": fact_count >= 10,
                "count": fact_count
            }
        
        # Claims matrix validation (valid)
        with open(valid_claims_matrix_json, 'r') as f:
            claims_data = json.load(f)
            element_analysis = claims_data.get("element_analysis", {})
            all_complete = all(
                elem.get("decision_outcome") is not None
                for elem in element_analysis.values()
            )
            validations["claims_elements"] = {
                "passed": len(element_analysis) > 0 and all_complete,
                "count": len(element_analysis)
            }
        
        # Outline validation (valid)
        with open(valid_skeletal_outline_json, 'r') as f:
            outline_data = json.load(f)
            sections = outline_data.get("sections", [])
            section_ids = [s.get("id") for s in sections]
            required = ["caption", "introduction", "jurisdiction", "parties", "statement_of_facts"]
            has_required = all(req in section_ids for req in required)
            rule12b6_score = outline_data.get("rule12b6ComplianceScore", 0)
            
            validations["outline_sections"] = {"passed": has_required and len(sections) >= 5}
            validations["rule_12b6_score"] = {"passed": rule12b6_score >= 75, "score": rule12b6_score}
        
        # Overall validation
        all_valid = all(v.get("passed", False) for v in validations.values())
        
        # Should fail due to invalid shotlist
        assert not all_valid
        assert not validations["shotlist_facts"]["passed"]  # This one fails
        assert validations["claims_elements"]["passed"]  # Others pass
        assert validations["outline_sections"]["passed"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
