"""
# Script Name: writer.py
# Description: Enhanced legal document writer with AI generation modules and Tavily claim validation
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Orchestration
#   - Group Tags: null
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape

# Import AI document generation modules
from lawyerfactory.export.renderers.legacy.modules.fact_synthesis import synthesize_facts
from lawyerfactory.export.renderers.legacy.modules.legal_theory_mapping import (
    integrate_citations,
    map_facts_to_elements,
 )

from ..agent_registry import AgentConfig, AgentInterface
from lawyerfactory.compose.maestro.base import Bot
# from lawyerfactory.compose.maestro.workflow import WorkflowTask
from ...outline.generator import SkeletalOutlineGenerator
from ...research.tavily_integration import ResearchQuery, TavilyResearchIntegration

logger = logging.getLogger(__name__)


class WriterBot:
    """Enhanced writing bot for professional legal document creation using AI modules and templates"""

    def __init__(self, config):
        """Initialize WriterBot with AgentConfig"""
        self.config = config  # Store the AgentConfig

        # Extract LLM configuration from AgentConfig
        self.llm_config = self.config.config if self.config.config else {}
        self.llm_provider = self.llm_config.get("provider", "openai")
        self.llm_model = self.llm_config.get("model", "gpt-4")
        self.llm_temperature = self.llm_config.get("temperature", 0.7)
        self.llm_max_tokens = self.llm_config.get("max_tokens", 4000)
        self.llm_api_key = self.llm_config.get("api_key")

        # Initialize template system (optional)
        self.jinja_env = None
        try:
            template_dir = Path(__file__).parent.parent.parent / "templates"
            if template_dir.exists():
                self.jinja_env = Environment(
                    loader=FileSystemLoader(template_dir),
                    autoescape=select_autoescape(['html', 'xml'])
                )
        except Exception as e:
            logger.warning(f"Template system initialization failed: {e}")

        # Initialize validation components (optional)
        self.outline_generator = None
        self.tavily_integration = None
        try:
            # These may not be available in all environments
            pass  # Will be set up when needed
        except Exception as e:
            logger.warning(f"Validation components initialization failed: {e}")

        # Initialize LLM service with extracted config
        self.llm_service = None
        try:
            from lawyerfactory.lf_core.llm.service import LLMService
            from lawyerfactory.lf_core.llm.config import LLMConfigManager

            # Create config manager and temporarily update with our config
            config_manager = LLMConfigManager()

            # Update the provider config with our parameters
            # provider_config = {
            #     "api_key": self.llm_api_key,
            #     "model": self.llm_model,
            #     "temperature": self.llm_temperature,
            #     "max_tokens": self.llm_max_tokens,
            #     "enabled": True,
            # }

            # Update the config for the specified provider
            # config_manager.update_provider_config(self.llm_provider, provider_config)
            # config_manager.set_current_provider(self.llm_provider)

            self.llm_service = LLMService(config_manager)
            logger.info("WriterBot initialized with LLM service")

        except Exception as e:
            logger.warning(f"LLM service initialization failed: {e}")
            self.llm_service = None

    async def process(self, message: str) -> str:
        """Legacy Bot interface implementation"""
        # Use professional template for basic processing
        try:
            if self.jinja_env:
                template = self.jinja_env.get_template("complaint_body.jinja2")
                # Create a basic structure for legacy interface
                causes_of_action = [
                    {
                        "name": "General Claim",
                        "elements": [{"name": "Basis", "fact_text": [message]}],
                    }
                ]
                research = {"citations": []}
                return template.render(
                    causes_of_action=causes_of_action, research=research
                )
            else:
                return f"Professional legal document based on: '{message}'"
        except Exception as e:
            logger.error(f"Template rendering failed: {e}")
            return f"Professional legal document based on: '{message}'"

    async def execute_task(
        self, task, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """AgentInterface implementation for orchestration system"""
        logger.info(f"WriterBot executing task: {task.id}")

        try:
            # Extract writing parameters from task context
            content_type = context.get("content_type", "complaint")
            case_facts = context.get("case_facts", [])
            research_findings = context.get("research_findings", {})
            case_data = context.get("case_data", {})

            # Perform claim validation if available
            validation_context = await self._validate_claims_for_drafting(
                case_facts, case_data, context
            )

            # Merge validation results into context
            if validation_context["validation_performed"]:
                context["claim_validation"] = validation_context
                research_findings["claim_validation"] = validation_context["validation_results"]

            # Execute professional writing task using AI modules
            if content_type == "complaint":
                result = await self._write_professional_complaint(
                    case_facts, research_findings, case_data, context
                )
            elif content_type == "motion":
                result = await self._write_professional_motion(
                    case_facts, research_findings, case_data, context
                )
            else:
                result = await self._write_professional_document(
                    case_facts, research_findings, case_data, context
                )

            # Add validation metadata to result
            result["claim_validation_performed"] = validation_context["validation_performed"]
            if validation_context["validation_performed"]:
                result["validation_recommendations"] = validation_context["recommendations"]
                result["validation_confidence"] = validation_context["validation_results"].get(
                    "overall_confidence", 0.0
                )

            return {
                "status": "completed",
                "content": result["content"],
                "content_type": content_type,
                "word_count": (
                    len(result["content"].split()) if result["content"] else 0
                ),
                "template_used": result.get("template_used"),
                "professional_formatting": True,
                "sections_included": result.get("sections_included", []),
            }

        except Exception as e:
            logger.error(f"WriterBot task execution failed: {e}")
            return {"status": "failed", "error": str(e), "content": None}

    async def _write_professional_complaint(
        self,
        case_facts: List[Dict],
        research_findings: Dict,
        case_data: Dict,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Write a professional complaint using Jinja2 templates and AI modules"""
        try:
            if not self.jinja_env:
                return {
                    "content": "Professional complaint generation requires template system",
                    "template_used": None,
                    "sections_included": [],
                }

            # Step 1: Synthesize facts into compelling narrative
            statement_of_facts = (
                synthesize_facts(case_facts)
                if case_facts
                else "Facts to be determined during discovery."
            )

            # Step 2: Map facts to legal elements and integrate citations
            causes_of_action = context.get("causes_of_action", [])
            if causes_of_action and case_facts:
                causes_of_action = map_facts_to_elements(causes_of_action, case_facts)
                causes_of_action = integrate_citations(
                    causes_of_action, research_findings
                )

            # Step 3: Prepare template context
            template_context = {
                "case": {
                    "case_caption": {
                        "court": case_data.get("court", "UNITED STATES DISTRICT COURT"),
                        "district": case_data.get(
                            "district", "NORTHERN DISTRICT OF CALIFORNIA"
                        ),
                        "plaintiff": case_data.get("plaintiff_name", "PLAINTIFF NAME"),
                        "defendant": case_data.get("defendant_name", "DEFENDANT NAME"),
                        "case_number": case_data.get(
                            "case_number", "Case No. [TO BE ASSIGNED]"
                        ),
                    }
                },
                "statement_of_facts": statement_of_facts,
                "causes_of_action": causes_of_action,
                "research": research_findings,
            }

            # Step 4: Render professional complaint using template
            complaint_template = self.jinja_env.get_template("complaint.jinja2")
            professional_content = complaint_template.render(**template_context)

            # Enhance with validation insights if available
            validation_context = context.get("claim_validation", {})
            if validation_context.get("validation_performed"):
                professional_content = self._enhance_content_with_validation(
                    professional_content, validation_context
                )

            return {
                "content": professional_content,
                "template_used": "complaint.jinja2",
                "sections_included": [
                    "cover_sheet",
                    "statement_of_facts",
                    "complaint_body",
                    "prayer_for_relief",
                    "bibliography",
                ],
                "validation_enhanced": validation_context.get("validation_performed", False),
            }

        except Exception as e:
            logger.error(f"Professional complaint generation failed: {e}")
            # Fallback to basic generation
            case_name = case_data.get("case_name", "Unknown Case")
            return {
                "content": f"PROFESSIONAL COMPLAINT FOR {case_name}\n\nBased on case facts and research findings.\n\n[Professional content would be generated here]",
                "template_used": None,
                "sections_included": ["basic"],
            }

    async def _write_professional_motion(
        self,
        case_facts: List[Dict],
        research_findings: Dict,
        case_data: Dict,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Write a professional motion using templates and legal theory mapping"""
        try:
            motion_type = context.get("motion_type", "Motion for Summary Judgment")
            statement_of_facts = synthesize_facts(case_facts) if case_facts else ""

            # Create professional motion structure
            professional_content = f"""
{case_data.get('court', 'UNITED STATES DISTRICT COURT')}
{case_data.get('district', 'NORTHERN DISTRICT OF CALIFORNIA')}

{case_data.get('plaintiff_name', 'PLAINTIFF')},
    Plaintiff,

v.                                              Case No. {case_data.get('case_number', '[TO BE ASSIGNED]')}

{case_data.get('defendant_name', 'DEFENDANT')},
    Defendant.

{motion_type.upper()}

TO THE HONORABLE COURT:

{statement_of_facts}

LEGAL STANDARD

{self._generate_legal_standard(research_findings)}

ARGUMENT

{self._generate_argument_from_research(research_findings, case_facts)}

CONCLUSION

For the foregoing reasons, Plaintiff respectfully requests that this Court grant this motion.

Respectfully submitted,

Attorney for Plaintiff
"""

            # Enhance with validation insights if available
            validation_context = context.get("claim_validation", {})
            if validation_context.get("validation_performed"):
                professional_content = self._enhance_content_with_validation(
                    professional_content, validation_context
                )

            return {
                "content": professional_content,
                "template_used": "motion_template",
                "sections_included": [
                    "header",
                    "facts",
                    "legal_standard",
                    "argument",
                    "conclusion",
                ],
                "validation_enhanced": validation_context.get("validation_performed", False),
            }

        except Exception as e:
            logger.error(f"Professional motion generation failed: {e}")
            motion_type = context.get("motion_type", "General Motion")
            return {
                "content": f"PROFESSIONAL {motion_type.upper()}\n\nBased on case facts and legal research.\n\n[Professional motion content would be generated here]",
                "template_used": None,
                "sections_included": ["basic"],
            }

    async def _write_professional_document(
        self,
        case_facts: List[Dict],
        research_findings: Dict,
        case_data: Dict,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Write a professional legal document using available templates"""
        statement_of_facts = synthesize_facts(case_facts) if case_facts else ""

        professional_content = f"""
PROFESSIONAL LEGAL DOCUMENT

Case: {case_data.get('case_name', 'Professional Legal Matter')}

STATEMENT OF FACTS

{statement_of_facts}

LEGAL ANALYSIS

{self._generate_argument_from_research(research_findings, case_facts)}

CONCLUSION

Based on the facts and applicable law, the following relief is appropriate.
"""

        return {
            "content": professional_content,
            "template_used": "professional_document",
            "sections_included": ["facts", "analysis", "conclusion"],
        }

    def _generate_legal_standard(self, research_findings: Dict) -> str:
        """Generate legal standard section from research findings"""
        citations = research_findings.get("citations", [])
        if citations:
            primary_citation = citations[0] if citations else {}
            cite_text = primary_citation.get("cite", "Relevant legal authority")
            return f"The applicable legal standard is well-established. {cite_text}."
        return "The applicable legal standard governs this matter."

    def _generate_argument_from_research(
        self, research_findings: Dict, case_facts: List[Dict]
    ) -> str:
        """Generate legal argument from research findings and facts"""
        argument_sections = []

        # Use research findings to build argument
        legal_issues = research_findings.get("legal_issues", [])
        citations = research_findings.get("citations", [])

        for i, issue in enumerate(legal_issues[:3]):  # Limit to top 3 issues
            section = f"Issue {i+1}: {issue}\n\n"
            if i < len(citations):
                citation = citations[i]
                section += f"As established in {citation.get('cite', 'controlling authority')}, "
                section += citation.get(
                    "summary", "the legal principle applies to the facts of this case."
                )
            section += "\n"
            argument_sections.append(section)

        if not argument_sections:
            return "The facts and law support the relief requested."

        return "\n".join(argument_sections)

    async def _validate_claims_for_drafting(
        self, case_facts: List[Dict], case_data: Dict, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate claims using Tavily research for drafting
        """
        if not self.outline_generator or not self.tavily_integration:
            return {"validation_performed": False, "error": "Validation components not available"}

        try:
            # Extract claims from context
            claims = self._extract_claims_from_context(case_facts, case_data, context)
            jurisdiction = case_data.get("jurisdiction", "California")

            if not claims:
                return {"validation_performed": False, "error": "No claims found to validate"}

            # Perform validation
            validation_result = await self.outline_generator.validate_claims_for_drafting(
                claims, jurisdiction
            )

            return validation_result

        except Exception as e:
            logger.error(f"Claim validation failed: {e}")
            return {"validation_performed": False, "error": str(e)}

    def _extract_claims_from_context(
        self, case_facts: List[Dict], case_data: Dict, context: Dict[str, Any]
    ) -> List[str]:
        """
        Extract legal claims from various context sources
        """
        claims = []

        # Extract from causes of action
        causes_of_action = context.get("causes_of_action", [])
        for coa in causes_of_action:
            if isinstance(coa, dict) and "name" in coa:
                claims.append(coa["name"])
            elif isinstance(coa, str):
                claims.append(coa)

        # Extract from case data
        if "primary_cause_of_action" in case_data:
            claims.append(case_data["primary_cause_of_action"])

        # Extract from research findings
        research_findings = context.get("research_findings", {})
        legal_issues = research_findings.get("legal_issues", [])
        claims.extend(legal_issues)

        # Remove duplicates and clean
        unique_claims = []
        seen = set()
        for claim in claims:
            claim_clean = str(claim).strip().lower()
            if claim_clean and claim_clean not in seen:
                unique_claims.append(str(claim).strip())
                seen.add(claim_clean)

        return unique_claims[:10]  # Limit to 10 claims for performance

    async def validate_specific_claim(
        self, claim_text: str, supporting_facts: List[str], jurisdiction: str
    ) -> Dict[str, Any]:
        """
        Validate a specific claim with supporting facts
        """
        if not self.tavily_integration:
            return {"validation_performed": False}

        try:
            # Create research query for claim validation
            research_query = ResearchQuery(
                query_text=f"{claim_text} {jurisdiction} legal requirements supporting facts",
                legal_issues=[claim_text],
                jurisdiction=jurisdiction,
                preferred_sources=["academic", "news"],
                max_results=10,
            )

            # Execute research
            research_result = await self.tavily_integration.comprehensive_research(research_query)

            # Analyze supporting facts against research
            validation_score = self._analyze_facts_against_research(
                supporting_facts, research_result
            )

            return {
                "validation_performed": True,
                "claim_text": claim_text,
                "jurisdiction": jurisdiction,
                "validation_score": validation_score,
                "research_findings": {
                    "content": research_result.content,
                    "sources": research_result.sources,
                    "confidence_score": research_result.confidence_score,
                },
                "supporting_facts_analysis": self._analyze_supporting_facts(supporting_facts),
                "recommendations": self._generate_claim_recommendations(
                    claim_text, validation_score, research_result
                ),
            }

        except Exception as e:
            logger.error(f"Specific claim validation failed: {e}")
            return {"validation_performed": False, "error": str(e)}

    def _analyze_facts_against_research(
        self, supporting_facts: List[str], research_result: Any
    ) -> float:
        """
        Analyze how well supporting facts align with research findings
        """
        if not hasattr(research_result, "content") or not research_result.content:
            return 0.5  # Neutral score if no research

        research_content = research_result.content.lower()
        alignment_score = 0.0
        total_facts = len(supporting_facts)

        if total_facts == 0:
            return 0.5

        for fact in supporting_facts:
            fact_lower = fact.lower()
            # Simple keyword matching for alignment
            fact_words = set(fact_lower.split())
            research_words = set(research_content.split())

            overlap = len(fact_words.intersection(research_words))
            if overlap > 0:
                alignment_score += min(1.0, overlap / len(fact_words))

        return alignment_score / total_facts

    def _analyze_supporting_facts(self, supporting_facts: List[str]) -> Dict[str, Any]:
        """
        Analyze the quality and completeness of supporting facts
        """
        analysis = {
            "total_facts": len(supporting_facts),
            "fact_quality_score": 0.0,
            "fact_specificity_score": 0.0,
            "temporal_coverage": False,
            "geographic_coverage": False,
        }

        if not supporting_facts:
            return analysis

        # Analyze fact quality
        quality_indicators = ["specific", "dated", "named", "quantified", "detailed"]
        specificity_indicators = ["date", "time", "location", "amount", "specific person"]

        for fact in supporting_facts:
            fact_lower = fact.lower()

            # Quality score
            quality_matches = sum(1 for indicator in quality_indicators if indicator in fact_lower)
            analysis["fact_quality_score"] += quality_matches / len(quality_indicators)

            # Specificity score
            specificity_matches = sum(
                1 for indicator in specificity_indicators if indicator in fact_lower
            )
            analysis["fact_specificity_score"] += specificity_matches / len(specificity_indicators)

            # Coverage analysis
            if any(word in fact_lower for word in ["date", "time", "when", "on ", "at "]):
                analysis["temporal_coverage"] = True
            if any(
                word in fact_lower for word in ["location", "place", "address", "city", "state"]
            ):
                analysis["geographic_coverage"] = True

        # Average the scores
        analysis["fact_quality_score"] /= len(supporting_facts)
        analysis["fact_specificity_score"] /= len(supporting_facts)

        return analysis

    def _generate_claim_recommendations(
        self, claim_text: str, validation_score: float, research_result: Any
    ) -> List[str]:
        """
        Generate recommendations based on claim validation
        """
        recommendations = []

        if validation_score < 0.4:
            recommendations.append(
                f"Consider strengthening the {claim_text} claim with additional supporting facts"
            )
            recommendations.append(
                "Review recent case law to ensure all elements are adequately pled"
            )

        if validation_score > 0.8:
            recommendations.append(
                f"The {claim_text} claim appears well-supported by current legal standards"
            )

        # Research-based recommendations
        if hasattr(research_result, "content") and research_result.content:
            content_lower = research_result.content.lower()

            if "recent case" in content_lower or "new decision" in content_lower:
                recommendations.append(
                    f"Consider citing recent case law developments for {claim_text}"
                )

            if "amended" in content_lower or "updated" in content_lower:
                recommendations.append(f"Review recent statutory amendments affecting {claim_text}")

        return (
            recommendations
            if recommendations
            else [f"Continue monitoring legal developments for {claim_text}"]
        )

    def _enhance_content_with_validation(
        self, content: str, validation_context: Dict[str, Any]
    ) -> str:
        """
        Enhance document content with validation insights
        """
        try:
            validation_results = validation_context.get("validation_results", {})
            recommendations = validation_context.get("recommendations", [])

            overall_confidence = validation_results.get("overall_confidence", 0.0)

            # Add validation disclaimer based on confidence
            if overall_confidence < 0.5:
                validation_note = """

CLAIM VALIDATION NOTE:
The claims in this document have been validated against recent legal developments.
Some claims may benefit from additional factual development or legal research.
Recommendations: """ + "\n".join(
                    f"- {rec}" for rec in recommendations[:3]
                )

            elif overall_confidence > 0.8:
                validation_note = """

CLAIM VALIDATION NOTE:
The claims in this document are well-supported by current legal landscape and recent developments.
The pleading appears sufficiently robust for Rule 12(b)(6) survival."""

            else:
                validation_note = """

CLAIM VALIDATION NOTE:
The claims in this document have been validated against recent legal developments.
The pleading appears adequate but should be monitored for relevant case law updates."""

            # Insert validation note before conclusion
            if "CONCLUSION" in content.upper():
                conclusion_index = content.upper().find("CONCLUSION")
                enhanced_content = (
                    content[:conclusion_index]
                    + validation_note
                    + "\n\n"
                    + content[conclusion_index:]
                )
            else:
                enhanced_content = content + "\n\n" + validation_note

            return enhanced_content

        except Exception as e:
            logger.warning(f"Content enhancement failed: {e}")
            return content


# Convenience functions
async def validate_claim_for_drafting(
    claim_text: str, supporting_facts: List[str], jurisdiction: str
) -> Dict[str, Any]:
    """
    Convenience function for claim validation
    """
    try:
        from lawyerfactory.kg.graph import KnowledgeGraph

        kg = KnowledgeGraph()
        generator = SkeletalOutlineGenerator(kg, None, None)

        return await generator.validate_claims_for_drafting([claim_text], jurisdiction)

    except Exception as e:
        logger.error(f"Claim validation failed: {e}")
        return {"validation_performed": False, "error": str(e)}
