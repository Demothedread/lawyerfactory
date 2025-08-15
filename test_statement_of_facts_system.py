"""
Comprehensive Test Suite for Statement of Facts Generation System
Tests all components: generation, templates, review interface, and export system
"""

import logging
import json
import tempfile
import shutil
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import unittest

# Import the Statement of Facts system components
from statement_of_facts_generator import StatementOfFactsGenerator, LegalFact, FactCategory
from legal_document_templates import LegalDocumentTemplates, DocumentType, CourtLevel
from attorney_review_interface import AttorneyReviewInterface, ReviewStatus, ReviewPriority
from document_export_system import DocumentExportSystem, ExportFormat, DocumentMetadata

logger = logging.getLogger(__name__)


class TestStatementOfFactsSystem(unittest.TestCase):
    """Comprehensive test suite for Statement of Facts system"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.session_id = "test_session_001"
        
        # Create test data
        self.test_case_data = {
            'plaintiff_name': 'John Doe',
            'defendant_name': 'MegaCorp Industries',
            'case_number': '2024-CV-12345',
            'court': 'Superior Court of California, County of Los Angeles',
            'document_purpose': 'Plaintiff\'s Motion for Summary Judgment',
            'attorney_name': 'Jane Attorney',
            'attorney_title': 'Attorney at Law',
            'bar_number': 'State Bar No. 123456',
            'conclusion_statement': 'the facts establish liability and entitle Plaintiff to judgment as a matter of law'
        }
        
        self.test_facts_matrix = {
            'undisputed_facts': [
                {
                    'text': 'On January 15, 2024, Plaintiff John Doe was employed by Defendant MegaCorp Industries.',
                    'confidence': 0.95,
                    'source_documents': ['employment_contract.pdf'],
                    'supporting_evidence': ['Ex. A'],
                    'date': '2024-01-15',
                    'legal_significance': 'employment_relationship'
                },
                {
                    'text': 'Defendant terminated Plaintiff\'s employment on March 20, 2024.',
                    'confidence': 0.9,
                    'source_documents': ['termination_letter.pdf'],
                    'supporting_evidence': ['Ex. B'],
                    'date': '2024-03-20',
                    'legal_significance': 'adverse_employment_action'
                }
            ],
            'disputed_facts': [
                {
                    'text': 'Defendant terminated Plaintiff because of his age.',
                    'confidence': 0.6,
                    'source_documents': ['witness_statement.pdf'],
                    'supporting_evidence': ['Witness Decl.'],
                    'is_disputed': True,
                    'legal_significance': 'discriminatory_motive'
                }
            ],
            'key_events': [
                {
                    'text': 'Plaintiff filed a complaint with HR regarding age discrimination on February 10, 2024.',
                    'confidence': 0.85,
                    'source_documents': ['hr_complaint.pdf'],
                    'supporting_evidence': ['Ex. C'],
                    'date': '2024-02-10',
                    'legal_significance': 'protected_activity'
                }
            ],
            'background_context': [
                {
                    'text': 'Plaintiff was 58 years old at the time of termination.',
                    'confidence': 0.95,
                    'source_documents': ['personnel_file.pdf'],
                    'supporting_evidence': ['Personnel Records'],
                    'legal_significance': 'protected_class'
                }
            ],
            'damages_claims': [
                {
                    'text': 'Plaintiff seeks damages for lost wages in the amount of $150,000.',
                    'confidence': 0.8,
                    'source_documents': ['wage_calculation.xlsx'],
                    'supporting_evidence': ['Damages Calculation'],
                    'legal_significance': 'compensatory_damages'
                }
            ]
        }
    
    def tearDown(self):
        """Clean up test environment"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_statement_of_facts_generator(self):
        """Test the core Statement of Facts generator"""
        print("\n=== Testing Statement of Facts Generator ===")
        
        # Create generator with mock knowledge graph
        generator = StatementOfFactsGenerator()
        
        # Mock the knowledge graph integration
        generator.kg_integration = MockKnowledgeGraphIntegration(self.test_facts_matrix)
        
        # Generate Statement of Facts
        result = generator.generate_statement_of_facts(
            self.session_id,
            self.test_case_data
        )
        
        # Verify results
        self.assertIn('document', result)
        self.assertIn('verification_report', result)
        self.assertIn('attorney_review_points', result)
        self.assertIn('export_formats', result)
        
        # Check document structure
        document = result['document']
        self.assertIn('content', document)
        self.assertIn('sections', document)
        self.assertGreater(document['word_count'], 0)
        self.assertGreater(document['paragraph_count'], 0)
        
        # Verify sections are properly structured
        sections = document['sections']
        section_titles = [section['title'] for section in sections]
        expected_sections = ['INTRODUCTION AND PARTIES', 'JURISDICTION AND VENUE', 
                           'BACKGROUND FACTS', 'MATERIAL FACTS', 'DAMAGES AND RELIEF SOUGHT']
        
        for expected in expected_sections:
            self.assertIn(expected, section_titles)
        
        print(f"✓ Generated document with {document['word_count']} words and {document['paragraph_count']} paragraphs")
        print(f"✓ Created {len(sections)} sections")
        print(f"✓ Identified {len(result['attorney_review_points'])} review points")
    
    def test_legal_document_templates(self):
        """Test the legal document templates system"""
        print("\n=== Testing Legal Document Templates ===")
        
        templates = LegalDocumentTemplates()
        
        # Test template loading
        statement_templates = templates.templates[DocumentType.STATEMENT_OF_FACTS.value]
        self.assertIn('header', statement_templates)
        self.assertIn('section', statement_templates)
        self.assertIn('fact_paragraph', statement_templates)
        self.assertIn('conclusion', statement_templates)
        
        # Test case caption formatting
        case_caption = templates.get_case_caption_template(CourtLevel.STATE_SUPERIOR)
        self.assertIn('{plaintiff_name}', case_caption)
        self.assertIn('{defendant_name}', case_caption)
        self.assertIn('{case_number}', case_caption)
        
        # Test Bluebook citation formats
        citation_formats = templates.get_bluebook_citation_formats()
        self.assertIn('case_citation', citation_formats)
        self.assertIn('record_citation', citation_formats)
        self.assertIn('exhibit_citation', citation_formats)
        
        # Test citation validation
        test_citation = "Smith v. Jones, 123 F.3d 456 (9th Cir. 2020)"
        validation = templates.validate_citation_format(test_citation, 'case_citation')
        self.assertIn('is_valid', validation)
        
        print("✓ Templates loaded successfully")
        print("✓ Case caption formatting verified")
        print("✓ Bluebook citation formats available")
        print("✓ Citation validation functional")
    
    def test_attorney_review_interface(self):
        """Test the attorney review interface"""
        print("\n=== Testing Attorney Review Interface ===")
        
        review_interface = AttorneyReviewInterface(str(self.test_dir / "review"))
        
        # Create mock document data
        document_data = {
            'document': {
                'sections': [
                    {
                        'title': 'MATERIAL FACTS',
                        'facts': [
                            {
                                'id': 'fact_001',
                                'text': 'Test fact requiring review',
                                'confidence': 0.6,
                                'is_disputed': False,
                                'citation': '(Ex. A)'
                            },
                            {
                                'id': 'fact_002',
                                'text': 'Disputed fact requiring attention',
                                'confidence': 0.4,
                                'is_disputed': True,
                                'citation': ''
                            }
                        ]
                    }
                ]
            },
            'verification_report': {
                'total_facts': 2,
                'disputed_facts_count': 1,
                'citation_coverage': 0.5
            },
            'attorney_review_points': [
                {
                    'type': 'confidence_review',
                    'priority': 'high',
                    'description': 'Review low confidence facts'
                }
            ]
        }
        
        # Initiate review session
        review_result = review_interface.initiate_review_session(
            self.session_id,
            document_data,
            "Attorney Jane Smith"
        )
        
        self.assertIn('session_id', review_result)
        self.assertGreater(review_result['review_items_count'], 0)
        self.assertGreater(review_result['pending_decisions_count'], 0)
        
        # Test fact review
        review_decision = {
            'decision': 'revise',
            'revised_text': 'Revised test fact with better evidence',
            'justification': 'Added stronger supporting evidence',
            'comment': 'This fact needed revision for clarity',
            'priority': 'medium'
        }
        
        fact_review_result = review_interface.review_fact(
            self.session_id,
            'fact_001',
            review_decision
        )
        
        self.assertEqual(fact_review_result['fact_id'], 'fact_001')
        self.assertEqual(fact_review_result['new_status'], ReviewStatus.REQUIRES_REVISION.value)
        self.assertTrue(fact_review_result['revision_created'])
        
        # Test dashboard
        dashboard = review_interface.get_review_dashboard(self.session_id)
        self.assertIn('session_info', dashboard)
        self.assertIn('progress', dashboard)
        self.assertIn('priority_items', dashboard)
        
        print("✓ Review session initiated successfully")
        print("✓ Fact review process functional")
        print("✓ Dashboard generation working")
        print(f"✓ Processing {review_result['review_items_count']} review items")
    
    def test_document_export_system(self):
        """Test the document export system"""
        print("\n=== Testing Document Export System ===")
        
        export_system = DocumentExportSystem(str(self.test_dir / "export"))
        
        # Create test document
        test_content = """STATEMENT OF FACTS

John Doe v. MegaCorp Industries
Case No. 2024-CV-12345

I. MATERIAL FACTS

1. On January 15, 2024, Plaintiff was employed by Defendant. (Ex. A)

2. Defendant terminated Plaintiff's employment on March 20, 2024. (Ex. B)

CONCLUSION

Based on the foregoing facts, Plaintiff is entitled to judgment as a matter of law.
"""
        
        # Create document metadata
        metadata = DocumentMetadata(
            document_id="test_doc_001",
            title="Statement of Facts - Doe v. MegaCorp",
            document_type="statement_of_facts",
            case_number="2024-CV-12345",
            client_name="John Doe",
            attorney_name="Jane Attorney",
            creation_date=datetime.now(),
            last_modified=datetime.now(),
            version="1.0",
            status="draft",
            word_count=len(test_content.split()),
            paragraph_count=2,
            citation_count=2
        )
        
        # Create document version
        version_info = export_system.create_document_version(
            "test_doc_001",
            test_content,
            "Attorney Jane Smith",
            "Initial Statement of Facts draft",
            metadata
        )
        
        self.assertIn('version_id', version_info.__dict__)
        self.assertEqual(version_info.author, "Attorney Jane Smith")
        
        # Test export in multiple formats
        export_package = export_system.export_document(
            "test_doc_001",
            formats=[ExportFormat.MARKDOWN, ExportFormat.PLAIN_TEXT, ExportFormat.HTML]
        )
        
        self.assertIn('package_id', export_package.__dict__)
        self.assertEqual(len(export_package.export_formats), 3)
        self.assertIn('statement_of_facts.md', export_package.documents)
        self.assertIn('statement_of_facts.txt', export_package.documents)
        self.assertIn('statement_of_facts.html', export_package.documents)
        
        # Test document history
        history = export_system.get_document_history("test_doc_001")
        self.assertEqual(history['version_count'], 1)
        self.assertEqual(history['total_authors'], 1)
        
        print("✓ Document version created successfully")
        print("✓ Multi-format export functional")
        print(f"✓ Exported in {len(export_package.export_formats)} formats")
        print("✓ Version history tracking working")
    
    def test_integration_workflow(self):
        """Test complete integration workflow"""
        print("\n=== Testing Complete Integration Workflow ===")
        
        # 1. Generate Statement of Facts
        generator = StatementOfFactsGenerator()
        generator.kg_integration = MockKnowledgeGraphIntegration(self.test_facts_matrix)
        
        statement_result = generator.generate_statement_of_facts(
            self.session_id,
            self.test_case_data
        )
        
        # 2. Initiate attorney review
        review_interface = AttorneyReviewInterface(str(self.test_dir / "review"))
        review_session = review_interface.initiate_review_session(
            self.session_id,
            statement_result,
            "Attorney Jane Smith"
        )
        
        # 3. Process some reviews
        high_priority_items = [item for item in review_session['priority_items'] 
                              if item.get('priority') == 'high']
        
        for item in high_priority_items[:2]:  # Review first 2 high priority items
            if item.get('fact_id'):
                review_interface.review_fact(
                    self.session_id,
                    item['fact_id'],
                    {
                        'decision': 'approve',
                        'comment': 'Fact verified and approved',
                        'priority': 'high'
                    }
                )
        
        # 4. Generate revised document
        revised_result = review_interface.generate_revised_document(self.session_id)
        
        # 5. Export final document
        export_system = DocumentExportSystem(str(self.test_dir / "export"))
        
        # Create final version
        final_version = export_system.create_document_version(
            f"{self.session_id}_final",
            revised_result['revised_document'],
            "Attorney Jane Smith",
            "Final attorney-reviewed Statement of Facts"
        )
        
        # Export in litigation-ready formats
        final_export = export_system.export_document(
            f"{self.session_id}_final",
            formats=[ExportFormat.MICROSOFT_WORD, ExportFormat.PDF, ExportFormat.MARKDOWN]
        )
        
        # 6. Generate comprehensive report
        review_report = review_interface.export_review_report(self.session_id)
        
        # Verify complete workflow
        self.assertIn('document', statement_result)
        self.assertGreater(len(review_session['priority_items']), 0)
        self.assertIn('revised_document', revised_result)
        self.assertIn('version_id', final_version.__dict__)
        self.assertEqual(len(final_export.export_formats), 3)
        self.assertIn('report_metadata', review_report)
        
        print("✓ End-to-end workflow completed successfully")
        print(f"✓ Generated {statement_result['document']['paragraph_count']} paragraph Statement of Facts")
        print(f"✓ Processed {len(review_session['priority_items'])} priority review items")
        print(f"✓ Created final document with {len(final_export.export_formats)} export formats")
        print("✓ Attorney review report generated")
    
    def test_legal_compliance_standards(self):
        """Test compliance with legal writing standards"""
        print("\n=== Testing Legal Compliance Standards ===")
        
        templates = LegalDocumentTemplates()
        
        # Test FRCP compliance checklist
        frcp_checklist = templates.get_frcp_compliance_checklist()
        self.assertIn('rule_8_pleadings', frcp_checklist)
        self.assertIn('rule_10_form', frcp_checklist)
        self.assertIn('rule_11_good_faith', frcp_checklist)
        
        # Test legal writing standards
        writing_standards = templates.get_legal_writing_standards()
        self.assertIn('fact_writing', writing_standards)
        self.assertIn('citation_requirements', writing_standards)
        self.assertIn('document_structure', writing_standards)
        
        # Generate test document and check compliance
        generator = StatementOfFactsGenerator()
        generator.kg_integration = MockKnowledgeGraphIntegration(self.test_facts_matrix)
        
        result = generator.generate_statement_of_facts(
            self.session_id,
            self.test_case_data
        )
        
        # Check quality metrics
        quality_metrics = result['quality_metrics']
        self.assertIn('legal_writing_compliance', quality_metrics)
        self.assertIn('frcp_compliance', quality_metrics['legal_writing_compliance'])
        
        print("✓ FRCP compliance checklist available")
        print("✓ Legal writing standards defined")
        print("✓ Document quality assessment functional")
        print(f"✓ Compliance score: {quality_metrics.get('overall_quality_score', 0):.2f}")


