"""
# Script Name: research_api.py
# Description: Claims Matrix Research Integration API - Phase 3.2 Main API interface for legal research integration with Claims Matrix
# Relationships:
#   - Entity Type: API
#   - Directory Group: Backend
#   - Group Tags: claims-analysis, legal-research, api
Claims Matrix Research Integration API - Phase 3.2
Main API interface for legal research integration with Claims Matrix
"""

import asyncio
import logging
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from cause_of_action_detector import (CauseDetectionResult,
                                      CauseOfActionDetector)
from enhanced_knowledge_graph import EnhancedKnowledgeGraph
from legal_authority_validator import LegalAuthorityValidator
from legal_research_cache_manager import LegalResearchCacheManager
from legal_research_integration import (LegalResearchAPIIntegration,
                                        LegalResearchRequest, ResearchPriority)

from src.lawyerfactory.knowledge_graph.core.jurisdiction_manager import JurisdictionManager

logger = logging.getLogger(__name__)


@dataclass
class ClaimsMatrixResearchRequest:
    """Research request specific to Claims Matrix context"""
    request_id: str
    cause_of_action: str
    jurisdiction: str
    legal_elements: List[str]
    case_facts: List[str]
    priority: ResearchPriority = ResearchPriority.MEDIUM
    include_definitions: bool = True
    include_case_law: bool = True
    include_academic_sources: bool = False
    validate_authorities: bool = True
    cache_results: bool = True
    attorney_id: Optional[str] = None
    case_id: Optional[str] = None


@dataclass
class ClaimsMatrixResearchResponse:
    """Comprehensive research response for Claims Matrix"""
    request_id: str
    cause_of_action: str
    jurisdiction: str
    research_status: str
    confidence_score: float
    legal_authorities: List[Dict[str, Any]]
    legal_definitions: List[Dict[str, Any]]
    case_law_citations: List[Dict[str, Any]]
    academic_sources: List[Dict[str, Any]]
    authority_validation: Dict[str, Any]
    research_gaps: List[str]
    recommendations: List[str]
    processing_time_seconds: float
    cached_result: bool = False
    created_at: Optional[datetime] = None


