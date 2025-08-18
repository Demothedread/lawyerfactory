"""
Test Suite for Legal Research Integration System - Phase 3.2
Comprehensive tests for Claims Matrix legal research capabilities
"""

import asyncio
import json
import logging
import unittest
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from enhanced_knowledge_graph import EnhancedKnowledgeGraph
from src.knowledge_graph.api.jurisdiction_manager import JurisdictionManager
from cause_of_action_detector import CauseOfActionDetector, CauseDetectionResult
from legal_research_integration import (
    LegalResearchAPIIntegration, LegalResearchRequest, ResearchPriority,
    AuthorityLevel
)
from legal_authority_validator import LegalAuthorityValidator, CitationCompliance
from legal_research_cache_manager import LegalResearchCacheManager
from claims_matrix.claims_matrix_research_api import (
    ClaimsMatrixResearchAPI, ClaimsMatrixResearchRequest, ClaimsMatrixResearchResponse
)
from maestro.bots.research_bot import LegalCitation

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestLegalResearchIntegration(unittest.IsolatedAsyncioTestCase):
    """Test the main legal research integration system"""
    
    async def asyncSetUp(self):
        """Set up test environment"""
        self.kg = EnhancedKnowledgeGraph(':memory:')
        self.jurisdiction_manager = JurisdictionManager(self.kg)
        self.cause_detector = CauseOfActionDetector(self.kg, self.jurisdiction_manager)
        
        # Initialize with mock API tokens
        self.research_integration = LegalResearchAPIIntegration(
            self.kg, self.jurisdiction_manager, self.cause_detector,
            courtlistener_token='test_token',
            scholar_contact_email='test@example.com'
        )
        
        # Start background services
        await self.research_integration.start_background_processor()
    
    async def asyncTearDown(self):
        """Clean up test environment"""
        await self.research_integration.stop_background_processor()
        self.kg.close()
    
    async def test_research_request_creation(self):
        """Test creating and validating research requests"""
        request = LegalResearchRequest(
            request_id='test_001',
            cause_of_action='negligence',
            jurisdiction='ca_state',
            legal_elements=['duty', 'breach', 'causation', 'damages'],
            fact_context=['Driver was texting', 'Accident occurred'],
            priority=ResearchPriority.HIGH
        )
        
        self.assertEqual(request.cause_of_action, 'negligence')
        self.assertEqual(request.jurisdiction, 'ca_state')
        self.assertEqual(len(request.legal_elements), 4)
        self.assertEqual(request.priority, ResearchPriority.HIGH)
    
    @patch('legal_research_integration.CourtListenerClient')
    async def test_courtlistener_integration(self, mock_client):
        """Test CourtListener API integration"""
        # Mock API response
        mock_client_instance = mock_client.return_value
        mock_client_instance.search_opinions = AsyncMock(return_value=[
            {
                'citation': '123 Cal.App.4th 456',
                'caseName': 'Test v. Example',
                'court': 'California Court of Appeal',
                'dateFiled': '2023-01-15',
                'absolute_url': 'https://example.com/case1'
            }
        ])
        
        # Create test request
        request = LegalResearchRequest(
            request_id='cl_test_001',
            cause_of_action='negligence',
            jurisdiction='ca_state',
            legal_elements=['duty'],
            fact_context=['test facts']
        )
        
        # Test research execution
        result = await self.research_integration.execute_research_request(request)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.query_id, 'cl_test_001')
        self.assertGreater(result.confidence_score, 0)
    
    async def test_research_query_building(self):
        """Test building research queries from requests"""
        request = LegalResearchRequest(
            request_id='query_test_001',
            cause_of_action='breach of contract',
            jurisdiction='federal',
            legal_elements=['formation', 'performance', 'breach'],
            fact_context=['Contract signed in 2023', 'Payment not made']
        )
        
        # Access protected method for testing
        queries = await self.research_integration._build_research_queries(request)
        
        self.assertGreater(len(queries), 0)
        self.assertIn('breach of contract', queries[0].query_text)
        self.assertEqual(queries[0].jurisdiction, 'federal')
    
    async def test_api_quota_management(self):
        """Test API quota tracking and limits"""
        # Check initial quota
        self.assertTrue(self.research_integration._check_api_quota('courtlistener'))
        
        # Simulate quota usage
        self.research_integration._update_api_usage('courtlistener', 100)
        
        # Check quota status
        quotas = self.research_integration.get_api_quotas()
        self.assertIn('courtlistener', quotas)
        self.assertEqual(quotas['courtlistener']['used'], 100)
    
    async def test_relevance_scoring(self):
        """Test citation relevance scoring algorithm"""
        # Create test citations
        citations = [
            LegalCitation(
                citation='123 F.3d 456',
                title='Negligence Case involving Texting Driver',
                court='9th Circuit',
                year=2022,
                jurisdiction='federal',
                citation_type='case',
                authority_level=AuthorityLevel.APPELLATE_COURT.value,
                relevance_score=0.0
            ),
            LegalCitation(
                citation='42 U.S.C. § 1983',
                title='Civil Rights Statute',
                year=1971,
                jurisdiction='federal',
                citation_type='statute',
                authority_level=AuthorityLevel.SUPREME_COURT.value,
                relevance_score=0.0
            )
        ]
        
        request = LegalResearchRequest(
            request_id='scoring_test',
            cause_of_action='negligence',
            jurisdiction='federal',
            legal_elements=['duty', 'breach'],
            fact_context=['texting while driving']
        )
        
        # Apply relevance scoring
        scored_citations = await self.research_integration._apply_relevance_scoring(citations, request)
        
        self.assertEqual(len(scored_citations), 2)
        # Check that citations are scored and sorted
        for citation in scored_citations:
            self.assertGreater(citation.relevance_score, 0)
        
        # First citation should have higher relevance due to title match
        self.assertGreater(scored_citations[0].relevance_score, scored_citations[1].relevance_score)