class MockKnowledgeGraphIntegration:
    """Mock knowledge graph integration for testing"""
    
    def __init__(self, facts_matrix: Dict[str, Any]):
        self.facts_matrix = facts_matrix
    
    def generate_facts_matrix_and_statement(self, session_id: str) -> Dict[str, Any]:
        """Mock facts matrix generation"""
        return {
            'session_id': session_id,
            'generation_timestamp': datetime.now().isoformat(),
            'facts_matrix': self.facts_matrix,
            'statement_of_facts_outline': {
                'introduction': {
                    'parties': ['Plaintiff John Doe', 'Defendant MegaCorp Industries'],
                    'jurisdiction_and_venue': ['Superior Court of California'],
                    'case_overview': 'Employment discrimination case'
                }
            },
            'attorney_review_points': [
                {
                    'type': 'confidence_review',
                    'priority': 'high',
                    'description': 'Review facts with confidence below 0.7'
                },
                {
                    'type': 'citation_review',
                    'priority': 'medium',
                    'description': 'Add citations for uncited facts'
                }
            ]
        }


def run_comprehensive_tests():
    """Run comprehensive test suite"""
    print("🏛️  STATEMENT OF FACTS GENERATION SYSTEM - COMPREHENSIVE TESTING")
    print("=" * 80)
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Create test suite
    test_loader = unittest.TestLoader()
    test_suite = test_loader.loadTestsFromTestCase(TestStatementOfFactsSystem)
    
    # Run tests
    test_runner = unittest.TextTestRunner(verbosity=2, stream=open('/dev/null', 'w'))
    
    # Custom test execution with detailed output
    test_instance = TestStatementOfFactsSystem()
    test_instance.setUp()
    
    try:
        print("\n📋 Running Individual Component Tests...")
        test_instance.test_statement_of_facts_generator()
        test_instance.test_legal_document_templates()
        test_instance.test_attorney_review_interface()
        test_instance.test_document_export_system()
        
        print("\n🔄 Running Integration Tests...")
        test_instance.test_integration_workflow()
        test_instance.test_legal_compliance_standards()
        
        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED - STATEMENT OF FACTS SYSTEM READY FOR PRODUCTION")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
        
    finally:
        test_instance.tearDown()


if __name__ == "__main__":
    success = run_comprehensive_tests()
    exit(0 if success else 1)