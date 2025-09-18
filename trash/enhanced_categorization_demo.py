"""
Enhanced Document Categorization Demo for LawyerFactory
Demonstrates the complete advanced document categorization system
with defendant-specific clusters and drafting validation.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict

from .phases05_drafting.drafting_validator import DraftingValidator

# Import the new enhanced components
from .phasesphaseA01_intake.enhanced_document_categorizer import (
    EnhancedDocumentCategorizer,
)
from .phasesphaseA01_intake.enhanced_intake_processor import EnhancedIntakeProcessor
from .phasesphaseA01_intake.legal_intake_form import IntakeFormData, LegalIntakeForm
from .phasesphaseA01_intake.vector_cluster_manager import VectorClusterManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnhancedCategorizationDemo:
    """
    Complete demonstration of the enhanced document categorization system.
    Shows how the system works with any defendant from intake forms.
    """

    def __init__(self):
        self.categorizer = EnhancedDocumentCategorizer()
        self.cluster_manager = VectorClusterManager()
        self.intake_processor = EnhancedIntakeProcessor(
            intake_processor=self,  # Self-reference for integration
            cluster_manager=self.cluster_manager
        )
        self.drafting_validator = DraftingValidator(
            intake_processor=self.intake_processor,
            cluster_manager=self.cluster_manager
        )
        self.intake_form = LegalIntakeForm()

    async def run_complete_demo(self):
        """Run the complete enhanced categorization demonstration"""
        print("🚀 Starting Enhanced Document Categorization Demo")
        print("=" * 60)

        # Step 1: Process intake form for Tesla case
        print("\n📋 Step 1: Processing Intake Form")
        tesla_case = await self._demo_intake_form_processing()

        # Step 2: Add various document types to clusters
        print("\n📄 Step 2: Processing Different Document Types")
        await self._demo_document_processing(tesla_case['case_id'])

        # Step 3: Show cluster analysis
        print("\n📊 Step 3: Cluster Analysis")
        await self._demo_cluster_analysis(tesla_case['case_id'])

        # Step 4: Validate draft complaint
        print("\n⚖️ Step 4: Draft Complaint Validation")
        await self._demo_draft_validation(tesla_case['case_id'])

        # Step 5: Process intake form for different defendant
        print("\n🏢 Step 5: Generic System - Different Defendant")
        await self._demo_generic_defendant()

        print("\n✅ Enhanced Categorization Demo Complete!")
        print("=" * 60)

    async def _demo_intake_form_processing(self) -> Dict[str, Any]:
        """Demonstrate intake form processing"""
        # Create sample Tesla intake form data
        intake_data = IntakeFormData(
            user_name="John Smith",
            user_address="123 Main St, Anytown, CA 12345",
            other_party_name="Tesla, Inc.",
            other_party_address="3500 Deer Creek Road, Palo Alto, CA 94304",
            party_role="plaintiff",
            event_location="San Francisco, CA",
            event_date="2024-01-15",
            claim_description="Vehicle autopilot system malfunction causing accident",
            selected_causes=["Negligence", "Products Liability"],
            jurisdiction="California Northern District",
            venue="San Francisco County",
            case_type="Personal Injury"
        )

        print(f"Processing intake form for: {intake_data.claim_description}")
        print(f"Defendant: {intake_data.other_party_name}")
        print(f"Jurisdiction: {intake_data.jurisdiction}")

        # Process the intake form
        result = await self.intake_processor.process_intake_form(intake_data)

        if result['success']:
            print("✅ Intake form processed successfully"            print(f"   Case ID: {result['case_id']}")
            print(f"   Cluster ID: {result['cluster_id']}")
            print(f"   Defendant: {result['defendant_name']}")
            print(".2%")

            return {
                'case_id': result['case_id'],
                'cluster_id': result['cluster_id'],
                'defendant_name': result['defendant_name']
            }
        else:
            print(f"❌ Intake form processing failed: {result['error']}")
            return {}

    async def _demo_document_processing(self, case_id: str):
        """Demonstrate processing different types of documents"""
        # Sample documents for different categories
        sample_documents = {
            "tesla_complaint_1.txt": {
                "content": """
                COMPLAINT FOR NEGLIGENCE AND PRODUCTS LIABILITY

                Plaintiff John Smith alleges:

                1. Defendant Tesla, Inc. designed, manufactured, and sold a vehicle equipped with an autopilot system.

                2. On January 15, 2024, in San Francisco, California, Plaintiff was operating the Tesla vehicle when the autopilot system malfunctioned.

                3. The malfunction caused the vehicle to accelerate uncontrollably, resulting in a collision.

                4. Tesla was negligent in the design, testing, and deployment of the autopilot system.

                5. The autopilot system was defectively designed and unreasonably dangerous.

                WHEREFORE, Plaintiff prays for judgment against Defendant Tesla, Inc. for damages, costs, and fees.
                """,
                "expected_type": "plaintiff_complaint"
            },
            "tesla_answer.txt": {
                "content": """
                DEFENDANT TESLA, INC.'S ANSWER TO COMPLAINT

                Defendant Tesla, Inc., by and through counsel, hereby answers the Complaint as follows:

                1. Admit that Tesla designed and manufactured vehicles with autopilot systems.

                2. Deny that any autopilot system malfunctioned on January 15, 2024.

                3. Deny that any alleged malfunction was caused by negligence or defective design.

                4. Assert that Plaintiff was solely responsible for the accident due to misuse of the vehicle.

                AFFIRMATIVE DEFENSES

                1. Comparative negligence
                2. Assumption of risk
                3. Product misuse

                WHEREFORE, Defendant Tesla, Inc. respectfully requests that this Court dismiss the Complaint with prejudice.
                """,
                "expected_type": "defendant_answer"
            },
            "judge_opinion.txt": {
                "content": """
                UNITED STATES DISTRICT COURT
                NORTHERN DISTRICT OF CALIFORNIA

                MEMORANDUM AND ORDER

                This matter comes before the Court on Defendant's motion to dismiss.

                The Court has reviewed the pleadings, papers, and evidence submitted by the parties.

                For the reasons stated below, Defendant's motion to dismiss is GRANTED.

                The Court finds that Plaintiff has failed to state a claim upon which relief can be granted.

                The complaint is DISMISSED WITH PREJUDICE.

                IT IS SO ORDERED this 15th day of March, 2024.

                /s/ Judge Mary Johnson
                UNITED STATES DISTRICT JUDGE
                """,
                "expected_type": "judge_opinion"
            }
        }

        for filename, doc_info in sample_documents.items():
            print(f"\nProcessing: {filename}")
            print(f"Expected type: {doc_info['expected_type']}")

            # Create temporary file
            temp_path = f"/tmp/{filename}"
            with open(temp_path, 'w') as f:
                f.write(doc_info['content'])

            # Process document
            result = await self.intake_processor.process_document(
                file_path=temp_path,
                case_id=case_id
            )

            if result['success']:
                print("✅ Document processed successfully"                print(f"   Document ID: {result['document_id']}")
                print(f"   Detected type: {result['document_type']}")
                print(f"   Authority level: {result['authority_level']}")
                print(".2%")
                print(f"   Similar documents: {result['similar_documents']}")
                print(f"   Defendant recognized: {result['defendant_recognized']}")
            else:
                print(f"❌ Document processing failed: {result['error']}")

            # Clean up temp file
            Path(temp_path).unlink(missing_ok=True)

    async def _demo_cluster_analysis(self, case_id: str):
        """Demonstrate cluster analysis capabilities"""
        case_info = self.intake_processor.active_cases.get(case_id)
        if not case_info:
            print("❌ Case not found for analysis")
            return

        cluster_id = case_info['cluster_id']
        print(f"Analyzing cluster: {cluster_id}")

        # Get cluster analysis
        analysis = await self.cluster_manager.get_cluster_analysis(cluster_id)

        if analysis:
            print("✅ Cluster analysis completed"            print(f"   Total documents: {analysis.total_documents}")
            print(f"   Average similarity: {analysis.average_similarity:.2f}")
            print(f"   Quality score: {analysis.quality_score:.2f}")
            print(f"   Validation threshold: {analysis.validation_threshold}")

            print("\n   Document types:")
            for doc_type, count in analysis.document_types.items():
                print(f"     - {doc_type.value}: {count}")

            print("\n   Authority levels:")
            for auth_level, count in analysis.authority_levels.items():
                print(f"     - {auth_level.value}: {count}")
        else:
            print("❌ Cluster analysis failed")

    async def _demo_draft_validation(self, case_id: str):
        """Demonstrate draft complaint validation"""
        # Sample draft complaint
        draft_complaint = """
        DRAFT COMPLAINT FOR NEGLIGENCE

        Plaintiff John Smith alleges:

        1. Defendant Tesla, Inc. is a corporation doing business in California.

        2. On January 15, 2024, Plaintiff was driving a Tesla vehicle in San Francisco.

        3. The autopilot system failed, causing an accident.

        4. Tesla was negligent in designing and testing the autopilot system.

        5. As a result, Plaintiff suffered injuries and damages.

        WHEREFORE, Plaintiff requests judgment against Tesla for $1,000,000 in damages.
        """

        print("Validating draft complaint...")
        print(f"Draft length: {len(draft_complaint)} characters")

        # Validate the draft
        validation_result = await self.drafting_validator.validate_draft_complaint(
            draft_text=draft_complaint,
            case_id=case_id
        )

        print("
📋 Validation Results:"        print(".2f"        print(".2f"        print(".2%"        print(f"   Valid: {'✅ YES' if validation_result.is_valid else '❌ NO'}")

        if validation_result.issues_found:
            print("
   Issues found:"            for issue in validation_result.issues_found[:3]:  # Show first 3
                print(f"     - {issue}")

        if validation_result.recommendations:
            print("
   Recommendations:"            for rec in validation_result.recommendations[:3]:  # Show first 3
                print(f"     - {rec}")

        if validation_result.missing_elements:
            print("
   Missing elements:"            for element in validation_result.missing_elements:
                print(f"     - {element}")

        print(".2f")

    async def _demo_generic_defendant(self):
        """Demonstrate the system working with a different defendant"""
        print("Testing system with different defendant: Apple Inc.")

        # Create intake form for Apple case
        apple_intake = IntakeFormData(
            user_name="Jane Doe",
            user_address="456 Oak Ave, Cupertino, CA 95014",
            other_party_name="Apple Inc.",
            other_party_address="One Apple Park Way, Cupertino, CA 95014",
            party_role="plaintiff",
            event_location="Cupertino, CA",
            event_date="2024-02-20",
            claim_description="Product defect in Apple device causing injury",
            selected_causes=["Products Liability", "Negligence"],
            jurisdiction="California Northern District",
            venue="Santa Clara County",
            case_type="Product Liability"
        )

        # Process Apple intake form
        apple_result = await self.intake_processor.process_intake_form(apple_intake)

        if apple_result['success']:
            print("✅ Apple case processed successfully"            print(f"   Case ID: {apple_result['case_id']}")
            print(f"   Cluster ID: {apple_result['cluster_id']}")
            print(f"   Defendant: {apple_result['defendant_name']}")

            # Show that different clusters are created for different defendants
            print("
📂 Current defendant-specific clusters:"            defendant_clusters = self.intake_processor.get_defendant_clusters()
            for cluster in defendant_clusters:
                print(f"   - {cluster}")

            print("
✅ System successfully creates separate clusters for different defendants!"        else:
            print(f"❌ Apple case processing failed: {apple_result['error']}")


async def main():
    """Main demonstration function"""
    demo = EnhancedCategorizationDemo()

    try:
        await demo.run_complete_demo()
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"\n❌ Demo failed with error: {e}")
        print("This might be due to missing dependencies or configuration issues.")
        print("The enhanced categorization system is designed to work with:")
        print("  - Vector embeddings (sentence-transformers or similar)")
        print("  - JSON storage for clusters")
        print("  - Legal document processing capabilities")


if __name__ == "__main__":
    print("🔧 Enhanced Document Categorization System Demo")
    print("This system provides:")
    print("  • Advanced document categorization beyond primary/secondary")
    print("  • Defendant-specific vector clusters")
    print("  • Judge opinions, complaints, answers, motions separation")
    print("  • Draft validation against ideal complaint datasets")
    print("  • Generic system for any defendant from intake forms")
    print()

    # Run the demo
    asyncio.run(main())