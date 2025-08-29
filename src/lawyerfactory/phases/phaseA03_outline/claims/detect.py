"""
# Script Name: detect.py
# Description: Cause of Action Detection Engine Identifies legal claims from case facts and builds element breakdown for Claims Matrix
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Workflow
#   - Group Tags: claims-analysis
Cause of Action Detection Engine
Identifies legal claims from case facts and builds element breakdown for Claims Matrix
"""

from dataclasses import dataclass
from datetime import datetime
import logging
import re
from typing import Any, Dict, List, Optional

from enhanced_knowledge_graph import (
    CauseOfAction,
    ElementQuestion,
    EnhancedKnowledgeGraph,
    LegalElement,
    LegalEntityType,
)

from lawyerfactory.kg.jurisdiction import JurisdictionManager

logger = logging.getLogger(__name__)


@dataclass
class CauseDetectionResult:
    """Result of cause of action detection"""

    cause_name: str
    confidence_score: float
    supporting_facts: List[str]
    jurisdiction: str
    elements_detected: List[Dict[str, Any]]
    authority_citation: Optional[str] = None


class CauseOfActionDetector:
    """Detects causes of action from case facts and builds legal element breakdown"""

    def __init__(
        self,
        enhanced_kg: EnhancedKnowledgeGraph,
        jurisdiction_manager: JurisdictionManager,
    ):
        self.kg = enhanced_kg
        self.jurisdiction_manager = jurisdiction_manager
        self.cause_patterns = self._initialize_cause_patterns()
        self.element_templates = self._initialize_element_templates()

    def _initialize_cause_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize regex patterns for cause of action detection"""
        return {
            "negligence": {
                "patterns": [
                    r"(?:negligent|negligence|failed\s+to\s+exercise\s+(?:reasonable\s+)?care)",
                    r"(?:duty\s+of\s+care|breach.*duty|standard\s+of\s+care)",
                    r"(?:proximately?\s+caused|caused.*(?:injury|damage|harm))",
                    r"(?:reasonable\s+person|reasonably\s+prudent)",
                ],
                "required_elements": ["duty", "breach", "causation", "damages"],
                "confidence_weights": {
                    "duty": 0.25,
                    "breach": 0.25,
                    "causation": 0.25,
                    "damages": 0.25,
                },
            },
            "breach_of_contract": {
                "patterns": [
                    r"(?:breach.*contract|breached.*agreement|violated.*terms)",
                    r"(?:contract|agreement|promise|obligation)",
                    r"(?:performance|non-performance|failure\s+to\s+perform)",
                    r"(?:material\s+breach|substantial\s+performance)",
                ],
                "required_elements": [
                    "contract_formation",
                    "performance",
                    "breach",
                    "damages",
                ],
                "confidence_weights": {
                    "contract_formation": 0.3,
                    "performance": 0.2,
                    "breach": 0.3,
                    "damages": 0.2,
                },
            },
            "fraud": {
                "patterns": [
                    r"(?:fraud|fraudulent|misrepresent|false\s+statement)",
                    r"(?:intent\s+to\s+deceive|knowingly\s+false|reckless\s+disregard)",
                    r"(?:reasonable\s+reliance|relied\s+on|justifiable\s+reliance)",
                    r"(?:damages.*reliance|injury.*misrepresentation)",
                ],
                "required_elements": [
                    "misrepresentation",
                    "scienter",
                    "intent",
                    "reliance",
                    "damages",
                ],
                "confidence_weights": {
                    "misrepresentation": 0.25,
                    "scienter": 0.25,
                    "intent": 0.15,
                    "reliance": 0.15,
                    "damages": 0.2,
                },
            },
            "intentional_infliction_emotional_distress": {
                "patterns": [
                    r"(?:intentional.*emotional\s+distress|IIED)",
                    r"(?:extreme.*outrageous|outrageous.*conduct)",
                    r"(?:severe\s+emotional\s+distress|extreme\s+emotional)",
                    r"(?:intent.*distress|reckless\s+disregard.*distress)",
                ],
                "required_elements": [
                    "extreme_outrageous_conduct",
                    "intent_recklessness",
                    "causation",
                    "severe_emotional_distress",
                ],
                "confidence_weights": {
                    "extreme_outrageous_conduct": 0.3,
                    "intent_recklessness": 0.25,
                    "causation": 0.2,
                    "severe_emotional_distress": 0.25,
                },
            },
            "defamation": {
                "patterns": [
                    r"(?:defamation|defamatory|libel|slander)",
                    r"(?:false\s+statement|publication|published)",
                    r"(?:reputation|defamatory\s+meaning|harm.*reputation)",
                    r"(?:privilege|qualified\s+privilege|absolute\s+privilege)",
                ],
                "required_elements": [
                    "defamatory_statement",
                    "publication",
                    "falsity",
                    "damages",
                ],
                "confidence_weights": {
                    "defamatory_statement": 0.3,
                    "publication": 0.25,
                    "falsity": 0.25,
                    "damages": 0.2,
                },
            },
        }

    def _initialize_element_templates(self) -> Dict[str, Dict[str, Any]]:
        """Initialize legal element templates with provable questions"""
        return {
            "negligence": {
                "duty": {
                    "definition": "A legal obligation to conform to a standard of reasonable care",
                    "questions": [
                        "Did defendant owe plaintiff a duty of care?",
                        "What standard of care applied to defendant's conduct?",
                        "Was the duty of care established by statute, common law, or special relationship?",
                    ],
                    "burden_of_proof": "preponderance",
                },
                "breach": {
                    "definition": "Failure to conform to the required standard of care",
                    "questions": [
                        "Did defendant's conduct fall below the applicable standard of care?",
                        "What would a reasonably prudent person have done in similar circumstances?",
                        "Did defendant violate any statutes or regulations?",
                    ],
                    "burden_of_proof": "preponderance",
                },
                "causation": {
                    "definition": "The breach must be both the cause in fact and proximate cause of harm",
                    "questions": [
                        "Was defendant's breach a substantial factor in causing plaintiff's harm?",
                        "Were plaintiff's injuries a foreseeable consequence of defendant's conduct?",
                        "Were there any intervening causes that broke the causal chain?",
                    ],
                    "burden_of_proof": "preponderance",
                },
                "damages": {
                    "definition": "Actual harm or injury resulting from the breach",
                    "questions": [
                        "What specific injuries or damages did plaintiff suffer?",
                        "Are the damages compensable under law?",
                        "Can the damages be quantified with reasonable certainty?",
                    ],
                    "burden_of_proof": "preponderance",
                },
            },
            "breach_of_contract": {
                "contract_formation": {
                    "definition": "Valid contract with offer, acceptance, and consideration",
                    "questions": [
                        "Was there a valid offer with definite terms?",
                        "Was the offer accepted without material changes?",
                        "Was there adequate consideration for the agreement?",
                    ],
                    "burden_of_proof": "preponderance",
                },
                "performance": {
                    "definition": "Plaintiff performed their contractual obligations",
                    "questions": [
                        "Did plaintiff substantially perform their contractual duties?",
                        "Were any conditions precedent satisfied?",
                        "Did any impossibility or frustration excuse performance?",
                    ],
                    "burden_of_proof": "preponderance",
                },
                "breach": {
                    "definition": "Defendant failed to perform contractual obligations",
                    "questions": [
                        "Did defendant fail to perform a material term of the contract?",
                        "Was the breach substantial or minor?",
                        "Did defendant have any valid excuse for non-performance?",
                    ],
                    "burden_of_proof": "preponderance",
                },
                "damages": {
                    "definition": "Harm resulting from the breach",
                    "questions": [
                        "What damages flow naturally from the breach?",
                        "Were consequential damages foreseeable at contract formation?",
                        "Did plaintiff mitigate their damages?",
                    ],
                    "burden_of_proof": "preponderance",
                },
            },
        }

    def detect_causes_from_facts(
        self, case_facts: List[Dict[str, Any]], jurisdiction: str
    ) -> List[CauseDetectionResult]:
        """Detect potential causes of action from case facts"""
        try:
            if not case_facts:
                return []

            # Combine all fact text for analysis
            combined_text = " ".join(
                [
                    fact.get("name", "") + " " + fact.get("description", "")
                    for fact in case_facts
                ]
            )

            detected_causes = []

            for cause_name, cause_config in self.cause_patterns.items():
                confidence_score = self._calculate_cause_confidence(
                    combined_text, cause_config, case_facts
                )

                if confidence_score > 0.3:  # Minimum threshold
                    supporting_facts = self._identify_supporting_facts(
                        case_facts, cause_config["patterns"]
                    )

                    elements_detected = self._detect_elements_for_cause(
                        combined_text, cause_name
                    )

                    detection_result = CauseDetectionResult(
                        cause_name=cause_name,
                        confidence_score=confidence_score,
                        supporting_facts=supporting_facts,
                        jurisdiction=jurisdiction,
                        elements_detected=elements_detected,
                    )

                    detected_causes.append(detection_result)

            # Sort by confidence score
            detected_causes.sort(key=lambda x: x.confidence_score, reverse=True)

            logger.info(f"Detected {len(detected_causes)} potential causes of action")
            return detected_causes

        except Exception as e:
            logger.exception(f"Failed to detect causes from facts: {e}")
            return []

    def _calculate_cause_confidence(
        self, text: str, cause_config: Dict[str, Any], facts: List[Dict[str, Any]]
    ) -> float:
        """Calculate confidence score for a potential cause of action"""
        try:
            patterns = cause_config["patterns"]
            element_weights = cause_config.get("confidence_weights", {})

            pattern_matches = 0
            total_patterns = len(patterns)

            text_lower = text.lower()

            # Check pattern matches
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    pattern_matches += 1

            pattern_confidence = (
                pattern_matches / total_patterns if total_patterns > 0 else 0
            )

            # Boost confidence based on fact types
            fact_type_boost = 0
            for fact in facts:
                fact_type = fact.get("type", "").lower()
                if fact_type in ["event", "action", "injury", "damage"]:
                    fact_type_boost += 0.1

            fact_type_boost = min(fact_type_boost, 0.3)  # Cap at 30%

            # Calculate overall confidence
            overall_confidence = min(1.0, pattern_confidence + fact_type_boost)

            return overall_confidence

        except Exception as e:
            logger.exception(f"Failed to calculate cause confidence: {e}")
            return 0.0

    def _identify_supporting_facts(
        self, facts: List[Dict[str, Any]], patterns: List[str]
    ) -> List[str]:
        """Identify facts that support a specific cause of action"""
        supporting_facts = []

        for fact in facts:
            fact_text = (
                fact.get("name", "") + " " + fact.get("description", "")
            ).lower()

            for pattern in patterns:
                if re.search(pattern, fact_text, re.IGNORECASE):
                    supporting_facts.append(fact.get("id", fact.get("name", "Unknown")))
                    break

        return supporting_facts

    def _detect_elements_for_cause(
        self, text: str, cause_name: str
    ) -> List[Dict[str, Any]]:
        """Detect which legal elements are present for a cause of action"""
        elements_detected = []

        if cause_name not in self.element_templates:
            return elements_detected

        element_template = self.element_templates[cause_name]

        for element_name, element_config in element_template.items():
            # Simple keyword-based detection (could be enhanced with NLP)
            element_keywords = self._get_element_keywords(element_name)
            element_confidence = 0.0

            text_lower = text.lower()
            keyword_matches = sum(
                1 for keyword in element_keywords if keyword in text_lower
            )

            if keyword_matches > 0:
                element_confidence = min(1.0, keyword_matches / len(element_keywords))

                elements_detected.append(
                    {
                        "element_name": element_name,
                        "confidence": element_confidence,
                        "definition": element_config["definition"],
                        "burden_of_proof": element_config["burden_of_proof"],
                        "questions": element_config["questions"],
                    }
                )

        return elements_detected

    def _get_element_keywords(self, element_name: str) -> List[str]:
        """Get keywords associated with a legal element for detection"""
        keyword_map = {
            "duty": ["duty", "obligation", "owe", "standard", "care"],
            "breach": ["breach", "violate", "fail", "negligent", "unreasonable"],
            "causation": [
                "cause",
                "result",
                "proximate",
                "substantial factor",
                "foreseeability",
            ],
            "damages": ["damage", "injury", "harm", "loss", "compensation"],
            "contract_formation": [
                "contract",
                "agreement",
                "offer",
                "acceptance",
                "consideration",
            ],
            "performance": ["perform", "fulfill", "complete", "satisfy"],
            "misrepresentation": ["false", "misrepresent", "statement", "fact"],
            "scienter": ["intent", "knowledge", "reckless", "knowing"],
            "reliance": ["rely", "reliance", "depend", "trust"],
            "extreme_outrageous_conduct": [
                "extreme",
                "outrageous",
                "shocking",
                "beyond bounds",
            ],
            "intent_recklessness": ["intent", "purpose", "reckless", "disregard"],
            "severe_emotional_distress": ["severe", "emotional", "distress", "trauma"],
            "defamatory_statement": ["defamatory", "false", "statement", "reputation"],
            "publication": ["publish", "communicate", "third party", "disseminate"],
            "falsity": ["false", "untrue", "inaccurate", "incorrect"],
        }

        return keyword_map.get(element_name, [element_name])

    def create_cause_of_action_in_kg(
        self, detection_result: CauseDetectionResult
    ) -> int:
        """Create a cause of action in the knowledge graph with elements"""
        try:
            # Create the cause of action
            cause = CauseOfAction(
                jurisdiction=detection_result.jurisdiction,
                cause_name=detection_result.cause_name,
                legal_definition=f"Detected cause of action: {detection_result.cause_name}",
                confidence_threshold=detection_result.confidence_score,
            )

            cause_id = self.kg.add_cause_of_action(cause)

            # Create legal elements
            for i, element_data in enumerate(detection_result.elements_detected):
                element = LegalElement(
                    cause_of_action_id=cause_id,
                    element_name=element_data["element_name"],
                    element_order=i + 1,
                    element_definition=element_data["definition"],
                    burden_of_proof=element_data["burden_of_proof"],
                )

                element_id = self.kg.add_legal_element(element)

                # Create provable questions for each element
                for j, question_text in enumerate(element_data["questions"]):
                    question = ElementQuestion(
                        legal_element_id=element_id,
                        question_text=question_text,
                        question_order=j + 1,
                        question_type="factual",
                    )

                    self.kg.add_element_question(question)

            logger.info(
                f"Created cause of action '{detection_result.cause_name}' with {len(detection_result.elements_detected)} elements"
            )
            return cause_id

        except Exception as e:
            logger.exception(
                f"Failed to create cause of action in knowledge graph: {e}"
            )
            raise

    def analyze_case_for_causes(
        self, session_id: str, jurisdiction: str
    ) -> Dict[str, Any]:
        """Comprehensive analysis of case facts for potential causes of action"""
        try:
            # Get case facts from knowledge graph
            case_entities = self.kg.search_entities_by_type(
                [
                    LegalEntityType.FACT.value,
                    LegalEntityType.EVENT.value,
                    LegalEntityType.EVIDENCE.value,
                ]
            )

            if not case_entities:
                return {
                    "error": "No case facts found for analysis",
                    "session_id": session_id,
                    "jurisdiction": jurisdiction,
                }

            # Convert entities to facts format
            case_facts = [
                {
                    "id": entity["id"],
                    "name": entity["name"],
                    "description": entity.get("description", ""),
                    "type": entity["type"],
                }
                for entity in case_entities
            ]

            # Detect causes of action
            detected_causes = self.detect_causes_from_facts(case_facts, jurisdiction)

            # Create causes in knowledge graph
            created_causes = []
            for detection in detected_causes:
                try:
                    cause_id = self.create_cause_of_action_in_kg(detection)
                    created_causes.append(
                        {
                            "cause_id": cause_id,
                            "cause_name": detection.cause_name,
                            "confidence": detection.confidence_score,
                            "elements_count": len(detection.elements_detected),
                        }
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to create cause '{detection.cause_name}': {e}"
                    )

            return {
                "session_id": session_id,
                "jurisdiction": jurisdiction,
                "analysis_timestamp": datetime.now().isoformat(),
                "total_facts_analyzed": len(case_facts),
                "potential_causes_detected": len(detected_causes),
                "causes_created": len(created_causes),
                "detected_causes": [
                    {
                        "cause_name": d.cause_name,
                        "confidence_score": d.confidence_score,
                        "supporting_facts_count": len(d.supporting_facts),
                        "elements_detected": len(d.elements_detected),
                    }
                    for d in detected_causes
                ],
                "created_causes": created_causes,
            }

        except Exception as e:
            logger.exception(f"Failed to analyze case for causes: {e}")
            return {"error": str(e), "session_id": session_id}


if __name__ == "__main__":
    # Test cause of action detector
    import sys

    logging.basicConfig(level=logging.INFO)

    from lawyerfactory.kg.enhanced_graph import EnhancedKnowledgeGraph

    from lawyerfactory.kg.jurisdiction import JurisdictionManager

    kg = EnhancedKnowledgeGraph("test_cause_detector.db")
    jurisdiction_manager = JurisdictionManager(kg)
    detector = CauseOfActionDetector(kg, jurisdiction_manager)

    try:
        # Test facts representing a negligence case
        test_facts = [
            {
                "id": "fact_1",
                "name": "Vehicle Collision",
                "description": "Defendant ran red light and collided with plaintiff vehicle",
                "type": "event",
            },
            {
                "id": "fact_2",
                "name": "Duty of Care",
                "description": "All drivers owe duty to exercise reasonable care",
                "type": "fact",
            },
            {
                "id": "fact_3",
                "name": "Injuries",
                "description": "Plaintiff suffered broken ribs and medical expenses of $25,000",
                "type": "evidence",
            },
        ]

        # Detect causes of action
        detected_causes = detector.detect_causes_from_facts(test_facts, "ca_state")
        print(f"Detected {len(detected_causes)} potential causes of action:")

        for cause in detected_causes:
            print(f"- {cause.cause_name}: {cause.confidence_score:.2f} confidence")
            print(f"  Elements detected: {len(cause.elements_detected)}")
            print(f"  Supporting facts: {len(cause.supporting_facts)}")

        # Test comprehensive analysis
        if jurisdiction_manager.select_jurisdiction("ca_state"):
            analysis = detector.analyze_case_for_causes("test_session", "ca_state")
            print(f"Case analysis: {analysis}")

    except Exception as e:
        print(f"Test failed: {e}")
        sys.exit(1)
    finally:
        kg.close()
