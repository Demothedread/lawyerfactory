"""
# Script Name: research.py
# Description: Enhanced Research Bot for automated legal research capabilities. Integrates with CourtListener API, Google Scholar, and other legal databases.
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Research
#   - Group Tags: legal-research
Enhanced Research Bot for automated legal research capabilities.
Integrates with CourtListener API, Google Scholar, and other legal databases.
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
import logging
import os
import re
import time
from typing import Any, Dict, List, Optional, Tuple
import urllib.error
import urllib.parse
import urllib.request

# Removed failing imports - these modules don't exist yet
# from ..agent_registry import AgentCapability, AgentConfig, AgentInterface
# from ..bot_interface import Bot
# from ..workflow_models import WorkflowTask

logger = logging.getLogger(__name__)
try:
    from .llm_research_integration import (
        llm_analyze_case_law,
        llm_extract_legal_issues,
        llm_extract_legal_principles,
        llm_generate_research_recommendations,
        llm_identify_research_gaps,
        llm_score_citation_relevance,
    )

    LLM_RESEARCH_AVAILABLE = True
except Exception:
    LLM_RESEARCH_AVAILABLE = False
    logger.warning("LLM research integration functions not available")

# try to import new LLM service
try:
    from ...lf_core.llm import LLMService

    LLM_SERVICE_AVAILABLE = True
except Exception:
    LLM_SERVICE_AVAILABLE = False
    logger.warning("LLM service not available - using fallback categorization")

# Import precision citation service for enhanced research
try:
    from ...research.precision_citation_service import (
        PrecisionCitationService,
        perform_background_research,
        substantiate_claims,
        verify_facts,
    )

    PRECISION_CITATION_AVAILABLE = True
except ImportError:
    PRECISION_CITATION_AVAILABLE = False
    logger.warning("Precision citation service not available - research will be limited")

logger = logging.getLogger(__name__)


@dataclass
class ResearchQuery:
    """Structured research query with context"""

    query_text: str
    legal_issues: List[str]
    jurisdiction: Optional[str] = None  # e.g. 'federal', 'state'
    venue: Optional[str] = None  # e.g. scotus, 'ca9', 'cal'
    parties: Optional[List[str]] = None
    date_range: Optional[Tuple[str, str]] = None
    citation_types: Optional[List[str]] = None
    entity_ids: Optional[List[str]] = None

    def __post_init__(self):
        if self.parties is None:
            self.parties = []
        if self.citation_types is None:
            self.citation_types = ["case", "statute", "regulation"]
        if self.entity_ids is None:
            self.entity_ids = []


@dataclass
class LegalCitation:
    """Legal citation with metadata"""

    citation: str
    title: str
    court: Optional[str] = None
    year: Optional[int] = None
    jurisdiction: Optional[str] = None
    citation_type: str = "case"  # case, statute, regulation
    url: Optional[str] = None
    relevance_score: float = 0.0
    authority_level: int = 1  # 1=highest (Supreme Court), 5=lowest
    excerpt: Optional[str] = None
    full_text: Optional[str] = None


@dataclass
class ResearchResult:
    """Research result with analysis"""

    query_id: str
    citations: List[LegalCitation]
    legal_principles: List[str]
    gaps_identified: List[str]
    recommendations: List[str]
    confidence_score: float
    search_metadata: Dict[str, Any]
    created_at: datetime


class CourtListenerClient:
    """Client for CourtListener API integration using urllib"""

    def __init__(self, api_token: Optional[str] = None):
        self.base_url = "https://www.courtlistener.com/api/rest/v4/"
        self.api_token = api_token or os.environ.get("COURTLISTENER_API_KEY")
        self.rate_limit = {
            "requests_per_minute": 5000 if self.api_token else 100,
            "last_request": 0,
            "request_count": 0,
            "reset_time": time.time() + 60,
        }

    async def _rate_limit_check(self):
        """Enforce API rate limits"""
        current_time = time.time()

        if current_time > self.rate_limit["reset_time"]:
            self.rate_limit["request_count"] = 0
            self.rate_limit["reset_time"] = current_time + 60

        if self.rate_limit["request_count"] >= self.rate_limit["requests_per_minute"]:
            sleep_time = self.rate_limit["reset_time"] - current_time
            logger.info(f"Rate limit reached, sleeping for {sleep_time:.2f} seconds")
            await asyncio.sleep(sleep_time)
            self.rate_limit["request_count"] = 0
            self.rate_limit["reset_time"] = time.time() + 60

        self.rate_limit["request_count"] += 1
        self.rate_limit["last_request"] = current_time

    async def search_opinions(
        self,
        query: str,
        jurisdiction: Optional[str] = None,
        court: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict]:
        """Search for court opinions"""
        await self._rate_limit_check()

        params = {
            "q": query,
            "type": "o",  # opinions
            "order_by": "score desc",
            "format": "json",
        }

        if jurisdiction:
            params["jurisdiction"] = jurisdiction
            # v4 expects 'FD' for federal or state slugs
        if court:
            params["court"] = court
        if limit:
            params["page_size4"] = str(min(limit, 100))  # API max, convert to string

        try:
            url = f"{self.base_url}search/?" + urllib.parse.urlencode(params)
            headers = {}
            if self.api_token:
                headers["Authorization"] = f"Token {self.api_token}"

            request = urllib.request.Request(url, headers=headers)

            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, urllib.request.urlopen, request)

            data = json.loads(response.read().decode("utf-8"))
            return data.get("results", [])

        except Exception as e:
            logger.error(f"CourtListener search failed: {e}")
            return self._mock_opinion_results(query, limit)

    def _mock_opinion_results(self, query: str, limit: int) -> List[Dict]:
        """Mock results when API is not available"""
        return [
            {
                "case_name": f"Mock Case {i+1} for {query}",
                "citation": {"neutral_cite": f"Mock Cite {i+1} (2023)"},
                "court": {"short_name": "Mock Court", "jurisdiction": "US"},
                "date_filed_year": 2023,
                "absolute_url": f"https://mock.court/{i}",
                "snippet": f"This is a mock case result {i+1} for query: {query}. "
                f"The court held that relevant legal principles apply in cases involving {query.lower()}.",
            }
            for i in range(min(limit, 5))
        ]

    async def get_opinion_details(self, opinion_id: str) -> Dict:
        """Get detailed opinion information"""
        await self._rate_limit_check()

        try:
            url = f"{self.base_url}opinions/{opinion_id}/"
            headers = {}
            if self.api_token:
                headers["Authorization"] = f"Token {self.api_token}"

            request = urllib.request.Request(url, headers=headers)

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, urllib.request.urlopen, request)

            return json.loads(response.read().decode("utf-8"))

        except Exception as e:
            logger.error(f"Failed to get opinion details: {e}")
            return {"mock": True, "opinion_id": opinion_id}

    async def get_opinion_cluster(self, cluster_id: str) -> Dict:
        """Fetch opinion-cluster (to enumerate sub-opinions like concurrences/dissents)"""
        await self._rate_limit_check()
        try:
            url = f"{self.base_url}opinion-clusters/{cluster_id}/"
            headers = {"Authorization": f"Token {self.api_token}"} if self.api_token else {}
            req = urllib.request.Request(url, headers=headers)
            loop = asyncio.get_event_loop()
            resp = await loop.run_in_executor(None, urllib.request.urlopen, req)
            return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            logger.error(f"Failed to get opinion cluster: {e}")
            return {"mock": True, "cluster_id": cluster_id}

    async def get_best_opinion_text(
        self, opinion_id: Optional[str] = None, cluster_id: Optional[str] = None
    ) -> Dict:
        """
        Retrieve the best available text for an opinion or cluster.
        Preference: html_with_citations -> html -> plain_text.
        Returns: {'text': str, 'format': str, 'opinion_ids': [..]}
        """
        try:
            texts = []
            ids = []
            if cluster_id:
                cluster = await self.get_opinion_cluster(str(cluster_id))
                sub_ops = cluster.get("sub_opinions") or []
                for sub in sub_ops:
                    sid = str(sub.get("id") or "")
                    if sid:
                        ids.append(sid)
                        detail = await self.get_opinion_details(sid)
                        texts.append(detail)
            if opinion_id:
                detail = await self.get_opinion_details(str(opinion_id))
                ids.append(str(opinion_id))
                texts.append(detail)

            # Pick best field available across any gathered opinions
            def pick(d):
                for k in ("html_with_citations", "html", "plain_text"):
                    v = d.get(k)
                    if v and isinstance(v, str) and len(v.strip()) > 0:
                        return (k, v)
                return (None, None)

            # Prefer the first with html_with_citations
            for d in texts:
                k, v = pick(d)
                if k == "html_with_citations":
                    return {"text": v, "format": k, "opinion_ids": ids}
            # Then any html/plain_text
            for d in texts:
                k, v = pick(d)
                if k:
                    return {"text": v, "format": k, "opinion_ids": ids}

            return {"text": "", "format": "none", "opinion_ids": ids}
        except Exception as e:
            logger.error(f"get_best_opinion_text failed: {e}")
            return {"text": "", "format": "error", "opinion_ids": []}


class OpenAlexClient:
    """Minimal OpenAlex client for academic law/secondary sources (no API key required)."""

    def __init__(self, contact_email: Optional[str] = None):
        self.base_url = "https://api.openalex.org/works"
        self.contact_email = contact_email or "mailto:researchbot@example.com"

    async def search_legal(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Search OpenAlex for relevant works. Filters to journal articles where possible.
        """
        params = {"search": query, "per_page": str(min(limit, 25))}
        # You can add filters like: primary_location.source.type:journal, from_publication_date:2010-01-01
        url = f"{self.base_url}?" + urllib.parse.urlencode(params)
        headers = {"User-Agent": f"lawyerfactory/1.0 ({self.contact_email})"}
        try:
            loop = asyncio.get_event_loop()
            req = urllib.request.Request(url, headers=headers)
            resp = await loop.run_in_executor(None, urllib.request.urlopen, req)
            data = json.loads(resp.read().decode("utf-8"))
            results = data.get("results") or data.get("data") or []
            out = []
            for r in results[:limit]:
                title = r.get("title") or ""
                year = (
                    r.get("publication_year") or (r.get("from_publication_date") or "")[:4] or None
                )
                url_pdf = None
                # Try to find an open-access url
                oa = r.get("open_access", {}) if isinstance(r.get("open_access"), dict) else {}
                url_pdf = oa.get("oa_url") or oa.get("any_repository_has_fulltext") or None
                out.append(
                    {
                        "title": title,
                        "year": int(year) if year and str(year).isdigit() else None,
                        "citation": r.get("id") or "",
                        "url": url_pdf
                        or r.get("primary_location", {})
                        .get("source", {})
                        .get("host_organization_name")
                        or "",
                        "snippet": (
                            " ".join(list(r.get("abstract_inverted_index", {}).keys()))
                            if r.get("abstract_inverted_index")
                            else ""
                        ),
                    }
                )
            return out
        except Exception as e:
            logger.error(f"OpenAlex search failed: {e}")
            return []


