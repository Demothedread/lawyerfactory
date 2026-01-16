"""
LLM Integration Functions for Research Phase

This module provides LLM-powered functions specifically for legal research,
including case law analysis, legal issue extraction, and research gap identification.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Try to import LLM service
try:
    from ...lf_core.llm import LLMService

    LLM_SERVICE_AVAILABLE = True
except Exception:
    LLM_SERVICE_AVAILABLE = False
    logger.warning("LLM service not available for research integration")


def llm_extract_legal_issues(text: str) -> List[str]:
    """Use LLM to extract legal issues from text with better understanding."""
    if not LLM_SERVICE_AVAILABLE:
        logger.warning("LLM service not available for legal issue extraction")
        return _fallback_extract_legal_issues(text)

    try:
        llm_service = LLMService()

        # Use LLM to extract legal issues
        result = llm_service.extract_legal_issues(text)

        if result.get("success", False):
            return result.get("legal_issues", _fallback_extract_legal_issues(text))
        else:
            logger.warning(
                "LLM legal issue extraction failed: %s",
                result.get("error", "Unknown error"),
            )
            return _fallback_extract_legal_issues(text)

    except Exception as e:
        logger.error("LLM legal issue extraction error: %s", e)
        return _fallback_extract_legal_issues(text)


def llm_analyze_case_law(case_text: str, query_context: str = None) -> Dict[str, Any]:
    """Use LLM to analyze case law and extract key components."""
    if not LLM_SERVICE_AVAILABLE:
        logger.warning("LLM service not available for case law analysis")
        return _fallback_analyze_case_law(case_text, query_context)

    try:
        llm_service = LLMService()

        # Use LLM to analyze case law
        result = llm_service.analyze_case_law(case_text, query_context)

        if result.get("success", False):
            analysis = result.get("analysis", {})
            return {
                "holding": analysis.get("holding", ""),
                "facts": analysis.get("facts", ""),
                "reasoning": analysis.get("reasoning", ""),
                "key_principles": analysis.get("key_principles", []),
                "relevance_score": analysis.get("relevance_score", 0.5),
                "analysis_method": "llm",
            }
        else:
            logger.warning(
                "LLM case law analysis failed: %s", result.get("error", "Unknown error")
            )
            return _fallback_analyze_case_law(case_text, query_context)

    except Exception as e:
        logger.error("LLM case law analysis error: %s", e)
        return _fallback_analyze_case_law(case_text, query_context)


def llm_identify_research_gaps(query: str, existing_results: List[str]) -> List[str]:
    """Use LLM to identify gaps in research based on query and existing results."""
    if not LLM_SERVICE_AVAILABLE:
        logger.warning("LLM service not available for research gap identification")
        return _fallback_identify_research_gaps(query, existing_results)

    try:
        llm_service = LLMService()

        # Use LLM to identify research gaps
        result = llm_service.identify_research_gaps(query, existing_results)

        if result.get("success", False):
            return result.get(
                "gaps", _fallback_identify_research_gaps(query, existing_results)
            )
        else:
            logger.warning(
                "LLM research gap identification failed: %s",
                result.get("error", "Unknown error"),
            )
            return _fallback_identify_research_gaps(query, existing_results)

    except Exception as e:
        logger.error("LLM research gap identification error: %s", e)
        return _fallback_identify_research_gaps(query, existing_results)


def llm_score_citation_relevance(citation_text: str, query: str) -> float:
    """Use LLM to score citation relevance based on semantic understanding."""
    if not LLM_SERVICE_AVAILABLE:
        logger.warning("LLM service not available for citation relevance scoring")
        return _fallback_score_citation_relevance(citation_text, query)

    try:
        llm_service = LLMService()

        # Use LLM to score relevance
        result = llm_service.score_citation_relevance(citation_text, query)

        if result.get("success", False):
            return result.get(
                "relevance_score",
                _fallback_score_citation_relevance(citation_text, query),
            )
        else:
            logger.warning(
                "LLM citation relevance scoring failed: %s",
                result.get("error", "Unknown error"),
            )
            return _fallback_score_citation_relevance(citation_text, query)

    except Exception as e:
        logger.error("LLM citation relevance scoring error: %s", e)
        return _fallback_score_citation_relevance(citation_text, query)


def llm_extract_legal_principles(text: str) -> List[str]:
    """Use LLM to extract legal principles from case law or legal text."""
    if not LLM_SERVICE_AVAILABLE:
        logger.warning("LLM service not available for legal principle extraction")
        return _fallback_extract_legal_principles(text)

    try:
        llm_service = LLMService()

        # Use LLM to extract legal principles
        result = llm_service.extract_legal_principles(text)

        if result.get("success", False):
            return result.get("principles", _fallback_extract_legal_principles(text))
        else:
            logger.warning(
                "LLM legal principle extraction failed: %s",
                result.get("error", "Unknown error"),
            )
            return _fallback_extract_legal_principles(text)

    except Exception as e:
        logger.error("LLM legal principle extraction error: %s", e)
        return _fallback_extract_legal_principles(text)


def llm_generate_research_recommendations(
    query: str, gaps: List[str], existing_results: List[str]
) -> List[str]:
    """Use LLM to generate research recommendations based on gaps and existing results."""
    if not LLM_SERVICE_AVAILABLE:
        logger.warning("LLM service not available for research recommendations")
        return _fallback_generate_research_recommendations(
            query, gaps, existing_results
        )

    try:
        llm_service = LLMService()

        # Use LLM to generate recommendations
        result = llm_service.generate_research_recommendations(
            query, gaps, existing_results
        )

        if result.get("success", False):
            return result.get(
                "recommendations",
                _fallback_generate_research_recommendations(
                    query, gaps, existing_results
                ),
            )
        else:
            logger.warning(
                "LLM research recommendations failed: %s",
                result.get("error", "Unknown error"),
            )
            return _fallback_generate_research_recommendations(
                query, gaps, existing_results
            )

    except Exception as e:
        logger.error("LLM research recommendations error: %s", e)
        return _fallback_generate_research_recommendations(
            query, gaps, existing_results
        )


# Fallback functions for when LLM is not available


def _fallback_extract_legal_issues(text: str) -> List[str]:
    """Fallback legal issue extraction using keyword matching."""
    legal_keywords = [
        "negligence",
        "breach",
        "contract",
        "tort",
        "liability",
        "damages",
        "jurisdiction",
        "venue",
        "standing",
        "mootness",
        "ripeness",
        "statute",
        "regulation",
        "ordinance",
        "precedent",
        "stare decisis",
        "due process",
        "equal protection",
        "first amendment",
        "fourth amendment",
        "fifth amendment",
        "sixth amendment",
        "eighth amendment",
        "fourteenth amendment",
    ]

    found_issues = []
    text_lower = text.lower()

    for keyword in legal_keywords:
        if keyword in text_lower:
            found_issues.append(keyword.title())

    return found_issues[:5] if found_issues else ["General legal issue"]


def _fallback_analyze_case_law(
    case_text: str, query_context: str = None
) -> Dict[str, Any]:
    """Fallback case law analysis using text patterns."""
    return {
        "holding": _extract_holding_fallback(case_text),
        "facts": _extract_facts_fallback(case_text),
        "reasoning": _extract_reasoning_fallback(case_text),
        "key_principles": _extract_principles_fallback(case_text),
        "relevance_score": 0.5,
        "analysis_method": "fallback",
    }


def _fallback_identify_research_gaps(
    query: str, existing_results: List[str]
) -> List[str]:
    """Fallback research gap identification."""
    gaps = []

    # Simple gap identification based on missing information
    query_lower = query.lower()

    if "supreme court" in query_lower and not any(
        "supreme court" in result.lower() for result in existing_results
    ):
        gaps.append("No Supreme Court precedent found")

    if "recent" in query_lower and not any(
        "2023" in result or "2024" in result for result in existing_results
    ):
        gaps.append("Limited recent case law")

    if len(existing_results) < 3:
        gaps.append("Insufficient number of relevant cases")

    return gaps if gaps else ["Further research may be beneficial"]


def _fallback_score_citation_relevance(citation_text: str, query: str) -> float:
    """Fallback citation relevance scoring using keyword overlap."""
    citation_words = set(citation_text.lower().split())
    query_words = set(query.lower().split())

    overlap = len(citation_words.intersection(query_words))
    total_words = len(citation_words.union(query_words))

    return overlap / total_words if total_words > 0 else 0.0


def _fallback_extract_legal_principles(text: str) -> List[str]:
    """Fallback legal principle extraction using patterns."""
    principles = []

    # Look for common legal principle indicators
    principle_indicators = [
        "therefore",
        "thus",
        "accordingly",
        "consequently",
        "it is established",
        "the court holds",
        "we conclude",
        "the law requires",
        "as a matter of law",
    ]

    sentences = text.split(".")
    for sentence in sentences:
        sentence_lower = sentence.lower()
        if any(indicator in sentence_lower for indicator in principle_indicators):
            principles.append(sentence.strip())

    return (
        principles[:3] if principles else ["Legal principles require further analysis"]
    )


def _fallback_generate_research_recommendations(
    query: str, gaps: List[str], existing_results: List[str]
) -> List[str]:
    """Fallback research recommendation generation."""
    recommendations = []

    if gaps:
        for gap in gaps:
            if "supreme court" in gap.lower():
                recommendations.append(
                    "Consider searching federal circuit courts for analogous decisions"
                )
            elif "recent" in gap.lower():
                recommendations.append(
                    "Look for recent district court decisions or pending appeals"
                )
            elif "insufficient" in gap.lower():
                recommendations.append(
                    "Expand search to include related legal theories"
                )

    if not recommendations:
        recommendations = [
            "Consider consulting legal databases for additional case law",
            "Review secondary sources and legal commentary",
            "Consult with subject matter experts in the field",
        ]

    return recommendations


# Helper functions for fallback analysis


def _extract_holding_fallback(text: str) -> str:
    """Extract holding using simple text patterns."""
    sentences = text.split(".")
    for sentence in sentences:
        if any(
            word in sentence.lower()
            for word in ["hold", "grant", "deny", "affirm", "reverse"]
        ):
            return sentence.strip()
    return "Holding requires detailed analysis"


def _extract_facts_fallback(text: str) -> str:
    """Extract facts using simple text patterns."""
    # Look for fact sections or early parts of the opinion
    if len(text) > 500:
        return text[:500] + "..."
    return text


def _extract_reasoning_fallback(text: str) -> str:
    """Extract reasoning using simple text patterns."""
    sentences = text.split(".")
    reasoning_sentences = []

    for sentence in sentences:
        if any(
            word in sentence.lower()
            for word in ["because", "therefore", "thus", "accordingly"]
        ):
            reasoning_sentences.append(sentence.strip())

    return (
        " ".join(reasoning_sentences[:3])
        if reasoning_sentences
        else "Reasoning requires detailed analysis"
    )


def _extract_principles_fallback(text: str) -> List[str]:
    """Extract legal principles using simple patterns."""
    return _fallback_extract_legal_principles(text)