class TestLegalAuthorityValidator(unittest.IsolatedAsyncioTestCase):
    """Test legal authority validation system"""
    
    async def asyncSetUp(self):
        self.kg = EnhancedKnowledgeGraph(':memory:')
        self.jurisdiction_manager = JurisdictionManager(self.kg)
        self.validator = LegalAuthorityValidator(self.kg, self.jurisdiction_manager)
    
    async def asyncTearDown(self):
        self.kg.close()
    
    async def test_authority_hierarchy_validation(self):
        """Test authority hierarchy validation"""
        citations = [
            LegalCitation(
                citation='550 U.S. 544',
                title='Supreme Court Case',
                court='Supreme Court',
                year=2007,
                jurisdiction='federal',
                citation_type='case',
                authority_level=AuthorityLevel.SUPREME_COURT.value
            ),
            LegalCitation(
                citation='123 F.3d 456',
                title='Appellate Court Case',
                court='9th Circuit',
                year=2020,
                jurisdiction='federal',
                citation_type='case',
                authority_level=AuthorityLevel.APPELLATE_COURT.value
            )
        ]
        
        result = await self.validator.validate_authority_hierarchy(citations, 'federal')
        
        self.assertIn('valid_authorities', result)
        self.assertIn('invalid_authorities', result)
        self.assertIn('conflicts', result)
        self.assertIn('recommendations', result)
    
    async def test_bluebook_citation_validation(self):
        """Test Bluebook citation format validation"""
        citations = [
            LegalCitation(citation='550 U.S. 544 (2007)', title='Proper Supreme Court Citation', citation_type='case'),
            LegalCitation(citation='123 Fed.3d 456', title='Improper Citation Format', citation_type='case'),
            LegalCitation(citation='42 U.S.C. § 1983', title='Proper Statute Citation', citation_type='statute'),
            LegalCitation(citation='Invalid Citation', title='Invalid Format', citation_type='case')
        ]
        
        validations = await self.validator.validate_bluebook_citations(citations)
        
        self.assertEqual(len(validations), 4)
        
        # First citation should be compliant
        self.assertTrue(validations[0].is_compliant)
        self.assertEqual(validations[0].compliance_level, CitationCompliance.BLUEBOOK_COMPLIANT)
        
        # Last citation should be non-compliant
        self.assertFalse(validations[3].is_compliant)
        self.assertEqual(validations[3].compliance_level, CitationCompliance.NON_COMPLIANT)
    
    async def test_federal_preemption_analysis(self):
        """Test federal preemption analysis"""
        federal_citations = [
            LegalCitation(
                citation='29 U.S.C. § 151',
                title='National Labor Relations Act',
                jurisdiction='federal',
                authority_level=AuthorityLevel.SUPREME_COURT.value
            )
        ]
        
        state_citations = [
            LegalCitation(
                citation='Cal. Labor Code § 1102',
                title='California Employment Law',
                jurisdiction='ca_state',
                authority_level=AuthorityLevel.TRIAL_COURT.value
            )
        ]
        
        analysis = await self.validator._analyze_federal_preemption(
            federal_citations, state_citations, 'ca_state'
        )
        
        self.assertIsInstance(analysis.preemption_exists, bool)
        self.assertIn(analysis.preemption_type, ['complete', 'partial', 'none'])
        self.assertIsNotNone(analysis.analysis_notes)
    
    def test_citation_format_validation(self):
        """Test basic citation format validation"""
        valid_cases = [
            '550 U.S. 544 (2007)',
            '123 F.3d 456 (9th Cir. 2020)',
            '789 Cal.App.4th 123 (2021)'
        ]
        
        invalid_cases = [
            'Invalid citation',
            '123',
            '',
            'Case without proper format'
        ]
        
        for citation in valid_cases:
            self.assertTrue(
                self.validator._validate_citation_format(citation),
                f"Valid citation failed validation: {citation}"
            )
        
        for citation in invalid_cases:
            self.assertFalse(
                self.validator._validate_citation_format(citation),
                f"Invalid citation passed validation: {citation}"
            )