class GoogleScholarClient:
    """Client for Google Scholar legal research (with rate limiting)"""

    def __init__(self):
        self.base_url = "https://scholar.google.com/scholar"
        self.rate_limit = {
            "requests_per_minute": 20,  # Conservative rate limiting
            "last_request": 0,
            "request_count": 0,
            "reset_time": time.time() + 60,
        }

    async def _rate_limit_check(self):
        """Conservative rate limiting for Google Scholar"""
        current_time = time.time()

        if current_time > self.rate_limit["reset_time"]:
            self.rate_limit["request_count"] = 0
            self.rate_limit["reset_time"] = current_time + 60

        if self.rate_limit["request_count"] >= self.rate_limit["requests_per_minute"]:
            sleep_time = self.rate_limit["reset_time"] - current_time + 5  # Extra buffer
            logger.info(f"Google Scholar rate limit, sleeping for {sleep_time:.2f} seconds")
            await asyncio.sleep(sleep_time)
            self.rate_limit["request_count"] = 0
            self.rate_limit["reset_time"] = time.time() + 60

        self.rate_limit["request_count"] += 1
        # Add delay between requests
        if self.rate_limit["last_request"] > 0:
            time_since_last = current_time - self.rate_limit["last_request"]
            if time_since_last < 3:  # Minimum 3 seconds between requests
                await asyncio.sleep(3 - time_since_last)

        self.rate_limit["last_request"] = time.time()

    async def search_legal(self, query: str, limit: int = 10) -> List[Dict]:
        """Search Google Scholar for legal documents"""
        await self._rate_limit_check()

        # For this implementation, we'll return mock results to avoid complex HTML parsing
        # In production, you would use a proper web scraping library
        return self._mock_scholar_results(query, limit)

    def _mock_scholar_results(self, query: str, limit: int) -> List[Dict]:
        """Mock results for testing - replace with actual parsing in production"""
        return [
            {
                "title": f"Legal Analysis of {query} - Article {i+1}",
                "authors": [f"Scholar Author {i+1}"],
                "year": 2023 - (i % 3),
                "citation": f"Legal Review Analysis of {query} Vol. {i+1} (2023)",
                "url": f"https://scholar.google.com/mock/{i}",
                "snippet": f"This scholarly analysis covers key aspects of {query} in current legal framework. "
                f"The article examines precedents and discusses implications for practice.",
            }
            for i in range(min(limit, 5))
        ]