class ClaimsMatrixResearchAPI:
    """Main API for Claims Matrix legal research integration"""
    
    def __init__(self, enhanced_kg: EnhancedKnowledgeGraph,
                 courtlistener_token: Optional[str] = None,
                 scholar_contact_email: Optional[str] = None):
        """Initialize the Claims Matrix Research API"""
        self.kg = enhanced_kg
        
        # Initialize core components
        self.jurisdiction_manager = JurisdictionManager(enhanced_kg)
        self.cause_detector = CauseOfActionDetector(enhanced_kg, self.jurisdiction_manager)
        self.cache_manager = LegalResearchCacheManager(enhanced_kg)
        self.research_integration = LegalResearchAPIIntegration(
            enhanced_kg, self.jurisdiction_manager, self.cause_detector,
            courtlistener_token, scholar_contact_email
        )
        self.authority_validator = LegalAuthorityValidator(enhanced_kg, self.jurisdiction_manager)
        
        # Request tracking
        self.active_requests: Dict[str, ClaimsMatrixResearchRequest] = {}
        
        logger.info("Claims Matrix Research API initialized")
    
    async def start_services(self):
        """Start background services"""
        await self.cache_manager.start_background_tasks()
        await self.research_integration.start_background_processor()
        logger.info("Claims Matrix Research API services started")
    
    async def stop_services(self):
        """Stop background services"""
        await self.cache_manager.stop_background_tasks()
        await self.research_integration.stop_background_processor()
        logger.info("Claims Matrix Research API services stopped")
    
    async def submit_research_request(self, request: ClaimsMatrixResearchRequest) -> str:
        """Submit a comprehensive research request"""
        try:
            # Validate request
            validation_result = await self._validate_research_request(request)
            if not validation_result['valid']:
                raise ValueError(f"Invalid request: {validation_result['error']}")
            
            # Store request
            self.active_requests[request.request_id] = request
            
            # Check cache first if enabled
            if request.cache_results:
                cached_result = await self._check_comprehensive_cache(request)
                if cached_result:
                    logger.info(f"Cache hit for research request {request.request_id}")
                    return request.request_id
            
            # Create research request for integration layer
            research_request = LegalResearchRequest(
                request_id=request.request_id,
                cause_of_action=request.cause_of_action,
                jurisdiction=request.jurisdiction,
                legal_elements=request.legal_elements,
                fact_context=request.case_facts,
                priority=request.priority
            )
            
            # Submit to research integration
            await self.research_integration.submit_research_request(research_request)
            
            logger.info(f"Submitted Claims Matrix research request: {request.request_id}")
            return request.request_id
            
        except Exception as e:
            logger.exception(f"Failed to submit research request: {e}")
            raise
    
    async def get_research_result(self, request_id: str) -> ClaimsMatrixResearchResponse:
        """Get comprehensive research results"""
        try:
            # Check if request exists
            if request_id not in self.active_requests:
                raise ValueError(f"Unknown request ID: {request_id}")
            
            request = self.active_requests[request_id]
            start_time = datetime.now()
            
            # Check cache first
            cached_result = await self._check_comprehensive_cache(request)
            if cached_result:
                cached_result.cached_result = True
                return cached_result
            
            # Execute comprehensive research
            research_request = LegalResearchRequest(
                request_id=request.request_id,
                cause_of_action=request.cause_of_action,
                jurisdiction=request.jurisdiction,
                legal_elements=request.legal_elements,
                fact_context=request.case_facts,
                priority=request.priority
            )
            
            # Get base research results
            base_results = await self.research_integration.execute_research_request(research_request)
            
            # Build comprehensive response
            response = ClaimsMatrixResearchResponse(
                request_id=request_id,
                cause_of_action=request.cause_of_action,
                jurisdiction=request.jurisdiction,
                research_status='completed',
                confidence_score=base_results.confidence_score,
                legal_authorities=[],
                legal_definitions=[],
                case_law_citations=[],
                academic_sources=[],
                authority_validation={},
                research_gaps=base_results.gaps_identified,
                recommendations=base_results.recommendations,
                processing_time_seconds=0.0,
                created_at=datetime.now()
            )
            
            # Process citations by type
            await self._process_research_citations(base_results.citations, response, request)
            
            # Validate authorities if requested
            if request.validate_authorities:
                response.authority_validation = await self._validate_research_authorities(
                    base_results.citations, request
                )
            
            # Get legal definitions if requested
            if request.include_definitions:
                response.legal_definitions = await self._get_legal_definitions(request)
            
            # Calculate processing time
            response.processing_time_seconds = (datetime.now() - start_time).total_seconds()
            
            # Cache results if enabled
            if request.cache_results:
                await self._cache_comprehensive_result(request, response)
            
            # Integrate with Claims Matrix
            await self._integrate_with_claims_matrix(request, response)
            
            # Cleanup request tracking
            if request_id in self.active_requests:
                del self.active_requests[request_id]
            
            logger.info(f"Completed Claims Matrix research request: {request_id}")
            return response
            
        except Exception as e:
            logger.exception(f"Failed to get research result for {request_id}: {e}")
            raise
    
    async def _validate_research_request(self, request: ClaimsMatrixResearchRequest) -> Dict[str, Any]:
        """Validate research request parameters"""
        try:
            # Basic validation
            if not request.cause_of_action:
                return {'valid': False, 'error': 'Cause of action is required'}
            
            if not request.jurisdiction:
                return {'valid': False, 'error': 'Jurisdiction is required'}
            
            # Validate jurisdiction
            if not self.jurisdiction_manager.select_jurisdiction(request.jurisdiction):
                return {'valid': False, 'error': f'Invalid jurisdiction: {request.jurisdiction}'}
            
            # Validate cause of action for jurisdiction
            cause_validation = self.jurisdiction_manager.validate_cause_for_jurisdiction(
                request.cause_of_action, request.jurisdiction
            )
            
            if not cause_validation['valid']:
                return {'valid': False, 'error': cause_validation.get('reason', 'Invalid cause of action')}
            
            return {'valid': True}
            
        except Exception as e:
            logger.error(f"Request validation failed: {e}")
            return {'valid': False, 'error': str(e)}
    
    async def _check_comprehensive_cache(self, request: ClaimsMatrixResearchRequest) -> Optional[ClaimsMatrixResearchResponse]:
        """Check for cached comprehensive results"""
        try:
            cache_key = self._generate_comprehensive_cache_key(request)
            cached_data = await self.cache_manager.get_cached_research(cache_key, request.jurisdiction)
            
            if cached_data and 'comprehensive_response' in cached_data:
                # Reconstruct response from cached data
                response_data = cached_data['comprehensive_response']
                response = ClaimsMatrixResearchResponse(**response_data)
                response.cached_result = True
                return response
            
            return None
            
        except Exception as e:
            logger.error(f"Cache check failed: {e}")
            return None
    
    async def _process_research_citations(self, citations: List[Any], 
                                        response: ClaimsMatrixResearchResponse,
                                        request: ClaimsMatrixResearchRequest):
        """Process and categorize research citations"""
        try:
            for citation in citations:
                citation_dict = {
                    'citation': citation.citation,
                    'title': citation.title,
                    'court': citation.court,
                    'year': citation.year,
                    'jurisdiction': citation.jurisdiction,
                    'citation_type': citation.citation_type,
                    'url': citation.url,
                    'relevance_score': citation.relevance_score,
                    'authority_level': citation.authority_level,
                    'excerpt': citation.excerpt
                }
                
                # Categorize by type
                if citation.citation_type == 'case':
                    response.case_law_citations.append(citation_dict)
                elif citation.citation_type in ['statute', 'regulation']:
                    response.legal_authorities.append(citation_dict)
                elif citation.citation_type == 'academic':
                    if request.include_academic_sources:
                        response.academic_sources.append(citation_dict)
                else:
                    response.legal_authorities.append(citation_dict)
            
            # Sort by relevance
            response.case_law_citations.sort(key=lambda x: x['relevance_score'], reverse=True)
            response.legal_authorities.sort(key=lambda x: x['relevance_score'], reverse=True)
            response.academic_sources.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            # Sort by relevance
            response.case_law_citations.sort(key=lambda x: x['relevance_score'], reverse=True)
            response.legal_authorities.sort(key=lambda x: x['relevance_score'], reverse=True)
            response.academic_sources.sort(key=lambda x: x['relevance_score'], reverse=True)
            
        except Exception as e:
            logger.error(f"Citation processing failed: {e}")
    
    async def _validate_research_authorities(self, citations: List[Any], 
                                           request: ClaimsMatrixResearchRequest) -> Dict[str, Any]:
        """Validate legal authorities using the authority validator"""
        try:
            validation_result = await self.authority_validator.validate_authority_hierarchy(
                citations, request.jurisdiction
            )
            
            # Add Bluebook validation
            bluebook_validations = await self.authority_validator.validate_bluebook_citations(citations)
            
            return {
                'hierarchy_validation': validation_result,
                'bluebook_compliance': {
                    'total_citations': len(citations),
                    'compliant_citations': len([v for v in bluebook_validations if v.is_compliant]),
                    'compliance_rate': len([v for v in bluebook_validations if v.is_compliant]) / len(citations) if citations else 0,
                    'violations': [v for v in bluebook_validations if not v.is_compliant]
                }
            }
            
        except Exception as e:
            logger.error(f"Authority validation failed: {e}")
            return {'error': str(e)}
    
    async def _get_legal_definitions(self, request: ClaimsMatrixResearchRequest) -> List[Dict[str, Any]]:
        """Get legal definitions for key terms"""
        try:
            definitions = []
            
            # Extract key legal terms from cause of action and elements
            legal_terms = set()
            legal_terms.add(request.cause_of_action.lower())
            legal_terms.update(element.lower() for element in request.legal_elements)
            
            # Get definitions from cache or research
            for term in legal_terms:
                cached_def = await self.cache_manager.get_cached_definition(term, request.jurisdiction)
                
                if cached_def:
                    definitions.append(cached_def)
                else:
                    # Could trigger additional research for definitions
                    # For now, create placeholder
                    definition = {
                        'term': term,
                        'definition': f"Legal definition for {term} - research required",
                        'jurisdiction': request.jurisdiction,
                        'authority_citation': 'Pending research',
                        'confidence_score': 0.3
                    }
                    definitions.append(definition)
            
            return definitions
            
        except Exception as e:
            logger.error(f"Definition retrieval failed: {e}")
            return []
    
    def _generate_comprehensive_cache_key(self, request: ClaimsMatrixResearchRequest) -> str:
        """Generate cache key for comprehensive research"""
        import hashlib
        
        key_components = [
            request.cause_of_action,
            request.jurisdiction,
            '|'.join(sorted(request.legal_elements)),
            '|'.join(sorted(request.case_facts[:5])),  # Limit fact context
            str(request.include_definitions),
            str(request.include_case_law),
            str(request.include_academic_sources)
        ]
        
        key_string = '||'.join(key_components)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    async def _cache_comprehensive_result(self, request: ClaimsMatrixResearchRequest,
                                        response: ClaimsMatrixResearchResponse):
        """Cache comprehensive research results"""
        try:
            cache_key = self._generate_comprehensive_cache_key(request)
            cache_data = {
                'comprehensive_response': asdict(response),
                'cached_at': datetime.now().isoformat(),
                'relevance_score': response.confidence_score
            }
            
            await self.cache_manager.cache_research_result(
                cache_key, request.jurisdiction, cache_data, 24
            )
            
        except Exception as e:
            logger.error(f"Failed to cache comprehensive result: {e}")
    
    async def _integrate_with_claims_matrix(self, request: ClaimsMatrixResearchRequest,
                                          response: ClaimsMatrixResearchResponse):
        """Integrate research results with Claims Matrix system"""
        try:
            # Store research results in knowledge graph
            for citation in response.case_law_citations[:10]:  # Top 10
                entity_id = f"research_citation_{uuid.uuid4().hex[:8]}"
                
                # Add citation as entity
                self.kg.add_legal_entity({
                    'id': entity_id,
                    'type': 'legal_citation',
                    'name': citation.get('title', citation.get('citation', '')),
                    'legal_attributes': citation
                })
            
            # Attach research results to legal elements
            cause_elements = self.kg.get_legal_elements_for_cause(request.cause_of_action)
            
            for element in cause_elements:
                # Find relevant citations for this element
                element_name_lower = element['element_name'].lower()
                relevant_citations = []
                
                for citation in response.case_law_citations:
                    title_lower = (citation.get('title', '') or '').lower()
                    excerpt_lower = (citation.get('excerpt', '') or '').lower()
                    
                    if (element_name_lower in title_lower or element_name_lower in excerpt_lower):
                        relevant_citations.append(citation)
                
                # Store element-citation relationships
                for citation in relevant_citations[:3]:  # Top 3 per element
                    # This would create fact-element attachments for research results
                    pass
            
            logger.debug(f"Integrated research results with Claims Matrix for request {request.request_id}")
            
        except Exception as e:
            logger.error(f"Claims Matrix integration failed: {e}")
    
    async def get_request_status(self, request_id: str) -> Dict[str, Any]:
        """Get status of a research request"""
        try:
            if request_id in self.active_requests:
                request = self.active_requests[request_id]
                return {
                    'request_id': request_id,
                    'status': 'processing',
                    'cause_of_action': request.cause_of_action,
                    'jurisdiction': request.jurisdiction,
                    'priority': request.priority.value,
                    'submitted_at': request.request_id  # Could be enhanced with timestamp
                }
            
            # Check if completed (would be in cache or knowledge graph)
            return await self.research_integration.get_research_status(request_id)
            
        except Exception as e:
            logger.error(f"Failed to get request status: {e}")
            return {'request_id': request_id, 'status': 'error', 'error': str(e)}
    
    async def trigger_cause_research(self, cause_detection: CauseDetectionResult,
                                   case_facts: List[str],
                                   priority: ResearchPriority = ResearchPriority.HIGH) -> str:
        """Trigger research automatically based on cause detection"""
        try:
            request_id = f"auto_research_{uuid.uuid4().hex[:12]}"
            
            # Extract legal elements from cause detection
            legal_elements = [elem['name'] for elem in cause_detection.elements_detected]
            
            # Create research request
            research_request = ClaimsMatrixResearchRequest(
                request_id=request_id,
                cause_of_action=cause_detection.cause_name,
                jurisdiction=cause_detection.jurisdiction,
                legal_elements=legal_elements,
                case_facts=case_facts,
                priority=priority,
                include_definitions=True,
                include_case_law=True,
                validate_authorities=True
            )
            
            # Submit request
            await self.submit_research_request(research_request)
            
            logger.info(f"Triggered automatic research for cause: {cause_detection.cause_name}")
            return request_id
            
        except Exception as e:
            logger.exception(f"Failed to trigger cause research: {e}")
            raise
    
    def get_api_statistics(self) -> Dict[str, Any]:
        """Get comprehensive API statistics"""
        try:
            cache_stats = self.cache_manager.get_cache_statistics()
            research_quotas = self.research_integration.get_api_quotas()
            validation_stats = self.authority_validator.get_validation_statistics()
            
            return {
                'active_requests': len(self.active_requests),
                'cache_performance': cache_stats,
                'api_quotas': research_quotas,
                'validation_statistics': validation_stats,
                'system_status': 'operational'
            }
            
        except Exception as e:
            logger.error(f"Failed to get API statistics: {e}")
            return {'error': str(e)}
    
    async def invalidate_research_cache(self, jurisdiction: str = None, 
                                      cause_of_action: str = None) -> Dict[str, Any]:
        """Invalidate research cache for jurisdiction or cause"""
        try:
            results = {}
            
            # Invalidate different cache types
            if jurisdiction:
                research_count = await self.cache_manager.invalidate_cache(
                    'legal_research_cache', jurisdiction=jurisdiction
                )
                definition_count = await self.cache_manager.invalidate_cache(
                    'definition_cache', jurisdiction=jurisdiction
                )
                case_law_count = await self.cache_manager.invalidate_cache(
                    'case_law_cache', jurisdiction=jurisdiction
                )
                
                results = {
                    'research_cache_invalidated': research_count,
                    'definition_cache_invalidated': definition_count,
                    'case_law_cache_invalidated': case_law_count,
                    'total_invalidated': research_count + definition_count + case_law_count
                }
            
            if cause_of_action:
                cause_count = await self.cache_manager.invalidate_cache(
                    'case_law_cache', pattern=cause_of_action
                )
                results['cause_specific_invalidated'] = cause_count
                results['total_invalidated'] = results.get('total_invalidated', 0) + cause_count
            
            logger.info(f"Cache invalidation completed: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Cache invalidation failed: {e}")
            return {'error': str(e)}


