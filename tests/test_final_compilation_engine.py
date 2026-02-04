#!/usr/bin/env python3
"""
Test script for the new Final Compilation Engine implementation
"""

import asyncio
from pathlib import Path
import sys

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from datetime import datetime

from lawyerfactory.phases.phaseC02_orchestration.final_compilation_engine import (
    get_final_compilation_engine,
)
from lawyerfactory.phases.phaseC02_orchestration.workflow_models import PhaseResult, PhaseStatus


async def test_final_compilation():
    """Test the final compilation engine with mock data"""
    print("🧪 Testing Final Compilation Engine")

    # Create test instance
    engine = get_final_compilation_engine()
    print(f"✓ Engine initialized: {type(engine).__name__}")

    # Create mock phase outputs
    phase_outputs = {
        "A01": PhaseResult(
            phase_id="A01",
            status=PhaseStatus.COMPLETED,
            output_data={
                "case_name": "Acme Corp. v. Widget Co.",
                "case_number": "SC-2024-00123",
                "court_name": "Superior Court of California, County of Alameda",
                "jurisdiction": "California",
                "parties": {"plaintiff": "Acme Corp.", "defendant": "Widget Co."},
                "evidence_table": [
                    {"id": "ev1", "description": "Contract document", "source": "Client files"},
                    {"id": "ev2", "description": "Email correspondence", "source": "Discovery"},
                ],
                "extracted_facts": [
                    "Plaintiff signed contract on 2023-01-15",
                    "Defendant failed to perform",
                ],
            },
            execution_time=45.2,
            timestamp=datetime.now(),
            quality_score=0.92,
        ),
        "A02": PhaseResult(
            phase_id="A02",
            status=PhaseStatus.COMPLETED,
            output_data={
                "legal_authorities": [
                    {
                        "citation": "Smith v. Jones, 123 F.3d 456 (2d Cir. 2023)",
                        "summary": "Contract breach precedent",
                    },
                    {"citation": "42 U.S.C. § 1234", "summary": "Applicable statute"},
                ],
                "precedent_cases": ["Smith v. Jones", "Brown v. Davis"],
            },
            execution_time=67.8,
            timestamp=datetime.now(),
            quality_score=0.89,
        ),
        "A03": PhaseResult(
            phase_id="A03",
            status=PhaseStatus.COMPLETED,
            output_data={
                "case_outline": {"sections": ["Jurisdiction", "Facts", "Claims", "Prayer"]},
                "claims_matrix": [{"claim": "Breach of Contract", "elements": ["Duty", "Breach"]}],
                "argument_structure": ["Liability", "Damages"],
            },
            execution_time=32.5,
            timestamp=datetime.now(),
            quality_score=0.91,
        ),
        "B01": PhaseResult(
            phase_id="B01",
            status=PhaseStatus.COMPLETED,
            output_data={
                "quality_assessment": {"score": 0.9},
                "missing_elements": [],
                "recommendations": ["Proceed to drafting."],
            },
            execution_time=21.0,
            timestamp=datetime.now(),
            quality_score=0.9,
        ),
        "B02": PhaseResult(
            phase_id="B02",
            status=PhaseStatus.COMPLETED,
            output_data={
                "draft_documents": [
                    {
                        "id": "complaint_draft",
                        "type": "complaint",
                        "title": "Complaint for Breach of Contract",
                        "content": "COMES NOW Plaintiff...",
                        "metadata": {"pages": 12, "word_count": 3456},
                    }
                ]
            },
            execution_time=123.4,
            timestamp=datetime.now(),
            quality_score=0.87,
        ),
        "C01": PhaseResult(
            phase_id="C01",
            status=PhaseStatus.COMPLETED,
            output_data={
                "formatted_documents": [
                    {
                        "id": "complaint_final",
                        "type": "complaint",
                        "title": "Complaint for Breach of Contract - Final",
                        "content": "COMES NOW Plaintiff, by and through undersigned counsel...",
                        "metadata": {"pages": 12, "word_count": 3456, "formatted": True},
                    }
                ]
            },
            execution_time=34.1,
            timestamp=datetime.now(),
            quality_score=0.95,
        ),
    }

    print(f"✓ Created {len(phase_outputs)} mock phase results")

    # Test compilation
    try:
        result = await engine.execute_final_compilation(
            case_id="TEST_CASE_001",
            phase_outputs=phase_outputs,
            client_requirements={"custom_format": {"title": "Executive Summary", "format": "pdf"}},
        )

        print(f"✓ Compilation completed successfully: {result.success}")
        print(f"✓ Generated {len(result.deliverables)} deliverables")
        print(f"✓ Compilation time: {result.compilation_time:.2f}s")
        print(f"✓ Export paths: {len(result.export_paths)}")
        deliverable_types = {deliverable["type"] for deliverable in result.deliverables}
        print("✓ Deliverable types:", ", ".join(sorted(deliverable_types)))
        assert "cover_sheet" in deliverable_types
        assert "table_of_authorities" in deliverable_types
        assert "evidence_appendix" in deliverable_types

        if result.validation_results:
            print(f"✓ Validation overall valid: {result.validation_results.get('overall_valid')}")

        return True

    except Exception as e:
        print(f"❌ Compilation failed: {e}")
        return False


async def main():
    """Main test function"""
    print("=" * 50)
    print("Final Compilation Engine Integration Test")
    print("=" * 50)

    success = await test_final_compilation()

    if success:
        print("\n🎉 All tests passed!")
    else:
        print("\n❌ Tests failed!")

    return success


if __name__ == "__main__":
    asyncio.run(main())
