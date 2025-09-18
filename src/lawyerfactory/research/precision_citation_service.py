"""
Precision Citation Service - Advanced legal research with source quality filtering
Provides structured search with academic/peer-reviewed prioritization and citation metrics.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import logging
import re

try:
    from .tavily_integration import TavilyResearchIntegration, ResearchQuery
    import weave
    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False
    TavilyResearchIntegration = None
    weave = None

logger = logging.getLogger(__name__)


@dataclass
class QualityMetrics:
    """Source quality assessment metrics"""
    domain: str
    authority_score: float = 0.0  # 1.0-5.0 scale
    citation_count_weight: float = 0.0  # Based on citations if available
    q_score_weight: float = 0.0  # Author/publication quality score
    recency_score: float = 0.0  # How recent the publication is
    overall_quality_score: float = 0.0  # Composite score 1.0-5.0


@dataclass
class PrecisionCitation:
    """Precision citation with quality metrics and structured data"""
    title: str
    url: str
    content: str
    source_type: str  # academic, news, web
    quality_metrics: QualityMetrics
    citation_count: int = 0
    author_q_score: float = 0.0
    publication_date: Optional[str] = None
    bluebook_citation: str = ""
    created_at: datetime = field(default_factory=datetime.now)


class PrecisionCitationService:
    """
    Advanced citation service with academic prioritization and quality filtering.
    Integrates with Tavily for comprehensive source discovery.
    """

    def __init__(self):
        if not TAVILY_AVAILABLE:
            logger.warning("Tavily integration not available, using fallback mode")
            self.tavily = None
        else:
            self.tavily = TavilyResearchIntegration()
        
        # Academic domain prioritization
        self.academic_domains = {
            # Top-tier academic publishers
            "scholar.google.com": 5.0,
            "ssrn.com": 4.8,
            "jstor.org": 4.7,
            "heinonline.org": 4.6,
            "westlaw.com": 4.5,
            "lexisnexis.com": 4.5,
            
            # University presses and journals
            "academic.oup.com": 4.3,
            "cambridge.org": 4.2,
            "springer.com": 4.1,
            "wiley.com": 4.0,
            "tandfonline.com": 3.9,
            "sagepub.com": 3.8,
            
            # Legal research platforms
            "courtlistener.com": 4.4,
            "justia.com": 3.5,
            "findlaw.com": 3.2,
            
            # Government sources
            "govinfo.gov": 4.6,
            "congress.gov": 4.5,
            "supremecourt.gov": 4.8,
            
            # Research institutions
            "researchgate.net": 3.7,
            "academia.edu": 3.4,
        }
        
        # News source quality ratings
        self.news_domains = {
            # Top-tier news sources
            "nytimes.com": 4.5,
            "wsj.com": 4.4,
            "reuters.com": 4.3,
            "apnews.com": 4.2,
            "bloomberg.com": 4.1,
            
            # Quality news sources
            "washingtonpost.com": 4.0,
            "bbc.com": 3.9,
            "cnn.com": 3.5,
            "foxnews.com": 3.4,
            "npr.org": 3.8,
            
            # Legal news
            "law.com": 3.9,
            "abajournal.com": 3.8,
            "legalreader.com": 3.3,
        }
        
        # Low-quality domains to exclude
        self.excluded_domains = {
            "wikipedia.org",
            "wikimedia.org",
            "answers.com",
            "quora.com",
            "reddit.com",
            "facebook.com",
            "twitter.com",
            "instagram.com",
            "linkedin.com",
            "medium.com",  # Unless from verified legal publication
            "blogspot.com",
            "wordpress.com",  # Unless verified legal blog
        }

    async def search_background_research(
        self,
        intake_data: Dict[str, Any],
        existing_evidence: Optional[Dict[str, Any]] = None,
        max_sources: int = 4
    ) -> List[PrecisionCitation]:
        """
        Perform background research for Phase A01 intake
        
        Args:
            intake_data: Intake form data
            existing_evidence: Existing evidence context
            max_sources: Maximum sources to return (3-4 for A01)
            
        Returns:
            List of precision citations with quality filtering
        """
        logger.info("Starting precision background research")
        
        # Extract search terms from intake data
        search_terms = self._extract_search_terms_from_intake(intake_data)
        
        # Perform searches across multiple source types
        all_citations = []
        
        for search_term in search_terms[:2]:  # Limit to 2 main search terms for A01
            # Academic search
            academic_citations = await self._search_academic_sources(
                search_term, intake_data, max_results=6
            )
            all_citations.extend(academic_citations)
            
            # News search for recent developments
            news_citations = await self._search_news_sources(
                search_term, intake_data, max_results=4
            )
            all_citations.extend(news_citations)
        
        # Apply quality filtering and ranking
        filtered_citations = self._filter_and_rank_citations(all_citations, max_sources)
        
        logger.info(f"Background research complete: {len(filtered_citations)} high-quality sources")
        return filtered_citations

    async def search_claim_substantiation(
        self,
        claims: List[str],
        jurisdiction: str,
        max_sources_per_claim: int = 3
    ) -> Dict[str, List[PrecisionCitation]]:
        """
        Perform claim substantiation research for Phase B01
        
        Args:
            claims: List of legal claims to substantiate
            jurisdiction: Legal jurisdiction
            max_sources_per_claim: Maximum sources per claim
            
        Returns:
            Dictionary mapping claims to citation lists
        """
        logger.info(f"Starting claim substantiation for {len(claims)} claims")
        
        results = {}
        
        for claim in claims:
            # Create targeted search query
            search_query = f"{claim} {jurisdiction} case law precedent"
            
            # Search academic sources for legal analysis
            academic_citations = await self._search_academic_sources(
                search_query, {"jurisdiction": jurisdiction}, max_results=5
            )
            
            # Search recent news for developments
            news_citations = await self._search_news_sources(
                search_query, {"jurisdiction": jurisdiction}, max_results=3
            )
            
            # Combine and filter
            all_citations = academic_citations + news_citations
            filtered_citations = self._filter_and_rank_citations(
                all_citations, max_sources_per_claim
            )
            
            results[claim] = filtered_citations
        
        return results

    async def search_fact_verification(
        self,
        facts: List[str],
        context: Dict[str, Any],
        max_sources_per_fact: int = 2
    ) -> Dict[str, List[PrecisionCitation]]:
        """
        Perform fact verification research for Phase C01
        
        Args:
            facts: List of facts to verify
            context: Case context
            max_sources_per_fact: Maximum sources per fact
            
        Returns:
            Dictionary mapping facts to citation lists
        """
        logger.info(f"Starting fact verification for {len(facts)} facts")
        
        results = {}
        
        for fact in facts:
            # Create verification-focused search query
            search_query = f"{fact} verification recent developments"
            
            # Focus on recent news and academic sources
            citations = []
            
            # Recent news for current developments
            news_citations = await self._search_news_sources(
                search_query, context, max_results=4
            )
            citations.extend(news_citations)
            
            # Academic sources for authoritative verification
            academic_citations = await self._search_academic_sources(
                search_query, context, max_results=3
            )
            citations.extend(academic_citations)
            
            # Filter for highest quality
            filtered_citations = self._filter_and_rank_citations(
                citations, max_sources_per_fact
            )
            
            results[fact] = filtered_citations
        
        return results

    def _extract_search_terms_from_intake(self, intake_data: Dict[str, Any]) -> List[str]:
        """Extract optimized search terms from intake data"""
        search_terms = []
        
        # Primary search term from causes of action + jurisdiction
        causes_of_action = intake_data.get("causes_of_action", [])
        jurisdiction = intake_data.get("jurisdiction", "")
        
        for coa in causes_of_action[:2]:  # Limit to first 2 COAs
            if jurisdiction:
                search_terms.append(f"{coa} {jurisdiction}")
            else:
                search_terms.append(str(coa))
        
        # Secondary search term from claim description
        claim_description = intake_data.get("claim_description", "")
        if claim_description:
            # Extract key legal terms from description
            legal_keywords = self._extract_legal_keywords(claim_description)
            if legal_keywords and jurisdiction:
                search_terms.append(f"{' '.join(legal_keywords[:3])} {jurisdiction}")
        
        # Fallback general search
        if not search_terms:
            search_terms.append("legal precedent case law")
        
        return search_terms[:2]  # Limit to 2 main searches for A01

    def _extract_legal_keywords(self, text: str) -> List[str]:
        """Extract legal keywords from text"""
        legal_patterns = [
            r'\b(negligence|breach|contract|tort|liability|damages)\b',
            r'\b(duty|care|injury|property|venue|jurisdiction)\b',
            r'\b(defendant|plaintiff|respondent|petitioner)\b',
            r'\b(statute|regulation|case law|precedent)\b'
        ]
        
        keywords = []
        text_lower = text.lower()
        
        for pattern in legal_patterns:
            matches = re.findall(pattern, text_lower)
            keywords.extend(matches)
        
        return list(set(keywords))  # Remove duplicates

    async def _search_academic_sources(
        self,
        query: str,
        context: Dict[str, Any],
        max_results: int = 5
    ) -> List[PrecisionCitation]:
        """Search academic sources with quality filtering"""
        if not self.tavily:
            return []
        
        try:
            # Use Tavily for academic search
            results = await self.tavily.search_academic_sources(
                query, max_results=max_results * 2  # Get more to filter
            )
            
            citations = []
            for result in results.get("results", []):
                citation = self._create_precision_citation(result, "academic", context)
                if citation and self._passes_quality_filter(citation):
                    citations.append(citation)
            
            return citations[:max_results]
            
        except Exception as e:
            logger.error(f"Academic search failed: {e}")
            return []

    async def _search_news_sources(
        self,
        query: str,
        context: Dict[str, Any],
        max_results: int = 3
    ) -> List[PrecisionCitation]:
        """Search news sources with quality filtering"""
        if not self.tavily:
            return []
        
        try:
            # Use Tavily for news search
            results = await self.tavily.search_news_sources(
                query, max_results=max_results * 2  # Get more to filter
            )
            
            citations = []
            for result in results.get("results", []):
                citation = self._create_precision_citation(result, "news", context)
                if citation and self._passes_quality_filter(citation):
                    citations.append(citation)
            
            return citations[:max_results]
            
        except Exception as e:
            logger.error(f"News search failed: {e}")
            return []

    def _create_precision_citation(
        self,
        search_result: Dict[str, Any],
        source_type: str,
        context: Dict[str, Any]
    ) -> Optional[PrecisionCitation]:
        """Create precision citation from search result"""
        try:
            url = search_result.get("url", "")
            title = search_result.get("title", "")
            content = search_result.get("content", "")
            
            if not url or not title:
                return None
            
            # Calculate quality metrics
            quality_metrics = self._calculate_quality_metrics(url, source_type, search_result)
            
            # Generate Bluebook citation
            bluebook_citation = self._generate_bluebook_citation(
                title, url, source_type, search_result
            )
            
            return PrecisionCitation(
                title=title,
                url=url,
                content=content,
                source_type=source_type,
                quality_metrics=quality_metrics,
                citation_count=search_result.get("citation_count", 0),
                author_q_score=search_result.get("author_q_score", 0.0),
                publication_date=search_result.get("published_date"),
                bluebook_citation=bluebook_citation
            )
            
        except Exception as e:
            logger.error(f"Failed to create precision citation: {e}")
            return None

    def _calculate_quality_metrics(
        self,
        url: str,
        source_type: str,
        search_result: Dict[str, Any]
    ) -> QualityMetrics:
        """Calculate comprehensive quality metrics for a source"""
        domain = self._extract_domain(url)
        
        # Base authority score from domain reputation
        if source_type == "academic":
            authority_score = self.academic_domains.get(domain, 2.0)
        elif source_type == "news":
            authority_score = self.news_domains.get(domain, 2.5)
        else:
            authority_score = 2.0  # Default for unknown sources
        
        # Citation count weight (if available)
        citation_count = search_result.get("citation_count", 0)
        citation_count_weight = min(1.0, citation_count / 100.0) if citation_count > 0 else 0.0
        
        # Q-score weight (author/publication quality)
        q_score = search_result.get("author_q_score", 0.0)
        q_score_weight = min(1.0, q_score / 10.0) if q_score > 0 else 0.0
        
        # Recency score (favor recent publications)
        recency_score = self._calculate_recency_score(search_result.get("published_date"))
        
        # Overall quality score (weighted combination)
        overall_quality_score = (
            authority_score * 0.5 +
            citation_count_weight * 1.0 +
            q_score_weight * 1.0 +
            recency_score * 0.5
        )
        overall_quality_score = min(5.0, overall_quality_score)
        
        return QualityMetrics(
            domain=domain,
            authority_score=authority_score,
            citation_count_weight=citation_count_weight,
            q_score_weight=q_score_weight,
            recency_score=recency_score,
            overall_quality_score=overall_quality_score
        )

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            # Simple domain extraction
            if "://" in url:
                domain = url.split("://")[1].split("/")[0]
            else:
                domain = url.split("/")[0]
            
            # Remove www. prefix
            if domain.startswith("www."):
                domain = domain[4:]
            
            return domain.lower()
        except:
            return "unknown"

    def _calculate_recency_score(self, published_date: Optional[str]) -> float:
        """Calculate recency score (0.0-1.0)"""
        if not published_date:
            return 0.3  # Default for unknown dates
        
        try:
            # Simple recency calculation - prefer last 2 years
            # In production, would parse actual dates
            current_year = datetime.now().year
            if str(current_year) in published_date or str(current_year - 1) in published_date:
                return 1.0
            elif str(current_year - 2) in published_date:
                return 0.8
            elif str(current_year - 3) in published_date:
                return 0.6
            else:
                return 0.4
        except:
            return 0.3

    def _passes_quality_filter(self, citation: PrecisionCitation) -> bool:
        """Check if citation passes quality filtering"""
        # Exclude low-quality domains
        if citation.quality_metrics.domain in self.excluded_domains:
            return False
        
        # Require minimum quality score
        if citation.quality_metrics.overall_quality_score < 2.5:
            return False
        
        # Require minimum content length
        if len(citation.content.strip()) < 100:
            return False
        
        return True

    def _filter_and_rank_citations(
        self,
        citations: List[PrecisionCitation],
        max_results: int
    ) -> List[PrecisionCitation]:
        """Filter and rank citations by quality"""
        # Remove duplicates by URL
        unique_citations = {}
        for citation in citations:
            if citation.url not in unique_citations:
                unique_citations[citation.url] = citation
            elif citation.quality_metrics.overall_quality_score > unique_citations[citation.url].quality_metrics.overall_quality_score:
                unique_citations[citation.url] = citation
        
        # Sort by quality score (descending)
        sorted_citations = sorted(
            unique_citations.values(),
            key=lambda x: x.quality_metrics.overall_quality_score,
            reverse=True
        )
        
        return sorted_citations[:max_results]

    def _generate_bluebook_citation(
        self,
        title: str,
        url: str,
        source_type: str,
        search_result: Dict[str, Any]
    ) -> str:
        """Generate basic Bluebook citation format"""
        try:
            if source_type == "academic":
                # Basic academic citation format
                author = search_result.get("author", "Author")
                year = search_result.get("published_date", "")
                year_match = re.search(r"(\d{4})", year) if year else None
                year_str = f"({year_match.group(1)})" if year_match else ""
                
                return f"{author}, {title} {year_str}"
            
            elif source_type == "news":
                # Basic news citation format
                publication = self._extract_domain(url).replace(".com", "").title()
                date = search_result.get("published_date", "")
                date_str = f"({date})" if date else ""
                
                return f"{title}, {publication} {date_str}"
            
            else:
                # Generic web citation
                domain = self._extract_domain(url)
                return f"{title}, {domain}"
                
        except Exception as e:
            logger.error(f"Failed to generate Bluebook citation: {e}")
            return f"{title}, {url}"


# Convenience functions for integration
async def perform_background_research(
    intake_data: Dict[str, Any],
    existing_evidence: Optional[Dict[str, Any]] = None,
    max_sources: int = 4
) -> List[PrecisionCitation]:
    """Convenience function for background research"""
    service = PrecisionCitationService()
    return await service.search_background_research(intake_data, existing_evidence, max_sources)


async def substantiate_claims(
    claims: List[str],
    jurisdiction: str,
    max_sources_per_claim: int = 3
) -> Dict[str, List[PrecisionCitation]]:
    """Convenience function for claim substantiation"""
    service = PrecisionCitationService()
    return await service.search_claim_substantiation(claims, jurisdiction, max_sources_per_claim)


async def verify_facts(
    facts: List[str],
    context: Dict[str, Any],
    max_sources_per_fact: int = 2
) -> Dict[str, List[PrecisionCitation]]:
    """Convenience function for fact verification"""
    service = PrecisionCitationService()
    return await service.search_fact_verification(facts, context, max_sources_per_fact)


if __name__ == "__main__":
    # Example usage
    async def test_precision_citation():
        service = PrecisionCitationService()
        
        # Test background research
        intake_data = {
            "jurisdiction": "California",
            "causes_of_action": ["negligence", "premises_liability"],
            "claim_description": "Defendant property owner failed to maintain safe premises"
        }
        
        citations = await service.search_background_research(intake_data, max_sources=3)
        print(f"Background research: {len(citations)} citations found")
        
        for citation in citations:
            print(f"- {citation.title} (Quality: {citation.quality_metrics.overall_quality_score:.1f})")
    
    asyncio.run(test_precision_citation())