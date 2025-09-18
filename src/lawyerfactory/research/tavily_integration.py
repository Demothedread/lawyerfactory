"""
Tavily Research Integration for LawyerFactory

This module provides enhanced web research capabilities using Tavily API
for tertiary knowledge, academic sources, and claim validation.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
import json
import logging
import os
from typing import Any, Dict, List, Optional, Union

try:
    from tavily import TavilyClient
    import weave

    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False
    TavilyClient = None
    weave = None

logger = logging.getLogger(__name__)


@dataclass
class ResearchQuery:
    """Enhanced research query with source preferences"""

    query_text: str
    legal_issues: List[str]
    jurisdiction: Optional[str] = None
    preferred_sources: List[str] = field(default_factory=lambda: ["academic", "news"])
    search_depth: str = "advanced"  # basic, intermediate, advanced
    max_results: int = 10
    time_range: Optional[str] = None  # day, week, month, year


@dataclass
class ResearchResult:
    """Enhanced research result with source metadata"""

    query_id: str
    content: str
    sources: List[Dict[str, Any]]
    citations: List[str]
    confidence_score: float
    source_types: List[str]
    academic_sources: List[Dict[str, Any]]
    news_sources: List[Dict[str, Any]]
    web_sources: List[Dict[str, Any]]
    created_at: datetime = field(default_factory=datetime.now)


class TavilyResearchIntegration:
    """
    Enhanced research integration using Tavily for web-based research
    with specialized academic and news source capabilities.
    """

    def __init__(self, api_key: Optional[str] = None):
        if not TAVILY_AVAILABLE:
            raise ImportError(
                "Tavily dependencies not available. Install tavily-python and langchain-tavily"
            )

        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        if not self.api_key:
            raise ValueError("TAVILY_API_KEY environment variable required")

        # Initialize Weave for observability
        if weave:
            weave.init(project_name="lawyerfactory-research")

        if TavilyClient is None:
            raise ImportError("TavilyClient not available")
        self.client = TavilyClient(api_key=self.api_key)

        # Specialized search configurations
        self.academic_domains = [
            "scholar.google.com",
            "ssrn.com",
            "jstor.org",
            "heinonline.org",
            "westlaw.com",
            "lexisnexis.com",
            "academic.oup.com",
            "cambridge.org",
            "springer.com",
            "wiley.com",
            "tandfonline.com",
            "sagepub.com",
        ]

        self.news_domains = [
            "nytimes.com",
            "wsj.com",
            "bloomberg.com",
            "reuters.com",
            "apnews.com",
            "bbc.com",
            "cnn.com",
            "foxnews.com",
        ]

        logger.info("Tavily Research Integration initialized")

    async def search_academic_sources(
        self, query: str, max_results: int = 8, time_range: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search specifically for academic and scholarly sources
        """
        try:
            # Handle time_range parameter
            search_params = {
                "query": query,
                "search_depth": "advanced",
                "include_domains": self.academic_domains,
                "max_results": max_results,
                "topic": "general",
            }
            if time_range:
                search_params["time_range"] = time_range

            response = self.client.search(**search_params)

            # Filter and enhance results
            academic_results = []
            for result in response.get("results", []):
                if any(domain in result.get("url", "") for domain in self.academic_domains):
                    result["source_type"] = "academic"
                    result["authority_level"] = self._assess_academic_authority(result)
                    academic_results.append(result)

            return {
                "query": query,
                "results": academic_results,
                "total_found": len(academic_results),
                "search_type": "academic",
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Academic search failed: {e}")
            return {"error": str(e), "results": []}

    async def search_news_sources(
        self, query: str, max_results: int = 6, time_range: str = "month"
    ) -> Dict[str, Any]:
        """
        Search specifically for recent news and current developments
        """
        try:
            # Handle time_range parameter
            search_params = {
                "query": query,
                "search_depth": "advanced",
                "include_domains": self.news_domains,
                "max_results": max_results,
                "topic": "news",
            }
            if time_range:
                search_params["time_range"] = time_range

            response = self.client.search(**search_params)

            # Enhance news results
            news_results = []
            for result in response.get("results", []):
                result["source_type"] = "news"
                result["recency_score"] = self._calculate_recency_score(result)
                news_results.append(result)

            return {
                "query": query,
                "results": news_results,
                "total_found": len(news_results),
                "search_type": "news",
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"News search failed: {e}")
            return {"error": str(e), "results": []}

    async def extract_content(
        self, urls: List[str], extract_depth: str = "advanced"
    ) -> Dict[str, Any]:
        """
        Extract full content from specified URLs
        """
        try:
            extracted_content = []

            for url in urls[:5]:  # Limit to 5 URLs per call
                try:
                    # Handle extract_depth parameter with proper typing
                    if extract_depth == "basic":
                        response = self.client.extract(urls=[url], extract_depth="basic")
                    elif extract_depth == "advanced":
                        response = self.client.extract(urls=[url], extract_depth="advanced")
                    else:
                        response = self.client.extract(urls=[url])

                    if response.get("results"):
                        result = response["results"][0]
                        result["source_url"] = url
                        result["extraction_timestamp"] = datetime.now().isoformat()
                        extracted_content.append(result)

                except Exception as e:
                    logger.warning(f"Failed to extract from {url}: {e}")

            return {
                "urls_requested": urls,
                "extracted_content": extracted_content,
                "successful_extractions": len(extracted_content),
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Content extraction failed: {e}")
            return {"error": str(e), "extracted_content": []}

    async def comprehensive_research(self, research_query: ResearchQuery) -> ResearchResult:
        """
        Perform comprehensive research across multiple source types
        """
        query_id = f"tavily_research_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        all_sources = []
        academic_sources = []
        news_sources = []
        web_sources = []

        # Execute searches based on preferred sources
        search_tasks = []

        if "academic" in research_query.preferred_sources:
            search_tasks.append(
                self.search_academic_sources(
                    research_query.query_text,
                    research_query.max_results // 2,
                    research_query.time_range,
                )
            )

        if "news" in research_query.preferred_sources:
            search_tasks.append(
                self.search_news_sources(
                    research_query.query_text,
                    research_query.max_results // 2,
                    research_query.time_range or "month",
                )
            )

        # Execute all searches concurrently
        search_results = await asyncio.gather(*search_tasks, return_exceptions=True)

        # Process results
        for result in search_results:
            if isinstance(result, Exception):
                logger.error(f"Search task failed: {result}")
                continue

            # Type check: result should be a dict at this point
            if not isinstance(result, dict):
                logger.error(f"Unexpected result type: {type(result)}")
                continue

            # Now result is guaranteed to be a dict
            search_type = result.get("search_type")
            if search_type == "academic":
                academic_sources.extend(result.get("results", []))
            elif search_type == "news":
                news_sources.extend(result.get("results", []))
            else:
                web_sources.extend(result.get("results", []))

        all_sources = academic_sources + news_sources + web_sources

        # Generate citations
        citations = self._generate_citations(all_sources)

        # Combine content
        combined_content = self._combine_search_results(all_sources)

        # Calculate confidence score
        confidence_score = self._calculate_research_confidence(all_sources)

        return ResearchResult(
            query_id=query_id,
            content=combined_content,
            sources=all_sources,
            citations=citations,
            confidence_score=confidence_score,
            source_types=list(
                set(
                    result.get("search_type", "web")
                    for result in search_results
                    if isinstance(result, dict)
                )
            ),
            academic_sources=academic_sources,
            news_sources=news_sources,
            web_sources=web_sources,
        )

    async def validate_legal_claims(
        self, claims: List[str], jurisdiction: str, max_validations_per_claim: int = 3
    ) -> Dict[str, Any]:
        """
        Validate legal claims against current web sources and developments
        """
        validation_results = {}

        for claim in claims:
            try:
                # Search for recent developments related to the claim
                search_query = f"{claim} {jurisdiction} recent developments case law"

                news_results = await self.search_news_sources(
                    search_query, max_results=max_validations_per_claim, time_range="month"
                )

                academic_results = await self.search_academic_sources(
                    search_query, max_results=max_validations_per_claim, time_range="year"
                )

                # Analyze results for claim validation
                validation = self._analyze_claim_validation(claim, news_results, academic_results)

                validation_results[claim] = {
                    "validation_score": validation["score"],
                    "supporting_sources": validation["sources"],
                    "conflicting_sources": validation["conflicts"],
                    "recommendations": validation["recommendations"],
                    "last_validated": datetime.now().isoformat(),
                }

            except Exception as e:
                logger.error(f"Claim validation failed for '{claim}': {e}")
                validation_results[claim] = {"error": str(e), "validation_score": 0.0}

        return {
            "claims_validated": claims,
            "validation_results": validation_results,
            "overall_confidence": (
                sum(r.get("validation_score", 0) for r in validation_results.values())
                / len(validation_results)
                if validation_results
                else 0.0
            ),
            "timestamp": datetime.now().isoformat(),
        }

    def _assess_academic_authority(self, result: Dict[str, Any]) -> int:
        """Assess the academic authority level of a source"""
        url = result.get("url", "").lower()
        title = result.get("title", "").lower()

        # High authority sources
        if any(
            domain in url for domain in ["harvard.edu", "stanford.edu", "berkeley.edu", "yale.edu"]
        ):
            return 5
        if any(domain in url for domain in ["ssrn.com", "jstor.org", "heinonline.org"]):
            return 4
        if any(domain in url for domain in ["academic.oup.com", "cambridge.org", "springer.com"]):
            return 3

        # Medium authority
        if "university" in url or "edu" in url:
            return 2

        # General academic content
        return 1

    def _calculate_recency_score(self, result: Dict[str, Any]) -> float:
        """Calculate how recent a news source is"""
        # This would use published date if available
        # For now, return a default score
        return 0.8

    def _generate_citations(self, sources: List[Dict[str, Any]]) -> List[str]:
        """Generate proper citations for sources"""
        citations = []

        for source in sources:
            title = source.get("title", "Untitled")
            url = source.get("url", "")
            source_type = source.get("source_type", "web")

            if source_type == "academic":
                citation = f"{title}. Available at: {url}"
            elif source_type == "news":
                citation = f"{title}. {url}"
            else:
                citation = f"{title}. Retrieved from: {url}"

            citations.append(citation)

        return citations

    def _combine_search_results(self, sources: List[Dict[str, Any]]) -> str:
        """Combine multiple search results into coherent content"""
        if not sources:
            return "No relevant sources found."

        combined = []

        # Group by source type
        academic_content = []
        news_content = []
        web_content = []

        for source in sources:
            content = source.get("content", "").strip()
            if not content:
                continue

            source_type = source.get("source_type", "web")

            if source_type == "academic":
                academic_content.append(content)
            elif source_type == "news":
                news_content.append(content)
            else:
                web_content.append(content)

        # Combine in priority order
        if academic_content:
            combined.append("### Academic Sources\n" + "\n\n".join(academic_content[:3]))

        if news_content:
            combined.append("### Recent Developments\n" + "\n\n".join(news_content[:3]))

        if web_content:
            combined.append("### Additional Sources\n" + "\n\n".join(web_content[:3]))

        return "\n\n".join(combined)

    def _calculate_research_confidence(self, sources: List[Dict[str, Any]]) -> float:
        """Calculate overall confidence score for research results"""
        if not sources:
            return 0.0

        # Factors: number of sources, source authority, recency
        source_count = len(sources)
        authority_sum = sum(source.get("authority_level", 1) for source in sources)
        avg_authority = authority_sum / source_count if source_count > 0 else 0

        # Base confidence from source count
        count_confidence = min(1.0, source_count / 10.0)

        # Authority confidence
        authority_confidence = min(1.0, avg_authority / 5.0)

        return (count_confidence * 0.6) + (authority_confidence * 0.4)

    def _analyze_claim_validation(
        self, claim: str, news_results: Dict[str, Any], academic_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze how well sources validate a legal claim"""
        supporting_sources = []
        conflicting_sources = []

        # Analyze news sources
        for result in news_results.get("results", []):
            content = result.get("content", "").lower()
            claim_lower = claim.lower()

            # Simple validation logic - can be enhanced with NLP
            if any(word in content for word in claim_lower.split()):
                supporting_sources.append(
                    {"title": result.get("title"), "url": result.get("url"), "relevance": "high"}
                )

        # Analyze academic sources
        for result in academic_results.get("results", []):
            content = result.get("content", "").lower()
            claim_lower = claim.lower()

            if any(word in content for word in claim_lower.split()):
                supporting_sources.append(
                    {
                        "title": result.get("title"),
                        "url": result.get("url"),
                        "authority_level": result.get("authority_level", 1),
                        "relevance": "academic",
                    }
                )

        # Calculate validation score
        total_sources = len(supporting_sources) + len(conflicting_sources)
        validation_score = len(supporting_sources) / max(total_sources, 1)

        return {
            "score": validation_score,
            "sources": supporting_sources,
            "conflicts": conflicting_sources,
            "recommendations": self._generate_validation_recommendations(
                validation_score, supporting_sources
            ),
        }

    def _generate_validation_recommendations(
        self, score: float, sources: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []

        if score < 0.3:
            recommendations.append("Consider strengthening claim with additional evidence")
            recommendations.append("Review recent case law for similar claims")

        if score >= 0.7:
            recommendations.append("Claim appears well-supported by current sources")
            recommendations.append("Monitor for recent developments that may affect claim")

        if not sources:
            recommendations.append("No recent sources found - consider traditional legal research")

        return recommendations


# Convenience functions for easy integration
async def search_academic(query: str, **kwargs) -> Dict[str, Any]:
    """Convenience function for academic searches"""
    integration = TavilyResearchIntegration()
    return await integration.search_academic_sources(query, **kwargs)


async def search_news(query: str, **kwargs) -> Dict[str, Any]:
    """Convenience function for news searches"""
    integration = TavilyResearchIntegration()
    return await integration.search_news_sources(query, **kwargs)


async def validate_claims(claims: List[str], jurisdiction: str) -> Dict[str, Any]:
    """Convenience function for claim validation"""
    integration = TavilyResearchIntegration()
    return await integration.validate_legal_claims(claims, jurisdiction)


if __name__ == "__main__":
    # Example usage
    async def test_integration():
        integration = TavilyResearchIntegration()

        # Test academic search
        academic_results = await integration.search_academic_sources(
            "negligence duty of care California"
        )
        print(f"Academic results: {len(academic_results.get('results', []))}")

        # Test news search
        news_results = await integration.search_news_sources("recent negligence cases California")
        print(f"News results: {len(news_results.get('results', []))}")

        # Test claim validation
        validation = await integration.validate_legal_claims(
            ["negligence", "breach of contract"], "California"
        )
        print(f"Validation results: {validation}")

    asyncio.run(test_integration())
