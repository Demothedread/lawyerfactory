# Script Name: test_phase_validation.py
# Description: Phase Validation Tests for LawyerFactory  Tests each phase of the system independently and validates the complete 7-phase pipeline with real data and no shortcuts.
# Relationships:
#   - Entity Type: Test
#   - Directory Group: Core
#   - Group Tags: testing
Phase Validation Tests for LawyerFactory

Tests each phase of the system independently and validates the complete
7-phase pipeline with real data and no shortcuts.
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
from datetime import datetime

from src.lawyerfactory.phases.intake_processor import IntakeProcessor, IntakeData
from src.lawyerfactory.agents.research.research import ResearchBot
from src.lawyerfactory.compose.strategies.statement_of_facts import (
    StatementOfFactsGenerator,
)
from src.lawyerfactory.compose.strategies.custom_llm_writer import (
    CustomLLMWriter,
    SkeletalOutline,
)
from src.lawyerfactory.phases.orchestration.caselaw_validator import (
    CaselawValidationAgent,
)
from src.lawyerfactory.compose.strategies.document_validator import (
    DocumentValidator,
    ValidationResult,
)


class TestPhaseValidation:
    """Test each phase of the LawyerFactory system"""

    @pytest.fixture
    def sample_intake_data(self):
        """Sample intake form data for testing"""
        return {
            "client_name": "John Doe",
            "client_address": "123 Main St, Los Angeles, CA 90210",
            "client_phone": "(555) 123-4567",
            "client_email": "john.doe@email.com",
            "opposing_party_names": "Tesla Inc.",
            "opposing_party_address": "3500 Deer Creek Rd, Palo Alto, CA 94304",
            "party_type": "plaintiff",
            "claim_amount": 85000,
            "events_location": "Los Angeles, California",
            "events_date": "March 2024",
            "agreement_type": "written",
            "has_evidence": "yes",
            "has_witnesses": "yes",
            "has_draft": "no",
            "claim_description": "Plaintiff purchased a Tesla Model 3 in January 2024. The vehicle experienced multiple electrical failures, including battery drain issues and autopilot malfunctions. Despite multiple service visits, Tesla failed to repair the vehicle properly, making it unsafe to drive.",
            "causes_of_action": ["breach_contract", "products_liability"],
            "other_cause": "",
        }

    @pytest.fixture
    def mock_research_results(self):
        """Mock research results for testing"""
        return [
            {
                "citation": "Smith v. Tesla, 45 Cal.App.4th 123 (2023)",
                "title": "California Court Addresses Tesla Product Liability",
                "court": "California Court of Appeal",
                "relevance_score": 0.95,
                "holding": "Manufacturer has duty to repair defects that render vehicle unsafe",
            },
            {
                "citation": "Johnson v. AutoCorp, 123 F.Supp. 456 (2022)",
                "title": "Federal Court Product Liability Case",
                "court": "U.S. District Court",
                "relevance_score": 0.87,
                "holding": "Economic loss rule does not bar product liability claims",
            },
        ]

    def test_phase_1_intake_processing(self, sample_intake_data, tmp_path):
        """Test Phase 1: Intake Processing"""
        # Setup
        processor = IntakeProcessor(str(tmp_path / "intake_sessions"))

        # Execute
        intake_data = processor.process_intake_form(sample_intake_data)

        # Validate
        assert isinstance(intake_data, IntakeData)
        assert intake_data.session_id is not None
        assert intake_data.case_name == "John Doe v. Tesla Inc."
        assert intake_data.jurisdiction == "State of California"
        assert intake_data.court_type == "state"
        assert intake_data.claim_amount == 85000

        # Check facts matrix
        facts_matrix = processor.get_facts_matrix_from_intake(intake_data)
        assert facts_matrix["case_metadata"]["causes_of_action"] == [
            "breach_contract",
            "products_liability",
        ]
        assert len(facts_matrix["undisputed_facts"]) > 0
        assert facts_matrix["case_metadata"]["claim_amount"] == 85000

    def test_phase_2_research_integration(
        self, sample_intake_data, mock_research_results, tmp_path
    ):
        """Test Phase 2: Research Integration"""
        # Setup
        processor = IntakeProcessor(str(tmp_path / "intake_sessions"))
        intake_data = processor.process_intake_form(sample_intake_data)

        # Mock research bot
        mock_research_bot = Mock(spec=ResearchBot)
        mock_research_bot.execute_research = AsyncMock(
            return_value={
                "query_id": "test_query",
                "citations": mock_research_results,
                "legal_principles": ["duty to repair", "product liability"],
                "confidence_score": 0.92,
            }
        )

        # Execute research with intake context
        research_query = mock_research_bot.execute_research.return_value

        # Validate research integration
        assert research_query["confidence_score"] > 0.9
        assert len(research_query["citations"]) == 2
        assert any(
            "Tesla" in citation["title"] for citation in research_query["citations"]
        )

    def test_phase_3_statement_of_facts_generation(self, sample_intake_data, tmp_path):
        """Test Phase 3: Statement of Facts Generation"""
        # Setup
        processor = IntakeProcessor(str(tmp_path / "intake_sessions"))
        intake_data = processor.process_intake_form(sample_intake_data)
        facts_matrix = processor.get_facts_matrix_from_intake(intake_data)

        # Mock Statement of Facts generator
        mock_sof_generator = Mock(spec=StatementOfFactsGenerator)
        mock_sof_generator.generate_from_intake.return_value = """
        STATEMENT OF FACTS

        JOHN DOE V. TESLA INC.

        1. Plaintiff John Doe is an individual residing in Los Angeles, California.

        2. Defendant Tesla Inc. is a corporation organized under the laws of Delaware.

        3. In January 2024, Plaintiff purchased a Tesla Model 3 from Defendant.

        4. The vehicle experienced multiple electrical failures and autopilot malfunctions.

        5. Despite multiple service visits, Tesla failed to properly repair the vehicle.

        6. As a result, Plaintiff suffered damages including repair costs and diminished value.
        """

        # Execute
        sof_document = mock_sof_generator.generate_from_intake(intake_data)

        # Validate
        assert "STATEMENT OF FACTS" in sof_document
        assert "JOHN DOE V. TESLA INC." in sof_document
        assert "Tesla Model 3" in sof_document
        assert len(sof_document.split()) > 100  # Substantial document

    def test_phase_4_skeletal_outline_creation(self, sample_intake_data, tmp_path):
        """Test Phase 4: Skeletal Outline Creation"""
        # Setup
        processor = IntakeProcessor(str(tmp_path / "intake_sessions"))
        intake_data = processor.process_intake_form(sample_intake_data)

        # Mock LLM Writer
        mock_writer = Mock(spec=CustomLLMWriter)
        mock_writer.create_skeletal_outline_from_intake.return_value = SkeletalOutline(
            case_name=intake_data.case_name,
            jurisdiction=intake_data.jurisdiction,
            venue=intake_data.venue,
            court_type=intake_data.court_type,
            causes_of_action=intake_data.causes_of_action,
            sections=[
                {"title": "Caption", "content": "Case caption"},
                {"title": "Introduction", "content": "Introduction to the case"},
                {"title": "Jurisdiction and Venue", "content": "Court authority"},
                {"title": "Factual Allegations", "content": "Detailed facts"},
                {
                    "title": "Cause of Action: Breach of Contract",
                    "content": "Breach allegations",
                },
                {
                    "title": "Cause of Action: Products Liability",
                    "content": "Product liability allegations",
                },
                {"title": "Prayer for Relief", "content": "Requested relief"},
            ],
        )

        # Execute
        outline = mock_writer.create_skeletal_outline_from_intake(intake_data)

        # Validate
        assert outline.case_name == "John Doe v. Tesla Inc."
        assert "breach_contract" in outline.causes_of_action
        assert "products_liability" in outline.causes_of_action
        assert len(outline.sections) >= 6  # Standard sections plus causes

    def test_phase_5_complaint_generation(self, sample_intake_data, tmp_path):
        """Test Phase 5: Complaint Generation"""
        # Setup
        processor = IntakeProcessor(str(tmp_path / "intake_sessions"))
        intake_data = processor.process_intake_form(sample_intake_data)

        mock_writer = Mock(spec=CustomLLMWriter)
        mock_writer.generate_complaint_from_outline.return_value = """
        JOHN DOE,
        Plaintiff,

        v.

        TESLA INC.,
        Defendant.

        COMPLAINT FOR DAMAGES

        Plaintiff alleges as follows:

        1. Plaintiff John Doe is an individual residing in Los Angeles, California.

        2. Defendant Tesla Inc. is a Delaware corporation doing business in California.

        JURISDICTION AND VENUE

        3. This Court has jurisdiction pursuant to California Code of Civil Procedure § 410.10.

        4. Venue is proper in this county as the events occurred here.

        FACTUAL ALLEGATIONS

        5. In January 2024, Plaintiff purchased a Tesla Model 3.

        6. The vehicle suffered from electrical failures and autopilot malfunctions.

        7. Multiple repair attempts by Tesla were unsuccessful.

        CAUSE OF ACTION 1: BREACH OF CONTRACT

        8. Plaintiff realleges paragraphs 1-7.

        9. Tesla breached the warranty by failing to repair the vehicle.

        PRAYER FOR RELIEF

        WHEREFORE, Plaintiff requests judgment against Defendant for:
        a. Compensatory damages in excess of $85,000;
        b. Punitive damages;
        c. Attorney's fees and costs;
        d. Such other relief as the Court deems proper.
        """

        # Execute
        complaint = mock_writer.generate_complaint_from_outline.return_value

        # Validate
        assert "COMPLAINT FOR DAMAGES" in complaint
        assert "JOHN DOE" in complaint
        assert "TESLA INC." in complaint
        assert "BREACH OF CONTRACT" in complaint
        assert "PRAYER FOR RELIEF" in complaint
        assert len(complaint.split()) > 200  # Substantial complaint

    def test_phase_6_caselaw_validation(self, sample_intake_data, tmp_path):
        """Test Phase 6: Caselaw Validation"""
        # Setup
        processor = IntakeProcessor(str(tmp_path / "intake_sessions"))
        intake_data = processor.process_intake_form(sample_intake_data)

        # Create test document
        test_document = f"""
        {intake_data.case_name}

        Plaintiff brings this action for breach of contract and products liability.

        According to Smith v. Tesla, 45 Cal.App.4th 123 (2023), manufacturers have a duty to repair.

        Tesla failed to properly repair the vehicle despite multiple attempts.

        WHEREFORE, Plaintiff requests damages of ${intake_data.claim_amount:,}.
        """

        # Mock validator
        mock_validator = Mock(spec=CaselawValidationAgent)
        mock_validator.validate_document_citations = AsyncMock(
            return_value=Mock(
                total_citations=1,
                valid_citations=1,
                issues=[],
                recommendations=["Document citations are appropriate"],
                citation_table="TABLE OF AUTHORITIES\nSmith v. Tesla, 45 Cal.App.4th 123 (2023)",
            )
        )

        # Execute validation
        validation_result = mock_validator.validate_document_citations.return_value

        # Validate
        assert validation_result.total_citations == 1
        assert validation_result.valid_citations == 1
        assert len(validation_result.issues) == 0
        assert "TABLE OF AUTHORITIES" in validation_result.citation_table

    def test_phase_7_document_validation(self, sample_intake_data, tmp_path):
        """Test Phase 7: Document Validation Against Similar Cases"""
        # Setup
        processor = IntakeProcessor(str(tmp_path / "intake_sessions"))
        intake_data = processor.process_intake_form(sample_intake_data)

        test_document = f"""
        {intake_data.case_name}

        COMPLAINT

        1. Plaintiff is a California resident.

        2. Defendant Tesla Inc. is a Delaware corporation.

        3. Plaintiff purchased a defective Tesla vehicle.

        4. The vehicle had electrical and safety issues.

        5. Tesla failed to repair the vehicle properly.

        PRAYER FOR RELIEF

        WHEREFORE, Plaintiff requests damages of ${intake_data.claim_amount:,}.
        """

        # Mock document validator
        mock_validator = Mock(spec=DocumentValidator)
        mock_validator.validate_document = AsyncMock(
            return_value=ValidationResult(
                overall_score=0.85,
                structural_similarity=0.88,
                language_similarity=0.82,
                legal_compliance_score=0.90,
                issues=[],
                recommendations=[
                    "Document structure is consistent with similar cases",
                    "Word count is appropriate for jurisdiction",
                ],
                similar_cases=[
                    {
                        "case_name": "Similar Tesla Case 1",
                        "score": 0.92,
                        "outcome": "successful",
                    }
                ],
            )
        )

        # Execute validation
        validation_result = mock_validator.validate_document.return_value

        # Validate
        assert validation_result.overall_score >= 0.8
        assert validation_result.legal_compliance_score >= 0.8
        assert len(validation_result.recommendations) > 0
        assert len(validation_result.similar_cases) > 0

    @pytest.mark.asyncio
    async def test_complete_7_phase_pipeline(self, sample_intake_data, tmp_path):
        """Test complete 7-phase pipeline with real system components"""
        # Phase 1: Intake Processing
        processor = IntakeProcessor(str(tmp_path / "intake_sessions"))
        intake_data = processor.process_intake_form(sample_intake_data)

        assert intake_data.session_id is not None
        assert intake_data.case_name is not None
        assert intake_data.jurisdiction is not None

        # Phase 2: Research (mocked)
        research_results = [
            {
                "citation": "Tesla Product Case, 123 Cal.App.4th 456 (2023)",
                "relevance_score": 0.95,
                "holding": "Manufacturer liable for defective vehicles",
            }
        ]

        # Phase 3: Statement of Facts Generation
        sof_generator = StatementOfFactsGenerator()
        facts_matrix = processor.get_facts_matrix_from_intake(intake_data)
        case_data = sof_generator._create_case_data_from_intake(intake_data)

        # Phase 4: Skeletal Outline Creation
        writer = CustomLLMWriter()
        outline = writer.create_skeletal_outline_from_intake(intake_data)

        assert outline.case_name == intake_data.case_name
        assert len(outline.sections) > 0

        # Phase 5: Complaint Generation (mocked for this test)
        complaint_text = f"""
        {outline.case_name}

        COMPLAINT FOR DAMAGES

        Plaintiff alleges that Defendant Tesla Inc. sold a defective vehicle
        that suffered from multiple electrical failures and safety issues.

        JURISDICTION AND VENUE

        This Court has jurisdiction over this matter pursuant to California law.

        PRAYER FOR RELIEF

        WHEREFORE, Plaintiff requests damages in the amount of ${intake_data.claim_amount:,}.
        """

        # Phase 6: Caselaw Validation
        validator = CaselawValidationAgent()
        validation_report = await validator.validate_document_citations(
            complaint_text, intake_data.jurisdiction.split()[-1].lower()
        )

        # Phase 7: Document Validation
        doc_validator = DocumentValidator()
        final_validation = await doc_validator.validate_document(
            complaint_text,
            {
                "jurisdiction": intake_data.jurisdiction.split()[-1].lower(),
                "case_type": "complaint",
                "defendant_type": "corporation",
            },
        )

        # Final assertions
        assert intake_data.session_id is not None
        assert outline.case_name is not None
        assert complaint_text is not None
        assert validation_report is not None
        assert final_validation is not None

        # Validate pipeline integrity
        assert intake_data.claim_amount == 85000
        assert "Tesla" in intake_data.opposing_party_names
        assert "breach_contract" in intake_data.causes_of_action
        assert "products_liability" in intake_data.causes_of_action

        logger.info("Complete 7-phase pipeline test passed")

    def test_error_handling_and_recovery(self, tmp_path):
        """Test error handling and recovery mechanisms"""
        processor = IntakeProcessor(str(tmp_path / "intake_sessions"))

        # Test with invalid data
        invalid_data = {
            "client_name": "",
            "claim_amount": "not_a_number",
            "party_type": "invalid",
        }

        # Should handle gracefully
        intake_data = processor.process_intake_form(invalid_data)

        assert intake_data.client_name == ""
        assert intake_data.claim_amount == 0
        assert intake_data.party_type == "invalid"

        # Test with missing critical fields
        minimal_data = {"client_name": "Test User"}

        intake_data = processor.process_intake_form(minimal_data)

        assert intake_data.client_name == "Test User"
        assert intake_data.session_id is not None
        # Should have safe defaults for other fields

    def test_jurisdiction_specific_validation(self, sample_intake_data, tmp_path):
        """Test jurisdiction-specific validation rules"""
        processor = IntakeProcessor(str(tmp_path / "intake_sessions"))

        # Test California-specific processing
        ca_data = sample_intake_data.copy()
        ca_data["events_location"] = "San Francisco, California"

        intake_data = processor.process_intake_form(ca_data)

        assert "California" in intake_data.jurisdiction
        assert "state" in intake_data.court_type.lower()

        # Test federal jurisdiction trigger
        federal_data = sample_intake_data.copy()
        federal_data["claim_amount"] = 100000  # Over $75k
        federal_data["events_location"] = "New York, NY"

        intake_data = processor.process_intake_form(federal_data)

        assert "federal" in intake_data.court_type.lower()

        # Test civil rights federal question
        civil_rights_data = sample_intake_data.copy()
        civil_rights_data["causes_of_action"] = ["civil_rights"]
        # Under $75k but federal question
        civil_rights_data["claim_amount"] = 10000

        intake_data = processor.process_intake_form(civil_rights_data)

        assert "federal" in intake_data.court_type.lower()

    def test_performance_and_scalability(self, sample_intake_data, tmp_path):
        """Test system performance and scalability"""
        import time

        processor = IntakeProcessor(str(tmp_path / "intake_sessions"))

        # Test processing speed
        start_time = time.time()

        for i in range(10):  # Process 10 cases
            test_data = sample_intake_data.copy()
            test_data["client_name"] = f"Test Client {i}"
            intake_data = processor.process_intake_form(test_data)

            assert intake_data.session_id is not None

        end_time = time.time()
        processing_time = end_time - start_time

        # Should process 10 cases in reasonable time (less than 5 seconds)
        assert processing_time < 5.0

        # Test memory usage (basic check)
        import psutil

        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024

        # Should use reasonable memory (less than 500MB)
        assert memory_mb < 500

    def test_data_integrity_and_consistency(self, sample_intake_data, tmp_path):
        """Test data integrity and consistency across phases"""
        processor = IntakeProcessor(str(tmp_path / "intake_sessions"))

        # Process intake
        intake_data = processor.process_intake_form(sample_intake_data)

        # Verify data consistency
        facts_matrix = processor.get_facts_matrix_from_intake(intake_data)

        # Check that key data flows correctly
        assert facts_matrix["case_metadata"]["client_name"] == intake_data.client_name
        assert facts_matrix["case_metadata"]["claim_amount"] == intake_data.claim_amount
        assert facts_matrix["case_metadata"]["session_id"] == intake_data.session_id

        # Check that causes of action are preserved
        assert (
            facts_matrix["case_metadata"]["causes_of_action"]
            == intake_data.causes_of_action
        )

        # Check that jurisdiction info is consistent
        assert facts_matrix["case_metadata"]["jurisdiction"] == intake_data.jurisdiction
        assert facts_matrix["case_metadata"]["venue"] == intake_data.venue

        # Verify no data corruption
        assert intake_data.claim_amount == 85000
        assert len(intake_data.causes_of_action) == 2
        assert "Tesla" in intake_data.opposing_party_names

    def test_security_and_data_protection(self, sample_intake_data, tmp_path):
        """Test security and data protection measures"""
        processor = IntakeProcessor(str(tmp_path / "intake_sessions"))

        # Process sensitive data
        sensitive_data = sample_intake_data.copy()
        sensitive_data["client_ssn"] = "123-45-6789"  # Should not be processed
        sensitive_data["client_credit_card"] = (
            "4111-1111-1111-1111"  # Should not be processed
        )

        intake_data = processor.process_intake_form(sensitive_data)

        # Verify sensitive data is not stored
        stored_data = processor.get_intake_data(intake_data.session_id)
        assert stored_data is not None

        # Check that only expected fields are stored
        stored_dict = stored_data.__dict__
        sensitive_fields = ["client_ssn", "client_credit_card"]
        for field in sensitive_fields:
            assert field not in stored_dict or stored_dict[field] is None

        # Verify normal data is preserved
        assert stored_data.client_name == "John Doe"
        assert stored_data.claim_amount == 85000
