"""
# Script Name: cause_of_action_definition_engine.py
# Description: Cause of Action Definition and Element Breakdown Engine - Phase 3.3 Comprehensive legal definition system with California-specific authorities and provable question generation
# Relationships:
#   - Entity Type: Engine
#   - Directory Group: Workflow
#   - Group Tags: claims-analysis
Cause of Action Definition and Element Breakdown Engine - Phase 3.3
Comprehensive legal definition system with California-specific authorities and provable question generation
"""

from dataclasses import dataclass, field
from datetime import datetime
import logging
from typing import Any, Dict, List, Optional

from lawyerfactory.kg.enhanced_graph import EnhancedKnowledgeGraph
from legal_authority_validator import LegalAuthorityValidator
from legal_research_integration import LegalResearchAPIIntegration

from lawyerfactory.kg.jurisdiction import JurisdictionManager

logger = logging.getLogger(__name__)


@dataclass
class LegalDefinition:
    """Comprehensive legal definition with authorities and clickable terms"""

    definition_id: str
    cause_of_action: str
    jurisdiction: str
    primary_definition: str
    authority_citations: List[str]
    clickable_terms: Dict[str, str]  # term -> expanded definition
    alternative_definitions: Dict[str, str]  # jurisdiction -> definition
    jury_instructions: List[str]
    case_law_examples: List[str]
    statutory_references: List[str]
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ElementBreakdown:
    """Detailed element breakdown with sub-elements and decision trees"""

    element_id: str
    element_name: str
    primary_definition: str
    authority_citations: List[str]
    sub_elements: List[Dict[str, Any]]
    decision_trees: List[Dict[str, Any]]
    burden_of_proof: str
    proof_standards: Dict[str, str]
    common_defenses: List[str]
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ProvableQuestion:
    """Attorney-ready provable question with guidance"""

    question_id: str
    question_text: str
    element_name: str
    question_type: str  # threshold, factual, legal, credibility
    evidence_types: List[str]
    proof_methods: List[str]
    common_challenges: List[str]
    practice_tips: List[str]
    sub_questions: List[str]
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class DecisionTreeNode:
    """Decision tree node for cascading legal analysis"""

    node_id: str
    condition: str
    true_path: Optional[str]
    false_path: Optional[str]
    outcome: Optional[str]
    legal_standard: str
    authority_citation: str
    practice_notes: List[str]