class TestLegalResearchCacheManager(unittest.IsolatedAsyncioTestCase):
    """Test legal research cache management"""
    
    async def asyncSetUp(self):
        self.kg = EnhancedKnowledgeGraph(':memory:')
        self.cache_manager = LegalResearchCacheManager(self.kg)
        await self.cache_manager.start_background_tasks()
    
    async def asyncTearDown(self):
        await self.cache_manager.stop_background_tasks()
        self.kg.close()
    
    async def test_cache_research_results(self):
        """Test caching and retrieving research results"""
        cache_key = 'test_research_key'
        jurisdiction = 'ca_state'
        test_data = {
            'query': 'negligence test',
            'results': ['citation1', 'citation2'],
            'confidence': 0.8
        }
        
        # Cache the data
        success = await self.cache_manager.cache_research_result(
            cache_key, jurisdiction, test_data, 24
        )
        self.assertTrue(success)
        
        # Retrieve the data
        cached_result = await self.cache_manager.get_cached_research(cache_key, jurisdiction)
        self.assertIsNotNone(cached_result)
        self.assertEqual(cached_result['query'], test_data['query'])
        self.assertEqual(cached_result['confidence'], test_data['confidence'])
    
    async def test_definition_cache(self):
        """Test legal definition caching"""
        legal_term = 'negligence'
        jurisdiction = 'ca_state'
        definition_data = {
            'term': legal_term,
            'definition': 'Failure to exercise reasonable care',
            'authority_citation': 'Restatement (Second) of Torts § 282',
            'confidence_score': 0.9
        }
        
        # Cache definition
        success = await self.cache_manager.cache_definition(
            legal_term, jurisdiction, definition_data
        )
        self.assertTrue(success)
        
        # Retrieve definition
        cached_def = await self.cache_manager.get_cached_definition(legal_term, jurisdiction)
        self.assertIsNotNone(cached_def)
        self.assertEqual(cached_def['term'], legal_term)
        self.assertEqual(cached_def['confidence_score'], 0.9)
    
    async def test_case_law_cache(self):
        """Test case law caching"""
        cause_of_action = 'negligence'
        jurisdiction = 'federal'
        cases = [
            {'citation': '550 U.S. 544', 'title': 'Test Case 1'},
            {'citation': '123 F.3d 456', 'title': 'Test Case 2'}
        ]
        
        # Cache case law
        success = await self.cache_manager.cache_case_law(
            cause_of_action, jurisdiction, cases
        )
        self.assertTrue(success)
        
        # Retrieve case law
        cached_cases = await self.cache_manager.get_cached_case_law(cause_of_action, jurisdiction)
        self.assertIsNotNone(cached_cases)
        self.assertEqual(len(cached_cases), 2)
        self.assertEqual(cached_cases[0]['citation'], '550 U.S. 544')
    
    async def test_cache_invalidation(self):
        """Test cache invalidation"""
        # Cache some test data
        await self.cache_manager.cache_research_result(
            'test_key_1', 'ca_state', {'test': 'data1'}, 24
        )
        await self.cache_manager.cache_research_result(
            'test_key_2', 'ny_state', {'test': 'data2'}, 24
        )
        
        # Invalidate CA cache
        invalidated_count = await self.cache_manager.invalidate_cache(
            'legal_research_cache', jurisdiction='ca_state'
        )
        
        self.assertGreater(invalidated_count, 0)
        
        # Verify CA cache is gone but NY cache remains
        ca_result = await self.cache_manager.get_cached_research('test_key_1', 'ca_state')
        ny_result = await self.cache_manager.get_cached_research('test_key_2', 'ny_state')
        
        self.assertIsNone(ca_result)
        self.assertIsNotNone(ny_result)
    
    def test_cache_statistics(self):
        """Test cache performance statistics"""
        stats = self.cache_manager.get_cache_statistics()
        
        self.assertIn('total_performance', stats)
        self.assertIn('by_cache_type', stats)
        
        for cache_type in ['legal_research_cache', 'definition_cache', 'case_law_cache']:
            self.assertIn(cache_type, stats['by_cache_type'])


