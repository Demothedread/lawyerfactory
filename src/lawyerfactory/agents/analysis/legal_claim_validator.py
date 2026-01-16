"""
# Script Name: legal_claim_validator.py
# Description: Legal Claim Validator Agent for LawyerFactory Orchestration Phase.  This agent validates legal claims to ensure they meet pleading standards and have sufficient legal merit. It performs:  - Rule 12(b)(6) compliance checking - Pleading sufficiency analysis - Legal theory validation - Claim viability assessment - Defense anticipation  The agent ensures that claims are properly pled and have a reasonable chance of success based on current law.
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Orchestration
#   - Group Tags: null
Legal Claim Validator Agent for LawyerFactory Orchestration Phase.

This agent validates legal claims to ensure they meet pleading standards
and have sufficient legal merit. It performs:

- Rule 12(b)(6) compliance checking
- Pleading sufficiency analysis
- Legal theory validation
- Claim viability assessment
- Defense anticipation

The agent ensures that claims are properly pled and have a reasonable
chance of success based on current law.
"""

from dataclasses import dataclass, field
import logging
from typing import Any, Dict, List, Optional

from ...compose.maestro.registry import AgentCapability, AgentInterface
from ...compose.maestro.workflow_models import WorkflowTask

# Import Tavily integration for claim substantiation
try:
    from ...research.precision_citation_service import (
        PrecisionCitationService,
        perform_background_research,
        substantiate_claims,
        verify_facts
    )
    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False
    logger.warning("Precision citation service not available - claim validation will be limited")

logger = logging.getLogger(__name__)


@dataclass
class ClaimValidation:
    """Validation result for a legal claim"""

    claim_title: str
    validation_status: str  # valid, invalid, needs_amendment
    rule_12b6_compliant: bool
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    confidence_score: float = 0.0
    required_elements: List[str] = field(default_factory=list)
    missing_elements: List[str] = field(default_factory=list)


