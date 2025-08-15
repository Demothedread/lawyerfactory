"""
Legal Research API Integration System for Claims Matrix Phase 3.2
Provides comprehensive legal research capabilities with CourtListener, Google Scholar, and OpenAlex integration
"""

import asyncio
import json
import logging
import hashlib
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict, field
from enum import Enum

from enhanced_knowledge_graph import EnhancedKnowledgeGraph
from jurisdiction_manager import JurisdictionManager
from cause_of_action_detector import CauseOfActionDetector, CauseDetectionResult
from maestro.bots.research_bot import (
    ResearchQuery, LegalCitation, ResearchResult,
    CourtListenerClient, OpenAlexClient, GoogleScholarClient
)

logger = logging.getLogger(__name__)


class ResearchPriority(Enum):
    """Priority levels for legal research requests"""
    CRITICAL = "critical"      # Immediate processing
    HIGH = "high"              # Process within 5 minutes
    MEDIUM = "medium"          # Process within 30 minutes
    LOW = "low"               # Process within 2 hours
    BACKGROUND = "background"  # Process when system is idle


class AuthorityLevel(Enum):
    """Legal authority hierarchy levels"""
    SUPREME_COURT = 1
    APPELLATE_COURT = 2
    TRIAL_COURT = 3
    ADMINISTRATIVE = 4
    SECONDARY_SOURCE = 5


@dataclass
class LegalResearchRequest:
    """Enhanced research request with Claims Matrix context"""
    request_id: str
    cause_of_action: str
    jurisdiction: str
    legal_elements: List[str]
    fact_context: List[str]
    priority: ResearchPriority = ResearchPriority.MEDIUM
    cache_expiry_hours: int = 24
    created_at: datetime = field(default_factory=datetime.now)
    attorney_reviewed: bool = False


@dataclass
class AuthorityValidation:
    """Validation result for legal authority"""
    is_valid: bool
    authority_level: AuthorityLevel
    jurisdiction_conflict: Optional[str] = None
    federal_preemption_issue: bool = False
    citation_compliance: bool = True
    confidence_score: float = 0.0
    validation_notes: str = ""


@dataclass
class ResearchCacheEntry:
    """Cache entry for legal research results"""
    cache_key: str
    jurisdiction: str
    search_query: str
    api_source: str
    result_data: Dict[str, Any]
    relevance_score: float
    cache_expiry: datetime
    hit_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)


