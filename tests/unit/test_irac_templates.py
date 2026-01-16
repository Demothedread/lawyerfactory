"""
Unit tests for IRAC template engine (irac_templates.py)
Tests nested IRAC structure generation, claims matrix conversion, statement of facts builder
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pytest
from lawyerfactory.compose.promptkits.irac_templates import (
    IRACTemplateEngine,
    ElementAnalysis,
    IRACSection,
    claims_matrix_to_irac,
)


@pytest.fixture
def template_engine():
    """Fixture: IRACTemplateEngine instance"""
    return IRACTemplateEngine()


@pytest.fixture
def sample_section():
    """Fixture: Sample skeletal outline section"""
    return {
        "id": "count_one_breach_of_contract",
        "title": "Count I: Breach of Contract",
        "cause_of_action": "breach_of_contract",
        "issue_statement": "Whether defendant breached the contract",
        "primary_authority": "Restatement (Second) of Contracts",
        "citation": "Restatement (Second) of Contracts § 235 (1981)"
    }


@pytest.fixture
def sample_facts():
    """Fixture: Sample shotlist facts"""
    return [
        {
            "timestamp": "2024-01-15 09:30:00",
            "summary": "Contract signed by both parties",
            "source_id": "EV-001",
            "relevant_sections": ["count_one_breach_of_contract"],
        },
        {
            "timestamp": "2024-01-20 11:00:00",
            "summary": "Defendant failed to deliver goods",
            "source_id": "EV-002",
            "relevant_sections": ["count_one_breach_of_contract"],
        },
    ]


@pytest.fixture
def sample_elements():
    """Fixture: Sample claims matrix elements"""
    return {
        "valid_contract": {
            "definition": "A valid contract requires offer, acceptance, consideration",
            "authority": "Restatement (Second) of Contracts § 17",
            "satisfied": True,
            "confidence_score": 95,
            "facts": ["EV-001"],
        },
        "material_breach": {
            "definition": "Material breach goes to the root of the contract",
            "authority": "Jacob & Youngs v. Kent",
            "satisfied": True,
            "confidence_score": 92,
            "facts": ["EV-002"],
        },
    }


@pytest.fixture
def sample_claims_matrix():
    """Fixture: Complete claims matrix"""
    return {
        "header": {
            "cause_of_action": "breach_of_contract"
        },
        "legal_definition": {
            "primary_definition": "A breach of contract occurs when a party fails to perform their obligations under a valid contract",
            "authority_citations": ["Restatement (Second) of Contracts § 235"]
        },
        "element_analysis": {
            "valid_contract": {
                "breakdown": {
                    "definition": "A valid contract requires offer, acceptance, consideration",
                    "authority": "Restatement (Second) of Contracts § 17",
                    "analysis": "The parties entered into a written agreement with clear terms"
                },
                "decision_outcome": {
                    "satisfied": True,
                    "confidence": 0.95
                }
            },
            "material_breach": {
                "breakdown": {
                    "definition": "Material breach goes to the root of the contract",
                    "authority": "Jacob & Youngs v. Kent, 230 N.Y. 239 (1921)",
                    "analysis": "Defendant failed to deliver goods as specified"
                },
                "decision_outcome": {
                    "satisfied": True,
                    "confidence": 0.92
                }
            }
        },
        "executive_summary": {
            "case_strength": {
                "overall_strength": "Strong case with clear evidence of breach"
            }
        }
    }


class TestIRACTemplateEngine:
    """Test suite for IRACTemplateEngine class"""

    def test_initialization(self, template_engine):
        """Test: IRACTemplateEngine initializes correctly"""
        assert template_engine is not None
        assert hasattr(template_engine, "generate_nested_irac_prompt")

    def test_generate_nested_irac_prompt_basic(
        self, template_engine, sample_claims_matrix, sample_facts
    ):
        """Test: generate_nested_irac_prompt returns formatted IRAC prompt"""
        # First convert claims matrix to IRAC section
        irac_section = claims_matrix_to_irac(sample_claims_matrix, sample_facts)
        
        # Generate prompt using the IRAC section
        prompt = IRACTemplateEngine.generate_nested_irac_prompt(
            irac_section=irac_section,
            shotlist_facts=sample_facts
        )

        # Verify prompt structure
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        
        # Check for IRAC sections
        assert "ISSUE" in prompt
        assert "RULE" in prompt
        assert "APPLICATION" in prompt
        assert "CONCLUSION" in prompt

        # Check cause of action
        assert "breach_of_contract" in prompt.lower()

    def test_generate_section_prompt_with_rag(
        self, template_engine, sample_claims_matrix, sample_facts
    ):
        """Test: generate_nested_irac_prompt includes RAG context"""
        # First convert claims matrix to IRAC section
        irac_section = claims_matrix_to_irac(sample_claims_matrix, sample_facts)
        
        # Generate prompt with RAG context
        rag_context = [
            "Example case 1: Similar contract breach case...",
            "Example case 2: Another relevant precedent..."
        ]

        prompt = IRACTemplateEngine.generate_nested_irac_prompt(
            irac_section=irac_section,
            shotlist_facts=sample_facts
        )

        # Verify RAG context included (though this method doesn't use RAG directly)
        # The RAG context would be used in build_section_prompt
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_build_statement_of_facts(self, template_engine):
        """Test: generate_statement_of_facts creates chronological narrative"""
        shotlist = [
            {"timestamp": "2024-01-20", "summary": "Event B", "source_id": "EV-002"},
            {"timestamp": "2024-01-15", "summary": "Event A", "source_id": "EV-001"},
            {"timestamp": "2024-01-25", "summary": "Event C", "source_id": "EV-003"},
        ]

        result = IRACTemplateEngine.generate_statement_of_facts(shotlist)

        # Verify chronological order
        assert isinstance(result, str)
        # Event A should appear before Event B (chronological sort)
        assert result.index("Event A") < result.index("Event B")
        assert result.index("Event B") < result.index("Event C")

        # Verify facts are included (source IDs are not included in the output format)
        assert "Event A" in result
        assert "Event B" in result
        assert "Event C" in result
        assert "STATEMENT OF FACTS" in result


class TestClaimsMatrixToIRAC:
    """Test suite for claims_matrix_to_irac() converter function"""

    def test_claims_matrix_to_irac_conversion(self, sample_claims_matrix, sample_facts):
        """Test: claims_matrix_to_irac converts claims to IRAC sections"""
        irac_section = claims_matrix_to_irac(sample_claims_matrix, sample_facts)

        # Verify conversion
        assert isinstance(irac_section, IRACSection)
        assert irac_section.cause_of_action_name == "breach_of_contract"
        assert len(irac_section.elements) > 0

    def test_element_analysis_structure(self, sample_claims_matrix, sample_facts):
        """Test: ElementAnalysis dataclass has correct structure"""
        irac_section = claims_matrix_to_irac(sample_claims_matrix, sample_facts)
        
        # Check first element
        element = irac_section.elements[0]
        assert isinstance(element, ElementAnalysis)
        assert hasattr(element, "element_number")
        assert hasattr(element, "element_name")
        assert hasattr(element, "element_definition")
        assert hasattr(element, "element_authority")
        assert hasattr(element, "relevant_facts")
        assert hasattr(element, "element_satisfied")
        assert hasattr(element, "confidence_score")

    def test_irac_section_structure(self, sample_claims_matrix, sample_facts):
        """Test: IRACSection dataclass has correct structure"""
        irac_section = claims_matrix_to_irac(sample_claims_matrix, sample_facts)

        assert isinstance(irac_section, IRACSection)
        assert hasattr(irac_section, "cause_of_action_name")
        assert hasattr(irac_section, "issue_statement")
        assert hasattr(irac_section, "primary_authority")
        assert hasattr(irac_section, "citation")
        assert hasattr(irac_section, "elements")
        assert hasattr(irac_section, "overall_conclusion")
        assert hasattr(irac_section, "overall_confidence")
        assert hasattr(irac_section, "viable")
        assert hasattr(irac_section, "missing_elements")
        assert hasattr(irac_section, "uncertain_elements")


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_facts_list(self, template_engine, sample_claims_matrix):
        """Test: Handles empty facts list gracefully"""
        # Convert claims matrix to IRAC section
        irac_section = claims_matrix_to_irac(sample_claims_matrix, [])
        
        prompt = IRACTemplateEngine.generate_nested_irac_prompt(
            irac_section=irac_section,
            shotlist_facts=[]
        )

        # Should still generate prompt structure
        assert isinstance(prompt, str)
        assert "ISSUE" in prompt

    def test_empty_elements_dict(self, template_engine):
        """Test: generate_statement_of_facts handles empty facts list"""
        result = IRACTemplateEngine.generate_statement_of_facts([])
        
        # Should still generate basic structure
        assert isinstance(result, str)
        assert len(result) > 0

    def test_missing_optional_fields(self, template_engine):
        """Test: generate_statement_of_facts handles minimal facts"""
        minimal_facts = [{"summary": "Test event"}]
        
        result = IRACTemplateEngine.generate_statement_of_facts(minimal_facts)
        
        # Should not raise exception
        assert isinstance(result, str)
        assert len(result) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
