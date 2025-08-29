# Script Name: test_claims_matrix_core.py
# Description: Test suite for Claims Matrix core functionality Tests the enhanced knowledge graph, jurisdiction manager, and cause detection
# Relationships:
#   - Entity Type: Test
#   - Directory Group: Core
#   - Group Tags: claims-analysis, testing
Test suite for Claims Matrix core functionality
Tests the enhanced knowledge graph, jurisdiction manager, and cause detection
"""

import logging
import os
import tempfile
import unittest

from cause_of_action_detector import CauseOfActionDetector
from enhanced_knowledge_graph import (CauseOfAction, EnhancedKnowledgeGraph,
                                      FactElementAttachment, LegalElement,
                                      LegalEntity, LegalEntityType)

from lawyerfactory.kg.jurisdiction import JurisdictionAuthority, JurisdictionManager

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestClaimsMatrixCore(unittest.TestCase):
    """Test core Claims Matrix functionality"""
    
    def setUp(self):
        """Set up test environment"""
        # Create temporary database
        self.db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db_path = self.db_file.name
        self.db_file.close()
        
        # Initialize components
        self.kg = EnhancedKnowledgeGraph(self.db_path)
        self.jurisdiction_manager = JurisdictionManager(self.kg)
        self.cause_detector = CauseOfActionDetector(self.kg, self.jurisdiction_manager)
    
    def tearDown(self):
        """Clean up test environment"""
        self.kg.close()
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def test_enhanced_knowledge_graph_schema(self):
        """Test that enhanced knowledge graph schema is properly initialized"""
        logger.info("Testing enhanced knowledge graph schema...")
        
        # Test that claims matrix tables exist
        cursor = self.kg.conn.cursor()
        
        # Check causes_of_action table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='causes_of_action'")
        self.assertIsNotNone(cursor.fetchone(), "causes_of_action table should exist")
        
        # Check legal_elements table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='legal_elements'")
        self.assertIsNotNone(cursor.fetchone(), "legal_elements table should exist")
        
        # Check element_questions table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='element_questions'")
        self.assertIsNotNone(cursor.fetchone(), "element_questions table should exist")
        
        # Check fact_element_attachments table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='fact_element_attachments'")
        self.assertIsNotNone(cursor.fetchone(), "fact_element_attachments table should exist")
        
        cursor.close()
        logger.info("✅ Schema validation passed")
    
    def test_cause_of_action_crud(self):
        """Test CRUD operations for causes of action"""
        logger.info("Testing cause of action CRUD operations...")
        
        # Create test cause of action
        cause = CauseOfAction(
            jurisdiction='ca_state',
            cause_name='negligence',
            legal_definition='Failure to exercise reasonable care',
            authority_citation='Cal. Civ. Code § 1714',
            confidence_threshold=0.7
        )
        
        # Add cause of action
        cause_id = self.kg.add_cause_of_action(cause)
        self.assertIsInstance(cause_id, int, "Should return integer ID")
        self.assertGreater(cause_id, 0, "ID should be positive")
        
        # Retrieve causes for jurisdiction
        causes = self.kg.get_causes_of_action_by_jurisdiction('ca_state')
        self.assertEqual(len(causes), 1, "Should retrieve one cause")
        self.assertEqual(causes[0]['cause_name'], 'negligence', "Should match cause name")
        self.assertEqual(causes[0]['jurisdiction'], 'ca_state', "Should match jurisdiction")
        
        logger.info("✅ Cause of action CRUD passed")
    
    def test_legal_elements_crud(self):
        """Test CRUD operations for legal elements"""
        logger.info("Testing legal elements CRUD operations...")
        
        # First create a cause of action
        cause = CauseOfAction(
            jurisdiction='ca_state',
            cause_name='negligence',
            legal_definition='Failure to exercise reasonable care'
        )
        cause_id = self.kg.add_cause_of_action(cause)
        
        # Create legal element
        element = LegalElement(
            cause_of_action_id=cause_id,
            element_name='duty',
            element_order=1,
            element_definition='Legal obligation to exercise reasonable care',
            burden_of_proof='preponderance'
        )
        
        # Add legal element
        element_id = self.kg.add_legal_element(element)
        self.assertIsInstance(element_id, int, "Should return integer ID")
        
        # Retrieve elements for cause
        elements = self.kg.get_legal_elements_for_cause(cause_id)
        self.assertEqual(len(elements), 1, "Should retrieve one element")
        self.assertEqual(elements[0]['element_name'], 'duty', "Should match element name")
        self.assertEqual(elements[0]['burden_of_proof'], 'preponderance', "Should match burden")
        
        logger.info("✅ Legal elements CRUD passed")
    
    def test_jurisdiction_manager(self):
        """Test jurisdiction manager functionality"""
        logger.info("Testing jurisdiction manager...")
        
        # Get available jurisdictions
        jurisdictions = self.jurisdiction_manager.get_available_jurisdictions()
        self.assertGreater(len(jurisdictions), 0, "Should have available jurisdictions")
        
        # Test jurisdiction selection
        success = self.jurisdiction_manager.select_jurisdiction('ca_state')
        self.assertTrue(success, "Should successfully select CA state jurisdiction")
        
        current = self.jurisdiction_manager.get_current_jurisdiction()
        self.assertIsNotNone(current, "Should have current jurisdiction")
        self.assertEqual(current.jurisdiction_code, 'ca_state', "Should match selected jurisdiction")
        
        # Test adding jurisdiction authority
        authority = JurisdictionAuthority(
            jurisdiction='ca_state',
            authority_type='statute',
            authority_name='California Civil Code Section 1714',
            authority_citation='Cal. Civ. Code § 1714',
            precedence_level=5
        )
        
        auth_id = self.jurisdiction_manager.add_jurisdiction_authority(authority)
        self.assertIsInstance(auth_id, int, "Should return integer ID")
        
        # Retrieve authorities
        authorities = self.jurisdiction_manager.get_jurisdiction_authorities('ca_state')
        self.assertEqual(len(authorities), 1, "Should retrieve one authority")
        self.assertEqual(authorities[0]['authority_name'], 'California Civil Code Section 1714')
        
        logger.info("✅ Jurisdiction manager passed")
    
    def test_cause_detection(self):
        """Test cause of action detection from facts"""
        logger.info("Testing cause of action detection...")
        
        # Create test facts representing negligence case
        test_facts = [
            {
                'id': 'fact_1',
                'name': 'Vehicle Collision',
                'description': 'Defendant ran red light and collided with plaintiff vehicle causing injury',
                'type': 'event'
            },
            {
                'id': 'fact_2',
                'name': 'Duty of Care',
                'description': 'All drivers owe duty to exercise reasonable care while driving',
                'type': 'fact'
            },
            {
                'id': 'fact_3',
                'name': 'Medical Expenses',
                'description': 'Plaintiff suffered broken ribs and incurred $25,000 in medical damages',
                'type': 'evidence'
            }
        ]
        
        # Detect causes of action
        detected_causes = self.cause_detector.detect_causes_from_facts(test_facts, 'ca_state')
        
        self.assertGreater(len(detected_causes), 0, "Should detect at least one cause")
        
        # Check for negligence detection
        negligence_detected = any(c.cause_name == 'negligence' for c in detected_causes)
        self.assertTrue(negligence_detected, "Should detect negligence cause of action")
        
        # Check confidence score
        negligence_cause = next(c for c in detected_causes if c.cause_name == 'negligence')
        self.assertGreater(negligence_cause.confidence_score, 0.3, "Should have reasonable confidence")
        self.assertGreater(len(negligence_cause.supporting_facts), 0, "Should have supporting facts")
        self.assertGreater(len(negligence_cause.elements_detected), 0, "Should detect elements")
        
        logger.info("✅ Cause detection passed")
    
    def test_fact_element_attachment(self):
        """Test attaching facts to legal elements"""
        logger.info("Testing fact-element attachment...")
        
        # First create the hierarchy: cause -> element -> attachment
        cause = CauseOfAction(jurisdiction='ca_state', cause_name='negligence')
        cause_id = self.kg.add_cause_of_action(cause)
        
        element = LegalElement(
            cause_of_action_id=cause_id,
            element_name='damages',
            element_definition='Actual harm resulting from breach'
        )
        element_id = self.kg.add_legal_element(element)
        
        # Create a fact entity
        fact_entity = LegalEntity(
            id='fact_damages_001',
            entity_type=LegalEntityType.EVIDENCE,
            name='Medical Bills',
            description='$25,000 in medical expenses from collision injuries'
        )
        self.kg.add_legal_entity(fact_entity)
        
        # Create attachment
        attachment = FactElementAttachment(
            fact_entity_id='fact_damages_001',
            legal_element_id=element_id,
            attachment_type='supports',
            relevance_score=0.9,
            confidence_score=0.8,
            attachment_reasoning='Medical bills directly prove monetary damages'
        )
        
        # Add attachment
        attachment_id = self.kg.attach_fact_to_element(attachment)
        self.assertIsInstance(attachment_id, int, "Should return integer ID")
        
        # Retrieve attachments
        attachments = self.kg.get_fact_attachments_for_element(element_id)
        self.assertEqual(len(attachments), 1, "Should retrieve one attachment")
        self.assertEqual(attachments[0]['attachment_type'], 'supports')
        self.assertEqual(attachments[0]['relevance_score'], 0.9)
        
        logger.info("✅ Fact-element attachment passed")
    
    def test_case_strength_analysis(self):
        """Test case strength analysis functionality"""
        logger.info("Testing case strength analysis...")
        
        # Create cause with elements and attachments
        cause = CauseOfAction(jurisdiction='ca_state', cause_name='negligence')
        cause_id = self.kg.add_cause_of_action(cause)
        
        # Add duty element
        duty_element = LegalElement(
            cause_of_action_id=cause_id,
            element_name='duty',
            element_order=1
        )
        duty_id = self.kg.add_legal_element(duty_element)
        
        # Add damages element
        damages_element = LegalElement(
            cause_of_action_id=cause_id,
            element_name='damages',
            element_order=4
        )
        damages_id = self.kg.add_legal_element(damages_element)
        
        # Create supporting facts
        duty_fact = LegalEntity(
            id='duty_fact_001',
            entity_type=LegalEntityType.FACT,
            name='Driver Duty',
            description='All drivers owe duty of reasonable care'
        )
        self.kg.add_legal_entity(duty_fact)
        
        damages_fact = LegalEntity(
            id='damages_fact_001',
            entity_type=LegalEntityType.EVIDENCE,
            name='Medical Bills',
            description='$25,000 in medical expenses'
        )
        self.kg.add_legal_entity(damages_fact)
        
        # Attach facts to elements
        self.kg.attach_fact_to_element(FactElementAttachment(
            fact_entity_id='duty_fact_001',
            legal_element_id=duty_id,
            attachment_type='supports',
            relevance_score=0.8,
            confidence_score=0.9
        ))
        
        self.kg.attach_fact_to_element(FactElementAttachment(
            fact_entity_id='damages_fact_001',
            legal_element_id=damages_id,
            attachment_type='supports',
            relevance_score=0.9,
            confidence_score=0.8
        ))
        
        # Analyze case strength
        analysis = self.kg.get_case_strength_analysis(cause_id)
        
        self.assertNotIn('error', analysis, "Should not have error")
        self.assertEqual(analysis['total_elements'], 2, "Should have 2 elements")
        self.assertEqual(analysis['elements_with_support'], 2, "Both elements should have support")
        self.assertGreater(analysis['overall_strength'], 0, "Should have positive strength score")
        
        logger.info("✅ Case strength analysis passed")


def run_tests():
    """Run all Claims Matrix core tests"""
    logger.info("🚀 Starting Claims Matrix Core Tests...")
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestClaimsMatrixCore)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    if result.wasSuccessful():
        logger.info("🎉 All Claims Matrix core tests passed!")
        logger.info(f"✅ Ran {result.testsRun} tests successfully")
    else:
        logger.error(f"❌ {len(result.failures)} test failures")
        logger.error(f"❌ {len(result.errors)} test errors")
        for test, error in result.failures:
            logger.error(f"FAIL: {test} - {error}")
        for test, error in result.errors:
            logger.error(f"ERROR: {test} - {error}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)