"""
LLM Integration Functions for LawyerFactory Assessor
Provides LLM-powered evidence classification, metadata extraction, and summarization.
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Try to import LLM service
try:
    from ...lf_core.llm import LLMService
    LLM_SERVICE_AVAILABLE = True
except Exception:
    LLM_SERVICE_AVAILABLE = False
    logger.warning("LLM service not available - using fallback functions")


def llm_classify_evidence(
    content: str, filename: str = None, defendant_hint: str = None
) -> Dict[str, Any]:
    """Use LLM service to classify evidence as primary/secondary with detailed categorization."""
    if not LLM_SERVICE_AVAILABLE:
        logger.warning("LLM service not available, falling back to basic categorization")
        return _fallback_classify_evidence(content, filename, defendant_hint)

    try:
        # Initialize LLM service
        llm_service = LLMService()

        # Use LLM to classify evidence
        result = llm_service.classify_evidence(content, filename)

        if result.get("success", False):
            classification = result.get("classification", {})
            return {
                "evidence_type": classification.get("evidence_type", "SECONDARY"),
                "specific_category": classification.get("specific_category", "Other"),
                "confidence_score": classification.get("confidence_score", 0.0),
                "reasoning": classification.get("reasoning", ""),
                "key_characteristics": classification.get("key_characteristics", []),
                "document_type": classification.get("specific_category", "general"),
                "authority_level": "primary" if classification.get("evidence_type") == "PRIMARY" else "secondary",
                "defendant_name": defendant_hint,
                "extracted_entities": [],
                "key_legal_issues": [],
                "cluster_id": None,
                "classification_method": "llm"
            }
        else:
            logger.warning("LLM classification failed: %s", result.get("error", "Unknown error"))
            return _fallback_classify_evidence(content, filename, defendant_hint)

    except Exception as e:
        logger.error("LLM evidence classification error: %s", e)
        return _fallback_classify_evidence(content, filename, defendant_hint)


def llm_extract_metadata(
    content: str, filename: str = None
) -> Dict[str, Any]:
    """Use LLM service to extract metadata from document content."""
    if not LLM_SERVICE_AVAILABLE:
        logger.warning("LLM service not available for metadata extraction")
        return _fallback_extract_metadata(content, filename)

    try:
        # Initialize LLM service
        llm_service = LLMService()

        # Use LLM to extract metadata
        result = llm_service.extract_metadata(content, filename)

        if result.get("success", False):
            metadata = result.get("metadata", {})
            return {
                "title": metadata.get("title", filename or "Unknown"),
                "author": metadata.get("author", ""),
                "date": metadata.get("date", ""),
                "parties_involved": metadata.get("parties_involved", []),
                "key_issues": metadata.get("key_issues", []),
                "summary": metadata.get("summary", _basic_summarize(content)),
                "relevance_score": metadata.get("relevance_score", 0.5),
                "legal_context": metadata.get("legal_context", ""),
                "extraction_method": "llm"
            }
        else:
            logger.warning("LLM metadata extraction failed: %s", result.get("error", "Unknown error"))
            return _fallback_extract_metadata(content, filename)

    except Exception as e:
        logger.error("LLM metadata extraction error: %s", e)
        return _fallback_extract_metadata(content, filename)


def llm_summarize_text(
    content: str, max_length: int = 200
) -> str:
    """Use LLM service to generate intelligent summaries."""
    if not LLM_SERVICE_AVAILABLE:
        logger.warning("LLM service not available for summarization")
        return _basic_summarize(content, max_sentences=3)

    try:
        # Initialize LLM service
        llm_service = LLMService()

        # Use LLM to summarize
        result = llm_service.summarize_text(content, max_length)

        if result.get("success", False):
            return result.get("text", _basic_summarize(content, max_sentences=3))
        else:
            logger.warning("LLM summarization failed: %s", result.get("error", "Unknown error"))
            return _basic_summarize(content, max_sentences=3)

    except Exception as e:
        logger.error("LLM summarization error: %s", e)
        return _basic_summarize(content, max_sentences=3)


def _fallback_classify_evidence(content: str, filename: str = None, defendant_hint: str = None) -> Dict[str, Any]:
    """Fallback evidence classification when LLM is not available."""
    # Simple keyword-based classification
    content_lower = (content or "").lower()

    # Primary evidence indicators
    primary_keywords = [
        "original", "first-hand", "witness", "statement", "testimony",
        "photograph", "video", "audio", "recording", "contract",
        "agreement", "police report", "medical record"
    ]

    # Secondary evidence indicators
    secondary_keywords = [
        "news", "article", "report", "blog", "social media",
        "press release", "journal", "academic paper", "website"
    ]

    primary_score = sum(1 for keyword in primary_keywords if keyword in content_lower)
    secondary_score = sum(1 for keyword in secondary_keywords if keyword in content_lower)

    if primary_score > secondary_score:
        evidence_type = "PRIMARY"
        category = "Witness Statement" if "witness" in content_lower else "Document"
    elif secondary_score > primary_score:
        evidence_type = "SECONDARY"
        category = "News Article" if "news" in content_lower else "Report"
    else:
        evidence_type = "SECONDARY"
        category = "Other"

    return {
        "evidence_type": evidence_type,
        "specific_category": category,
        "confidence_score": 0.5,
        "reasoning": "Keyword-based classification (LLM not available)",
        "key_characteristics": [],
        "document_type": category,
        "authority_level": "primary" if evidence_type == "PRIMARY" else "secondary",
        "defendant_name": defendant_hint,
        "extracted_entities": [],
        "key_legal_issues": [],
        "cluster_id": None,
        "classification_method": "fallback"
    }


def _fallback_extract_metadata(content: str, filename: str = None) -> Dict[str, Any]:
    """Fallback metadata extraction when LLM is not available."""
    return {
        "title": filename or "Unknown",
        "author": "",
        "date": "",
        "parties_involved": [],
        "key_issues": [],
        "summary": _basic_summarize(content),
        "relevance_score": 0.5,
        "legal_context": "",
        "extraction_method": "fallback"
    }


def _basic_summarize(text: str, max_sentences: int = 2) -> str:
    """Basic text summarization using sentence splitting."""
    if not text:
        return ""

    # Simple sentence splitting
    import re
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    sentences = [s for s in sentences if s]

    return " ".join(sentences[:max_sentences]) if sentences else text[:200]