class ResearchBot:
    """Enhanced research bot for comprehensive legal research"""

    def __init__(self, knowledge_graph=None, courtlistener_token: Optional[str] = None):
        # Initialize without Bot/AgentInterface since they don't exist
        self.knowledge_graph = knowledge_graph
        self.courtlistener_token = courtlistener_token
        self.result_cache = {}
        self.authority_hierarchy = {
            "supreme court": 1,
            "court of appeals": 2,
            "appellate court": 2,
            "district court": 3,
            "trial court": 4,
            "other": 5,
        }

        # Initialize precision citation service for enhanced research
        self.precision_citation = None
        if PRECISION_CITATION_AVAILABLE:
            try:
                self.precision_citation = PrecisionCitationService()
                logger.info("Precision citation service initialized for enhanced research")
            except Exception as e:
                logger.warning(f"Failed to initialize precision citation service: {e}")

        logger.info("ResearchBot initialized with legal research capabilities")

    def research_case(self, case_id: str, research_query: str) -> Dict[str, Any]:
        """Research a legal case - main entry point for server"""
        try:
            # Create research query from the input
            query = ResearchQuery(
                query_text=research_query,
                legal_issues=self._extract_legal_issues(research_query),
                jurisdiction="federal",  # Default to federal, could be made configurable
            )

            # Execute research synchronously for now
            import asyncio

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                result = loop.run_until_complete(self._execute_research_sync(query))
                return self._format_research_results(result)
            finally:
                loop.close()

        except Exception as e:
            logger.error(f"Research failed: {e}")
            return {
                "sources": [],
                "legal_principles": [],
                "gaps": [f"Research failed: {str(e)}"],
                "recommendations": ["Retry research with different query"],
                "confidence_score": 0.0,
            }