class CauseOfActionDefinitionEngine:
    """Comprehensive cause of action definition and element breakdown engine"""

    def __init__(
        self,
        enhanced_kg: EnhancedKnowledgeGraph,
        jurisdiction_manager: JurisdictionManager,
        research_integration: LegalResearchAPIIntegration,
        authority_validator: LegalAuthorityValidator,
    ):
        self.kg = enhanced_kg
        self.jurisdiction_manager = jurisdiction_manager
        self.research_integration = research_integration
        self.authority_validator = authority_validator

        # Initialize California-specific legal definitions
        self.california_definitions = self._initialize_california_definitions()

        # Initialize element breakdown templates
        self.element_breakdowns = self._initialize_element_breakdowns()

        # Initialize provable question generators
        self.question_generators = self._initialize_question_generators()

        # Initialize decision tree logic
        self.decision_trees = self._initialize_decision_trees()

        logger.info("Cause of Action Definition Engine initialized")

    def _initialize_california_definitions(self) -> Dict[str, LegalDefinition]:
        """Initialize comprehensive California-specific cause of action definitions"""
        return {
            "negligence": LegalDefinition(
                definition_id="ca_negligence_001",
                cause_of_action="negligence",
                jurisdiction="ca_state",
                primary_definition=(
                    "To establish a cause of action for negligence, a plaintiff must prove: "
                    "(1) defendant owed plaintiff a **duty of care**; (2) defendant **breached** that duty; "
                    "(3) the breach was a **substantial factor** in causing plaintiff's harm; and "
                    "(4) plaintiff suffered **actual damages**."
                ),
                authority_citations=[
                    "Rowland v. Christian (1968) 69 Cal.2d 108, 112",
                    "Cal. Civ. Code § 1714(a)",
                    "CACI No. 400 (Negligence—Essential Factual Elements)",
                ],
                clickable_terms={
                    "duty of care": "A legal obligation imposed on an individual requiring adherence to a standard of reasonable care while performing acts that could foreseeably harm others.",
                    "breached": "The failure to exercise the standard of care that a reasonably prudent person would have exercised in a similar situation.",
                    "substantial factor": "The defendant's conduct must be of such a nature that it is a substantial factor in bringing about the occurrence which produces the damage.",
                    "actual damages": "Real, substantial, and just damages, as opposed to nominal or speculative damages.",
                },
                alternative_definitions={
                    "federal": "Under federal common law, negligence requires duty, breach, causation, and damages with substantial factor causation test.",
                    "restatement": "Restatement (Third) of Torts defines negligence as failure to exercise reasonable care under the circumstances.",
                },
                jury_instructions=[
                    "CACI No. 400 (Negligence—Essential Factual Elements)",
                    "CACI No. 401 (Negligence—Standard of Care)",
                    "CACI No. 430 (Causation—Substantial Factor)",
                ],
                case_law_examples=[
                    "Rowland v. Christian (1968) 69 Cal.2d 108 - duty of care to invitees",
                    "Ballard v. Uribe (1986) 41 Cal.3d 564 - substantial factor causation",
                    "Knight v. Jewett (1992) 3 Cal.4th 296 - primary assumption of risk",
                ],
                statutory_references=[
                    "Cal. Civ. Code § 1714(a) - general duty of care",
                    "Cal. Civ. Code § 1714.1 - liability of parents for minor children",
                    "Cal. Veh. Code § 17150 - owner liability for permissive use",
                ],
            ),
            "breach_of_contract": LegalDefinition(
                definition_id="ca_contract_001",
                cause_of_action="breach_of_contract",
                jurisdiction="ca_state",
                primary_definition=(
                    "To establish breach of contract under California law, plaintiff must prove: "
                    "(1) existence of a **valid contract**; (2) plaintiff's **performance** or excuse for nonperformance; "
                    "(3) defendant's **material breach**; and (4) **damages** proximately caused by the breach."
                ),
                authority_citations=[
                    "Oasis West Realty, LLC v. Goldman (2011) 51 Cal.4th 811, 821",
                    "Reichert v. General Ins. Co. (1968) 68 Cal.2d 822, 830",
                    "CACI No. 303 (Breach of Contract—Essential Factual Elements)",
                ],
                clickable_terms={
                    "valid contract": "A contract that satisfies all legal requirements: offer, acceptance, consideration, legal capacity, and lawful object.",
                    "performance": "Substantial performance of contractual duties or legal excuse for nonperformance such as impossibility or frustration.",
                    "material breach": "A failure to perform that goes to the essence of the contract and defeats the object of the parties in making the agreement.",
                    "damages": "Loss suffered as a direct and proximate result of the breach, including expectancy and consequential damages.",
                },
                alternative_definitions={
                    "federal": "Under federal contract law, breach requires valid contract formation, performance, breach, and causation of damages.",
                    "ucc": "Under UCC Article 2, sale of goods contracts have specific performance and breach standards.",
                },
                jury_instructions=[
                    "CACI No. 303 (Breach of Contract—Essential Factual Elements)",
                    "CACI No. 304 (Breach of Contract—Liability)",
                    "CACI No. 350 (Affirmative Defense—Failure of Consideration)",
                ],
                case_law_examples=[
                    "Oasis West Realty, LLC v. Goldman (2011) 51 Cal.4th 811 - contract formation elements",
                    "Carma Developers, Inc. v. Marathon Dev. Cal. (1992) 2 Cal.4th 342 - material breach standard",
                    "Applied Equipment Corp. v. Litton Saudi Arabia Ltd. (1994) 7 Cal.4th 503 - damages calculation",
                ],
                statutory_references=[
                    "Cal. Civ. Code § 1549 - contract formation requirements",
                    "Cal. Civ. Code § 1511 - performance of contractual obligations",
                    "Cal. Com. Code § 2106 - UCC definitions for sale of goods",
                ],
            ),
            "fraud": LegalDefinition(
                definition_id="ca_fraud_001",
                cause_of_action="fraud",
                jurisdiction="ca_state",
                primary_definition=(
                    "Fraud requires proof of: (1) **misrepresentation** of a material fact; "
                    "(2) **knowledge** of falsity (scienter); (3) **intent** to induce reliance; "
                    "(4) **justifiable reliance**; and (5) **resulting damages**."
                ),
                authority_citations=[
                    "Lazar v. Superior Court (1996) 12 Cal.4th 631, 638",
                    "Small v. Fritz Companies, Inc. (2003) 30 Cal.4th 167, 173",
                    "CACI No. 1900 (Intentional Misrepresentation)",
                ],
                clickable_terms={
                    "misrepresentation": "A false statement of material fact, or concealment of material fact when there is a duty to disclose.",
                    "knowledge": "Actual knowledge of falsity or reckless disregard for truth (scienter requirement).",
                    "intent": "Intent to induce the plaintiff to rely on the misrepresentation in his or her conduct.",
                    "justifiable reliance": "Plaintiff's reliance on the misrepresentation was reasonable under the circumstances.",
                    "resulting damages": "Actual economic loss proximately caused by reliance on the misrepresentation.",
                },
                alternative_definitions={
                    "federal": "Federal fraud claims under securities laws require materiality, scienter, reliance, and loss causation.",
                    "negligent_misrep": "Negligent misrepresentation requires only negligent conduct, not knowledge of falsity.",
                },
                jury_instructions=[
                    "CACI No. 1900 (Intentional Misrepresentation)",
                    "CACI No. 1901 (Negligent Misrepresentation)",
                    "CACI No. 1902 (Promise Made Without Intention to Perform)",
                ],
                case_law_examples=[
                    "Lazar v. Superior Court (1996) 12 Cal.4th 631 - scienter requirement",
                    "Engalla v. Permanente Medical Group (1997) 15 Cal.4th 951 - concealment fraud",
                    "Apollo Capital Fund LLC v. Roth Capital Partners (2007) 158 Cal.App.4th 226 - justifiable reliance",
                ],
                statutory_references=[
                    "Cal. Civ. Code § 1572 - actual fraud definition",
                    "Cal. Civ. Code § 1573 - constructive fraud",
                    "Cal. Corp. Code § 25401 - securities fraud liability",
                ],
            ),
            "intentional_infliction_emotional_distress": LegalDefinition(
                definition_id="ca_iied_001",
                cause_of_action="intentional_infliction_emotional_distress",
                jurisdiction="ca_state",
                primary_definition=(
                    "IIED requires: (1) **extreme and outrageous** conduct by defendant; "
                    "(2) **intent** to cause emotional distress or reckless disregard; "
                    "(3) severe emotional distress suffered by plaintiff; and "
                    "(4) defendant's conduct was a **substantial factor** in causing the distress."
                ),
                authority_citations=[
                    "Hughes v. Pair (2009) 46 Cal.4th 1035, 1050-1051",
                    "Christensen v. Superior Court (1991) 54 Cal.3d 868, 903",
                    "CACI No. 1600 (Intentional Infliction of Emotional Distress)",
                ],
                clickable_terms={
                    "extreme and outrageous": "Conduct that exceeds all bounds usually tolerated by decent society and is of such a nature as to be regarded as atrocious and utterly intolerable.",
                    "intent": "Intent to cause severe emotional distress, or reckless disregard of the probability of causing such distress.",
                    "substantial factor": "The defendant's conduct must be a substantial factor in causing the plaintiff's severe emotional distress.",
                },
                alternative_definitions={
                    "federal": "Federal IIED claims follow similar elements but may have different standards for outrageousness.",
                    "workplace": "Workplace IIED claims may require showing conduct beyond normal employment disciplinary actions.",
                },
                jury_instructions=[
                    "CACI No. 1600 (Intentional Infliction of Emotional Distress)",
                    "CACI No. 1601 (Negligent Infliction of Emotional Distress)",
                    "CACI No. 1602 (Bystander Emotional Distress)",
                ],
                case_law_examples=[
                    "Hughes v. Pair (2009) 46 Cal.4th 1035 - extreme and outrageous conduct standard",
                    "Christensen v. Superior Court (1991) 54 Cal.3d 868 - sexual harassment context",
                    "Fisher v. San Pedro Peninsula Hospital (1989) 214 Cal.App.3d 590 - medical context",
                ],
                statutory_references=[
                    "Cal. Civ. Code § 52.4 - hate violence causing emotional distress",
                    "Cal. Gov. Code § 12940 - workplace harassment protections",
                ],
            ),
            "defamation": LegalDefinition(
                definition_id="ca_defamation_001",
                cause_of_action="defamation",
                jurisdiction="ca_state",
                primary_definition=(
                    "Defamation requires: (1) **defamatory statement** concerning plaintiff; "
                    "(2) **publication** to a third party; (3) **falsity** of the statement; "
                    "(4) **damages** to reputation; and (5) absence of **privilege**."
                ),
                authority_citations=[
                    "Taus v. Loftus (2007) 40 Cal.4th 683, 720",
                    "Smith v. Maldonado (1999) 72 Cal.App.4th 637, 645",
                    "CACI No. 1700 (Defamation—Essential Factual Elements)",
                ],
                clickable_terms={
                    "defamatory statement": "A statement that tends to injure reputation in the eyes of the community or deter third persons from associating with the plaintiff.",
                    "publication": "Communication of the defamatory statement to someone other than the plaintiff.",
                    "falsity": "The statement must be false; truth is an absolute defense to defamation.",
                    "damages": "Injury to reputation, including special damages (economic loss) and general damages (presumed harm).",
                    "privilege": "Absolute or qualified privilege may protect certain statements from defamation liability.",
                },
                alternative_definitions={
                    "federal": "First Amendment considerations require public figures to prove actual malice for defamation claims.",
                    "anti_slapp": "California Anti-SLAPP statute provides procedural protections for defendants in defamation cases.",
                },
                jury_instructions=[
                    "CACI No. 1700 (Defamation—Essential Factual Elements)",
                    "CACI No. 1701 (Defamation—Publication)",
                    "CACI No. 1723 (Defamation—Qualified Privilege Defense)",
                ],
                case_law_examples=[
                    "Taus v. Loftus (2007) 40 Cal.4th 683 - defamatory meaning standard",
                    "Gilbert v. Sykes (2007) 147 Cal.App.4th 13 - Anti-SLAPP motion practice",
                    "Blatty v. New York Times Co. (1986) 42 Cal.3d 1033 - public figure standard",
                ],
                statutory_references=[
                    "Cal. Civ. Code § 44 - libel definition",
                    "Cal. Civ. Code § 46 - slander per se categories",
                    "Cal. Code Civ. Proc. § 425.16 - Anti-SLAPP statute",
                ],
            ),
        }

    def _initialize_element_breakdowns(self) -> Dict[str, Dict[str, ElementBreakdown]]:
        """Initialize comprehensive element breakdowns with sub-elements and decision trees"""
        return {
            "negligence": {
                "duty": ElementBreakdown(
                    element_id="ca_neg_duty_001",
                    element_name="duty",
                    primary_definition="A legal obligation to use reasonable care to avoid harm to others",
                    authority_citations=[
                        "Rowland v. Christian (1968) 69 Cal.2d 108",
                        "Ann M. v. Pacific Plaza Shopping Center (1993) 6 Cal.4th 666",
                        "CACI No. 401",
                    ],
                    sub_elements=[
                        {
                            "name": "duty_source",
                            "description": "Source of the duty (statutory, common law, special relationship)",
                            "questions": [
                                "Is the duty imposed by statute?",
                                "Does common law recognize a duty in these circumstances?",
                                "Is there a special relationship creating a duty?",
                            ],
                        },
                        {
                            "name": "duty_scope",
                            "description": "Scope and extent of the duty owed",
                            "questions": [
                                "What is the specific nature of the duty?",
                                "To whom is the duty owed?",
                                "Under what circumstances does the duty arise?",
                            ],
                        },
                        {
                            "name": "duty_standard",
                            "description": "Standard of care required",
                            "questions": [
                                "Is this ordinary negligence or professional malpractice?",
                                "Does a statute set the standard of care?",
                                "Is there a custom or industry standard?",
                            ],
                        },
                    ],
                    decision_trees=[
                        {
                            "root": "statutory_duty",
                            "condition": "Does a statute impose a specific duty?",
                            "true_path": "apply_statutory_standard",
                            "false_path": "check_common_law_duty",
                        },
                        {
                            "root": "check_common_law_duty",
                            "condition": "Does common law recognize a duty?",
                            "true_path": "apply_reasonable_care_standard",
                            "false_path": "check_special_relationship",
                        },
                    ],
                    burden_of_proof="preponderance",
                    proof_standards={
                        "professional_malpractice": "Expert testimony required to establish professional standard",
                        "statutory_violation": "Negligence per se if statute violated",
                        "premises_liability": "Duty varies based on plaintiff's status (invitee, licensee, trespasser)",
                    },
                    common_defenses=[
                        "No duty owed under circumstances",
                        "Duty limited by statute",
                        "Primary assumption of risk eliminates duty",
                    ],
                ),
                "breach": ElementBreakdown(
                    element_id="ca_neg_breach_001",
                    element_name="breach",
                    primary_definition="Failure to exercise the standard of care required by the duty",
                    authority_citations=[
                        "Christensen v. Superior Court (1991) 54 Cal.3d 868",
                        "Ortega v. Kmart Corp. (2001) 26 Cal.4th 1200",
                        "CACI No. 401",
                    ],
                    sub_elements=[
                        {
                            "name": "conduct_analysis",
                            "description": "Analysis of defendant's actual conduct",
                            "questions": [
                                "What did defendant do or fail to do?",
                                "Was defendant's conduct voluntary?",
                                "Are there competing explanations for defendant's conduct?",
                            ],
                        },
                        {
                            "name": "reasonable_person_standard",
                            "description": "Comparison to reasonable person standard",
                            "questions": [
                                "What would a reasonably prudent person have done?",
                                "Should defendant have foreseen the risk of harm?",
                                "Were there feasible alternatives to defendant's conduct?",
                            ],
                        },
                        {
                            "name": "statutory_compliance",
                            "description": "Compliance with applicable statutes and regulations",
                            "questions": [
                                "Did defendant violate any applicable statutes?",
                                "Was the violation excused or justified?",
                                "Does statutory compliance establish reasonable care?",
                            ],
                        },
                    ],
                    decision_trees=[
                        {
                            "root": "statutory_violation",
                            "condition": "Did defendant violate a safety statute?",
                            "true_path": "negligence_per_se_analysis",
                            "false_path": "reasonable_person_analysis",
                        },
                        {
                            "root": "negligence_per_se_analysis",
                            "condition": "Does negligence per se apply?",
                            "true_path": "breach_established",
                            "false_path": "reasonable_person_analysis",
                        },
                    ],
                    burden_of_proof="preponderance",
                    proof_standards={
                        "negligence_per_se": "Statutory violation establishes breach if statute designed to prevent type of harm",
                        "res_ipsa_loquitur": "Breach inferred from circumstances when accident wouldn't ordinarily occur without negligence",
                        "professional_standard": "Expert testimony required to establish professional standard of care",
                    },
                    common_defenses=[
                        "Conduct met reasonable person standard",
                        "Emergency doctrine applied",
                        "Statutory violation excused by emergency",
                    ],
                ),
                "causation": ElementBreakdown(
                    element_id="ca_neg_causation_001",
                    element_name="causation",
                    primary_definition="Defendant's breach must be a substantial factor in causing plaintiff's harm",
                    authority_citations=[
                        "Rutherford v. Owens-Illinois, Inc. (1997) 16 Cal.4th 953",
                        "Mitchell v. Gonzales (1991) 54 Cal.3d 1041",
                        "CACI No. 430",
                    ],
                    sub_elements=[
                        {
                            "name": "but_for_causation",
                            "description": "Cause in fact analysis",
                            "questions": [
                                "But for defendant's breach, would harm have occurred?",
                                "Were there multiple sufficient causes?",
                                "Can causation be established despite evidentiary gaps?",
                            ],
                        },
                        {
                            "name": "substantial_factor",
                            "description": "Substantial factor in bringing about harm",
                            "questions": [
                                "Was defendant's conduct a substantial factor?",
                                "How significant was defendant's contribution to harm?",
                                "Were there other substantial factors?",
                            ],
                        },
                        {
                            "name": "proximate_cause",
                            "description": "Legal causation and foreseeability",
                            "questions": [
                                "Was the harm a foreseeable consequence?",
                                "Were there intervening causes?",
                                "Was the manner of harm foreseeable?",
                            ],
                        },
                        {
                            "name": "intervening_causes",
                            "description": "Analysis of intervening and superseding causes",
                            "questions": [
                                "Were there intervening acts by third parties?",
                                "Were intervening causes foreseeable?",
                                "Do intervening causes break the causal chain?",
                            ],
                        },
                    ],
                    decision_trees=[
                        {
                            "root": "but_for_test",
                            "condition": "But for defendant's breach, would harm have occurred?",
                            "true_path": "no_but_for_causation",
                            "false_path": "substantial_factor_test",
                        },
                        {
                            "root": "substantial_factor_test",
                            "condition": "Was defendant's breach a substantial factor?",
                            "true_path": "check_proximate_cause",
                            "false_path": "no_causation",
                        },
                        {
                            "root": "check_proximate_cause",
                            "condition": "Was harm a foreseeable consequence?",
                            "true_path": "causation_established",
                            "false_path": "check_intervening_causes",
                        },
                    ],
                    burden_of_proof="preponderance",
                    proof_standards={
                        "multiple_causes": "Substantial factor test applies when multiple causes contribute to harm",
                        "loss_of_chance": "Special causation rules for medical malpractice loss of chance cases",
                        "toxic_tort": "Burden shifting may apply in toxic tort cases with multiple exposures",
                    },
                    common_defenses=[
                        "No but-for causation",
                        "Not a substantial factor",
                        "Unforeseeable harm",
                        "Superseding intervening cause",
                    ],
                ),
                "damages": ElementBreakdown(
                    element_id="ca_neg_damages_001",
                    element_name="damages",
                    primary_definition="Actual harm or injury resulting from defendant's breach",
                    authority_citations=[
                        "Civ. Code § 3333 - general damages",
                        "Civ. Code § 3281 - special damages",
                        "CACI No. 3903A - economic damages",
                    ],
                    sub_elements=[
                        {
                            "name": "economic_damages",
                            "description": "Quantifiable financial losses",
                            "questions": [
                                "What are plaintiff's medical expenses?",
                                "What income has plaintiff lost?",
                                "What is the cost of future medical care?",
                                "Are there other out-of-pocket expenses?",
                            ],
                        },
                        {
                            "name": "non_economic_damages",
                            "description": "Pain, suffering, and loss of enjoyment",
                            "questions": [
                                "What is the extent of plaintiff's pain and suffering?",
                                "How have injuries affected plaintiff's daily activities?",
                                "Is there permanent disability or disfigurement?",
                                "What is the psychological impact of injuries?",
                            ],
                        },
                        {
                            "name": "property_damage",
                            "description": "Damage to plaintiff's property",
                            "questions": [
                                "What property was damaged or destroyed?",
                                "What is the cost of repair or replacement?",
                                "Is there diminution in value?",
                                "What is the loss of use value?",
                            ],
                        },
                    ],
                    decision_trees=[
                        {
                            "root": "injury_severity",
                            "condition": "Are there significant physical injuries?",
                            "true_path": "calculate_medical_damages",
                            "false_path": "property_damage_only",
                        },
                        {
                            "root": "calculate_medical_damages",
                            "condition": "Are future medical expenses reasonably certain?",
                            "true_path": "include_future_medical",
                            "false_path": "past_medical_only",
                        },
                    ],
                    burden_of_proof="preponderance",
                    proof_standards={
                        "reasonable_certainty": "Future damages must be established with reasonable certainty",
                        "medical_testimony": "Medical expert testimony usually required for future medical expenses",
                        "economic_expert": "Economic expert may be needed for complex lost earnings calculations",
                    },
                    common_defenses=[
                        "No actual damages suffered",
                        "Pre-existing condition caused harm",
                        "Failure to mitigate damages",
                        "Damages not proximately caused by breach",
                    ],
                ),
            },
            "breach_of_contract": {
                "contract_formation": ElementBreakdown(
                    element_id="ca_contract_formation_001",
                    element_name="contract_formation",
                    primary_definition="Valid contract requiring offer, acceptance, consideration, capacity, and lawful object",
                    authority_citations=[
                        "Civ. Code § 1549 - contract requirements",
                        "Civ. Code § 1550 - essential elements",
                        "CACI No. 303",
                    ],
                    sub_elements=[
                        {
                            "name": "offer",
                            "description": "Clear and definite offer with essential terms",
                            "questions": [
                                "Was there a clear offer with definite terms?",
                                "Were the essential terms specified?",
                                "Was the offer communicated to the offeree?",
                                "Was the offer still open when accepted?",
                            ],
                        },
                        {
                            "name": "acceptance",
                            "description": "Unconditional acceptance of offer terms",
                            "questions": [
                                "Was the offer accepted unconditionally?",
                                "Was acceptance communicated properly?",
                                "Did acceptance occur before offer expired?",
                                "Was there a mirror image acceptance or counteroffer?",
                            ],
                        },
                        {
                            "name": "consideration",
                            "description": "Legally sufficient consideration exchanged",
                            "questions": [
                                "What consideration did each party provide?",
                                "Was consideration legally sufficient?",
                                "Was there a pre-existing duty issue?",
                                "Does promissory estoppel apply if no consideration?",
                            ],
                        },
                        {
                            "name": "capacity",
                            "description": "Legal capacity to enter contract",
                            "questions": [
                                "Did parties have legal capacity?",
                                "Were there any minors involved?",
                                "Was there mental incapacity?",
                                "Was there authority to bind entity?",
                            ],
                        },
                        {
                            "name": "lawful_object",
                            "description": "Contract purpose must be lawful",
                            "questions": [
                                "Is the contract purpose lawful?",
                                "Does contract violate public policy?",
                                "Are there illegal provisions that can be severed?",
                            ],
                        },
                    ],
                    decision_trees=[
                        {
                            "root": "written_contract",
                            "condition": "Is there a written contract?",
                            "true_path": "analyze_written_terms",
                            "false_path": "check_oral_contract_validity",
                        },
                        {
                            "root": "check_oral_contract_validity",
                            "condition": "Does Statute of Frauds apply?",
                            "true_path": "requires_written_contract",
                            "false_path": "oral_contract_valid",
                        },
                    ],
                    burden_of_proof="preponderance",
                    proof_standards={
                        "parol_evidence": "Parol evidence rule limits outside evidence for integrated written contracts",
                        "statute_of_frauds": "Certain contracts must be in writing to be enforceable",
                        "unconscionability": "Contracts may be unenforceable if unconscionable",
                    },
                    common_defenses=[
                        "No valid offer or acceptance",
                        "Lack of consideration",
                        "Statute of Frauds violation",
                        "Lack of capacity",
                        "Duress or undue influence",
                        "Unconscionability",
                    ],
                )
            },
        }

    def _initialize_question_generators(self) -> Dict[str, List[ProvableQuestion]]:
        """Initialize provable question generators for each cause of action element"""
        return {
            "negligence_duty": [
                ProvableQuestion(
                    question_id="neg_duty_001",
                    question_text="Did defendant owe plaintiff a duty of care?",
                    element_name="duty",
                    question_type="threshold",
                    evidence_types=[
                        "statutory authority",
                        "case law precedent",
                        "special relationship evidence",
                    ],
                    proof_methods=[
                        "legal authority citation",
                        "factual relationship establishment",
                        "expert testimony",
                    ],
                    common_challenges=[
                        "No duty owed",
                        "Limited scope of duty",
                        "Primary assumption of risk",
                    ],
                    practice_tips=[
                        "Research Rowland factors for duty analysis",
                        "Check for statutory duties",
                        "Consider special relationships (doctor-patient, etc.)",
                        "Review Ann M. decision for no-duty policy considerations",
                    ],
                    sub_questions=[
                        "What is the source of the alleged duty (statute, common law, relationship)?",
                        "To whom is this duty owed (general public, specific class, individual)?",
                        "Under what circumstances does this duty arise?",
                        "Are there any policy reasons to limit or deny duty?",
                    ],
                ),
                ProvableQuestion(
                    question_id="neg_duty_002",
                    question_text="What standard of care applied to defendant's conduct?",
                    element_name="duty",
                    question_type="legal",
                    evidence_types=[
                        "professional standards",
                        "industry custom",
                        "statutory requirements",
                        "expert testimony",
                    ],
                    proof_methods=[
                        "expert witness testimony",
                        "authoritative treatises",
                        "industry standards documentation",
                    ],
                    common_challenges=[
                        "Professional standard not established",
                        "Custom not proven",
                        "Emergency exception",
                    ],
                    practice_tips=[
                        "Retain qualified expert for professional malpractice cases",
                        "Research industry standards and best practices",
                        "Consider whether emergency doctrine applies",
                        "Check for statutory standards that set duty",
                    ],
                    sub_questions=[
                        "Is this ordinary negligence or professional malpractice?",
                        "What is the relevant professional or industry standard?",
                        "Did any emergency circumstances affect the standard?",
                        "Are there applicable statutory or regulatory standards?",
                    ],
                ),
            ],
            "negligence_causation": [
                ProvableQuestion(
                    question_id="neg_causation_001",
                    question_text="But for defendant's conduct, would the injury have occurred?",
                    element_name="causation",
                    question_type="factual",
                    evidence_types=[
                        "expert testimony",
                        "medical records",
                        "accident reconstruction",
                        "timeline evidence",
                    ],
                    proof_methods=[
                        "expert analysis",
                        "comparative scenarios",
                        "medical testimony",
                        "scientific testing",
                    ],
                    common_challenges=[
                        "Multiple causes",
                        "Pre-existing conditions",
                        "Insufficient evidence",
                    ],
                    practice_tips=[
                        "Use expert testimony for complex causation issues",
                        "Consider substantial factor test for multiple causes",
                        "Address pre-existing conditions proactively",
                        "Gather comprehensive medical records",
                    ],
                    sub_questions=[
                        "Would the accident have occurred without defendant's conduct?",
                        "Were there other sufficient causes of the harm?",
                        "How do pre-existing conditions affect causation analysis?",
                        "Is there sufficient evidence to establish but-for causation?",
                    ],
                ),
                ProvableQuestion(
                    question_id="neg_causation_002",
                    question_text="Was defendant's conduct a substantial factor in causing the harm?",
                    element_name="causation",
                    question_type="mixed",
                    evidence_types=[
                        "expert testimony",
                        "comparative fault evidence",
                        "multiple defendant evidence",
                    ],
                    proof_methods=[
                        "expert analysis",
                        "apportionment evidence",
                        "comparative negligence analysis",
                    ],
                    common_challenges=[
                        "Multiple defendants",
                        "Comparative fault",
                        "Apportionment issues",
                    ],
                    practice_tips=[
                        "Use substantial factor test when multiple causes present",
                        "Prepare for comparative fault analysis",
                        "Consider joint and several liability rules",
                        "Address each defendant's contribution separately",
                    ],
                    sub_questions=[
                        "How significant was defendant's contribution to the harm?",
                        "Were there other substantial factors?",
                        "How should fault be apportioned among multiple parties?",
                        "Does joint and several liability apply?",
                    ],
                ),
                ProvableQuestion(
                    question_id="neg_causation_003",
                    question_text="Was the harm a foreseeable consequence of defendant's breach?",
                    element_name="causation",
                    question_type="legal",
                    evidence_types=[
                        "foreseeability evidence",
                        "industry knowledge",
                        "prior incidents",
                    ],
                    proof_methods=[
                        "reasonableness analysis",
                        "industry standard testimony",
                        "prior similar incidents",
                    ],
                    common_challenges=[
                        "Unforeseeable harm",
                        "Intervening causes",
                        "Scope of liability",
                    ],
                    practice_tips=[
                        "Focus on type of harm, not specific manner",
                        "Research similar cases for foreseeability precedent",
                        "Address intervening causes proactively",
                        "Consider whether harm was within risk created by breach",
                    ],
                    sub_questions=[
                        "Was the type of harm foreseeable?",
                        "Were there intervening causes that broke the causal chain?",
                        "Was the harm within the scope of defendant's liability?",
                        "Should liability be limited based on policy considerations?",
                    ],
                ),
            ],
        }

    def _initialize_decision_trees(self) -> Dict[str, List[DecisionTreeNode]]:
        """Initialize decision tree logic for cascading legal analysis"""
        return {
            "negligence_duty_analysis": [
                DecisionTreeNode(
                    node_id="duty_root",
                    condition="Is there a statute imposing a specific duty?",
                    true_path="statutory_duty_analysis",
                    false_path="common_law_duty_analysis",
                    outcome=None,
                    legal_standard="Statutory duties create specific obligations",
                    authority_citation="Alarcon v. Murphy (1985) 201 Cal.App.3d 1159",
                    practice_notes=[
                        "Research all applicable statutes",
                        "Check for negligence per se application",
                    ],
                ),
                DecisionTreeNode(
                    node_id="statutory_duty_analysis",
                    condition="Is plaintiff within class protected by statute?",
                    true_path="statutory_duty_established",
                    false_path="common_law_duty_analysis",
                    outcome=None,
                    legal_standard="Statute must be designed to protect plaintiff class",
                    authority_citation="Elsner v. Uveges (2004) 34 Cal.4th 915",
                    practice_notes=[
                        "Identify protected class",
                        "Confirm harm type statute prevents",
                    ],
                ),
                DecisionTreeNode(
                    node_id="common_law_duty_analysis",
                    condition="Do Rowland factors support duty recognition?",
                    true_path="common_law_duty_established",
                    false_path="check_special_relationship",
                    outcome=None,
                    legal_standard="Rowland factors: foreseeability, certainty of harm, connection between conduct and injury, moral blame, policy considerations, burden of prevention",
                    authority_citation="Rowland v. Christian (1968) 69 Cal.2d 108",
                    practice_notes=[
                        "Analyze all Rowland factors",
                        "Consider policy arguments both ways",
                    ],
                ),
                DecisionTreeNode(
                    node_id="check_special_relationship",
                    condition="Is there a special relationship creating duty?",
                    true_path="special_relationship_duty",
                    false_path="no_duty_found",
                    outcome=None,
                    legal_standard="Special relationships can create affirmative duties",
                    authority_citation="Tarasoff v. Regents (1976) 17 Cal.3d 425",
                    practice_notes=[
                        "Common special relationships: therapist-patient, employer-employee, business-invitee"
                    ],
                ),
            ]
        }

    def generate_comprehensive_definition(
        self, cause_of_action: str, jurisdiction: str
    ) -> Optional[LegalDefinition]:
        """Generate comprehensive legal definition with authorities and clickable terms"""
        try:
            key = f"{jurisdiction}_{cause_of_action}"

            if (
                jurisdiction == "ca_state"
                and cause_of_action in self.california_definitions
            ):
                definition = self.california_definitions[cause_of_action]

                # Enhance with real-time research if needed
                if self.research_integration:
                    enhanced_definition = self._enhance_definition_with_research(
                        definition
                    )
                    return enhanced_definition

                return definition

            # Generate definition for other jurisdictions
            return self._generate_jurisdiction_specific_definition(
                cause_of_action, jurisdiction
            )

        except Exception as e:
            logger.exception(
                f"Failed to generate comprehensive definition for {cause_of_action} in {jurisdiction}: {e}"
            )
            return None

    def generate_element_breakdown(
        self, cause_of_action: str, element_name: str, jurisdiction: str
    ) -> Optional[ElementBreakdown]:
        """Generate detailed element breakdown with sub-elements and decision trees"""
        try:
            if cause_of_action in self.element_breakdowns:
                if element_name in self.element_breakdowns[cause_of_action]:
                    breakdown = self.element_breakdowns[cause_of_action][element_name]

                    # Enhance with jurisdiction-specific authorities
                    enhanced_breakdown = (
                        self._enhance_breakdown_with_jurisdiction_authorities(
                            breakdown, jurisdiction
                        )
                    )

                    return enhanced_breakdown

            # Generate breakdown for unlisted elements
            return self._generate_custom_element_breakdown(
                cause_of_action, element_name, jurisdiction
            )

        except Exception as e:
            logger.exception(
                f"Failed to generate element breakdown for {element_name} in {cause_of_action}: {e}"
            )
            return None

    def generate_provable_questions(
        self, cause_of_action: str, element_name: str
    ) -> List[ProvableQuestion]:
        """Generate attorney-ready provable questions for legal element"""
        try:
            question_key = f"{cause_of_action}_{element_name}"

            if question_key in self.question_generators:
                questions = self.question_generators[question_key]

                # Enhance questions with practice tips and recent case law
                enhanced_questions = []
                for question in questions:
                    enhanced_question = self._enhance_question_with_practice_guidance(
                        question
                    )
                    enhanced_questions.append(enhanced_question)

                return enhanced_questions

            # Generate default questions
            return self._generate_default_questions(cause_of_action, element_name)

        except Exception as e:
            logger.exception(
                f"Failed to generate provable questions for {element_name} in {cause_of_action}: {e}"
            )
            return []

    def build_decision_tree(
        self, cause_of_action: str, element_name: str, case_facts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Build interactive decision tree for element analysis"""
        try:
            tree_key = f"{cause_of_action}_{element_name}_analysis"

            if tree_key in self.decision_trees:
                nodes = self.decision_trees[tree_key]

                # Build interactive tree structure
                tree_structure = self._build_interactive_tree_structure(
                    nodes, case_facts
                )

                # Add fact-specific guidance
                fact_specific_tree = self._customize_tree_for_facts(
                    tree_structure, case_facts
                )

                return fact_specific_tree

            # Generate default decision tree
            return self._generate_default_decision_tree(cause_of_action, element_name)

        except Exception as e:
            logger.exception(
                f"Failed to build decision tree for {element_name} in {cause_of_action}: {e}"
            )
            return {}

    def _enhance_definition_with_research(
        self, definition: LegalDefinition
    ) -> LegalDefinition:
        """Enhance definition with real-time legal research"""
        # This would integrate with the legal research API to get current case law
        # For now, return the base definition
        return definition

    def _generate_jurisdiction_specific_definition(
        self, cause_of_action: str, jurisdiction: str
    ) -> Optional[LegalDefinition]:
        """Generate definition for non-California jurisdictions"""
        # Template for generating definitions for other jurisdictions
        return None

    def _enhance_breakdown_with_jurisdiction_authorities(
        self, breakdown: ElementBreakdown, jurisdiction: str
    ) -> ElementBreakdown:
        """Enhance element breakdown with jurisdiction-specific authorities"""
        if jurisdiction == "ca_state":
            # Add California-specific authorities and standards
            pass

        return breakdown

    def _generate_custom_element_breakdown(
        self, cause_of_action: str, element_name: str, jurisdiction: str
    ) -> Optional[ElementBreakdown]:
        """Generate breakdown for elements not in templates"""
        return None

    def _enhance_question_with_practice_guidance(
        self, question: ProvableQuestion
    ) -> ProvableQuestion:
        """Enhance provable question with current practice guidance"""
        # Add recent case law, practice tips, etc.
        return question

    def _generate_default_questions(
        self, cause_of_action: str, element_name: str
    ) -> List[ProvableQuestion]:
        """Generate default questions for unlisted elements"""
        return []

    def _build_interactive_tree_structure(
        self, nodes: List[DecisionTreeNode], case_facts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Build interactive decision tree structure"""
        return {}

    def _customize_tree_for_facts(
        self, tree_structure: Dict[str, Any], case_facts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Customize decision tree based on case facts"""
        return tree_structure

    def _generate_default_decision_tree(
        self, cause_of_action: str, element_name: str
    ) -> Dict[str, Any]:
        """Generate default decision tree for unlisted elements"""
        return {}


if __name__ == "__main__":
    # Test the definition engine
    import sys

    logging.basicConfig(level=logging.INFO)

    from lawyerfactory.kg.enhanced_graph import EnhancedKnowledgeGraph

    from src.lawyerfactory.knowledge_graph.core.jurisdiction_manager import (
        JurisdictionManager,
    )

    try:
        kg = EnhancedKnowledgeGraph("test_definition_engine.db")
        jurisdiction_manager = JurisdictionManager(kg)

        # Initialize with mock research integration for testing
        definition_engine = CauseOfActionDefinitionEngine(
            kg, jurisdiction_manager, None, None
        )

        # Test California negligence definition
        if jurisdiction_manager.select_jurisdiction("ca_state"):
            definition = definition_engine.generate_comprehensive_definition(
                "negligence", "ca_state"
            )
            if definition:
                print("Generated definition for negligence:")
                print(f"Primary definition: {definition.primary_definition}")
                print(f"Authority citations: {definition.authority_citations}")
                print(f"Clickable terms: {list(definition.clickable_terms.keys())}")

            # Test element breakdown
            duty_breakdown = definition_engine.generate_element_breakdown(
                "negligence", "duty", "ca_state"
            )
            if duty_breakdown:
                print("\nGenerated element breakdown for duty:")
                print(f"Definition: {duty_breakdown.primary_definition}")
                print(f"Sub-elements: {len(duty_breakdown.sub_elements)}")

            # Test provable questions
            questions = definition_engine.generate_provable_questions(
                "negligence", "duty"
            )
            print(f"\nGenerated {len(questions)} provable questions for duty element")
            for q in questions:
                print(f"- {q.question_text}")

    except Exception as e:
        print(f"Test failed: {e}")
        sys.exit(1)
    finally:
        kg.close()
