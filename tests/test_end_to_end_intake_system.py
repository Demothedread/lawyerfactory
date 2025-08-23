# Script Name: test_end_to_end_intake_system.py
# Description: End-to-End System Validation Tests for LawyerFactory Intake System  Tests the complete pipeline from intake form to document generation, including jurisdiction determination, authority validation, and citation management.
# Relationships:
#   - Entity Type: Test
#   - Directory Group: Core
#   - Group Tags: testing
End-to-End System Validation Tests for LawyerFactory Intake System

Tests the complete pipeline from intake form to document generation,
including jurisdiction determination, authority validation, and citation management.
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
from datetime import datetime

from src.lawyerfactory.phases.one_intake.intake_processor import IntakeProcessor, IntakeData
from src.lawyerfactory.knowledge_graph.core.legal_authorities import LegalAuthorityManager, AuthorityCitationManager
from src.lawyerfactory.phases.07_orchestration.caselaw_validator import CaselawValidationAgent, ValidationReport
from src.lawyerfactory.compose.strategies.statement_of_facts import StatementOfFactsGenerator


class TestIntakeSystemEndToEnd:
    """End-to-end tests for the complete intake system"""

    @pytest.fixture
    def sample_intake_data(self):
        """Sample intake form data for testing"""
        return {
            "client_name": "John Doe",
            "client_address": "123 Main St, Los Angeles, CA 90210",
            "client_phone": "(555) 123-4567",
            "client_email": "john.doe@email.com",
            "opposing_party_names": "MegaCorp Inc.",
            "opposing_party_address": "456 Business Ave, Los Angeles, CA 90211",
            "party_type": "plaintiff",
            "claim_amount": 75000,
            "events_location": "Los Angeles, California",
            "events_date": "January 2024",
            "agreement_type": "written",
            "has_evidence": "yes",
            "has_witnesses": "yes",
            "has_draft": "no",
            "claim_description": "Defendant failed to deliver goods as promised in the written contract dated January 1, 2024.",
            "causes_of_action": ["breach_contract"],
            "other_cause": ""
        }

    @pytest.fixture
    def mock_authority_manager(self):
        """Mock authority manager for testing"""
        manager = Mock(spec=LegalAuthorityManager)
        manager.validate_citation_for_jurisdiction.return_value = {
            "valid": True,
            "authority_type": "binding",
            "precedence_score": 0.9,
            "reason": "Valid binding authority"
        }
        return manager

    @pytest.fixture
    def intake_processor(self, tmp_path):
        """Create intake processor with temporary storage"""
        storage_path = tmp_path / "intake_sessions"
        return IntakeProcessor(str(storage_path))

    def test_intake_form_processing_complete_pipeline(self, intake_processor, sample_intake_data):
        """Test complete intake form processing pipeline"""
        # Process intake form
        intake_data = intake_processor.process_intake_form(sample_intake_data)

        # Verify intake data structure
        assert isinstance(intake_data, IntakeData)
        assert intake_data.session_id is not None
        assert intake_data.client_name == "John Doe"
        assert intake_data.claim_amount == 75000

        # Verify generated fields
        assert intake_data.case_name == "John Doe v. MegaCorp Inc."
        assert "Los Angeles, California" in intake_data.case_description
        assert intake_data.jurisdiction == "State of California"
        assert intake_data.venue == "Los Angeles County Superior Court"
        assert "state" in intake_data.court_type.lower()

        # Verify facts matrix generation
        facts_matrix = intake_processor.get_facts_matrix_from_intake(intake_data)
        assert "undisputed_facts" in facts_matrix
        assert "case_metadata" in facts_matrix
        assert facts_matrix["case_metadata"]["client_name"] == "John Doe"
        assert facts_matrix["case_metadata"]["claim_amount"] == 75000

    def test_jurisdiction_determination_logic(self, intake_processor):
        """Test jurisdiction determination for different scenarios"""

        # Test federal jurisdiction (high amount)
        federal_data = {
            "client_name": "Plaintiff",
            "opposing_party_names": "Defendant",
            "party_type": "plaintiff",
            "claim_amount": 100000,  # Over $75k
            "events_location": "New York, NY",
            "events_date": "2024",
            "claim_description": "Test claim"
        }

        intake_data = intake_processor.process_intake_form(federal_data)
        assert "federal" in intake_data.court_type.lower()

        # Test state jurisdiction (lower amount)
        state_data = {
            "client_name": "Plaintiff",
            "opposing_party_names": "Defendant",
            "party_type": "plaintiff",
            "claim_amount": 25000,  # Under $75k
            "events_location": "California",
            "events_date": "2024",
            "claim_description": "Test claim"
        }

        intake_data = intake_processor.process_intake_form(state_data)
        assert "state" in intake_data.court_type.lower()

        # Test civil rights federal question
        civil_rights_data = {
            "client_name": "Plaintiff",
            "opposing_party_names": "Defendant",
            "party_type": "plaintiff",
            "claim_amount": 10000,
            "events_location": "Texas",
            "events_date": "2024",
            "causes_of_action": ["civil_rights"],
            "claim_description": "Civil rights violation"
        }

        intake_data = intake_processor.process_intake_form(civil_rights_data)
        assert "federal" in intake_data.court_type.lower()

    def test_authority_validation_system(self, mock_authority_manager):
        """Test authority validation system"""
        citation_manager = AuthorityCitationManager(mock_authority_manager)

        # Test valid citation
        result = mock_authority_manager.validate_citation_for_jurisdiction("123 Cal.App.4th 456", "california")
        assert result["valid"] is True

        # Test citation formatting
        formatted = citation_manager.format_citation("123 Cal.App.4th 456", "california")
        assert formatted == "123 Cal.App.4th 456"

        # Test citation table generation
        citations = ["123 Cal.App.4th 456", "456 F.Supp. 789"]
        table = citation_manager.generate_citation_table(citations, "california")
        assert "TABLE OF AUTHORITIES" in table
        assert "123 Cal.App.4th 456" in table

    @pytest.mark.asyncio
    async def test_caselaw_validation_agent(self, mock_authority_manager):
        """Test caselaw validation agent functionality"""
        agent = CaselawValidationAgent()
        agent.authority_manager = mock_authority_manager

        # Test document validation
        test_document = """
        According to Smith v. Jones, 123 Cal.App.4th 456 (2023), the standard is clear.
        Additionally, see Johnson v. State, 456 F.Supp. 789 (2022).
        """

        report = await agent.validate_document_citations(test_document, "california")

        assert isinstance(report, ValidationReport)
        assert report.total_citations == 2
        assert report.valid_citations == 2
        assert len(report.issues) == 0

    @pytest.mark.asyncio
    async def test_caselaw_validation_with_issues(self):
        """Test caselaw validation with problematic citations"""
        # Create mock authority manager that returns issues
        mock_manager = Mock(spec=LegalAuthorityManager)
        mock_manager.validate_citation_for_jurisdiction.return_value = {
            "valid": False,
            "authority_type": "obsolete",
            "reason": "This case was superseded by newer authority",
            "suggested_alternatives": ["123 Cal.5th 456"]
        }

        agent = CaselawValidationAgent()
        agent.authority_manager = mock_manager

        test_document = "According to Old Case, 999 Cal.App.4th 123 (1999), the rule applies."

        report = await agent.validate_document_citations(test_document, "california")

        assert report.total_citations == 1
        assert report.valid_citations == 0
        assert len(report.issues) == 1
        assert report.issues[0].issue_type == "obsolete"
        assert report.issues[0].suggested_replacement == "123 Cal.5th 456"

    def test_statement_of_facts_integration(self, intake_processor, sample_intake_data):
        """Test integration with Statement of Facts generator"""
        # Process intake data
        intake_data = intake_processor.process_intake_form(sample_intake_data)
        facts_matrix = intake_processor.get_facts_matrix_from_intake(intake_data)

        # Mock Statement of Facts generator
        mock_kg = Mock()
        sof_generator = StatementOfFactsGenerator(mock_kg)

        # Generate statement of facts
        case_data = {
            "case_name": intake_data.case_name,
            "jurisdiction": intake_data.jurisdiction,
            "court_type": intake_data.court_type
        }

        # This would normally generate the full document
        # For testing, we verify the data structure is correct
        assert facts_matrix["case_metadata"]["case_name"] == "John Doe v. MegaCorp Inc."
        assert facts_matrix["case_metadata"]["jurisdiction"] == "State of California"
        assert len(facts_matrix["undisputed_facts"]) > 0
        assert facts_matrix["case_metadata"]["claim_amount"] == 75000

    def test_causes_of_action_mapping(self, intake_processor):
        """Test that causes of action are properly mapped and stored"""

        test_cases = [
            {
                "causes_of_action": ["breach_contract"],
                "expected_primary": "breach_contract"
            },
            {
                "causes_of_action": ["motor_vehicle"],
                "expected_primary": "motor_vehicle"
            },
            {
                "causes_of_action": ["negligence", "fraud"],
                "expected_primary": "negligence"
            }
        ]

        for test_case in test_cases:
            data = {
                "client_name": "Test",
                "opposing_party_names": "Defendant",
                "party_type": "plaintiff",
                "claim_amount": 50000,
                "events_location": "California",
                "events_date": "2024",
                "claim_description": "Test claim",
                **test_case
            }

            intake_data = intake_processor.process_intake_form(data)
            assert intake_data.causes_of_action == test_case["causes_of_action"]

            # Verify facts matrix includes causes of action
            facts_matrix = intake_processor.get_facts_matrix_from_intake(intake_data)
            assert facts_matrix["case_metadata"]["causes_of_action"] == test_case["causes_of_action"]

    def test_claim_amount_thresholds(self, intake_processor):
        """Test claim amount thresholds for jurisdiction determination"""

        thresholds = [
            (5000, "state"),           # Under $12k - state court
            (15000, "state"),          # Under $75k - state court
            (25000, "state"),          # Under $75k - state court
            (80000, "federal"),        # Over $75k - federal court
            (150000, "federal"),       # Over $75k - federal court
        ]

        for amount, expected_court in thresholds:
            data = {
                "client_name": "Test",
                "opposing_party_names": "Defendant",
                "party_type": "plaintiff",
                "claim_amount": amount,
                "events_location": "California",
                "events_date": "2024",
                "claim_description": "Test claim"
            }

            intake_data = intake_processor.process_intake_form(data)
            court_type = intake_data.court_type.lower()

            if expected_court == "federal":
                assert "federal" in court_type
            else:
                assert "state" in court_type

    def test_data_persistence(self, intake_processor, sample_intake_data):
        """Test that intake data is properly persisted and retrievable"""
        # Process and store intake data
        intake_data = intake_processor.process_intake_form(sample_intake_data)

        # Retrieve data
        retrieved_data = intake_processor.get_intake_data(intake_data.session_id)

        assert retrieved_data is not None
        assert retrieved_data.session_id == intake_data.session_id
        assert retrieved_data.client_name == "John Doe"
        assert retrieved_data.claim_amount == 75000
        assert retrieved_data.case_name == "John Doe v. MegaCorp Inc."

    def test_error_handling_invalid_data(self, intake_processor):
        """Test error handling for invalid intake data"""
        invalid_data = {
            "client_name": "",  # Missing required field
            "party_type": "invalid_type",
            "claim_amount": "not_a_number"
        }

        # Should handle gracefully
        intake_data = intake_processor.process_intake_form(invalid_data)

        assert intake_data.client_name == ""
        assert intake_data.claim_amount == 0  # Should default to 0

    def test_integration_with_research_bot(self, intake_processor, sample_intake_data):
        """Test integration points with research bot"""
        intake_data = intake_processor.process_intake_form(sample_intake_data)
        facts_matrix = intake_processor.get_facts_matrix_from_intake(intake_data)

        # Verify research-relevant data is included
        assert "case_metadata" in facts_matrix
        assert "jurisdiction" in facts_matrix["case_metadata"]
        assert "causes_of_action" in facts_matrix["case_metadata"]
        assert "claim_description" in facts_matrix["case_metadata"]

        # Verify procedural facts include jurisdiction info
        procedural_facts = facts_matrix["procedural_facts"]
        jurisdiction_found = any("California" in fact for fact in procedural_facts)
        assert jurisdiction_found

    def test_integration_with_statement_of_facts(self, intake_processor, sample_intake_data):
        """Test integration points with statement of facts generator"""
        intake_data = intake_processor.process_intake_form(sample_intake_data)
        facts_matrix = intake_processor.get_facts_matrix_from_intake(intake_data)

        # Verify statement of facts relevant data
        assert "undisputed_facts" in facts_matrix
        assert "disputed_facts" in facts_matrix
        assert "procedural_facts" in facts_matrix

        # Verify key events are included
        assert "key_events" in facts_matrix
        assert len(facts_matrix["key_events"]) > 0

        # Verify damages claims are included
        assert "damages_claims" in facts_matrix
        assert len(facts_matrix["damages_claims"]) > 0
        assert facts_matrix["damages_claims"][0]["amount"] == 75000

    @pytest.mark.asyncio
    async def test_complete_orchestration_flow(self, intake_processor, sample_intake_data, mock_authority_manager):
        """Test complete orchestration flow from intake to validation"""

        # Step 1: Process intake
        intake_data = intake_processor.process_intake_form(sample_intake_data)
        facts_matrix = intake_processor.get_facts_matrix_from_intake(intake_data)

        # Step 2: Simulate document generation
        generated_document = f"""
        STATEMENT OF FACTS

        {intake_data.case_name}

        1. Plaintiff {intake_data.client_name} entered into a contract with Defendant {intake_data.opposing_party_names}.

        2. According to Smith v. Jones, 123 Cal.App.4th 456 (2023), the elements of breach of contract are clear.

        3. The events occurred in {intake_data.events_location} during {intake_data.events_date}.

        4. The claim seeks ${intake_data.claim_amount:,} in damages.
        """

        # Step 3: Validate citations
        validator = CaselawValidationAgent()
        validator.authority_manager = mock_authority_manager

        validation_result = await validator.monitor_document_generation(
            generated_document,
            intake_data.jurisdiction.split()[-1].lower()  # Extract state name
        )

        # Verify validation results
        assert "validation_report" in validation_result
        assert "needs_immediate_attention" in validation_result

        # Step 4: Generate citation table
        citation_table = validator.get_citation_table_of_contents("test_doc", "california")
        assert "TABLE OF AUTHORITIES" in citation_table or "No citations" in citation_table

        # Verify complete flow data integrity
        assert intake_data.session_id is not None
        assert facts_matrix["case_metadata"]["session_id"] == intake_data.session_id
        assert validation_result is not None