class LegalResearchAPIIntegration:
    """Comprehensive legal research API integration system"""
    
    def __init__(self, enhanced_kg: EnhancedKnowledgeGraph, 
                 jurisdiction_manager: JurisdictionManager,
                 cause_detector: CauseOfActionDetector,
                 courtlistener_token: Optional[str] = None,
                 scholar_contact_email: Optional[str] = None):
        """Initialize the legal research integration system"""
        self.kg = enhanced_kg
        self.jurisdiction_manager = jurisdiction_manager
        self.cause_detector = cause_detector
        
        # API clients
        self.courtlistener_client = CourtListenerClient(courtlistener_token)
        self.openalex_client = OpenAlexClient(scholar_contact_email)
        self.scholar_client = GoogleScholarClient()
        
        # API quota management
        self.api_quotas = {
            'courtlistener': {'daily_limit': 5000, 'used': 0, 'reset_time': self._get_next_reset()},
            'openalex': {'daily_limit': 10000, 'used': 0, 'reset_time': self._get_next_reset()},
            'scholar': {'daily_limit': 100, 'used': 0, 'reset_time': self._get_next_reset()}
        }
        
        # Research processing queue
        self.research_queue = asyncio.Queue()
        self.background_processor_running = False
        
        # Cache management
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'invalidations': 0,
            'size_mb': 0.0
        }
        
        logger.info("Legal Research API Integration system initialized")
    
    def _get_next_reset(self) -> datetime:
        """Get next API quota reset time (daily)"""
        tomorrow = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        return tomorrow + timedelta(days=1)
    
    async def start_background_processor(self):
        """Start background research processing"""
        if self.background_processor_running:
            return
            
        self.background_processor_running = True
        logger.info("Starting background research processor")
        
        # Start background tasks
        asyncio.create_task(self._background_research_processor())
        asyncio.create_task(self._cache_maintenance_task())
        asyncio.create_task(self._quota_reset_task())
    
    async def stop_background_processor(self):
        """Stop background research processing"""
        self.background_processor_running = False
        logger.info("Stopped background research processor")
    
    async def submit_research_request(self, request: LegalResearchRequest) -> str:
        """Submit a research request for processing"""
        await self.research_queue.put(request)
        logger.info(f"Submitted research request {request.request_id} with priority {request.priority.value}")
        return request.request_id
    
    async def execute_research_request(self, request: LegalResearchRequest) -> ResearchResult:
        """Execute comprehensive legal research for a specific request"""
        logger.info(f"Executing research request: {request.request_id}")
        
        try:
            # Check cache first
            cached_result = await self._check_research_cache(request)
            if cached_result:
                logger.info(f"Cache hit for research request {request.request_id}")
                self.cache_stats['hits'] += 1
                return cached_result
            
            self.cache_stats['misses'] += 1
            
            # Build comprehensive research query
            research_queries = await self._build_research_queries(request)
            
            # Execute parallel research across APIs
            all_citations = []
            research_metadata = {
                'apis_used': [],
                'total_results': 0,
                'processing_time': 0,
                'cache_status': 'miss'
            }
            
            start_time = time.time()
            
            # Execute research tasks in parallel
            research_tasks = []
            
            # CourtListener case law research
            if self._check_api_quota('courtlistener'):
                for query in research_queries:
                    research_tasks.append(self._research_courtlistener(query, request))
            
            # Google Scholar academic research
            if self._check_api_quota('scholar'):
                for query in research_queries:
                    research_tasks.append(self._research_google_scholar(query, request))
            
            # OpenAlex academic research
            if self._check_api_quota('openalex'):
                for query in research_queries:
                    research_tasks.append(self._research_openalex(query, request))
            
            # Execute all research tasks
            research_results = await asyncio.gather(*research_tasks, return_exceptions=True)
            
            # Process results
            for result in research_results:
                if isinstance(result, Exception):
                    logger.error(f"Research task failed: {result}")
                    continue
                
                if isinstance(result, list):
                    all_citations.extend(result)
                    research_metadata['total_results'] += len(result)
            
            research_metadata['processing_time'] = time.time() - start_time
            
            # Apply relevance scoring and authority validation
            scored_citations = await self._apply_relevance_scoring(all_citations, request)
            validated_citations = await self._validate_legal_authorities(scored_citations, request)
            
            # Generate legal analysis
            legal_principles = await self._extract_legal_principles(validated_citations, request)
            gaps_identified = await self._identify_research_gaps(validated_citations, request)
            recommendations = await self._generate_research_recommendations(validated_citations, request)
            
            # Create research result
            result = ResearchResult(
                query_id=request.request_id,
                citations=validated_citations,
                legal_principles=legal_principles,
                gaps_identified=gaps_identified,
                recommendations=recommendations,
                confidence_score=await self._calculate_overall_confidence(validated_citations, request),
                search_metadata=research_metadata,
                created_at=datetime.now()
            )
            
            # Cache the result
            await self._cache_research_result(request, result)
            
            # Store in knowledge graph
            await self._store_research_in_kg(request, result)
            
            logger.info(f"Completed research request {request.request_id} with {len(validated_citations)} citations")
            return result
            
        except Exception as e:
            logger.exception(f"Failed to execute research request {request.request_id}: {e}")
            raise
    
    async def _build_research_queries(self, request: LegalResearchRequest) -> List[ResearchQuery]:
        """Build comprehensive research queries for the request"""
        queries = []
        
        # Base query for cause of action
        base_query = ResearchQuery(
            query_text=f"{request.cause_of_action} {request.jurisdiction}",
            legal_issues=[request.cause_of_action],
            jurisdiction=request.jurisdiction,
            citation_types=["case", "statute", "regulation"]
        )
        queries.append(base_query)
        
        # Element-specific queries
        for element in request.legal_elements:
            element_query = ResearchQuery(
                query_text=f"{request.cause_of_action} {element} {request.jurisdiction}",
                legal_issues=[element],
                jurisdiction=request.jurisdiction,
                citation_types=["case", "statute"]
            )
            queries.append(element_query)
        
        # Fact-specific queries for complex issues
        if len(request.fact_context) > 0:
            fact_keywords = self._extract_legal_keywords(request.fact_context)
            if fact_keywords:
                fact_query = ResearchQuery(
                    query_text=f"{request.cause_of_action} {' '.join(fact_keywords[:3])} {request.jurisdiction}",
                    legal_issues=fact_keywords[:5],
                    jurisdiction=request.jurisdiction,
                    citation_types=["case"]
                )
                queries.append(fact_query)
        
        return queries
    
    def _extract_legal_keywords(self, fact_context: List[str]) -> List[str]:
        """Extract legal keywords from fact context"""
        keywords = set()
        legal_terms = [
            'contract', 'breach', 'negligent', 'duty', 'care', 'damages',
            'fraud', 'misrepresentation', 'defamation', 'liability',
            'intentional', 'reckless', 'causation', 'proximate'
        ]
        
        for fact in fact_context:
            fact_lower = fact.lower()
            for term in legal_terms:
                if term in fact_lower:
                    keywords.add(term)
        
        return list(keywords)
    
    async def _research_courtlistener(self, query: ResearchQuery, request: LegalResearchRequest) -> List[LegalCitation]:
        """Research using CourtListener API with Claims Matrix context"""
        try:
            if not self._check_api_quota('courtlistener'):
                logger.warning("CourtListener API quota exceeded")
                return []
            
            # Use existing CourtListener client with enhanced context
            results = await self.courtlistener_client.search_opinions(query.query_text, limit=20)
            citations = []
            
            for result in results:
                citation = await self._parse_courtlistener_result(result, request)
                if citation:
                    citations.append(citation)
            
            self._update_api_usage('courtlistener', len(results))
            logger.info(f"CourtListener research returned {len(citations)} citations for {query.query_text}")
            
            return citations
            
        except Exception as e:
            logger.error(f"CourtListener research failed: {e}")
            return []
    
    async def _research_google_scholar(self, query: ResearchQuery, request: LegalResearchRequest) -> List[LegalCitation]:
        """Research using Google Scholar with enhanced parsing"""
        try:
            if not self._check_api_quota('scholar'):
                logger.warning("Google Scholar API quota exceeded")
                return []
            
            # Enhanced query for legal scholarship
            enhanced_query = f"{query.query_text} legal analysis precedent"
            results = await self.scholar_client.search_legal(enhanced_query, limit=10)
            
            citations = []
            for result in results:
                citation = LegalCitation(
                    citation=result.get('citation', ''),
                    title=result.get('title', ''),
                    year=result.get('year'),
                    citation_type='academic',
                    url=result.get('url', ''),
                    excerpt=result.get('snippet', ''),
                    relevance_score=0.5,  # Will be enhanced later
                    authority_level=AuthorityLevel.SECONDARY_SOURCE.value
                )
                citations.append(citation)
            
            self._update_api_usage('scholar', len(results))
            logger.info(f"Google Scholar research returned {len(citations)} citations for {query.query_text}")
            
            return citations
            
        except Exception as e:
            logger.error(f"Google Scholar research failed: {e}")
            return []
    
    async def _research_openalex(self, query: ResearchQuery, request: LegalResearchRequest) -> List[LegalCitation]:
        """Research using OpenAlex API with legal focus"""
        try:
            if not self._check_api_quota('openalex'):
                logger.warning("OpenAlex API quota exceeded")
                return []
            
            # Enhanced query for legal academic research
            enhanced_query = f"{query.query_text} law legal jurisprudence"
            results = await self.openalex_client.search_legal(enhanced_query, limit=15)
            
            citations = []
            for result in results:
                citation = LegalCitation(
                    citation=result.get('citation', ''),
                    title=result.get('title', ''),
                    year=result.get('year'),
                    citation_type='academic',
                    url=result.get('url', ''),
                    excerpt=result.get('snippet', ''),
                    relevance_score=0.5,  # Will be enhanced later
                    authority_level=AuthorityLevel.SECONDARY_SOURCE.value
                )
                citations.append(citation)
            
            self._update_api_usage('openalex', len(results))
            logger.info(f"OpenAlex research returned {len(citations)} citations for {query.query_text}")
            
            return citations
            
        except Exception as e:
            logger.error(f"OpenAlex research failed: {e}")
            return []
    
    async def _parse_courtlistener_result(self, result: Dict, request: LegalResearchRequest) -> Optional[LegalCitation]:
        """Parse CourtListener result with enhanced Claims Matrix context"""
        try:
            # Get court information for authority level
            court_name = result.get('court', '').lower()
            authority_level = self._determine_authority_level(court_name)
            
            # Extract jurisdiction information
            jurisdiction = self._extract_jurisdiction_from_court(court_name)
            
            # Validate jurisdiction compatibility
            if not self._is_jurisdiction_compatible(jurisdiction, request.jurisdiction):
                return None
            
            citation = LegalCitation(
                citation=result.get('citation', ''),
                title=result.get('caseName', ''),
                court=result.get('court', ''),
                year=result.get('dateFiled', '')[:4] if result.get('dateFiled') else None,
                jurisdiction=jurisdiction,
                citation_type='case',
                url=result.get('absolute_url', ''),
                authority_level=authority_level.value,
                excerpt=result.get('snippet', ''),
                relevance_score=0.5  # Will be calculated later
            )
            
            return citation
            
        except Exception as e:
            logger.error(f"Failed to parse CourtListener result: {e}")
            return None
    
    def _determine_authority_level(self, court_name: str) -> AuthorityLevel:
        """Determine authority level from court name"""
        court_lower = court_name.lower()
        
        if 'supreme' in court_lower:
            return AuthorityLevel.SUPREME_COURT
        elif any(term in court_lower for term in ['appellate', 'appeals', 'circuit']):
            return AuthorityLevel.APPELLATE_COURT
        elif any(term in court_lower for term in ['district', 'superior', 'trial']):
            return AuthorityLevel.TRIAL_COURT
        elif any(term in court_lower for term in ['administrative', 'agency']):
            return AuthorityLevel.ADMINISTRATIVE
        else:
            return AuthorityLevel.TRIAL_COURT
    
    def _extract_jurisdiction_from_court(self, court_name: str) -> str:
        """Extract jurisdiction from court name"""
        # Mapping of common court patterns to jurisdictions
        court_lower = court_name.lower()
        
        if 'federal' in court_lower or 'united states' in court_lower:
            return 'federal'
        elif 'california' in court_lower or 'ca' in court_lower:
            return 'ca_state'
        elif 'new york' in court_lower or 'ny' in court_lower:
            return 'ny_state'
        else:
            return 'unknown'
    
    def _is_jurisdiction_compatible(self, result_jurisdiction: str, request_jurisdiction: str) -> bool:
        """Check if result jurisdiction is compatible with request"""
        if result_jurisdiction == request_jurisdiction:
            return True
        
        # Federal law applies to all jurisdictions
        if result_jurisdiction == 'federal':
            return True
        
        # Check jurisdiction manager for compatibility
        return self.jurisdiction_manager.is_jurisdiction_compatible(result_jurisdiction, request_jurisdiction)
    
    async def _apply_relevance_scoring(self, citations: List[LegalCitation], request: LegalResearchRequest) -> List[LegalCitation]:
        """Apply enhanced relevance scoring to citations"""
        for citation in citations:
            score = 0.0
            
            # Authority level scoring (higher authority = higher score)
            authority_scores = {
                AuthorityLevel.SUPREME_COURT.value: 1.0,
                AuthorityLevel.APPELLATE_COURT.value: 0.8,
                AuthorityLevel.TRIAL_COURT.value: 0.6,
                AuthorityLevel.ADMINISTRATIVE.value: 0.4,
                AuthorityLevel.SECONDARY_SOURCE.value: 0.3
            }
            score += authority_scores.get(citation.authority_level, 0.3)
            
            # Jurisdiction matching
            if citation.jurisdiction == request.jurisdiction:
                score += 0.3
            elif citation.jurisdiction == 'federal':
                score += 0.2
            
            # Recency scoring (more recent = higher score)
            if citation.year:
                current_year = datetime.now().year
                years_old = current_year - citation.year
                if years_old <= 5:
                    score += 0.2
                elif years_old <= 10:
                    score += 0.1
            
            # Cause of action matching in title/excerpt
            title_text = (citation.title or '').lower()
            excerpt_text = (citation.excerpt or '').lower()
            cause_lower = request.cause_of_action.lower()
            
            if cause_lower in title_text:
                score += 0.3
            elif cause_lower in excerpt_text:
                score += 0.2
            
            # Element matching
            element_matches = sum(1 for element in request.legal_elements
                                if element.lower() in title_text or element.lower() in excerpt_text)
            score += min(element_matches * 0.1, 0.3)
            
            citation.relevance_score = min(score, 1.0)
        
        # Sort by relevance score
        return sorted(citations, key=lambda c: c.relevance_score, reverse=True)
    
    async def _validate_legal_authorities(self, citations: List[LegalCitation], request: LegalResearchRequest) -> List[LegalCitation]:
        """Validate legal authorities for jurisdiction and precedence"""
        validated_citations = []
        
        for citation in citations:
            validation = await self._validate_single_authority(citation, request)
            
            # Only include valid authorities
            if validation.is_valid:
                validated_citations.append(citation)
                logger.debug(f"Validated citation: {citation.citation} (score: {validation.confidence_score:.2f})")
            else:
                logger.debug(f"Rejected citation: {citation.citation} - {validation.validation_notes}")
        
        return validated_citations
    
    async def _validate_single_authority(self, citation: LegalCitation, request: LegalResearchRequest) -> AuthorityValidation:
        """Validate a single legal authority"""
        try:
            # Check jurisdiction compatibility
            if not self._is_jurisdiction_compatible(citation.jurisdiction, request.jurisdiction):
                return AuthorityValidation(
                    is_valid=False,
                    authority_level=AuthorityLevel(citation.authority_level),
                    jurisdiction_conflict=f"Incompatible jurisdiction: {citation.jurisdiction}",
                    validation_notes="Jurisdiction mismatch"
                )
            
            # Check for federal preemption issues
            preemption_issue = await self._check_federal_preemption(citation, request)
            
            # Basic citation format validation
            citation_valid = self._validate_citation_format(citation.citation)
            
            # Calculate confidence score
            confidence = self._calculate_authority_confidence(citation, request)
            
            return AuthorityValidation(
                is_valid=confidence > 0.3,
                authority_level=AuthorityLevel(citation.authority_level),
                federal_preemption_issue=preemption_issue,
                citation_compliance=citation_valid,
                confidence_score=confidence,
                validation_notes=f"Authority validated with confidence {confidence:.2f}"
            )
            
        except Exception as e:
            logger.error(f"Authority validation failed: {e}")
            return AuthorityValidation(
                is_valid=False,
                authority_level=AuthorityLevel.SECONDARY_SOURCE,
                validation_notes=f"Validation error: {e}"
            )
    
    async def _check_federal_preemption(self, citation: LegalCitation, request: LegalResearchRequest) -> bool:
        """Check for federal preemption issues"""
        # Use jurisdiction manager to check preemption
        return self.jurisdiction_manager.check_federal_preemption(
            citation.jurisdiction, 
            request.cause_of_action
        )
    
    def _validate_citation_format(self, citation_text: str) -> bool:
        """Basic validation of citation format"""
        if not citation_text or len(citation_text) < 5:
            return False
        
        # Basic patterns for common citation formats
        patterns = [
            r'\d+\s+\w+\s+\d+',  # Volume Reporter Page
            r'\d+\s+\w+\.?\s+\d+d?\s+\d+',  # Volume Reporter Series Page
            r'\w+\s+v\.?\s+\w+',  # Case name pattern
        ]
        
        import re
        for pattern in patterns:
            if re.search(pattern, citation_text):
                return True
        
        return False
    
    def _calculate_authority_confidence(self, citation: LegalCitation, request: LegalResearchRequest) -> float:
        """Calculate confidence score for legal authority"""
        confidence = 0.0
        
        # Base confidence from authority level
        authority_confidence = {
            AuthorityLevel.SUPREME_COURT.value: 0.9,
            AuthorityLevel.APPELLATE_COURT.value: 0.7,
            AuthorityLevel.TRIAL_COURT.value: 0.5,
            AuthorityLevel.ADMINISTRATIVE.value: 0.4,
            AuthorityLevel.SECONDARY_SOURCE.value: 0.3
        }
        confidence += authority_confidence.get(citation.authority_level, 0.3)
        
        # Jurisdiction match bonus
        if citation.jurisdiction == request.jurisdiction:
            confidence += 0.1
        
        # Relevance score contribution
        confidence += citation.relevance_score * 0.2
        
        return min(confidence, 1.0)
    
    async def _extract_legal_principles(self, citations: List[LegalCitation], request: LegalResearchRequest) -> List[str]:
        """Extract legal principles from validated citations"""
        principles = []
        
        # Extract principles from highest authority citations
        top_citations = sorted(citations, key=lambda c: (c.authority_level, -c.relevance_score))[:10]
        
        for citation in top_citations:
            if citation.excerpt:
                # Extract legal principles using keyword analysis
                excerpt_principles = self._analyze_text_for_principles(citation.excerpt, request.cause_of_action)
                principles.extend(excerpt_principles)
        
        # Deduplicate and return most relevant principles
        unique_principles = list(dict.fromkeys(principles))  # Preserve order while deduplicating
        return unique_principles[:15]  # Limit to most important principles
    
    def _analyze_text_for_principles(self, text: str, cause_of_action: str) -> List[str]:
        """Analyze text to extract legal principles"""
        principles = []
        
        # Common legal principle patterns
        principle_patterns = [
            r'[Tt]he (plaintiff|defendant) must (prove|establish|show|demonstrate) ([^.]+)\.',
            r'[Tt]o establish ([^,]+), ([^.]+)\.',
            r'[Tt]he test for ([^i]+) is ([^.]+)\.',
            r'[Tt]he standard for ([^i]+) requires ([^.]+)\.',
            r'[Tt]he elements? of ([^a]+) are? ([^.]+)\.'
        ]
        
        import re
        for pattern in principle_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    principle = ' '.join(match).strip()
                    if len(principle) > 10 and len(principle) < 200:
                        principles.append(principle)
        
        return principles
    
    async def _identify_research_gaps(self, citations: List[LegalCitation], request: LegalResearchRequest) -> List[str]:
        """Identify gaps in legal research coverage"""
        gaps = []
        
        # Check element coverage
        covered_elements = set()
        for citation in citations:
            title_text = (citation.title or '').lower()
            excerpt_text = (citation.excerpt or '').lower()
            
            for element in request.legal_elements:
                if element.lower() in title_text or element.lower() in excerpt_text:
                    covered_elements.add(element)
        
        uncovered_elements = set(request.legal_elements) - covered_elements
        for element in uncovered_elements:
            gaps.append(f"Limited authority for element: {element}")
        
        # Check jurisdiction coverage
        jurisdictions_covered = set(c.jurisdiction for c in citations if c.jurisdiction)
        if request.jurisdiction not in jurisdictions_covered:
            gaps.append(f"No direct authority from {request.jurisdiction}")
        
        # Check recency
        recent_citations = [c for c in citations if c.year and c.year >= datetime.now().year - 5]
        if len(recent_citations) < 3:
            gaps.append("Limited recent authority (last 5 years)")
        
        # Check authority levels
        high_authority = [c for c in citations if c.authority_level <= 2]
        if len(high_authority) < 2:
            gaps.append("Limited high-level authority (Supreme/Appellate courts)")
        
        return gaps
    
    async def _generate_research_recommendations(self, citations: List[LegalCitation], request: LegalResearchRequest) -> List[str]:
        """Generate research recommendations based on current results"""
        recommendations = []
        
        # Recommendations based on gaps
        gaps = await self._identify_research_gaps(citations, request)
        
        if any("Limited authority for element" in gap for gap in gaps):
            recommendations.append("Conduct additional element-specific research using narrower search terms")
        
        if any("No direct authority from" in gap for gap in gaps):
            recommendations.append(f"Search for {request.jurisdiction}-specific statutes and regulations")
        
        if any("Limited recent authority" in gap for gap in gaps):
            recommendations.append("Focus on cases from the last 3-5 years for current trends")
        
        if any("Limited high-level authority" in gap for gap in gaps):
            recommendations.append("Research Supreme Court and Appellate court decisions for binding precedent")
        
        # General recommendations
        if len(citations) < 10:
            recommendations.append("Expand search terms to include synonyms and related legal concepts")
        
        if len([c for c in citations if c.citation_type == 'statute']) < 2:
            recommendations.append("Research relevant statutes and regulatory authority")
        
        return recommendations[:10]  # Limit recommendations
    
    async def _calculate_overall_confidence(self, citations: List[LegalCitation], request: LegalResearchRequest) -> float:
        """Calculate overall confidence score for research results"""
        if not citations:
            return 0.0
        
        # Weight factors
        authority_weight = 0.4
        coverage_weight = 0.3
        recency_weight = 0.2
        quantity_weight = 0.1
        
        # Authority score (based on highest authority citations)
        authority_scores = [c.authority_level for c in citations[:5]]
        avg_authority = sum(authority_scores) / len(authority_scores) if authority_scores else 5
        authority_score = 1.0 - (avg_authority - 1) / 4  # Normalize to 0-1
        
        # Coverage score (elements covered)
        covered_elements = set()
        for citation in citations:
            title_text = (citation.title or '').lower()
            excerpt_text = (citation.excerpt or '').lower()
            for element in request.legal_elements:
                if element.lower() in title_text or element.lower() in excerpt_text:
                    covered_elements.add(element)
        
        coverage_score = len(covered_elements) / len(request.legal_elements) if request.legal_elements else 1.0
        
        # Recency score
        current_year = datetime.now().year
        recent_citations = [c for c in citations if c.year and c.year >= current_year - 5]
        recency_score = min(len(recent_citations) / 5, 1.0)  # Normalize to max 5 recent citations
        
        # Quantity score
        quantity_score = min(len(citations) / 20, 1.0)  # Normalize to max 20 citations
        
        # Calculate weighted confidence
        confidence = (
            authority_score * authority_weight +
            coverage_score * coverage_weight +
            recency_score * recency_weight +
            quantity_score * quantity_weight
        )
        
        return round(confidence, 3)
    
    def _check_api_quota(self, api_name: str) -> bool:
        """Check if API quota is available"""
        quota_info = self.api_quotas.get(api_name, {})
        current_time = datetime.now()
        
        # Reset quota if needed
        if current_time >= quota_info.get('reset_time', current_time):
            quota_info['used'] = 0
            quota_info['reset_time'] = self._get_next_reset()
        
        return quota_info.get('used', 0) < quota_info.get('daily_limit', 1000)
    
    def _update_api_usage(self, api_name: str, count: int):
        """Update API usage statistics"""
        if api_name in self.api_quotas:
            self.api_quotas[api_name]['used'] += count
    
    async def _check_research_cache(self, request: LegalResearchRequest) -> Optional[ResearchResult]:
        """Check if research results are cached"""
        cache_key = self._generate_cache_key(request)
        
        try:
            # Query cache from database
            cached_data = self.kg._execute("""
                SELECT result_data, cache_expiry, relevance_score
                FROM legal_research_cache 
                WHERE jurisdiction = ? AND search_query = ? 
                AND cache_expiry > datetime('now')
                ORDER BY created_at DESC LIMIT 1
            """, (request.jurisdiction, cache_key)).fetchone()
            
            if cached_data:
                result_data, cache_expiry, relevance_score = cached_data
                
                # Parse cached result
                result_dict = json.loads(result_data)
                result = ResearchResult(**result_dict)
                
                # Update cache access statistics
                self._update_cache_access(cache_key)
                
                return result
            
            return None
            
        except Exception as e:
            logger.error(f"Cache check failed: {e}")
            return None
    
    def _generate_cache_key(self, request: LegalResearchRequest) -> str:
        """Generate cache key for research request"""
        key_components = [
            request.cause_of_action,
            request.jurisdiction,
            '|'.join(sorted(request.legal_elements)),
            '|'.join(sorted(request.fact_context[:5]))  # Limit fact context for key generation
        ]
        key_string = '||'.join(key_components)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    async def _cache_research_result(self, request: LegalResearchRequest, result: ResearchResult):
        """Cache research results in database"""
        cache_key = self._generate_cache_key(request)
        cache_expiry = datetime.now() + timedelta(hours=request.cache_expiry_hours)
        
        try:
            # Store in legal_research_cache table
            self.kg._execute("""
                INSERT OR REPLACE INTO legal_research_cache
                (jurisdiction, search_query, api_source, result_data, 
                 relevance_score, cache_expiry, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                request.jurisdiction,
                cache_key,
                'integrated_research',
                json.dumps(asdict(result)),
                result.confidence_score,
                cache_expiry,
                datetime.now()
            ))
            
            self.kg.conn.commit()
            logger.debug(f"Cached research result for key: {cache_key}")
            
        except Exception as e:
            logger.error(f"Failed to cache research result: {e}")
    
    def _update_cache_access(self, cache_key: str):
        """Update cache access statistics"""
        # This could be expanded to track cache hit patterns
        pass
    
    async def _store_research_in_kg(self, request: LegalResearchRequest, result: ResearchResult):
        """Store research results in knowledge graph"""
        try:
            # Store key citations as entities
            for citation in result.citations[:10]:  # Store top 10 citations
                entity_id = f"citation_{hashlib.md5(citation.citation.encode()).hexdigest()[:8]}"
                
                legal_entity = {
                    'id': entity_id,
                    'type': 'legal_citation',
                    'name': citation.title or citation.citation,
                    'legal_attributes': {
                        'citation': citation.citation,
                        'court': citation.court,
                        'year': citation.year,
                        'jurisdiction': citation.jurisdiction,
                        'authority_level': citation.authority_level,
                        'relevance_score': citation.relevance_score
                    }
                }
                
                # Store entity in knowledge graph
                await self.kg.add_entity(
                    entity_id=entity_id,
                    entity_type='legal_citation',
                    name=citation.title or citation.citation,
                    legal_attributes=legal_entity['legal_attributes']
                )
            
            logger.info(f"Stored {len(result.citations[:10])} citations in knowledge graph")
            
        except Exception as e:
            logger.error(f"Failed to store research in knowledge graph: {e}")
    
    async def _background_research_processor(self):
        """Background processor for research requests"""
        logger.info("Background research processor started")
        
        while self.background_processor_running:
            try:
                # Process research queue with priority ordering
                pending_requests = []
                
                # Collect all pending requests
                while not self.research_queue.empty():
                    try:
                        request = self.research_queue.get_nowait()
                        pending_requests.append(request)
                    except asyncio.QueueEmpty:
                        break
                
                if pending_requests:
                    # Sort by priority
                    priority_order = {
                        ResearchPriority.CRITICAL: 0,
                        ResearchPriority.HIGH: 1,
                        ResearchPriority.MEDIUM: 2,
                        ResearchPriority.LOW: 3,
                        ResearchPriority.BACKGROUND: 4
                    }
                    
                    pending_requests.sort(key=lambda r: priority_order.get(r.priority, 5))
                    
                    # Process high priority requests first
                    for request in pending_requests:
                        if not self.background_processor_running:
                            break
                        
                        try:
                            await self.execute_research_request(request)
                        except Exception as e:
                            logger.error(f"Background research failed for {request.request_id}: {e}")
                
                # Sleep before next iteration
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Background processor error: {e}")
                await asyncio.sleep(60)  # Longer sleep on error
        
        logger.info("Background research processor stopped")
    
    async def _cache_maintenance_task(self):
        """Background task for cache maintenance"""
        while self.background_processor_running:
            try:
                # Clean expired cache entries
                expired_count = self.kg._execute("""
                    DELETE FROM legal_research_cache 
                    WHERE cache_expiry < datetime('now')
                """).rowcount
                
                if expired_count > 0:
                    logger.info(f"Cleaned {expired_count} expired cache entries")
                    self.kg.conn.commit()
                
                # Update cache statistics
                cache_size = self.kg._execute("""
                    SELECT COUNT(*), SUM(LENGTH(result_data)) 
                    FROM legal_research_cache
                """).fetchone()
                
                if cache_size:
                    self.cache_stats['size_mb'] = (cache_size[1] or 0) / (1024 * 1024)
                
                await asyncio.sleep(3600)  # Run every hour
                
            except Exception as e:
                logger.error(f"Cache maintenance error: {e}")
                await asyncio.sleep(1800)  # 30 minutes on error
    
    async def _quota_reset_task(self):
        """Background task to reset API quotas daily"""
        while self.background_processor_running:
            try:
                current_time = datetime.now()
                
                for api_name, quota_info in self.api_quotas.items():
                    if current_time >= quota_info['reset_time']:
                        quota_info['used'] = 0
                        quota_info['reset_time'] = self._get_next_reset()
                        logger.info(f"Reset API quota for {api_name}")
                
                await asyncio.sleep(3600)  # Check every hour
                
            except Exception as e:
                logger.error(f"Quota reset task error: {e}")
                await asyncio.sleep(1800)
    
    async def get_research_status(self, request_id: str) -> Dict[str, Any]:
        """Get status of a research request"""
        try:
            # Check if completed (in cache or knowledge graph)
            cached_result = self.kg._execute("""
                SELECT cache_expiry, relevance_score, created_at
                FROM legal_research_cache 
                WHERE search_query LIKE ? 
                ORDER BY created_at DESC LIMIT 1
            """, (f"%{request_id}%",)).fetchone()
            
            if cached_result:
                return {
                    'request_id': request_id,
                    'status': 'completed',
                    'completion_time': cached_result[2],
                    'confidence_score': cached_result[1]
                }
            
            # Check queue
            queue_size = self.research_queue.qsize()
            
            return {
                'request_id': request_id,
                'status': 'queued' if queue_size > 0 else 'processing',
                'queue_position': queue_size,
                'estimated_completion': datetime.now() + timedelta(minutes=queue_size * 5)
            }
            
        except Exception as e:
            logger.error(f"Failed to get research status: {e}")
            return {
                'request_id': request_id,
                'status': 'error',
                'error': str(e)
            }
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        return {
            'hit_rate': self.cache_stats['hits'] / max(self.cache_stats['hits'] + self.cache_stats['misses'], 1),
            'total_hits': self.cache_stats['hits'],
            'total_misses': self.cache_stats['misses'],
            'cache_size_mb': self.cache_stats['size_mb'],
            'invalidations': self.cache_stats['invalidations']
        }
    
    def get_api_quotas(self) -> Dict[str, Any]:
        """Get current API quota usage"""
        return {
            api_name: {
                'used': info['used'],
                'limit': info['daily_limit'],
                'reset_time': info['reset_time'].isoformat(),
                'remaining': info['daily_limit'] - info['used']
            }
            for api_name, info in self.api_quotas.items()
        }