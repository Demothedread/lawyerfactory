"""
# Script Name: cascading_decision_tree_engine.py
# Description: Cascading Decision Tree Engine for Claims Matrix Interactive legal analysis with clickable keyword expansion and fact-driven decision paths
# Relationships:
#   - Entity Type: Engine
#   - Directory Group: Workflow
#   - Group Tags: null
Cascading Decision Tree Engine for Claims Matrix
Interactive legal analysis with clickable keyword expansion and fact-driven decision paths
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from cause_of_action_definition_engine import CauseOfActionDefinitionEngine
from enhanced_knowledge_graph import EnhancedKnowledgeGraph

from src.lawyerfactory.knowledge_graph.core.jurisdiction_manager import JurisdictionManager

logger = logging.getLogger(__name__)


class DecisionOutcome(Enum):
    """Possible outcomes of decision tree analysis"""
    ELEMENT_SATISFIED = "element_satisfied"
    ELEMENT_NOT_SATISFIED = "element_not_satisfied"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    REQUIRES_EXPERT_TESTIMONY = "requires_expert_testimony"
    AFFIRMATIVE_DEFENSE_AVAILABLE = "affirmative_defense_available"
    FURTHER_DISCOVERY_NEEDED = "further_discovery_needed"


@dataclass
class ClickableTerm:
    """Represents a clickable legal term with expandable definition"""
    term_id: str
    term_text: str
    primary_definition: str
    authority_citations: List[str]
    related_terms: List[str]
    case_examples: List[str]
    practice_notes: List[str]
    jurisdiction_variations: Dict[str, str]
    sub_terms: List[str]  # Terms within this definition that are also clickable
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class DecisionPathResult:
    """Result of following a decision tree path"""
    path_id: str
    decisions_made: List[Dict[str, Any]]
    final_outcome: DecisionOutcome
    confidence_score: float
    supporting_evidence: List[str]
    missing_evidence: List[str]
    recommended_actions: List[str]
    alternative_theories: List[str]
    practice_guidance: List[str]


@dataclass
class FactPattern:
    """Represents a fact pattern for decision tree matching"""
    pattern_id: str
    fact_elements: List[str]
    legal_significance: str
    common_outcomes: List[str]
    distinguishing_factors: List[str]
    precedent_cases: List[str]


class CascadingDecisionTreeEngine:
    """Interactive decision tree engine with clickable term expansion"""
    
    def __init__(self, enhanced_kg: EnhancedKnowledgeGraph,
                 jurisdiction_manager: JurisdictionManager,
                 definition_engine: CauseOfActionDefinitionEngine):
        self.kg = enhanced_kg
        self.jurisdiction_manager = jurisdiction_manager
        self.definition_engine = definition_engine
        
        # Initialize clickable terms dictionary
        self.clickable_terms = self._initialize_clickable_terms()
        
        # Initialize decision tree templates
        self.decision_templates = self._initialize_decision_templates()
        
        # Initialize fact patterns
        self.fact_patterns = self._initialize_fact_patterns()
        
        logger.info("Cascading Decision Tree Engine initialized")
    
    def _initialize_clickable_terms(self) -> Dict[str, ClickableTerm]:
        """Initialize comprehensive clickable legal terms dictionary"""
        return {
            'duty_of_care': ClickableTerm(
                term_id='ca_duty_of_care_001',
                term_text='duty of care',
                primary_definition=(
                    "A legal obligation imposed on an individual requiring adherence to a "
                    "**standard of reasonable care** while performing acts that could foreseeably "
                    "harm others. The duty is established through **statutory law**, **common law**, "
                    "or **special relationships** between parties."
                ),
                authority_citations=[
                    'Rowland v. Christian (1968) 69 Cal.2d 108, 112',
                    'Cal. Civ. Code § 1714(a)',
                    'Ann M. v. Pacific Plaza Shopping Center (1993) 6 Cal.4th 666'
                ],
                related_terms=['standard of care', 'reasonable person', 'foreseeability', 'special relationship'],
                case_examples=[
                    'Rowland v. Christian - landowner duty to all entrants',
                    'Tarasoff v. Regents - therapist duty to warn third parties',
                    'Knight v. Jewett - sports participants\' limited duty'
                ],
                practice_notes=[
                    'Research Rowland factors for novel duty questions',
                    'Check for statutory duties that may apply',
                    'Consider policy arguments for limiting duty',
                    'Distinguish between misfeasance and nonfeasance'
                ],
                jurisdiction_variations={
                    'federal': 'Federal common law follows similar duty principles but may apply different policy considerations',
                    'ny_state': 'New York follows traditional categories approach rather than Rowland factors'
                },
                sub_terms=['standard of reasonable care', 'statutory law', 'common law', 'special relationships']
            ),
            
            'standard_of_reasonable_care': ClickableTerm(
                term_id='ca_std_care_001',
                term_text='standard of reasonable care',
                primary_definition=(
                    "The degree of care that a **reasonably prudent person** would exercise "
                    "in similar circumstances. For **professionals**, the standard is that of "
                    "a reasonably competent member of the profession. The standard is **objective**, "
                    "not based on the particular defendant's abilities or limitations."
                ),
                authority_citations=[
                    'Landeros v. Flood (1976) 17 Cal.3d 399',
                    'Flowers v. Torrance Memorial Medical Center (1994) 8 Cal.4th 992',
                    'CACI No. 401'
                ],
                related_terms=['reasonably prudent person', 'professional standard', 'custom and usage'],
                case_examples=[
                    'Landeros v. Flood - physician standard of care',
                    'Lucas v. Hamm - attorney malpractice standard',
                    'Christensen v. Superior Court - emergency room standard'
                ],
                practice_notes=[
                    'Retain qualified expert for professional malpractice cases',
                    'Custom evidence is admissible but not conclusive',
                    'Emergency doctrine may modify standard',
                    'Statutory compliance may be evidence of reasonable care'
                ],
                jurisdiction_variations={
                    'federal': 'Federal courts apply similar reasonable person standard',
                    'professional': 'Professional standards require expert testimony to establish'
                },
                sub_terms=['reasonably prudent person', 'professionals', 'objective']
            ),
            
            'reasonably_prudent_person': ClickableTerm(
                term_id='ca_reasonable_person_001',
                term_text='reasonably prudent person',
                primary_definition=(
                    "A hypothetical person in the defendant's position who exercises **average care**, "
                    "**skill**, and **judgment** in conduct that society recognizes as necessary to "
                    "protect others from **unreasonable risk** of harm. This is an **objective standard** "
                    "that does not account for defendant's particular limitations, experience, or intelligence."
                ),
                authority_citations=[
                    'Vaughan v. Menlove (1837) 3 Bing.(N.C.) 468 [foundational case]',
                    'Roberts v. State of California (1999) 188 Cal.App.4th 1173',
                    'CACI No. 401'
                ],
                related_terms=['objective standard', 'unreasonable risk', 'community standards'],
                case_examples=[
                    'Vaughan v. Menlove - objective standard established',
                    'Delair v. McAdoo - reasonable person considers weather conditions',
                    'Fletcher v. Aberdeen - reasonable person accounts for known hazards'
                ],
                practice_notes=[
                    'Focus on what defendant should have done, not defendant\'s subjective state',
                    'Consider circumstances known or reasonably knowable to defendant',
                    'Physical disabilities may be considered, mental ones generally not',
                    'Children judged by standard of reasonable child of same age/experience'
                ],
                jurisdiction_variations={
                    'children': 'Children under 5 generally incapable of negligence; 5-18 judged by child standard',
                    'professionals': 'Professionals judged by reasonable member of their profession'
                },
                sub_terms=['average care', 'skill', 'judgment', 'unreasonable risk', 'objective standard']
            ),
            
            'substantial_factor': ClickableTerm(
                term_id='ca_substantial_factor_001',
                term_text='substantial factor',
                primary_definition=(
                    "A cause that plays an important part in bringing about the harm, even if "
                    "other causes also contribute. The conduct need not be the **sole cause** or "
                    "even the **primary cause**, but must be more than a **trivial** or **insignificant** "
                    "contribution to the result. Used when multiple causes contribute to harm."
                ),
                authority_citations=[
                    'Mitchell v. Gonzales (1991) 54 Cal.3d 1041',
                    'Rutherford v. Owens-Illinois, Inc. (1997) 16 Cal.4th 953',
                    'CACI No. 430'
                ],
                related_terms=['but-for causation', 'proximate cause', 'multiple sufficient causes'],
                case_examples=[
                    'Mitchell v. Gonzales - substantial factor in medical malpractice',
                    'Rutherford v. Owens-Illinois - asbestos exposure substantial factor',
                    'Summers v. Tice - alternative liability for substantial factor'
                ],
                practice_notes=[
                    'Use substantial factor test when multiple causes present',
                    'Expert testimony often needed to establish substantial factor',
                    'Consider comparative fault implications',
                    'Address pre-existing conditions that may be contributing factors'
                ],
                jurisdiction_variations={
                    'toxic_tort': 'Special rules apply for toxic exposure cases',
                    'medical_malpractice': 'Lost chance doctrine modifies substantial factor test'
                },
                sub_terms=['sole cause', 'primary cause', 'trivial', 'insignificant']
            ),
            
            'material_breach': ClickableTerm(
                term_id='ca_material_breach_001',
                term_text='material breach',
                primary_definition=(
                    "A failure to perform that goes to the **essence of the contract** and "
                    "defeats the **object of the parties** in making the agreement. A material "
                    "breach excuses the non-breaching party from further performance and allows "
                    "recovery of damages. Distinguished from **minor breach** which does not "
                    "excuse performance but allows damages."
                ),
                authority_citations=[
                    'Carma Developers, Inc. v. Marathon Dev. Cal. (1992) 2 Cal.4th 342',
                    'Universal Sales Corp. v. California Press Manufacturing Co. (1942) 20 Cal.2d 751',
                    'CACI No. 303'
                ],
                related_terms=['essence of contract', 'substantial performance', 'minor breach'],
                case_examples=[
                    'Carma Developers - factors for determining material breach',
                    'Jacob & Youngs v. Kent - minor breach does not excuse performance',
                    'Walker v. Walker - time of performance materiality'
                ],
                practice_notes=[
                    'Consider: extent of non-performance, hardship to breaching party, willful vs. inadvertent',
                    'Time is not of essence unless contract specifies or circumstances require',
                    'Perfect tender rule applies to sale of goods under UCC',
                    'Cure provisions may prevent breach from becoming material'
                ],
                jurisdiction_variations={
                    'ucc': 'Perfect tender rule under UCC Article 2 for sale of goods',
                    'real_estate': 'Time often of essence in real estate transactions'
                },
                sub_terms=['essence of the contract', 'object of the parties', 'minor breach']
            ),
            
            'justifiable_reliance': ClickableTerm(
                term_id='ca_justifiable_reliance_001',
                term_text='justifiable reliance',
                primary_definition=(
                    "Reliance that is **reasonable under the circumstances** and not the result of "
                    "plaintiff's **failure to use ordinary care**. The plaintiff must show actual "
                    "reliance on the misrepresentation and that such reliance was a **substantial factor** "
                    "in plaintiff's decision to act. Reliance is not justifiable if the truth was "
                    "**readily ascertainable** by plaintiff."
                ),
                authority_citations=[
                    'Alliance Mortgage Co. v. Rothwell (1995) 10 Cal.4th 1226',
                    'Seeger v. Odell (1987) 18 Cal.3d 619',
                    'CACI No. 1900'
                ],
                related_terms=['reasonable reliance', 'due diligence', 'obvious falsity'],
                case_examples=[
                    'Alliance Mortgage - sophisticated party\'s duty to investigate',
                    'Seeger v. Odell - reliance on attorney\'s misrepresentations',
                    'Small v. Fritz Companies - reliance must be reasonable'
                ],
                practice_notes=[
                    'Sophistication of plaintiff affects reasonableness of reliance',
                    'Obvious or easily discoverable falsity defeats justifiable reliance',
                    'Independent investigation does not negate reliance if misrep was factor',
                    'Consider whether plaintiff had equal access to information'
                ],
                jurisdiction_variations={
                    'sophisticated_parties': 'Higher standard for sophisticated commercial parties',
                    'fiduciary': 'Greater reliance justified in fiduciary relationships'
                },
                sub_terms=['reasonable under the circumstances', 'failure to use ordinary care', 'substantial factor', 'readily ascertainable']
            ),
            
            'extreme_and_outrageous': ClickableTerm(
                term_id='ca_extreme_outrageous_001',
                term_text='extreme and outrageous',
                primary_definition=(
                    "Conduct that exceeds **all bounds usually tolerated by decent society** "
                    "and is of such a nature as to be regarded as **atrocious** and **utterly intolerable**. "
                    "The conduct must be more than **insulting**, **indecent**, **annoying**, "
                    "**petty oppression**, or other trivialities. Liability arises only where "
                    "conduct is so outrageous in character and extreme in degree as to go beyond "
                    "**all possible bounds of decency**."
                ),
                authority_citations=[
                    'Hughes v. Pair (2009) 46 Cal.4th 1035',
                    'Christensen v. Superior Court (1991) 54 Cal.3d 868',
                    'CACI No. 1600'
                ],
                related_terms=['civilized community', 'reasonable person', 'social utility'],
                case_examples=[
                    'Hughes v. Pair - sexual harassment not per se extreme and outrageous',
                    'Christensen v. Superior Court - supervisor\'s conduct toward subordinate',
                    'McDaniel v. Gile - debt collection practices'
                ],
                practice_notes=[
                    'High bar - most conduct does not meet this standard',
                    'Consider relationship between parties (supervisor/subordinate, etc.)',
                    'Repeated pattern of conduct may be more likely extreme/outrageous',
                    'Context matters - same conduct may be worse in certain settings'
                ],
                jurisdiction_variations={
                    'workplace': 'Workplace conduct may more readily satisfy standard',
                    'debt_collection': 'Debt collection practices subject to statutory limits'
                },
                sub_terms=['all bounds usually tolerated by decent society', 'atrocious', 'utterly intolerable', 'insulting', 'indecent', 'annoying', 'petty oppression', 'all possible bounds of decency']
            )
        }
    
    def _initialize_decision_templates(self) -> Dict[str, List[Dict[str, Any]]]:
        """Initialize decision tree templates for common legal analyses"""
        return {
            'negligence_duty_analysis': [
                {
                    'id': 'duty_threshold',
                    'question': 'Is there a **statute** imposing a specific duty of care?',
                    'type': 'threshold',
                    'yes_path': 'statutory_duty_analysis',
                    'no_path': 'common_law_duty_analysis',
                    'authority': 'Alarcon v. Murphy (1985) 201 Cal.App.3d 1159',
                    'guidance': [
                        'Research Vehicle Code, Health & Safety Code, Civil Code',
                        'Look for duties imposed on specific categories (drivers, property owners, etc.)',
                        'Consider whether negligence per se applies'
                    ]
                },
                {
                    'id': 'statutory_duty_analysis',
                    'question': 'Is plaintiff within the **class of persons** the statute was designed to protect?',
                    'type': 'legal',
                    'yes_path': 'statutory_harm_analysis',
                    'no_path': 'common_law_duty_analysis',
                    'authority': 'Elsner v. Uveges (2004) 34 Cal.4th 915',
                    'guidance': [
                        'Identify the protected class from statutory language',
                        'Consider legislative intent and purpose',
                        'Check case law interpreting the specific statute'
                    ]
                },
                {
                    'id': 'statutory_harm_analysis',
                    'question': 'Is the harm that occurred the **type of harm** the statute was designed to prevent?',
                    'type': 'legal',
                    'yes_path': 'statutory_duty_established',
                    'no_path': 'common_law_duty_analysis',
                    'authority': 'Elsner v. Uveges (2004) 34 Cal.4th 915',
                    'guidance': [
                        'Match actual harm to statutory purpose',
                        'Consider whether harm was within contemplated risks',
                        'Review legislative history if available'
                    ]
                },
                {
                    'id': 'common_law_duty_analysis',
                    'question': 'Under **Rowland factors**, should a duty of care be imposed?',
                    'type': 'multi_factor',
                    'factors': [
                        'Foreseeability of harm',
                        'Degree of certainty of injury',
                        'Closeness of connection between conduct and injury',
                        'Moral blame attached to conduct',
                        'Policy of preventing future harm',
                        'Extent of burden of imposing duty',
                        'Consequences to community',
                        'Availability of insurance'
                    ],
                    'yes_path': 'common_law_duty_established',
                    'no_path': 'check_special_relationship',
                    'authority': 'Rowland v. Christian (1968) 69 Cal.2d 108',
                    'guidance': [
                        'Analyze each Rowland factor systematically',
                        'Consider policy arguments both for and against duty',
                        'Review similar cases in jurisdiction'
                    ]
                },
                {
                    'id': 'check_special_relationship',
                    'question': 'Is there a **special relationship** creating an affirmative duty?',
                    'type': 'factual',
                    'relationships': [
                        'Common carrier - passenger',
                        'Innkeeper - guest',
                        'Business - invitee',
                        'Employer - employee',
                        'School - student',
                        'Therapist - patient',
                        'Jailer - prisoner'
                    ],
                    'yes_path': 'special_relationship_duty',
                    'no_path': 'no_duty_found',
                    'authority': 'Tarasoff v. Regents (1976) 17 Cal.3d 425',
                    'guidance': [
                        'Identify nature of relationship',
                        'Consider whether relationship creates control or dependence',
                        'Review cases involving similar relationships'
                    ]
                }
            ],
            
            'negligence_causation_analysis': [
                {
                    'id': 'but_for_threshold',
                    'question': '**But for** defendant\'s conduct, would the harm have occurred?',
                    'type': 'threshold',
                    'yes_path': 'no_but_for_causation',
                    'no_path': 'substantial_factor_analysis',
                    'authority': 'Mitchell v. Gonzales (1991) 54 Cal.3d 1041',
                    'guidance': [
                        'Consider hypothetical scenario without defendant\'s conduct',
                        'Look for alternative sufficient causes',
                        'Expert testimony may be needed for complex causation'
                    ]
                },
                {
                    'id': 'substantial_factor_analysis',
                    'question': 'Was defendant\'s conduct a **substantial factor** in causing the harm?',
                    'type': 'factual',
                    'yes_path': 'proximate_cause_analysis',
                    'no_path': 'no_factual_causation',
                    'authority': 'Rutherford v. Owens-Illinois, Inc. (1997) 16 Cal.4th 953',
                    'guidance': [
                        'Consider magnitude of defendant\'s contribution',
                        'Compare to other contributing factors',
                        'Use when multiple sufficient causes present'
                    ]
                },
                {
                    'id': 'proximate_cause_analysis',
                    'question': 'Was the harm a **foreseeable consequence** of defendant\'s conduct?',
                    'type': 'legal',
                    'yes_path': 'check_intervening_causes',
                    'no_path': 'unforeseeable_harm',
                    'authority': 'Bigbee v. Pacific Tel. & Tel. Co. (1983) 34 Cal.3d 49',
                    'guidance': [
                        'Focus on type of harm, not specific manner',
                        'Consider whether harm was within risk created',
                        'Review similar cases for foreseeability precedent'
                    ]
                },
                {
                    'id': 'check_intervening_causes',
                    'question': 'Were there **intervening causes** that break the causal chain?',
                    'type': 'factual',
                    'superseding_factors': [
                        'Unforeseeable criminal acts by third parties',
                        'Extraordinary natural phenomena',
                        'Highly unusual responses by plaintiff',
                        'Independent negligent acts not foreseeable'
                    ],
                    'yes_path': 'superseding_cause_analysis',
                    'no_path': 'proximate_cause_established',
                    'authority': 'Lugtu v. California Highway Patrol (2001) 26 Cal.4th 703',
                    'guidance': [
                        'Determine if intervening cause was foreseeable',
                        'Consider whether defendant\'s conduct increased risk of intervening cause',
                        'Analyze whether intervening cause was independent or dependent'
                    ]
                }
            ],
            
            'contract_formation_analysis': [
                {
                    'id': 'written_contract_check',
                    'question': 'Is there a **written contract** between the parties?',
                    'type': 'threshold',
                    'yes_path': 'written_contract_analysis',
                    'no_path': 'oral_contract_analysis',
                    'authority': 'Wolf v. Walt Disney Pictures (2008) 162 Cal.App.4th 1107',
                    'guidance': [
                        'Identify all written documents that might constitute contract',
                        'Consider email exchanges and electronic communications',
                        'Look for signature or other manifestation of assent'
                    ]
                },
                {
                    'id': 'oral_contract_analysis',
                    'question': 'Does the **Statute of Frauds** require this contract to be in writing?',
                    'type': 'legal',
                    'statute_of_frauds_categories': [
                        'Contracts not to be performed within one year',
                        'Contracts for sale of goods $500 or more',
                        'Contracts for sale of real property',
                        'Contracts to answer for debt of another',
                        'Contracts in consideration of marriage'
                    ],
                    'yes_path': 'statute_of_frauds_compliance',
                    'no_path': 'oral_contract_elements',
                    'authority': 'Civ. Code § 1624',
                    'guidance': [
                        'Analyze contract terms to determine if within statute',
                        'Consider whether partial performance removes from statute',
                        'Look for written confirmation or admissions'
                    ]
                },
                {
                    'id': 'oral_contract_elements',
                    'question': 'Are the essential elements of contract formation present?',
                    'type': 'multi_element',
                    'elements': {
                        'offer': 'Was there a clear offer with definite terms?',
                        'acceptance': 'Was the offer accepted unconditionally?',
                        'consideration': 'Was there legally sufficient consideration?',
                        'capacity': 'Did parties have legal capacity?',
                        'lawful_object': 'Was the contract purpose lawful?'
                    },
                    'yes_path': 'valid_oral_contract',
                    'no_path': 'contract_formation_failed',
                    'authority': 'Civ. Code § 1550',
                    'guidance': [
                        'Each element must be proven by preponderance',
                        'Consider parol evidence rule limitations',
                        'Look for course of dealing evidence'
                    ]
                }
            ]
        }
    
    def _initialize_fact_patterns(self) -> Dict[str, FactPattern]:
        """Initialize common fact patterns that trigger specific legal analyses"""
        return {
            'auto_accident_negligence': FactPattern(
                pattern_id='auto_001',
                fact_elements=[
                    'motor vehicle collision',
                    'traffic violation',
                    'personal injury',
                    'property damage'
                ],
                legal_significance='Likely negligence per se if traffic law violated',
                common_outcomes=[
                    'Duty established by Vehicle Code',
                    'Breach shown by traffic violation',
                    'Causation usually clear in rear-end collisions',
                    'Comparative fault possible'
                ],
                distinguishing_factors=[
                    'Emergency circumstances',
                    'Sudden mechanical failure',
                    'Act of God (weather, earthquake)',
                    'Criminal act of third party'
                ],
                precedent_cases=[
                    'Newing v. Cheatham (1975) 15 Cal.3d 351 - sudden emergency',
                    'Leo v. Dunham (1953) 41 Cal.2d 712 - rear-end collision presumption'
                ]
            ),
            
            'premises_liability': FactPattern(
                pattern_id='premises_001',
                fact_elements=[
                    'injury on defendant\'s property',
                    'dangerous condition',
                    'plaintiff\'s status (invitee/licensee/trespasser)',
                    'notice actual or constructive'
                ],
                legal_significance='Duty varies based on plaintiff\'s status and defendant\'s knowledge',
                common_outcomes=[
                    'Business invitees owed highest duty',
                    'Licensees protected against known dangers',
                    'Trespassers generally owed no duty',
                    'Notice requirement for dangerous conditions'
                ],
                distinguishing_factors=[
                    'Obvious and apparent dangers',
                    'Criminal acts of third parties',
                    'Natural conditions vs. artificial',
                    'Active vs. passive negligence'
                ],
                precedent_cases=[
                    'Rowland v. Christian (1968) 69 Cal.2d 108 - duty to all entrants',
                    'Ann M. v. Pacific Plaza (1993) 6 Cal.4th 666 - duty to protect from crime'
                ]
            ),
            
            'medical_malpractice': FactPattern(
                pattern_id='medical_001',
                fact_elements=[
                    'physician-patient relationship',
                    'medical treatment or advice',
                    'adverse outcome',
                    'departure from standard of care'
                ],
                legal_significance='Professional standard of care requires expert testimony',
                common_outcomes=[
                    'Expert testimony required to establish standard',
                    'Informed consent issues possible',
                    'Causation complex in medical context',
                    'Damage caps may apply'
                ],
                distinguishing_factors=[
                    'Emergency room treatment',
                    'Referral vs. treating physician',
                    'Informed consent obtained',
                    'Complications vs. negligence'
                ],
                precedent_cases=[
                    'Landeros v. Flood (1976) 17 Cal.3d 399 - standard of care',
                    'Cobbs v. Grant (1972) 8 Cal.3d 229 - informed consent'
                ]
            ),
            
            'contract_breach_sale_goods': FactPattern(
                pattern_id='contract_goods_001',
                fact_elements=[
                    'sale of goods contract',
                    'non-conforming delivery',
                    'rejection or acceptance',
                    'commercial context'
                ],
                legal_significance='UCC Article 2 governs with perfect tender rule',
                common_outcomes=[
                    'Perfect tender rule allows rejection for any non-conformity',
                    'Acceptance limits remedies',
                    'Cure rights for seller',
                    'Cover damages for buyer'
                ],
                distinguishing_factors=[
                    'Installment contract',
                    'Acceptance despite non-conformity',
                    'Waiver of perfect tender',
                    'Course of dealing modifications'
                ],
                precedent_cases=[
                    'Mexia v. Rinker Materials (2013) 220 Cal.App.4th 1102 - UCC perfect tender',
                    'Weil & Duffy v. American Dye Works (1950) 37 Cal.2d 44 - substantial performance'
                ]
            )
        }
    
    def expand_clickable_term(self, term_text: str, context: Optional[str] = None) -> Optional[ClickableTerm]:
        """Expand a clickable legal term with full definition and related information"""
        try:
            term_key = term_text.lower().replace(' ', '_')
            
            if term_key in self.clickable_terms:
                term = self.clickable_terms[term_key]
                
                # Customize based on context if provided
                if context:
                    term = self._contextualize_term_definition(term, context)
                
                return term
            
            # Search for partial matches or synonyms
            return self._find_similar_term(term_text)
            
        except Exception as e:
            logger.exception(f"Failed to expand clickable term '{term_text}': {e}")
            return None
    
    def build_decision_tree(self, cause_of_action: str, element_name: str, 
                          case_facts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build interactive decision tree for legal element analysis"""
        try:
            template_key = f"{cause_of_action}_{element_name}_analysis"
            
            if template_key in self.decision_templates:
                template = self.decision_templates[template_key]
                
                # Build interactive tree structure
                tree = self._build_interactive_tree(template, case_facts)
                
                # Add fact-specific guidance
                tree = self._add_fact_specific_guidance(tree, case_facts)
                
                # Include clickable terms
                tree = self._add_clickable_terms_to_tree(tree)
                
                return tree
            
            # Generate default tree structure
            return self._generate_default_tree(cause_of_action, element_name, case_facts)
            
        except Exception as e:
            logger.exception(f"Failed to build decision tree for {element_name} in {cause_of_action}: {e}")
            return {}
    
    def analyze_decision_path(self, tree_id: str, decisions: List[Dict[str, Any]], 
                            case_facts: List[Dict[str, Any]]) -> DecisionPathResult:
        """Analyze a complete decision path and provide outcome assessment"""
        try:
            path_id = f"{tree_id}_{uuid.uuid4().hex[:8]}"
            
            # Follow decision path
            final_outcome = self._determine_final_outcome(decisions, case_facts)
            
            # Calculate confidence score
            confidence_score = self._calculate_path_confidence(decisions, case_facts)
            
            # Identify supporting and missing evidence
            supporting_evidence, missing_evidence = self._analyze_evidence_gaps(decisions, case_facts)
            
            # Generate recommendations
            recommended_actions = self._generate_action_recommendations(final_outcome, missing_evidence)
            
            # Identify alternative theories
            alternative_theories = self._identify_alternative_theories(decisions, case_facts)
            
            # Provide practice guidance
            practice_guidance = self._generate_practice_guidance(final_outcome, decisions)
            
            return DecisionPathResult(
                path_id=path_id,
                decisions_made=decisions,
                final_outcome=final_outcome,
                confidence_score=confidence_score,
                supporting_evidence=supporting_evidence,
                missing_evidence=missing_evidence,
                recommended_actions=recommended_actions,
                alternative_theories=alternative_theories,
                practice_guidance=practice_guidance
            )
            
        except Exception as e:
            logger.exception(f"Failed to analyze decision path for tree {tree_id}: {e}")
            return DecisionPathResult(
                path_id=f"error_{uuid.uuid4().hex[:8]}",
                decisions_made=decisions,
                final_outcome=DecisionOutcome.INSUFFICIENT_EVIDENCE,
                confidence_score=0.0,
                supporting_evidence=[],
                missing_evidence=['Analysis failed due to system error'],
                recommended_actions=['Retry analysis or consult with technical support'],
                alternative_theories=[],
                practice_guidance=['System error occurred during analysis']
            )
    
    def match_fact_patterns(self, case_facts: List[Dict[str, Any]]) -> List[Tuple[FactPattern, float]]:
        """Match case facts to known legal fact patterns"""
        try:
            pattern_matches = []
            
            # Extract fact keywords from case
            fact_keywords = self._extract_fact_keywords(case_facts)
            
            for pattern_id, pattern in self.fact_patterns.items():
                # Calculate similarity score
                similarity = self._calculate_pattern_similarity(fact_keywords, pattern.fact_elements)
                
                if similarity > 0.3:  # Minimum threshold
                    pattern_matches.append((pattern, similarity))
            
            # Sort by similarity score
            pattern_matches.sort(key=lambda x: x[1], reverse=True)
            
            return pattern_matches
            
        except Exception as e:
            logger.exception(f"Failed to match fact patterns: {e}")
            return []
    
    def _contextualize_term_definition(self, term: ClickableTerm, context: str) -> ClickableTerm:
        """Customize term definition based on legal context"""
        # Add context-specific information
        return term
    
    def _find_similar_term(self, term_text: str) -> Optional[ClickableTerm]:
        """Find similar terms using fuzzy matching"""
        # Simple implementation - could be enhanced with NLP
        for key, term in self.clickable_terms.items():
            if term_text.lower() in term.term_text.lower() or term.term_text.lower() in term_text.lower():
                return term
        return None
    
    def _build_interactive_tree(self, template: List[Dict[str, Any]], 
                              case_facts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build interactive tree structure from template"""
        tree = {
            'root': template[0]['id'],
            'nodes': {},
            'current_node': template[0]['id'],
            'completed_paths': [],
            'metadata': {
                'case_facts_count': len(case_facts),
                'tree_type': 'legal_analysis',
                'created_at': datetime.now().isoformat()
            }
        }
        
        # Build node structure
        for node in template:
            tree['nodes'][node['id']] = {
                'question': node['question'],
                'type': node['type'],
                'authority': node.get('authority', ''),
                'guidance': node.get('guidance', []),
                'yes_path': node.get('yes_path'),
                'no_path': node.get('no_path'),
                'factors': node.get('factors', []),
                'elements': node.get('elements', {}),
                'relationships': node.get('relationships', [])
            }
        
        return tree
    
    def _add_fact_specific_guidance(self, tree: Dict[str, Any], 
                                  case_facts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Add guidance specific to the case facts"""
        # Analyze facts and add relevant guidance to each node
        return tree
    
    def _add_clickable_terms_to_tree(self, tree: Dict[str, Any]) -> Dict[str, Any]:
        """Identify and mark clickable terms in decision tree questions"""
        for node_id, node in tree['nodes'].items():
            question = node['question']
            
            # Find clickable terms in question text
            clickable_positions = []
            for term_key, term in self.clickable_terms.items():
                if term.term_text in question.lower():
                    clickable_positions.append({
                        'term': term.term_text,
                        'term_id': term.term_id,
                        'position': question.lower().find(term.term_text)
                    })
            
            node['clickable_terms'] = clickable_positions
        
        return tree
    
    def _generate_default_tree(self, cause_of_action: str, element_name: str, 
                             case_facts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a default decision tree structure"""
        return {
            'root': 'default_analysis',
            'nodes': {
                'default_analysis': {
                    'question': f'Is there sufficient evidence to establish {element_name}?',
                    'type': 'threshold',
                    'authority': 'Standard preponderance of evidence',
                    'guidance': ['Gather additional evidence', 'Consult expert if needed'],
                    'clickable_terms': []
                }
            },
            'current_node': 'default_analysis',
            'completed_paths': [],
            'metadata': {
                'case_facts_count': len(case_facts),
                'tree_type': 'default_analysis'
            }
        }
    
    def _determine_final_outcome(self, decisions: List[Dict[str, Any]], 
                               case_facts: List[Dict[str, Any]]) -> DecisionOutcome:
        """Determine the final outcome based on decision path"""
        # Analyze decisions to determine likely outcome
        positive_decisions = sum(1 for d in decisions if d.get('answer') == 'yes')
        total_decisions = len(decisions)
        
        if total_decisions == 0:
            return DecisionOutcome.INSUFFICIENT_EVIDENCE
        
        confidence_ratio = positive_decisions / total_decisions
        
        if confidence_ratio >= 0.8:
            return DecisionOutcome.ELEMENT_SATISFIED
        elif confidence_ratio >= 0.5:
            return DecisionOutcome.FURTHER_DISCOVERY_NEEDED
        else:
            return DecisionOutcome.ELEMENT_NOT_SATISFIED
    
    def _calculate_path_confidence(self, decisions: List[Dict[str, Any]], 
                                 case_facts: List[Dict[str, Any]]) -> float:
        """Calculate confidence score for decision path"""
        if not decisions:
            return 0.0
        
        # Simple confidence calculation - could be enhanced with ML
        decision_confidences = [d.get('confidence', 0.5) for d in decisions]
        return sum(decision_confidences) / len(decision_confidences)
    
    def _analyze_evidence_gaps(self, decisions: List[Dict[str, Any]], 
                             case_facts: List[Dict[str, Any]]) -> Tuple[List[str], List[str]]:
        """Identify supporting evidence and evidence gaps"""
        supporting_evidence = []
        missing_evidence = []
        
        for decision in decisions:
            if decision.get('answer') == 'yes' and decision.get('supporting_facts'):
                supporting_evidence.extend(decision['supporting_facts'])
            elif decision.get('answer') == 'no':
                missing_evidence.append(f"Evidence needed for: {decision.get('question', 'Unknown')}")
        
        return supporting_evidence, missing_evidence
    
    def _generate_action_recommendations(self, outcome: DecisionOutcome, 
                                       missing_evidence: List[str]) -> List[str]:
        """Generate recommended actions based on analysis outcome"""
        recommendations = []
        
        if outcome == DecisionOutcome.ELEMENT_SATISFIED:
            recommendations.extend([
                'Document supporting evidence thoroughly',
                'Prepare witness testimony',
                'Consider motion for summary judgment if appropriate'
            ])
        elif outcome == DecisionOutcome.INSUFFICIENT_EVIDENCE:
            recommendations.extend([
                'Conduct additional discovery',
                'Retain expert witnesses if needed',
                'Consider alternative legal theories'
            ])
        elif outcome == DecisionOutcome.FURTHER_DISCOVERY_NEEDED:
            recommendations.extend([
                'Propound targeted discovery requests',
                'Take depositions of key witnesses',
                'Request production of relevant documents'
            ])
        
        # Add specific recommendations based on missing evidence
        for missing in missing_evidence:
            if 'expert' in missing.lower():
                recommendations.append('Retain qualified expert witness')
            elif 'document' in missing.lower():
                recommendations.append('Request document production')
        
        return recommendations
    
    def _identify_alternative_theories(self, decisions: List[Dict[str, Any]], 
                                     case_facts: List[Dict[str, Any]]) -> List[str]:
        """Identify alternative legal theories based on decision analysis"""
        alternatives = []
        
        # Simple heuristic - could be enhanced with legal knowledge base
        fact_keywords = self._extract_fact_keywords(case_facts)
        
        if 'contract' in fact_keywords and 'negligence' in str(decisions):
            alternatives.append('Breach of contract')
        if 'professional' in fact_keywords and 'negligence' in str(decisions):
            alternatives.append('Professional malpractice')
        if 'property' in fact_keywords:
            alternatives.append('Premises liability')
        
        return alternatives
    
    def _generate_practice_guidance(self, outcome: DecisionOutcome, 
                                  decisions: List[Dict[str, Any]]) -> List[str]:
        """Generate practice guidance based on outcome"""
        guidance = []
        
        if outcome == DecisionOutcome.ELEMENT_SATISFIED:
            guidance.extend([
                'Prepare comprehensive witness list',
                'Organize evidence chronologically',
                'Consider settlement discussions from position of strength'
            ])
        elif outcome == DecisionOutcome.ELEMENT_NOT_SATISFIED:
            guidance.extend([
                'Evaluate case for dismissal or settlement',
                'Consider amending complaint with alternative theories',
                'Reassess damages calculation'
            ])
        
        return guidance
    
    def _extract_fact_keywords(self, case_facts: List[Dict[str, Any]]) -> List[str]:
        """Extract keywords from case facts for pattern matching"""
        keywords = []
        for fact in case_facts:
            fact_text = f"{fact.get('name', '')} {fact.get('description', '')}"
            # Simple keyword extraction - could use NLP
            words = re.findall(r'\b\w+\b', fact_text.lower())
            keywords.extend(words)
        return list(set(keywords))
    
    def _calculate_pattern_similarity(self, fact_keywords: List[str], 
                                    pattern_elements: List[str]) -> float:
        """Calculate similarity between case facts and pattern elements"""
        if not pattern_elements:
            return 0.0
        
        matches = 0
        for element in pattern_elements:
            element_words = element.lower().split()
            if any(word in fact_keywords for word in element_words):
                matches += 1
        
        return matches / len(pattern_elements)


if __name__ == "__main__":
    # Test the cascading decision tree engine
    import sys
    logging.basicConfig(level=logging.INFO)
    
    from cause_of_action_definition_engine import CauseOfActionDefinitionEngine
    from enhanced_knowledge_graph import EnhancedKnowledgeGraph

    from src.lawyerfactory.knowledge_graph.core.jurisdiction_manager import \
        JurisdictionManager
    
    try:
        kg = EnhancedKnowledgeGraph("test_decision_tree.db")
        jurisdiction_manager = JurisdictionManager(kg)
        definition_engine = CauseOfActionDefinitionEngine(kg, jurisdiction_manager, None, None)
        
        tree_engine = CascadingDecisionTreeEngine(kg, jurisdiction_manager, definition_engine)
        
        # Test clickable term expansion
        duty_term = tree_engine.expand_clickable_term("duty of care")
        if duty_term:
            print(f"Expanded term: {duty_term.term_text}")
            print(f"Definition: {duty_term.primary_definition}")
            print(f"Sub-terms: {duty_term.sub_terms}")
        
        # Test decision tree building
        test_facts = [
            {'name': 'Vehicle collision', 'description': 'Defendant ran red light'},
            {'name': 'Injuries', 'description': 'Plaintiff suffered broken ribs'}
        ]
        
        tree = tree_engine.build_decision_tree('negligence', 'duty', test_facts)
        print(f"\nBuilt decision tree with {len(tree.get('nodes', {}))} nodes")
        
        # Test fact pattern matching
        patterns = tree_engine.match_fact_patterns(test_facts)
        print(f"Matched {len(patterns)} fact patterns")
        for pattern, score in patterns:
            print(f"- {pattern.pattern_id}: {score:.2f}")
        
    except Exception as e:
        print(f"Test failed: {e}")
        sys.exit(1)
    finally:
        kg.close()