class TestClaimsMatrixResearchAPI(unittest.IsolatedAsyncioTestCase):
    """Test the main Claims Matrix Research API"""
    
    async def asyncSetUp(self):
        self.kg = EnhancedKnowledgeGraph(':memory:')
        self.api = ClaimsMatrixResearchAPI(self.kg)
        await self.api.start_services()
    
    async def asyncTearDown(self):
        await self.api.stop_services()
        self.kg.close()
    
    async def test_research_request_submission(self):
        """Test submitting research requests"""
        request = ClaimsMatrixResearchRequest(
            request_id='api_test_001',
            cause_of_action='negligence',
            jurisdiction='ca_state',
            legal_elements=['duty', 'breach', 'causation', 'damages'],
            case_facts=['Driver was texting while driving'],
            priority=ResearchPriority.HIGH
        )
        
        # Mock the underlying research integration
        with patch.object(self.api.research_integration, 'submit_research_request', 
                         new_callable=AsyncMock) as mock_submit:
            request_id = await self.api.submit_research_request(request)
            
            self.assertEqual(request_id, 'api_test_001')
            mock_submit.assert_called_once()
    
    async def test_request_validation(self):
        """Test research request validation"""
        # Valid request
        valid_request = ClaimsMatrixResearchRequest(
            request_id='valid_test',
            cause_of_action='negligence',
            jurisdiction='ca_state',
            legal_elements=['duty'],
            case_facts=['test fact']
        )
        
        validation = await self.api._validate_research_request(valid_request)
        self.assertTrue(validation['valid'])
        
        # Invalid request - missing cause of action
        invalid_request = ClaimsMatrixResearchRequest(
            request_id='invalid_test',
            cause_of_action='',
            jurisdiction='ca_state',
            legal_elements=['duty'],
            case_facts=['test fact']
        )
        
        validation = await self.api._validate_research_request(invalid_request)
        self.assertFalse(validation['valid'])
        self.assertIn('Cause of action is required', validation['error'])
    
    @patch('claims_matrix_research_api.uuid.uuid4')
    async def test_automatic_cause_research_trigger(self, mock_uuid):
        """Test automatically triggering research based on cause detection"""
        mock_uuid.return_value.hex = 'test123456789012'
        
        # Mock cause detection result
        cause_detection = CauseDetectionResult(
            cause_name='negligence',
            confidence_score=0.8,
            supporting_facts=['fact1', 'fact2'],
            jurisdiction='ca_state',
            elements_detected=[
                {'name': 'duty', 'confidence': 0.9},
                {'name': 'breach', 'confidence': 0.7}
            ]
        )
        
        case_facts = ['Driver was speeding', 'Accident occurred at intersection']
        
        # Mock the submit method
        with patch.object(self.api, 'submit_research_request', 
                         new_callable=AsyncMock) as mock_submit:
            mock_submit.return_value = 'auto_research_test123456789'
            
            request_id = await self.api.trigger_cause_research(
                cause_detection, case_facts, ResearchPriority.HIGH
            )
            
            self.assertEqual(request_id, 'auto_research_test123456789')
            mock_submit.assert_called_once()
            
            # Verify request parameters
            call_args = mock_submit.call_args[0][0]
            self.assertEqual(call_args.cause_of_action, 'negligence')
            self.assertEqual(call_args.jurisdiction, 'ca_state')
            self.assertEqual(call_args.legal_elements, ['duty', 'breach'])
            self.assertEqual(call_args.priority, ResearchPriority.HIGH)
    
    def test_api_statistics(self):
        """Test API statistics collection"""
        stats = self.api.get_api_statistics()
        
        self.assertIn('active_requests', stats)
        self.assertIn('cache_performance', stats)
        self.assertIn('api_quotas', stats)
        self.assertIn('system_status', stats)
        
        self.assertEqual(stats['system_status'], 'operational')