async def create_claims_matrix_research_api(enhanced_kg: EnhancedKnowledgeGraph,
                                          courtlistener_token: str = None,
                                          scholar_contact_email: str = None) -> ClaimsMatrixResearchAPI:
    """Factory function to create and initialize Claims Matrix Research API"""
    api = ClaimsMatrixResearchAPI(enhanced_kg, courtlistener_token, scholar_contact_email)
    await api.start_services()
    return api


# Example usage and testing functions
async def example_research_workflow():
    """Example workflow for Claims Matrix research"""
    try:
        # Initialize knowledge graph
        kg = EnhancedKnowledgeGraph()
        
        # Create API
        api = await create_claims_matrix_research_api(kg)
        
        # Example research request
        request = ClaimsMatrixResearchRequest(
            request_id=f"example_{uuid.uuid4().hex[:8]}",
            cause_of_action="negligence",
            jurisdiction="ca_state",
            legal_elements=["duty", "breach", "causation", "damages"],
            case_facts=[
                "Driver was texting while driving",
                "Accident occurred at intersection",
                "Plaintiff suffered injuries"
            ],
            priority=ResearchPriority.HIGH,
            include_definitions=True,
            include_case_law=True,
            validate_authorities=True
        )
        
        # Submit and get results
        request_id = await api.submit_research_request(request)
        print(f"Submitted research request: {request_id}")
        
        # Get results (would typically wait for background processing)
        result = await api.get_research_result(request_id)
        print(f"Research completed with confidence: {result.confidence_score}")
        print(f"Found {len(result.case_law_citations)} case law citations")
        print(f"Found {len(result.legal_definitions)} definitions")
        
        # Clean up
        await api.stop_services()
        
    except Exception as e:
        logger.exception(f"Example workflow failed: {e}")


if __name__ == "__main__":
    # Run example workflow
    asyncio.run(example_research_workflow())