class LegalClaimValidatorAgent(AgentInterface):
    """Agent that validates legal claims for sufficiency and viability"""

    def __init__(self, knowledge_graph=None):
        self.knowledge_graph = knowledge_graph
        self.capabilities = [
            AgentCapability.LEGAL_RESEARCH,
            AgentCapability.CASE_ANALYSIS,
        ]

        # Initialize precision citation service for claim substantiation
        self.citation_service = None
        if TAVILY_AVAILABLE:
            try:
                self.citation_service = PrecisionCitationService()
                logger.info("Precision citation service initialized for claim validation")
            except Exception as e:
                logger.warning(f"Failed to initialize precision citation service: {e}")

        # Load claim validation rules
        self._load_claim_validation_rules()

    def _load_claim_validation_rules(self):
        """Load rules for validating different types of claims"""
        self.claim_elements = {
            "negligence": {
                "required": ["duty", "breach", "causation", "damages"],
                "optional": ["contributory_negligence", "assumption_of_risk"],
                "common_defenses": [
                    "statute_of_limitations",
                    "immunities",
                    "contributory_negligence",
                ],
            },
            "breach_of_contract": {
                "required": [
                    "offer",
                    "acceptance",
                    "consideration",
                    "breach",
                    "damages",
                ],
                "optional": ["conditions_precedent", "force_majeure"],
                "common_defenses": [
                    "statute_of_limitations",
                    "impossibility",
                    "frustration",
                ],
            },
            "fraud": {
                "required": ["misrepresentation", "materiality", "reliance", "damages"],
                "optional": ["scienter", "justifiable_reliance"],
                "common_defenses": ["truth", "no_reliance", "due_diligence"],
            },
            "products_liability": {
                "required": ["defect", "causation", "damages"],
                "optional": ["manufacturing_defect", "design_defect", "warning_defect"],
                "common_defenses": [
                    "statute_of_limitations",
                    "assumption_of_risk",
                    "product_misuse",
                ],
            },
            "intentional_tort": {
                "required": ["intent", "act", "causation", "damages"],
                "optional": ["extreme_emotional_distress", "severe_conduct"],
                "common_defenses": ["consent", "self-defense", "privilege"],
            },
        }

        self.pleading_standards = {
            "factual_pleading": "Must allege sufficient facts to state a claim",
            "plausibility": "Facts must plausibly suggest entitlement to relief",
            "particularity": "Fraud claims require particularized allegations",
            "heightened_pleading": "Some claims require more than conclusory statements",
        }

    async def process(self, message: str) -> str:
        """Process a natural language request for claim validation"""
        try:
            # Extract claims from the message
            claims = self._extract_claims_from_text(message)

            # Extract jurisdiction from context
            jurisdiction = context.get("jurisdiction") or context.get("case_jurisdiction")

            # Validate claims with research substantiation
            validations = await self.validate_claims(claims, jurisdiction)

            # Generate response
            response = "Legal Claim Validation Analysis:\n\n"
            for i, validation in enumerate(validations, 1):
                response += f"{i}. **{validation.claim_title}**\n"
                response += f"   Status: {validation.validation_status}\n"
                response += (
                    f"   Rule 12(b)(6) Compliant: {validation.rule_12b6_compliant}\n"
                )
                response += f"   Confidence: {validation.confidence_score:.2f}/1.0\n"

                if validation.issues:
                    response += f"   Issues: {', '.join(validation.issues)}\n"

                if validation.recommendations:
                    response += (
                        f"   Recommendations: {', '.join(validation.recommendations)}\n"
                    )

                response += "\n"

            return response

        except Exception as e:
            logger.error(f"Error processing claim validation request: {e}")
            return f"Error validating claims: {str(e)}"

    async def execute_task(
        self, task: WorkflowTask, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a workflow task related to claim validation"""
        try:
            # Extract claims from context
            claims = self._extract_claims_from_context(context)

            # Validate claims
            validations = await self.validate_claims(claims)

            # Generate summary
            summary = self._generate_validation_summary(validations)

            return {
                "status": "completed",
                "claims_validated": len(claims),
                "validations": [validation.__dict__ for validation in validations],
                "summary": summary,
                "overall_compliance": self._assess_overall_compliance(validations),
            }

        except Exception as e:
            logger.error(f"Error executing claim validation task: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "claims_validated": 0,
                "validations": [],
                "summary": "",
                "overall_compliance": "unknown",
            }

    async def health_check(self) -> bool:
        """Check if the agent is functioning properly"""
        try:
            # Test basic functionality
            test_claims = ["negligence"]
            validations = await self.validate_claims(test_claims)
            return len(validations) > 0
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    async def initialize(self) -> None:
        """Initialize the agent"""
        try:
            logger.info("Legal Claim Validator Agent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Legal Claim Validator Agent: {e}")

    async def cleanup(self) -> None:
        """Clean up resources"""
        pass

    async def can_handle_task(self, task: WorkflowTask) -> bool:
        """Check if this agent can handle the given task"""
        task_text = f"{task.description} {task.agent_type}".lower()
        return any(
            keyword in task_text
            for keyword in ["claim", "validate", "pleading", "12(b)(6)", "sufficiency"]
        )

    async def validate_claims(self, claims: List[str], jurisdiction: Optional[str] = None) -> List[ClaimValidation]:
        """Validate a list of legal claims with optional research substantiation"""
        validations = []

        for claim in claims:
            validation = await self._validate_single_claim(claim)

            # Perform claim substantiation research if citation service is available
            if self.citation_service and jurisdiction:
                try:
                    substantiation_result = await self._perform_claim_substantiation_research(
                        claim, jurisdiction
                    )
                    validation = self._integrate_substantiation_results(validation, substantiation_result)
                    logger.info(f"Integrated substantiation research for claim: {claim}")
                except Exception as e:
                    logger.warning(f"Claim substantiation research failed for '{claim}': {e}")

            validations.append(validation)

        return validations

    async def _validate_single_claim(self, claim: str) -> ClaimValidation:
        """Validate a single legal claim"""
        claim_lower = claim.lower()

        # Find matching claim type
        claim_type = self._identify_claim_type(claim_lower)
        elements = self.claim_elements.get(claim_type, {})

        validation = ClaimValidation(
            claim_title=claim,
            validation_status="pending",
            rule_12b6_compliant=False,
            required_elements=elements.get("required", []),
            missing_elements=[],
            confidence_score=0.5,
        )

        # Check for required elements
        missing_elements = []
        for element in elements.get("required", []):
            if not self._element_present_in_claim(element, claim_lower):
                missing_elements.append(element)

        validation.missing_elements = missing_elements

        # Assess Rule 12(b)(6) compliance
        issues = []
        recommendations = []

        if missing_elements:
            issues.append(f"Missing required elements: {', '.join(missing_elements)}")
            recommendations.append(
                "Add factual allegations supporting missing elements"
            )

        # Check for conclusory statements
        if self._has_conclusory_allegations(claim):
            issues.append("Contains conclusory allegations without factual support")
            recommendations.append(
                "Replace conclusory statements with specific factual allegations"
            )

        # Check pleading standard
        pleading_issues = self._check_pleading_standard(claim, claim_type)
        issues.extend(pleading_issues)

        validation.issues = issues
        validation.recommendations = recommendations

        # Determine validation status
        if not issues:
            validation.validation_status = "valid"
            validation.rule_12b6_compliant = True
            validation.confidence_score = 0.9
        elif len(issues) <= 2:
            validation.validation_status = "needs_amendment"
            validation.rule_12b6_compliant = False
            validation.confidence_score = 0.6
        else:
            validation.validation_status = "invalid"
            validation.rule_12b6_compliant = False
            validation.confidence_score = 0.2

        return validation

    def _identify_claim_type(self, claim_text: str) -> str:
        """Identify the type of legal claim"""
        claim_text = claim_text.lower()

        for claim_type in self.claim_elements.keys():
            if claim_type.replace("_", " ") in claim_text:
                return claim_type

        # Default to general civil claim
        return "general_civil"

    def _element_present_in_claim(self, element: str, claim_text: str) -> bool:
        """Check if a required element is present in the claim"""
        element_keywords = {
            "duty": ["duty", "responsible", "obligation", "care"],
            "breach": ["breach", "failed", "violate", "not comply"],
            "causation": ["caused", "resulted", "led to", "because"],
            "damages": ["damages", "harm", "injury", "loss", "cost"],
            "offer": ["offer", "proposal", "agreement"],
            "acceptance": ["accept", "agree", "consent"],
            "consideration": ["payment", "value", "exchange"],
            "misrepresentation": ["misrepresent", "false", "deceit", "lie"],
            "materiality": ["material", "important", "significant"],
            "reliance": ["relied", "trusted", "depended"],
            "defect": ["defect", "flaw", "problem", "malfunction"],
        }

        keywords = element_keywords.get(element.lower(), [element.lower()])
        return any(keyword in claim_text for keyword in keywords)

    def _has_conclusory_allegations(self, claim: str) -> bool:
        """Check if claim contains conclusory allegations"""
        conclusory_phrases = [
            "was negligent",
            "breached the contract",
            "committed fraud",
            "was careless",
            "acted intentionally",
            "was reckless",
            "failed to properly",
            "negligent behavior",
        ]

        claim_lower = claim.lower()
        return any(phrase in claim_lower for phrase in conclusory_phrases)

    def _check_pleading_standard(self, claim: str, claim_type: str) -> List[str]:
        """Check if claim meets appropriate pleading standard"""
        issues = []

        # Fraud claims require heightened pleading
        if claim_type == "fraud":
            if not self._has_particularized_allegations(claim):
                issues.append(
                    "Fraud claims require particularized allegations under Rule 9(b)"
                )

        # Check for plausibility
        if not self._has_plausible_allegations(claim):
            issues.append("Claim lacks plausible factual allegations")

        return issues

    def _has_particularized_allegations(self, claim: str) -> bool:
        """Check if fraud claim has particularized allegations"""
        # Look for specific details like dates, amounts, exact statements
        has_date = any(word.isdigit() and len(word) == 4 for word in claim.split())
        has_quote = '"' in claim or "'" in claim
        has_specific_detail = len(claim.split()) > 15

        return has_date or has_quote or has_specific_detail

    def _has_plausible_allegations(self, claim: str) -> bool:
        """Check if claim has plausible factual allegations"""
        # Basic check for sufficient factual detail
        word_count = len(claim.split())
        has_facts = word_count > 10

        # Look for specific factual indicators
        factual_indicators = ["on", "at", "by", "with", "from", "to"]
        has_indicators = any(
            indicator in claim.lower() for indicator in factual_indicators
        )

        return has_facts and has_indicators

    def _extract_claims_from_text(self, text: str) -> List[str]:
        """Extract claims from natural language text"""
        # Simple extraction - look for common claim patterns
        claims = []

        text_lower = text.lower()

        if "negligence" in text_lower:
            claims.append("negligence")
        if "breach of contract" in text_lower or "contract" in text_lower:
            claims.append("breach of contract")
        if "fraud" in text_lower:
            claims.append("fraud")
        if "products liability" in text_lower or "product" in text_lower:
            claims.append("products liability")
        if "intentional tort" in text_lower:
            claims.append("intentional tort")

        return claims

    def _extract_claims_from_context(self, context: Dict[str, Any]) -> List[str]:
        """Extract claims from workflow context"""
        claims = []

        # Look for claims in claims matrix
        claims_matrix = context.get("claims_matrix", {})
        if isinstance(claims_matrix, dict):
            matrix_claims = claims_matrix.get("claims", [])
            for claim in matrix_claims:
                if isinstance(claim, dict):
                    claims.append(claim.get("title", ""))
                elif isinstance(claim, str):
                    claims.append(claim)

        # Look for claims in other context fields
        if "claims" in context:
            context_claims = context["claims"]
            if isinstance(context_claims, list):
                claims.extend(context_claims)

        return list(set(claims))  # Remove duplicates

    async def _perform_claim_substantiation_research(self, claim: str, jurisdiction: str) -> Dict[str, Any]:
        """Perform claim substantiation research using precision citation service"""
        try:
            # Use the precision citation service for claim substantiation
            substantiation_results = await self.citation_service.search_claim_substantiation(
                [claim], jurisdiction, max_sources_per_claim=3
            )

            return {
                "claim": claim,
                "citations": substantiation_results.get(claim, []),
                "citations_found": len(substantiation_results.get(claim, [])),
                "research_performed": True
            }

        except Exception as e:
            logger.error(f"Claim substantiation research failed for '{claim}': {e}")
            return {
                "claim": claim,
                "citations": [],
                "citations_found": 0,
                "research_performed": False,
                "error": str(e)
            }

    def _integrate_substantiation_results(self, validation: ClaimValidation, substantiation_result: Dict[str, Any]) -> ClaimValidation:
        """Integrate substantiation research results into claim validation"""
        if not substantiation_result.get("research_performed", False):
            return validation

        citations = substantiation_result.get("citations", [])
        if not citations:
            return validation

        # Boost confidence score based on research results
        base_confidence = validation.confidence_score
        research_boost = min(0.3, len(citations) * 0.1)  # Up to 0.3 boost for 3+ citations
        validation.confidence_score = min(1.0, base_confidence + research_boost)

        # Add research-based recommendations
        if citations:
            validation.recommendations.append(
                f"Found {len(citations)} substantiating sources - review for additional legal authority"
            )

            # Check for high-quality academic sources
            academic_sources = [c for c in citations if c.source_type == "academic"]
            if academic_sources:
                validation.recommendations.append(
                    f"Includes {len(academic_sources)} academic sources for legal analysis"
                )

        # Update validation status if confidence improved significantly
        if validation.confidence_score >= 0.8 and validation.validation_status == "needs_amendment":
            validation.validation_status = "valid"
            validation.rule_12b6_compliant = True

        return validation

    def _generate_validation_summary(self, validations: List[ClaimValidation]) -> str:
        """Generate a summary of claim validations"""
        summary = "Claim Validation Summary:\n\n"

        valid_claims = [v for v in validations if v.validation_status == "valid"]
        needs_amendment = [
            v for v in validations if v.validation_status == "needs_amendment"
        ]
        invalid_claims = [v for v in validations if v.validation_status == "invalid"]

        summary += f"Total Claims Validated: {len(validations)}\n"
        summary += f"Valid Claims: {len(valid_claims)}\n"
        summary += f"Needs Amendment: {len(needs_amendment)}\n"
        summary += f"Invalid Claims: {len(invalid_claims)}\n\n"

        if valid_claims:
            summary += "Valid Claims:\n"
            for validation in valid_claims:
                summary += f"  ✓ {validation.claim_title}\n"

        if needs_amendment:
            summary += "\nClaims Needing Amendment:\n"
            for validation in needs_amendment:
                summary += f"  ⚠ {validation.claim_title}\n"
                if validation.issues:
                    summary += f"    Issues: {', '.join(validation.issues[:2])}\n"

        if invalid_claims:
            summary += "\nInvalid Claims:\n"
            for validation in invalid_claims:
                summary += f"  ✗ {validation.claim_title}\n"
                if validation.issues:
                    summary += f"    Issues: {', '.join(validation.issues[:2])}\n"

        return summary

    def _assess_overall_compliance(self, validations: List[ClaimValidation]) -> str:
        """Assess overall compliance with pleading standards"""
        if not validations:
            return "no_claims"

        compliant_count = sum(1 for v in validations if v.rule_12b6_compliant)
        compliance_rate = compliant_count / len(validations)

        if compliance_rate >= 0.8:
            return "compliant"
        elif compliance_rate >= 0.5:
            return "partial_compliance"
        else:
            return "non_compliant"