class TestIntegrationWorkflow(unittest.IsolatedAsyncioTestCase):
    """Test complete integration workflows"""
    
    async def asyncSetUp(self):
        self.kg = EnhancedKnowledgeGraph(':memory:')
        self.api = ClaimsMatrixResearchAPI(self.kg)
        await self.api.start_services()
    
    async def asyncTearDown(self):
        await self.api.stop_services()
        self.kg.close()
    
    @patch('legal_research_integration.CourtListenerClient')
    @patch('legal_research_integration.GoogleScholarClient')  
    @patch('legal_research_integration.OpenAlexClient')
    async def test_end_to_end_research_workflow(self, mock_openalex, mock_scholar, mock_courtlistener):
        """Test complete end-to-end research workflow"""
        # Mock API responses
        mock_courtlistener_instance = mock_courtlistener.return_value
        mock_courtlistener_instance.search_opinions = AsyncMock(return_value=[
            {
                'citation': '123 Cal.App.4th 456',
                'caseName': 'Negligence Case Example',
                'court': 'California Court of Appeal',
                'dateFiled': '2023-01-15'
            }
        ])
        
        mock_scholar_instance = mock_scholar.return_value
        mock_scholar_instance.search_legal = AsyncMock(return_value=[
            {
                'title': 'Academic Analysis of Negligence',
                'citation': 'Law Review Article',
                'year': 2023,
                'url': 'https://example.com/article'
            }
        ])
        
        mock_openalex_instance = mock_openalex.return_value
        mock_openalex_instance.search_legal = AsyncMock(return_value=[
            {
                'title': 'Legal Research on Negligence',
                'citation': 'Academic Source',
                'year': 2022,
                'url': 'https://example.com/source'
            }
        ])
        
        # Create comprehensive research request
        request = ClaimsMatrixResearchRequest(
            request_id='workflow_test_001',
            cause_of_action='negligence',
            jurisdiction='ca_state',
            legal_elements=['duty', 'breach', 'causation', 'damages'],
            case_facts=[
                'Driver was texting while driving',
                'Accident occurred at busy intersection',
                'Plaintiff suffered serious injuries'
            ],
            priority=ResearchPriority.HIGH,
            include_definitions=True,
            include_case_law=True,
            include_academic_sources=True,
            validate_authorities=True
        )
        
        # Submit request
        request_id = await self.api.submit_research_request(request)
        self.assertEqual(request_id, 'workflow_test_001')
        
        # Mock the research execution to avoid actual API calls
        with patch.object(self.api.research_integration, 'execute_research_request') as mock_execute:
            from maestro.bots.research_bot import ResearchResult
            
            mock_result = ResearchResult(
                query_id='workflow_test_001',
                citations=[
                    LegalCitation(
                        citation='123 Cal.App.4th 456',
                        title='Negligence Case Example',
                        court='California Court of Appeal',
                        year=2023,
                        jurisdiction='ca_state',
                        citation_type='case',
                        authority_level=AuthorityLevel.APPELLATE_COURT.value,
                        relevance_score=0.8
                    )
                ],
                legal_principles=['Duty of reasonable care', 'Proximate causation standard'],
                gaps_identified=['Limited recent authority'],
                recommendations=['Seek additional appellate decisions'],
                confidence_score=0.75,
                search_metadata={'sources': ['courtlistener'], 'api_calls': 1},
                created_at=datetime.now()
            )
            
            mock_execute.return_value = mock_result
            
            # Get comprehensive results
            response = await self.api.get_research_result(request_id)
            
            # Verify response structure
            self.assertIsInstance(response, ClaimsMatrixResearchResponse)
            self.assertEqual(response.request_id, 'workflow_test_001')
            self.assertEqual(response.cause_of_action, 'negligence')
            self.assertEqual(response.jurisdiction, 'ca_state')
            self.assertEqual(response.research_status, 'completed')
            self.assertGreater(response.confidence_score, 0)
            
            # Verify citation processing
            self.assertGreater(len(response.case_law_citations), 0)
            
            # Verify research gaps and recommendations
            self.assertIsInstance(response.research_gaps, list)
            self.assertIsInstance(response.recommendations, list)


# Additional utility functions for testing
def create_test_legal_citation(citation_type='case', authority_level=3, relevance_score=0.5):
    """Create a test legal citation for testing purposes"""
    return LegalCitation(
        citation=f'Test Citation {citation_type}',
        title=f'Test {citation_type.title()} Title',
        court='Test Court',
        year=2023,
        jurisdiction='test_jurisdiction',
        citation_type=citation_type,
        url='https://example.com/test',
        relevance_score=relevance_score,
        authority_level=authority_level,
        excerpt='Test excerpt for citation'
    )


def create_test_research_request(request_id='test_001'):
    """Create a test research request for testing purposes"""
    return LegalResearchRequest(
        request_id=request_id,
        cause_of_action='negligence',
        jurisdiction='ca_state',
        legal_elements=['duty', 'breach'],
        fact_context=['test fact 1', 'test fact 2'],
        priority=ResearchPriority.MEDIUM
    )


if __name__ == '__main__':
    # Run the test suite
    unittest.main()