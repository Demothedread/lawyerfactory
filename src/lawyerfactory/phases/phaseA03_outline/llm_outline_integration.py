"""
LLM Integration Functions for Outline Phase

This module provides LLM-powered functions specifically for legal document outlining,
cause of action detection, and claims analysis.
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
    logger.warning("LLM service not available for outline integration")


def llm_detect_causes_of_action(
    text: str, jurisdiction: str = "general"
) -> List[Dict[str, Any]]:
    """Use LLM to detect causes of action from case facts with better accuracy."""
    if not LLM_SERVICE_AVAILABLE:
        logger.warning("LLM service not available for cause of action detection")
        return _fallback_detect_causes_of_action(text, jurisdiction)

    try:
        llm_service = LLMService()

        # Use LLM to detect causes of action
        result = llm_service.detect_causes_of_action(text, jurisdiction)

        if result.get("success", False):
            return result.get(
                "causes_of_action",
                _fallback_detect_causes_of_action(text, jurisdiction),
            )
        else:
            logger.warning(
                "LLM cause of action detection failed: %s",
                result.get("error", "Unknown error"),
            )
            return _fallback_detect_causes_of_action(text, jurisdiction)

    except Exception as e:
        logger.error("LLM cause of action detection error: %s", e)
        return _fallback_detect_causes_of_action(text, jurisdiction)


def llm_analyze_legal_elements(text: str, cause_of_action: str) -> Dict[str, Any]:
    """Use LLM to analyze legal elements for a specific cause of action."""
    if not LLM_SERVICE_AVAILABLE:
        logger.warning("LLM service not available for legal element analysis")
        return _fallback_analyze_legal_elements(text, cause_of_action)

    try:
        llm_service = LLMService()

        # Use LLM to analyze legal elements
        result = llm_service.analyze_legal_elements(text, cause_of_action)

        if result.get("success", False):
            return result.get(
                "element_analysis",
                _fallback_analyze_legal_elements(text, cause_of_action),
            )
        else:
            logger.warning(
                "LLM legal element analysis failed: %s",
                result.get("error", "Unknown error"),
            )
            return _fallback_analyze_legal_elements(text, cause_of_action)

    except Exception as e:
        logger.error("LLM legal element analysis error: %s", e)
        return _fallback_analyze_legal_elements(text, cause_of_action)


def llm_generate_document_outline(
    case_facts: str, cause_of_action: str, jurisdiction: str = "general"
) -> Dict[str, Any]:
    """Use LLM to generate intelligent document outline based on case facts."""
    if not LLM_SERVICE_AVAILABLE:
        logger.warning("LLM service not available for document outline generation")
        return _fallback_generate_document_outline(
            case_facts, cause_of_action, jurisdiction
        )

    try:
        llm_service = LLMService()

        # Use LLM to generate document outline
        result = llm_service.generate_document_outline(
            case_facts, cause_of_action, jurisdiction
        )

        if result.get("success", False):
            return result.get(
                "outline",
                _fallback_generate_document_outline(
                    case_facts, cause_of_action, jurisdiction
                ),
            )
        else:
            logger.warning(
                "LLM document outline generation failed: %s",
                result.get("error", "Unknown error"),
            )
            return _fallback_generate_document_outline(
                case_facts, cause_of_action, jurisdiction
            )

    except Exception as e:
        logger.error("LLM document outline generation error: %s", e)
        return _fallback_generate_document_outline(
            case_facts, cause_of_action, jurisdiction
        )


def llm_generate_provable_questions(
    cause_of_action: str, element_name: str, case_facts: str
) -> List[Dict[str, Any]]:
    """Use LLM to generate attorney-ready provable questions."""
    if not LLM_SERVICE_AVAILABLE:
        logger.warning("LLM service not available for provable question generation")
        return _fallback_generate_provable_questions(
            cause_of_action, element_name, case_facts
        )

    try:
        llm_service = LLMService()

        # Use LLM to generate provable questions
        result = llm_service.generate_provable_questions(
            cause_of_action, element_name, case_facts
        )

        if result.get("success", False):
            return result.get(
                "questions",
                _fallback_generate_provable_questions(
                    cause_of_action, element_name, case_facts
                ),
            )
        else:
            logger.warning(
                "LLM provable question generation failed: %s",
                result.get("error", "Unknown error"),
            )
            return _fallback_generate_provable_questions(
                cause_of_action, element_name, case_facts
            )

    except Exception as e:
        logger.error("LLM provable question generation error: %s", e)
        return _fallback_generate_provable_questions(
            cause_of_action, element_name, case_facts
        )


def llm_enhance_legal_definition(
    cause_of_action: str, jurisdiction: str, existing_definition: str
) -> Dict[str, Any]:
    """Use LLM to enhance existing legal definitions with better context and examples."""
    if not LLM_SERVICE_AVAILABLE:
        logger.warning("LLM service not available for legal definition enhancement")
        return _fallback_enhance_legal_definition(
            cause_of_action, jurisdiction, existing_definition
        )

    try:
        llm_service = LLMService()

        # Use LLM to enhance legal definition
        result = llm_service.enhance_legal_definition(
            cause_of_action, jurisdiction, existing_definition
        )

        if result.get("success", False):
            return result.get(
                "enhanced_definition",
                _fallback_enhance_legal_definition(
                    cause_of_action, jurisdiction, existing_definition
                ),
            )
        else:
            logger.warning(
                "LLM legal definition enhancement failed: %s",
                result.get("error", "Unknown error"),
            )
            return _fallback_enhance_legal_definition(
                cause_of_action, jurisdiction, existing_definition
            )

    except Exception as e:
        logger.error("LLM legal definition enhancement error: %s", e)
        return _fallback_enhance_legal_definition(
            cause_of_action, jurisdiction, existing_definition
        )


def llm_build_decision_tree(
    cause_of_action: str, element_name: str, case_facts: str
) -> Dict[str, Any]:
    """Use LLM to build intelligent decision trees for legal analysis."""
    if not LLM_SERVICE_AVAILABLE:
        logger.warning("LLM service not available for decision tree building")
        return _fallback_build_decision_tree(cause_of_action, element_name, case_facts)

    try:
        llm_service = LLMService()

        # Use LLM to build decision tree
        result = llm_service.build_decision_tree(
            cause_of_action, element_name, case_facts
        )

        if result.get("success", False):
            return result.get(
                "decision_tree",
                _fallback_build_decision_tree(
                    cause_of_action, element_name, case_facts
                ),
            )
        else:
            logger.warning(
                "LLM decision tree building failed: %s",
                result.get("error", "Unknown error"),
            )
            return _fallback_build_decision_tree(
                cause_of_action, element_name, case_facts
            )

    except Exception as e:
        logger.error("LLM decision tree building error: %s", e)
        return _fallback_build_decision_tree(cause_of_action, element_name, case_facts)


# Fallback functions for when LLM is not available


def _fallback_detect_causes_of_action(
    text: str, jurisdiction: str = "general"
) -> List[Dict[str, Any]]:
    """Fallback cause of action detection using keyword patterns."""
    causes = []

    # Simple keyword-based detection
    cause_keywords = {
        "negligence": ["negligent", "negligence", "duty", "breach", "care"],
        "breach_of_contract": [
            "breach",
            "contract",
            "agreement",
            "terms",
            "performance",
        ],
        "fraud": ["fraud", "misrepresentation", "deceit", "false", "intent"],
        "defamation": ["defamation", "libel", "slander", "reputation", "false"],
        "intentional_infliction": ["emotional", "distress", "outrageous", "extreme"],
    }

    text_lower = text.lower()

    for cause, keywords in cause_keywords.items():
        if any(keyword in text_lower for keyword in keywords):
            confidence = sum(1 for keyword in keywords if keyword in text_lower) / len(
                keywords
            )
            causes.append(
                {
                    "cause_name": cause.replace("_", " ").title(),
                    "confidence_score": min(confidence, 1.0),
                    "supporting_facts": [
                        f"Contains keyword: {keyword}"
                        for keyword in keywords
                        if keyword in text_lower
                    ],
                    "jurisdiction": jurisdiction,
                    "elements_detected": [],
                    "detection_method": "fallback",
                }
            )

    return (
        causes
        if causes
        else [
            {
                "cause_name": "General Legal Issue",
                "confidence_score": 0.1,
                "supporting_facts": ["Limited keyword matches"],
                "jurisdiction": jurisdiction,
                "elements_detected": [],
                "detection_method": "fallback",
            }
        ]
    )


def _fallback_analyze_legal_elements(text: str, cause_of_action: str) -> Dict[str, Any]:
    """Fallback legal element analysis using pattern matching."""
    return {
        "cause_of_action": cause_of_action,
        "elements_analyzed": ["duty", "breach", "causation", "damages"],
        "element_confidence": {
            "duty": 0.5,
            "breach": 0.5,
            "causation": 0.5,
            "damages": 0.5,
        },
        "supporting_evidence": ["Pattern-based analysis"],
        "analysis_method": "fallback",
    }


def _fallback_generate_document_outline(
    case_facts: str, cause_of_action: str, jurisdiction: str = "general"
) -> Dict[str, Any]:
    """Fallback document outline generation using templates."""
    return {
        "cause_of_action": cause_of_action,
        "jurisdiction": jurisdiction,
        "sections": [
            {"title": "Introduction", "content": "Brief overview of the case"},
            {"title": "Factual Background", "content": "Summary of relevant facts"},
            {"title": "Legal Analysis", "content": f"Analysis of {cause_of_action}"},
            {"title": "Conclusion", "content": "Summary and recommendations"},
        ],
        "generation_method": "fallback",
    }


def _fallback_generate_provable_questions(
    cause_of_action: str, element_name: str, case_facts: str
) -> List[Dict[str, Any]]:
    """Fallback provable question generation using templates."""
    return [
        {
            "question_id": f"{element_name}_001",
            "question_text": f"Did the defendant have a duty to exercise {element_name}?",
            "element_name": element_name,
            "question_type": "factual",
            "evidence_types": ["testimony", "documents"],
            "proof_methods": ["witness examination", "document review"],
            "common_challenges": ["Vague standards", "Expert testimony required"],
            "practice_tips": ["Use expert witnesses", "Establish clear standards"],
            "sub_questions": [],
            "generation_method": "fallback",
        }
    ]


def _fallback_enhance_legal_definition(
    cause_of_action: str, jurisdiction: str, existing_definition: str
) -> Dict[str, Any]:
    """Fallback legal definition enhancement."""
    return {
        "cause_of_action": cause_of_action,
        "jurisdiction": jurisdiction,
        "enhanced_definition": existing_definition,
        "additional_context": "Definition provided as-is due to LLM unavailability",
        "enhancement_method": "fallback",
    }


def _fallback_build_decision_tree(
    cause_of_action: str, element_name: str, case_facts: str
) -> Dict[str, Any]:
    """Fallback decision tree building using templates."""
    return {
        "cause_of_action": cause_of_action,
        "element_name": element_name,
        "nodes": [
            {
                "node_id": f"{element_name}_001",
                "condition": f"Is {element_name} established?",
                "true_path": "proven",
                "false_path": "not_proven",
                "outcome": None,
                "legal_standard": f"Standard for {element_name}",
                "authority_citation": "General legal principles",
                "practice_notes": ["Consult jurisdiction-specific authorities"],
            }
        ],
        "building_method": "fallback",
    }
