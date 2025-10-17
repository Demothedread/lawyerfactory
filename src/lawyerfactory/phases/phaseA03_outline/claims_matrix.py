"""
# Script Name: matrix.py
# Description: Comprehensive Claims Matrix Integration - Phase 3.3 Complete System Integrates cause of action definition engine, cascading decision trees, and interactive legal analysis
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Core
#   - Group Tags: claims-analysis
Comprehensive Claims Matrix Integration - Phase 3.3 Complete System
Integrates cause of action definition engine, cascading decision trees, and interactive legal analysis
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime
import logging
from typing import Any, Dict, List, Optional

from src.ingestion.api.cause_of_action_definition_engine import (
    CauseOfActionDefinitionEngine,
    ElementBreakdown,
    LegalDefinition,
    ProvableQuestion,
)
from lawyerfactory.kg.graph_api import EnhancedKnowledgeGraph
from lawyerfactory.kg.jurisdiction import JurisdictionManager

# cascading_decision_tree_engine may live in claims_matrix or src; try src first and fall back
try:
    from src.claims_matrix.cascading_decision_tree_engine import (
        CascadingDecisionTreeEngine,
        ClickableTerm,
        DecisionOutcome,
        DecisionPathResult,
    )
except Exception:
    from cascading_decision_tree_engine import (
        CascadingDecisionTreeEngine,
        ClickableTerm,
        DecisionOutcome,
        DecisionPathResult,
    )

try:
    pass
except Exception:
    pass

try:
    pass
except Exception:
    pass

from claims_matrix.claims_matrix_research_api import ClaimsMatrixResearchAPI

logger = logging.getLogger(__name__)


@dataclass
class InteractiveAnalysisSession:
    """Represents an interactive legal analysis session"""

    session_id: str
    jurisdiction: str
    cause_of_action: str
    case_facts: List[Dict[str, Any]]
    current_element: Optional[str] = None
    analysis_path: List[Dict[str, Any]] = field(default_factory=list)
    clickable_terms_expanded: Dict[str, str] = field(default_factory=dict)
    decision_tree_state: Dict[str, Any] = field(default_factory=dict)
    attorney_notes: List[str] = field(default_factory=list)
    confidence_assessments: Dict[str, float] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class AttorneyReadyAnalysis:
    """Complete attorney-ready legal analysis"""

    analysis_id: str
    session_id: str
    cause_of_action: str
    jurisdiction: str

    # Legal definitions and authorities
    comprehensive_definition: LegalDefinition
    element_breakdowns: Dict[str, ElementBreakdown]
    authority_validation: Dict[str, Any]

    # Interactive analysis results
    provable_questions: Dict[str, List[ProvableQuestion]]
    decision_tree_outcomes: Dict[str, DecisionPathResult]
    clickable_terms_used: Dict[str, ClickableTerm]

    # Attorney guidance
    case_strength_assessment: Dict[str, Any]
    discovery_recommendations: List[str]
    expert_witness_needs: List[str]
    alternative_theories: List[str]
    practice_guidance: List[str]

    # California-specific analysis
    california_authorities: List[Dict[str, Any]]
    jury_instructions: List[str]
    case_law_precedents: List[Dict[str, Any]]

    created_at: datetime = field(default_factory=datetime.now)


class ComprehensiveClaimsMatrixIntegration:
    """Complete integrated system for attorney-ready legal analysis"""

    def __init__(
        self,
        enhanced_kg: EnhancedKnowledgeGraph,
        courtlistener_token: Optional[str] = None,
        scholar_contact_email: Optional[str] = None,
    ):
        """Initialize comprehensive claims matrix system"""
        self.kg = enhanced_kg

        # Initialize core components
        self.jurisdiction_manager = JurisdictionManager(enhanced_kg)
        self.definition_engine = CauseOfActionDefinitionEngine(
            enhanced_kg, self.jurisdiction_manager, None, None
        )
        self.tree_engine = CascadingDecisionTreeEngine(
            enhanced_kg, self.jurisdiction_manager, self.definition_engine
        )

        # Initialize research integration if tokens provided
        if courtlistener_token or scholar_contact_email:
            try:
                from legal_authority_validator import LegalAuthorityValidator
                from legal_research_integration import LegalResearchAPIIntegration

                self.authority_validator = LegalAuthorityValidator(
                    enhanced_kg, self.jurisdiction_manager
                )
                self.research_integration = LegalResearchAPIIntegration(
                    enhanced_kg,
                    self.jurisdiction_manager,
                    None,
                    courtlistener_token,
                    scholar_contact_email,
                )
                self.research_api = ClaimsMatrixResearchAPI(
                    enhanced_kg, courtlistener_token, scholar_contact_email
                )
            except ImportError:
                logger.warning("Research integration components not available")
                self.research_integration = None
                self.authority_validator = None
                self.research_api = None
        else:
            self.research_integration = None
            self.authority_validator = None
            self.research_api = None

        # Session management
        self.active_sessions: Dict[str, InteractiveAnalysisSession] = {}

        logger.info("Comprehensive Claims Matrix Integration initialized")

    def start_interactive_analysis(
        self,
        jurisdiction: str,
        cause_of_action: str,
        case_facts: List[Dict[str, Any]],
        session_id: Optional[str] = None,
    ) -> str:
        """Start new interactive legal analysis session"""
        try:
            if not session_id:
                session_id = f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.active_sessions)}"

            # Validate jurisdiction
            if not self.jurisdiction_manager.select_jurisdiction(jurisdiction):
                raise ValueError(f"Invalid jurisdiction: {jurisdiction}")

            # Create analysis session
            session = InteractiveAnalysisSession(
                session_id=session_id,
                jurisdiction=jurisdiction,
                cause_of_action=cause_of_action,
                case_facts=case_facts,
            )

            self.active_sessions[session_id] = session

            logger.info(f"Started interactive analysis session: {session_id}")
            return session_id

        except Exception as e:
            logger.exception(f"Failed to start interactive analysis: {e}")
            raise

    def get_comprehensive_definition(
        self, session_id: str
    ) -> Optional[LegalDefinition]:
        """Get comprehensive legal definition for cause of action"""
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                return None

            definition = self.definition_engine.generate_comprehensive_definition(
                session.cause_of_action, session.jurisdiction
            )

            return definition

        except Exception as e:
            logger.exception(f"Failed to get comprehensive definition: {e}")
            return None

    def expand_clickable_term(
        self, session_id: str, term_text: str
    ) -> Optional[ClickableTerm]:
        """Expand clickable legal term with context"""
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                return None

            # Get term expansion with context
            context = f"{session.cause_of_action}_{session.jurisdiction}"
            term = self.tree_engine.expand_clickable_term(term_text, context)

            if term:
                # Track expanded terms
                session.clickable_terms_expanded[term_text] = term.term_id
                session.last_updated = datetime.now()

            return term

        except Exception as e:
            logger.exception(f"Failed to expand clickable term '{term_text}': {e}")
            return None

    def get_element_breakdown(
        self, session_id: str, element_name: str
    ) -> Optional[ElementBreakdown]:
        """Get detailed breakdown for legal element"""
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                return None

            breakdown = self.definition_engine.generate_element_breakdown(
                session.cause_of_action, element_name, session.jurisdiction
            )

            if breakdown:
                session.current_element = element_name
                session.last_updated = datetime.now()

            return breakdown

        except Exception as e:
            logger.exception(
                f"Failed to get element breakdown for '{element_name}': {e}"
            )
            return None

    def get_provable_questions(
        self, session_id: str, element_name: str
    ) -> List[ProvableQuestion]:
        """Get attorney-ready provable questions for element"""
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                return []

            questions = self.definition_engine.generate_provable_questions(
                session.cause_of_action, element_name
            )

            return questions

        except Exception as e:
            logger.exception(
                f"Failed to get provable questions for '{element_name}': {e}"
            )
            return []

    def build_interactive_decision_tree(
        self, session_id: str, element_name: str
    ) -> Dict[str, Any]:
        """Build interactive decision tree for element analysis"""
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                return {}

            tree = self.tree_engine.build_decision_tree(
                session.cause_of_action, element_name, session.case_facts
            )

            if tree:
                session.decision_tree_state[element_name] = tree
                session.last_updated = datetime.now()

            return tree

        except Exception as e:
            logger.exception(f"Failed to build decision tree for '{element_name}': {e}")
            return {}

    def analyze_decision_path(
        self, session_id: str, element_name: str, decisions: List[Dict[str, Any]]
    ) -> Optional[DecisionPathResult]:
        """Analyze complete decision path for element"""
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                return None

            tree_id = f"{session.cause_of_action}_{element_name}"
            result = self.tree_engine.analyze_decision_path(
                tree_id, decisions, session.case_facts
            )

            if result:
                # Update session with analysis
                session.analysis_path.append(
                    {
                        "element": element_name,
                        "decisions": decisions,
                        "outcome": result.final_outcome.value,
                        "confidence": result.confidence_score,
                        "timestamp": datetime.now().isoformat(),
                    }
                )
                session.confidence_assessments[element_name] = result.confidence_score
                session.last_updated = datetime.now()

            return result

        except Exception as e:
            logger.exception(
                f"Failed to analyze decision path for '{element_name}': {e}"
            )
            return None

    def get_california_authorities(self, session_id: str) -> List[Dict[str, Any]]:
        """Get California-specific legal authorities"""
        try:
            session = self.active_sessions.get(session_id)
            if not session or session.jurisdiction != "ca_state":
                return []

            authorities = self.jurisdiction_manager.get_jurisdiction_authorities(
                "ca_state"
            )

            # Filter for relevant authorities
            cause_relevant = [
                auth
                for auth in authorities
                if session.cause_of_action.lower()
                in auth.get("authority_name", "").lower()
                or "general" in auth.get("authority_type", "").lower()
            ]

            return cause_relevant

        except Exception as e:
            logger.exception(f"Failed to get California authorities: {e}")
            return []

    async def enhance_with_legal_research(self, session_id: str) -> Dict[str, Any]:
        """Enhance analysis with real-time legal research"""
        try:
            if not self.research_api:
                return {"error": "Research integration not available"}

            session = self.active_sessions.get(session_id)
            if not session:
                return {"error": "Session not found"}

            # Create research request
            from claims_matrix.claims_matrix_research_api import (
                ClaimsMatrixResearchRequest,
                ResearchPriority,
            )

            request = ClaimsMatrixResearchRequest(
                request_id=f"research_{session_id}",
                cause_of_action=session.cause_of_action,
                jurisdiction=session.jurisdiction,
                legal_elements=(
                    [session.current_element] if session.current_element else []
                ),
                case_facts=[
                    f"{f.get('name', '')}: {f.get('description', '')}"
                    for f in session.case_facts
                ],
                priority=ResearchPriority.HIGH,
                include_definitions=True,
                include_case_law=True,
                validate_authorities=True,
            )

            # Execute research
            response = await self.research_api.execute_comprehensive_research(request)

            return asdict(response) if response else {"error": "Research failed"}

        except Exception as e:
            logger.exception(f"Failed to enhance with legal research: {e}")
            return {"error": str(e)}

    def generate_attorney_ready_analysis(
        self, session_id: str
    ) -> Optional[AttorneyReadyAnalysis]:
        """Generate complete attorney-ready legal analysis"""
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                return None

            analysis_id = f"attorney_analysis_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # Get comprehensive definition
            comprehensive_definition = self.get_comprehensive_definition(session_id)
            if not comprehensive_definition:
                raise ValueError("Could not generate comprehensive definition")

            # Get element breakdowns for all elements
            element_breakdowns = {}
            if session.cause_of_action == "negligence":
                elements = ["duty", "breach", "causation", "damages"]
            elif session.cause_of_action == "breach_of_contract":
                elements = ["contract_formation", "performance", "breach", "damages"]
            elif session.cause_of_action == "fraud":
                elements = [
                    "misrepresentation",
                    "scienter",
                    "intent",
                    "reliance",
                    "damages",
                ]
            elif session.cause_of_action == "intentional_infliction_emotional_distress":
                elements = [
                    "extreme_outrageous_conduct",
                    "intent_recklessness",
                    "causation",
                    "severe_emotional_distress",
                ]
            elif session.cause_of_action == "defamation":
                elements = ["defamatory_statement", "publication", "falsity", "damages"]
            else:
                elements = ["unknown_elements"]

            for element in elements:
                breakdown = self.get_element_breakdown(session_id, element)
                if breakdown:
                    element_breakdowns[element] = breakdown

            # Get provable questions for all elements
            provable_questions = {}
            for element in elements:
                questions = self.get_provable_questions(session_id, element)
                provable_questions[element] = questions

            # Get decision tree outcomes from session
            decision_tree_outcomes = {}
            for analysis in session.analysis_path:
                element = analysis["element"]
                # Reconstruct decision path result for summary
                decision_tree_outcomes[element] = DecisionPathResult(
                    path_id=f"path_{element}",
                    decisions_made=analysis["decisions"],
                    final_outcome=DecisionOutcome(analysis["outcome"]),
                    confidence_score=analysis["confidence"],
                    supporting_evidence=[],
                    missing_evidence=[],
                    recommended_actions=[],
                    alternative_theories=[],
                    practice_guidance=[],
                )

            # Get clicked terms
            clickable_terms_used = {}
            for term_text, term_id in session.clickable_terms_expanded.items():
                term = self.tree_engine.expand_clickable_term(term_text)
                if term:
                    clickable_terms_used[term_text] = term

            # Generate case strength assessment
            case_strength = self._assess_case_strength(session)

            # Generate discovery recommendations
            discovery_recs = self._generate_discovery_recommendations(
                session, element_breakdowns
            )

            # Generate expert witness needs
            expert_needs = self._identify_expert_witness_needs(
                session.cause_of_action, element_breakdowns
            )

            # Get California authorities
            california_authorities = self.get_california_authorities(session_id)

            # Generate jury instructions list
            jury_instructions = self._get_california_jury_instructions(
                session.cause_of_action
            )

            # Get case law precedents
            case_law_precedents = self._get_case_law_precedents(
                session.cause_of_action, session.jurisdiction
            )

            # Generate alternative theories
            alternative_theories = self._identify_alternative_theories(
                session.case_facts, session.cause_of_action
            )

            # Generate practice guidance
            practice_guidance = self._generate_comprehensive_practice_guidance(
                session, case_strength
            )

            # Create attorney-ready analysis
            attorney_analysis = AttorneyReadyAnalysis(
                analysis_id=analysis_id,
                session_id=session_id,
                cause_of_action=session.cause_of_action,
                jurisdiction=session.jurisdiction,
                comprehensive_definition=comprehensive_definition,
                element_breakdowns=element_breakdowns,
                authority_validation={},  # Would be populated with research integration
                provable_questions=provable_questions,
                decision_tree_outcomes=decision_tree_outcomes,
                clickable_terms_used=clickable_terms_used,
                case_strength_assessment=case_strength,
                discovery_recommendations=discovery_recs,
                expert_witness_needs=expert_needs,
                alternative_theories=alternative_theories,
                practice_guidance=practice_guidance,
                california_authorities=california_authorities,
                jury_instructions=jury_instructions,
                case_law_precedents=case_law_precedents,
            )

            return attorney_analysis

        except Exception as e:
            logger.exception(f"Failed to generate attorney-ready analysis: {e}")
            return None

    def export_analysis_report(
        self, analysis: AttorneyReadyAnalysis, format_type: str = "comprehensive"
    ) -> Dict[str, Any]:
        """Export attorney analysis as structured report"""
        try:
            if format_type == "comprehensive":
                return {
                    "header": {
                        "analysis_id": analysis.analysis_id,
                        "cause_of_action": analysis.cause_of_action.replace(
                            "_", " "
                        ).title(),
                        "jurisdiction": (
                            "California State Court"
                            if analysis.jurisdiction == "ca_state"
                            else analysis.jurisdiction
                        ),
                        "generated_date": analysis.created_at.strftime("%B %d, %Y"),
                        "attorney_ready": True,
                    },
                    "executive_summary": {
                        "case_strength": analysis.case_strength_assessment,
                        "key_challenges": [
                            outcome.missing_evidence
                            for outcome in analysis.decision_tree_outcomes.values()
                        ],
                        "recommended_actions": list(
                            set(
                                [
                                    rec
                                    for recs in [
                                        outcome.recommended_actions
                                        for outcome in analysis.decision_tree_outcomes.values()
                                    ]
                                    for rec in recs
                                ]
                            )
                        ),
                    },
                    "legal_definition": {
                        "primary_definition": analysis.comprehensive_definition.primary_definition,
                        "authority_citations": analysis.comprehensive_definition.authority_citations,
                        "clickable_terms": analysis.comprehensive_definition.clickable_terms,
                        "jury_instructions": analysis.comprehensive_definition.jury_instructions,
                    },
                    "element_analysis": {
                        element: {
                            "breakdown": asdict(breakdown),
                            "provable_questions": [
                                asdict(q)
                                for q in analysis.provable_questions.get(element, [])
                            ],
                            "decision_outcome": (
                                asdict(analysis.decision_tree_outcomes.get(element))
                                if element in analysis.decision_tree_outcomes
                                else None
                            ),
                        }
                        for element, breakdown in analysis.element_breakdowns.items()
                    },
                    "california_authorities": analysis.california_authorities,
                    "practice_guidance": analysis.practice_guidance,
                    "discovery_recommendations": analysis.discovery_recommendations,
                    "expert_witness_needs": analysis.expert_witness_needs,
                    "alternative_theories": analysis.alternative_theories,
                    "appendices": {
                        "case_law_precedents": analysis.case_law_precedents,
                        "clickable_terms_expanded": {
                            k: asdict(v)
                            for k, v in analysis.clickable_terms_used.items()
                        },
                    },
                }

            elif format_type == "summary":
                return {
                    "case_overview": f"{analysis.cause_of_action.replace('_', ' ').title()} - {analysis.jurisdiction}",
                    "strength_assessment": analysis.case_strength_assessment.get(
                        "overall_strength", "Unknown"
                    ),
                    "key_authorities": analysis.comprehensive_definition.authority_citations[
                        :3
                    ],
                    "critical_elements": list(analysis.element_breakdowns.keys()),
                    "next_steps": analysis.practice_guidance[:5],
                }

            else:
                return {"error": f"Unknown format type: {format_type}"}

        except Exception as e:
            logger.exception(f"Failed to export analysis report: {e}")
            return {"error": str(e)}

    def _assess_case_strength(
        self, session: InteractiveAnalysisSession
    ) -> Dict[str, Any]:
        """Assess overall case strength based on element analysis"""
        if not session.confidence_assessments:
            return {
                "overall_strength": "Insufficient Analysis",
                "confidence_score": 0.0,
                "strong_elements": [],
                "weak_elements": [],
                "critical_gaps": ["Complete element analysis needed"],
            }

        avg_confidence = sum(session.confidence_assessments.values()) / len(
            session.confidence_assessments
        )

        strong_elements = [
            elem for elem, conf in session.confidence_assessments.items() if conf >= 0.7
        ]
        weak_elements = [
            elem for elem, conf in session.confidence_assessments.items() if conf < 0.5
        ]

        if avg_confidence >= 0.75:
            strength = "Strong"
        elif avg_confidence >= 0.5:
            strength = "Moderate"
        else:
            strength = "Weak"

        return {
            "overall_strength": strength,
            "confidence_score": avg_confidence,
            "strong_elements": strong_elements,
            "weak_elements": weak_elements,
            "critical_gaps": [
                f"Strengthen evidence for {elem}" for elem in weak_elements
            ],
        }

    def _generate_discovery_recommendations(
        self,
        session: InteractiveAnalysisSession,
        element_breakdowns: Dict[str, ElementBreakdown],
    ) -> List[str]:
        """Generate discovery recommendations based on element analysis"""
        recommendations = []

        # General discovery based on cause of action
        if session.cause_of_action == "negligence":
            recommendations.extend(
                [
                    "Request incident reports and documentation",
                    "Depose defendant regarding standard operating procedures",
                    "Request training materials and safety protocols",
                    "Obtain expert accident reconstruction if needed",
                ]
            )
        elif session.cause_of_action == "breach_of_contract":
            recommendations.extend(
                [
                    "Request all contract documents and amendments",
                    "Depose parties regarding contract negotiations",
                    "Request correspondence related to performance",
                    "Obtain financial records showing damages",
                ]
            )
        elif session.cause_of_action == "fraud":
            recommendations.extend(
                [
                    "Request all communications containing alleged misrepresentations",
                    "Depose defendant regarding knowledge and intent",
                    "Request financial records showing reliance and damages",
                    "Obtain expert testimony on industry standards if applicable",
                ]
            )

        # Element-specific discovery
        for element, breakdown in element_breakdowns.items():
            if element == "causation":
                recommendations.append("Retain medical expert to establish causation")
            elif element == "damages":
                recommendations.append(
                    "Request medical records and financial documentation"
                )
            elif element == "duty":
                recommendations.append(
                    "Research applicable statutes and industry standards"
                )

        return list(set(recommendations))  # Remove duplicates

    def _identify_expert_witness_needs(
        self, cause_of_action: str, element_breakdowns: Dict[str, ElementBreakdown]
    ) -> List[str]:
        """Identify expert witness needs based on cause and elements"""
        expert_needs = []

        if cause_of_action == "negligence":
            if "duty" in element_breakdowns or "breach" in element_breakdowns:
                expert_needs.append(
                    "Standard of care expert for professional malpractice"
                )
            if "causation" in element_breakdowns:
                expert_needs.append("Medical expert for causation testimony")
            expert_needs.append("Accident reconstruction expert if applicable")

        elif cause_of_action == "breach_of_contract":
            expert_needs.extend(
                [
                    "Industry expert for contract interpretation",
                    "Damages expert for economic loss calculation",
                ]
            )

        elif cause_of_action == "fraud":
            expert_needs.extend(
                [
                    "Industry expert for standard practices",
                    "Financial expert for damage calculation",
                    "Handwriting expert if document authenticity disputed",
                ]
            )

        return expert_needs

    def _get_california_jury_instructions(self, cause_of_action: str) -> List[str]:
        """Get relevant California jury instructions"""
        instructions = []

        if cause_of_action == "negligence":
            instructions.extend(
                [
                    "CACI No. 400 (Negligence—Essential Factual Elements)",
                    "CACI No. 401 (Negligence—Standard of Care)",
                    "CACI No. 430 (Causation—Substantial Factor)",
                    "CACI No. 3903A (Economic Damages)",
                ]
            )
        elif cause_of_action == "breach_of_contract":
            instructions.extend(
                [
                    "CACI No. 303 (Breach of Contract—Essential Factual Elements)",
                    "CACI No. 304 (Breach of Contract—Liability)",
                    "CACI No. 350 (Affirmative Defense—Failure of Consideration)",
                ]
            )
        elif cause_of_action == "fraud":
            instructions.extend(
                [
                    "CACI No. 1900 (Intentional Misrepresentation)",
                    "CACI No. 1901 (Negligent Misrepresentation)",
                ]
            )
        elif cause_of_action == "intentional_infliction_emotional_distress":
            instructions.extend(
                [
                    "CACI No. 1600 (Intentional Infliction of Emotional Distress)",
                    "CACI No. 1601 (Negligent Infliction of Emotional Distress)",
                ]
            )
        elif cause_of_action == "defamation":
            instructions.extend(
                [
                    "CACI No. 1700 (Defamation—Essential Factual Elements)",
                    "CACI No. 1701 (Defamation—Publication)",
                ]
            )

        return instructions

    def _get_case_law_precedents(
        self, cause_of_action: str, jurisdiction: str
    ) -> List[Dict[str, Any]]:
        """Get key case law precedents"""
        precedents = []

        if jurisdiction == "ca_state":
            if cause_of_action == "negligence":
                precedents.extend(
                    [
                        {
                            "citation": "Rowland v. Christian (1968) 69 Cal.2d 108",
                            "principle": "Duty of care analysis using policy factors",
                            "significance": "Foundational case for duty determination",
                        },
                        {
                            "citation": "Mitchell v. Gonzales (1991) 54 Cal.3d 1041",
                            "principle": "Substantial factor causation test",
                            "significance": "Standard for causation in medical malpractice",
                        },
                    ]
                )
            elif cause_of_action == "breach_of_contract":
                precedents.extend(
                    [
                        {
                            "citation": "Oasis West Realty, LLC v. Goldman (2011) 51 Cal.4th 811",
                            "principle": "Elements of breach of contract",
                            "significance": "Modern statement of contract breach elements",
                        }
                    ]
                )

        return precedents

    def _identify_alternative_theories(
        self, case_facts: List[Dict[str, Any]], primary_cause: str
    ) -> List[str]:
        """Identify alternative legal theories based on facts"""
        alternatives = []

        # Simple heuristic based on fact keywords
        fact_text = " ".join(
            [f"{f.get('name', '')} {f.get('description', '')}" for f in case_facts]
        ).lower()

        if "contract" in fact_text and primary_cause != "breach_of_contract":
            alternatives.append("Breach of Contract")
        if "professional" in fact_text and primary_cause != "negligence":
            alternatives.append("Professional Malpractice")
        if (
            "false" in fact_text
            and "statement" in fact_text
            and primary_cause != "fraud"
        ):
            alternatives.append("Fraud/Misrepresentation")
        if "property" in fact_text and primary_cause != "negligence":
            alternatives.append("Premises Liability")
        if "emotional" in fact_text and "distress" in fact_text:
            alternatives.append("Intentional Infliction of Emotional Distress")

        return alternatives

    def _generate_comprehensive_practice_guidance(
        self, session: InteractiveAnalysisSession, case_strength: Dict[str, Any]
    ) -> List[str]:
        """Generate comprehensive practice guidance"""
        guidance = []

        # Strength-based guidance
        if case_strength["overall_strength"] == "Strong":
            guidance.extend(
                [
                    "Consider early motion for summary judgment on strong elements",
                    "Prepare comprehensive settlement demand",
                    "Document all evidence thoroughly for trial",
                ]
            )
        elif case_strength["overall_strength"] == "Weak":
            guidance.extend(
                [
                    "Evaluate case for early settlement or dismissal",
                    "Consider alternative legal theories",
                    "Focus discovery on strengthening weak elements",
                ]
            )

        # Cause-specific guidance
        if session.cause_of_action == "negligence":
            guidance.extend(
                [
                    "Prepare Rowland factor analysis for duty questions",
                    "Retain medical expert early for complex causation",
                    "Consider res ipsa loquitur if applicable",
                    "Address comparative fault proactively",
                ]
            )
        elif session.cause_of_action == "breach_of_contract":
            guidance.extend(
                [
                    "Review parol evidence rule implications",
                    "Consider UCC vs. common law application",
                    "Prepare mitigation of damages evidence",
                    "Address any Statute of Frauds issues",
                ]
            )

        # California-specific guidance
        if session.jurisdiction == "ca_state":
            guidance.extend(
                [
                    "Review California Civil Code provisions",
                    "Consider Anti-SLAPP motion if applicable",
                    "Prepare for California discovery rules",
                    "Review local court rules for procedure",
                ]
            )

        return guidance


# Integration testing and example usage
if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)

    try:
        # Initialize system
        kg = EnhancedKnowledgeGraph("test_comprehensive_integration.db")
        integration = ComprehensiveClaimsMatrixIntegration(kg)

        # Test case facts
        test_facts = [
            {
                "id": "fact_1",
                "name": "Vehicle Collision",
                "description": "Defendant ran red light and collided with plaintiff vehicle at intersection",
                "type": "event",
            },
            {
                "id": "fact_2",
                "name": "Traffic Violation",
                "description": "Police report indicates defendant violated Vehicle Code § 21453(a)",
                "type": "evidence",
            },
            {
                "id": "fact_3",
                "name": "Personal Injuries",
                "description": "Plaintiff suffered broken ribs, concussion, and required surgery",
                "type": "damages",
            },
            {
                "id": "fact_4",
                "name": "Medical Expenses",
                "description": "Medical bills totaling $45,000 with ongoing physical therapy",
                "type": "damages",
            },
        ]

        # Start interactive analysis
        session_id = integration.start_interactive_analysis(
            "ca_state", "negligence", test_facts
        )
        print(f"Started analysis session: {session_id}")

        # Get comprehensive definition
        definition = integration.get_comprehensive_definition(session_id)
        if definition:
            print("\nComprehensive definition generated")
            print(f"Primary definition: {definition.primary_definition[:100]}...")
            print(f"Authority citations: {len(definition.authority_citations)}")

        # Test clickable term expansion
        duty_term = integration.expand_clickable_term(session_id, "duty of care")
        if duty_term:
            print("\nExpanded 'duty of care' term")
            print(f"Sub-terms: {duty_term.sub_terms}")

        # Get element breakdown
        duty_breakdown = integration.get_element_breakdown(session_id, "duty")
        if duty_breakdown:
            print("\nDuty element breakdown generated")
            print(f"Sub-elements: {len(duty_breakdown.sub_elements)}")

        # Build decision tree
        duty_tree = integration.build_interactive_decision_tree(session_id, "duty")
        print(f"\nDecision tree built with {len(duty_tree.get('nodes', {}))} nodes")

        # Simulate decision path
        test_decisions = [
            {"question": "statutory_duty", "answer": "yes", "confidence": 0.9},
            {"question": "protected_class", "answer": "yes", "confidence": 0.8},
        ]

        path_result = integration.analyze_decision_path(
            session_id, "duty", test_decisions
        )
        if path_result:
            print("\nDecision path analyzed")
            print(f"Outcome: {path_result.final_outcome.value}")
            print(f"Confidence: {path_result.confidence_score:.2f}")

        # Generate attorney-ready analysis
        attorney_analysis = integration.generate_attorney_ready_analysis(session_id)
        if attorney_analysis:
            print("\nGenerated attorney-ready analysis")
            print(
                f"Elements analyzed: {list(attorney_analysis.element_breakdowns.keys())}"
            )
            print(
                f"Practice guidance items: {len(attorney_analysis.practice_guidance)}"
            )
            print(
                f"Discovery recommendations: {len(attorney_analysis.discovery_recommendations)}"
            )

        # Export comprehensive report
        if attorney_analysis:
            report = integration.export_analysis_report(
                attorney_analysis, "comprehensive"
            )
            print(f"\nExported comprehensive report with {len(report)} sections")

            summary_report = integration.export_analysis_report(
                attorney_analysis, "summary"
            )
            print(
                f"Exported summary report: {summary_report.get('case_overview', 'N/A')}"
            )

        print("\n✅ Comprehensive integration test completed successfully")

    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        sys.exit(1)
    finally:
        kg.close()