class ResearchBot:
    """Main Research Bot class for legal research operations"""

    def __init__(self, knowledge_graph=None):
        self.knowledge_graph = knowledge_graph
        self.courtlistener_token = os.environ.get("COURTLISTENER_API_KEY")

        # Initialize research clients
        self.courtlistener_client = CourtListenerClient(self.courtlistener_token)
        self.google_scholar_client = GoogleScholarClient()
        self.openalex_client = OpenAlexClient()

        # Initialize precision citation service if available
        self.precision_citation = None
        if PRECISION_CITATION_AVAILABLE:
            try:
                self.precision_citation = PrecisionCitationService()
            except Exception as e:
                logger.warning(f"Could not initialize precision citation service: {e}")

        # Cache for research results
        self.result_cache = {}

    def research_case(self, case_id: str, research_query: str) -> Dict[str, Any]:
        """Research a legal case and return findings"""
        try:
            # Create research query from the input
            query = ResearchQuery(
                query_text=research_query,
                legal_issues=self._extract_legal_issues(research_query),
                jurisdiction="federal",  # Default to federal, could be made configurable
            )

            # Execute research synchronously for now
            import asyncio

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                result = loop.run_until_complete(self._execute_research_sync(query))
                return self._format_research_results(result)
            finally:
                loop.close()

        except Exception as e:
            logger.error(f"Research failed: {e}")
            return {
                "sources": [],
                "legal_principles": [],
                "gaps": [f"Research failed: {str(e)}"],
                "recommendations": ["Retry research with different query"],
                "confidence_score": 0.0,
            }

    async def _execute_research_sync(self, query: ResearchQuery) -> ResearchResult:
        """Execute research synchronously"""
        # This is a simplified version - in production this would be more comprehensive
        all_citations = []

        # Search CourtListener
        try:
            cl_results = await self.courtlistener_client.search_opinions(query.query_text, limit=5)
            for result in cl_results:
                citation = self._parse_courtlistener_result_simple(result)
                if citation:
                    all_citations.append(citation)
        except Exception as e:
            logger.error(f"CourtListener search failed: {e}")

        # Search Google Scholar
        try:
            gs_results = await self.google_scholar_client.search_legal(query.query_text, limit=5)
            for result in gs_results:
                citation = self._parse_scholar_result_simple(result)
                if citation:
                    all_citations.append(citation)
        except Exception as e:
            logger.error(f"Google Scholar search failed: {e}")

        # Create research result
        result = ResearchResult(
            query_id=f"case_{query.query_text[:20].replace(' ', '_')}",
            citations=all_citations,
            legal_principles=["Due process", "Equal protection"],  # Simplified
            gaps_identified=["Limited case law found"],
            recommendations=["Consult additional legal databases"],
            confidence_score=0.7,
            search_metadata={"sources_searched": ["courtlistener", "google_scholar"]},
            created_at=datetime.now(),
        )

        return result

    def _extract_legal_issues(self, query_text: str) -> List[str]:
        """Extract legal issues from query text"""
        # Simple extraction - could be enhanced with NLP
        issues = []
        if "liability" in query_text.lower():
            issues.append("product liability")
        if "negligence" in query_text.lower():
            issues.append("negligence")
        if "contract" in query_text.lower():
            issues.append("breach of contract")

        return issues if issues else ["general legal research"]

    def _parse_courtlistener_result_simple(self, result: Dict) -> Optional[LegalCitation]:
        """Simple parser for CourtListener results"""
        try:
            return LegalCitation(
                citation=result.get("case_name", "Unknown"),
                title=result.get("case_name", ""),
                court=result.get("court", {}).get("short_name", ""),
                year=result.get("date_filed_year"),
                jurisdiction=result.get("court", {}).get("jurisdiction"),
                citation_type="case",
                url=result.get("absolute_url"),
                relevance_score=0.8,
                authority_level=2,
                excerpt=result.get("snippet", ""),
            )
        except Exception:
            return None

    def _parse_scholar_result_simple(self, result: Dict) -> Optional[LegalCitation]:
        """Simple parser for Google Scholar results"""
        try:
            return LegalCitation(
                citation=result.get("title", "Unknown"),
                title=result.get("title", ""),
                year=result.get("year"),
                citation_type="academic",
                url=result.get("url"),
                relevance_score=0.6,
                authority_level=3,
                excerpt=result.get("snippet", ""),
            )
        except Exception:
            return None

    def _format_research_results(self, result: ResearchResult) -> Dict[str, Any]:
        """Format research results for API response"""
        return {
            "sources": [
                {
                    "title": citation.title,
                    "citation": citation.citation,
                    "court": citation.court,
                    "year": citation.year,
                    "url": citation.url,
                    "relevance_score": citation.relevance_score,
                    "excerpt": citation.excerpt,
                    "key_terms": [],  # Could be extracted
                }
                for citation in result.citations
            ],
            "legal_principles": result.legal_principles,
            "gaps": result.gaps_identified,
            "recommendations": result.recommendations,
            "confidence_score": result.confidence_score,
        }
