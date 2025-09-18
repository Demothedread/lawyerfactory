"""
Enhanced Skeletal Outline Generator with Tavily Integration

This module extends the base outline generator to use Tavily for tertiary knowledge
when the LLM's knowledge appears thin, and for claim validation during drafting.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from lawyerfactory.outline.generator import SkeletalOutlineGenerator, SkeletalSection
from lawyerfactory.research.tavily_integration import ResearchQuery, TavilyResearchIntegration
from lawyerfactory.storage.enhanced_unified_storage_api import get_enhanced_unified_storage_api

logger = logging.getLogger(__name__)


class EnhancedSkeletalOutlineGenerator(SkeletalOutlineGenerator):
    """
    Enhanced outline generator with Tavily integration for tertiary knowledge
    and claim validation capabilities.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Initialize Tavily integration
        self.tavily_integration = None
        try:
            self.tavily_integration = TavilyResearchIntegration()
            logger.info("Tavily integration enabled for outline generation")
        except Exception as e:
            logger.warning(f"Tavily integration not available: {e}")

    async def generate_enhanced_outline(self, case_id: str, session_id: str) -> Dict[str, Any]:
        """
        Generate enhanced skeletal outline with Tavily research integration
        """
        try:
            # Generate base outline (not async)
            base_outline = self.generate_skeletal_outline(case_id, session_id)

            # Enhance with tertiary knowledge if available
            if self.tavily_integration:
                enhanced_sections = await self._enhance_sections_with_tertiary_knowledge(
                    base_outline.sections, case_id
                )
                base_outline.sections = enhanced_sections

                # Add research metadata
                base_outline.global_context["tavily_research_enabled"] = True
                base_outline.global_context["tertiary_knowledge_integrated"] = True

            return {
                "outline": base_outline,
                "enhancement_metadata": {
                    "tavily_enabled": self.tavily_integration is not None,
                    "sections_enhanced": len(base_outline.sections),
                    "research_integrated": True,
                },
            }

        except Exception as e:
            logger.exception(f"Enhanced outline generation failed: {e}")
            # Fallback to base outline
            base_outline = self.generate_skeletal_outline(case_id, session_id)
            return {
                "outline": base_outline,
                "enhancement_metadata": {"tavily_enabled": False, "error": str(e)},
            }

    async def _enhance_sections_with_tertiary_knowledge(
        self, sections: List[SkeletalSection], case_id: str
    ) -> List[SkeletalSection]:
        """
        Enhance outline sections with tertiary knowledge from Tavily
        """
        enhanced_sections: List[SkeletalSection] = []

        for section in sections:
            try:
                # Assess if section needs tertiary knowledge enhancement
                knowledge_assessment = await self._assess_knowledge_depth(section)

                if knowledge_assessment["needs_enhancement"]:
                    # Enhance section with tertiary knowledge
                    enhanced_section = await self._enhance_section_with_research(
                        section, knowledge_assessment
                    )
                    enhanced_sections.append(enhanced_section)
                else:
                    enhanced_sections.append(section)

            except Exception as e:
                logger.warning(f"Failed to enhance section {section.section_id}: {e}")
                enhanced_sections.append(section)

        return enhanced_sections

    async def _assess_knowledge_depth(self, section: SkeletalSection) -> Dict[str, Any]:
        """
        Assess whether a section's knowledge depth appears thin and needs enhancement
        """
        assessment: Dict[str, Any] = {
            "needs_enhancement": False,
            "enhancement_type": None,
            "research_queries": [],
            "confidence_score": 1.0,
        }

        # Assess based on section content and context
        section_text = f"{section.title} {section.prompt_template}"

        # Check for indicators of thin knowledge
        thin_knowledge_indicators = [
            "research required",
            "to be determined",
            "pending research",
            "further investigation needed",
            "additional analysis required",
            "expert consultation recommended",
        ]

        if any(indicator in section_text.lower() for indicator in thin_knowledge_indicators):
            assessment["needs_enhancement"] = True
            assessment["enhancement_type"] = "tertiary_knowledge"
            assessment["confidence_score"] = 0.3

        # Assess based on section type
        if section.section_type.value == "cause_of_action":
            # COA sections often benefit from recent developments
            assessment["needs_enhancement"] = True
            assessment["enhancement_type"] = "recent_developments"
            assessment["research_queries"].append(
                f"recent {section.title.lower()} case law developments"
            )

        elif section.section_type.value == "jurisdiction_venue":
            # Jurisdiction sections benefit from procedural updates
            assessment["needs_enhancement"] = True
            assessment["enhancement_type"] = "procedural_updates"
            assessment["research_queries"].append(
                f"{section.title.lower()} recent procedural changes"
            )

        return assessment

    async def _enhance_section_with_research(
        self, section: SkeletalSection, assessment: Dict[str, Any]
    ) -> SkeletalSection:
        """
        Enhance a section with research from Tavily
        """
        try:
            enhanced_section = section  # Start with original

            # Generate research queries based on assessment
            research_queries = assessment.get("research_queries", [])

            if not research_queries:
                # Generate default research query from section content
                research_queries = [f"{section.title} legal analysis and recent developments"]

            # Execute research
            research_results = []
            for query in research_queries[:2]:  # Limit to 2 queries per section
                try:
                    research_query = ResearchQuery(
                        query_text=query,
                        legal_issues=[section.title],
                        preferred_sources=["academic", "news"],
                        max_results=5,
                    )

                    if self.tavily_integration:
                        result = await self.tavily_integration.comprehensive_research(
                            research_query
                        )
                        research_results.append(result)

                except Exception as e:
                    logger.warning(f"Research query failed for '{query}': {e}")

            if research_results:
                # Enhance section prompt with research findings
                enhanced_prompt = await self._integrate_research_into_prompt(
                    section.prompt_template, research_results
                )

                # Create enhanced section with research metadata
                enhanced_section = SkeletalSection(
                    section_id=f"{section.section_id}_enhanced",
                    section_type=section.section_type,
                    title=f"{section.title} (Enhanced)",
                    roman_numeral=section.roman_numeral,
                    subsections=section.subsections,
                    prompt_template=enhanced_prompt,
                    context_references=section.context_references,
                    legal_authorities=section.legal_authorities,
                    word_count_target=section.word_count_target,
                    priority_level=section.priority_level,
                    dependencies=section.dependencies,
                    evidence_mapping=section.evidence_mapping,
                    fact_mapping=section.fact_mapping,
                )

                # Add research metadata to context_references
                research_metadata = {
                    "tavily_research_performed": True,
                    "research_queries_executed": research_queries,
                    "sources_consulted": len(research_results),
                    "enhancement_timestamp": json.dumps(
                        {"timestamp": str(asyncio.get_event_loop().time())}
                    ),
                }
                enhanced_section.context_references.append(
                    f"research_metadata:{json.dumps(research_metadata)}"
                )

            return enhanced_section

        except Exception as e:
            logger.error(f"Section enhancement failed: {e}")
            return section

    async def _integrate_research_into_prompt(
        self, original_prompt: str, research_results: List[Any]
    ) -> str:
        """
        Integrate research findings into the section prompt
        """
        try:
            # Extract key insights from research results
            research_insights: List[str] = []

            for result in research_results:
                if hasattr(result, "content") and result.content:
                    # Extract key sentences or insights
                    content_lines = result.content.split("\n")
                    key_insights = [
                        line.strip()
                        for line in content_lines
                        if len(line.strip()) > 20 and not line.startswith("#")
                    ][
                        :3
                    ]  # Take top 3 insights

                    research_insights.extend(key_insights)

            if research_insights:
                # Enhance the original prompt
                enhancement_text = (
                    """

ADDITIONAL CONTEXT FROM RECENT RESEARCH:
The following insights from recent academic and news sources should be considered:

"""
                    + "\n".join(f"- {insight}" for insight in research_insights[:5])
                    + """

INTEGRATE THESE INSIGHTS NATURALLY INTO YOUR RESPONSE WHERE APPROPRIATE.
PRIORITIZE WELL-ESTABLISHED LEGAL PRINCIPLES WHILE CONSIDERING RECENT DEVELOPMENTS.
"""
                )

                enhanced_prompt = original_prompt + enhancement_text
                return enhanced_prompt

            return original_prompt

        except Exception as e:
            logger.warning(f"Research integration failed: {e}")
            return original_prompt

    async def validate_claims_for_drafting(
        self, claims: List[str], jurisdiction: str
    ) -> Dict[str, Any]:
        """
        Validate legal claims using Tavily research for drafting phase
        """
        if not self.tavily_integration:
            return {"validation_performed": False, "error": "Tavily integration not available"}

        try:
            validation_results = await self.tavily_integration.validate_legal_claims(
                claims, jurisdiction
            )

            return {
                "validation_performed": True,
                "claims_validated": claims,
                "validation_results": validation_results,
                "recommendations": self._generate_drafting_recommendations(validation_results),
                "timestamp": json.dumps({"timestamp": str(asyncio.get_event_loop().time())}),
            }

        except Exception as e:
            logger.error(f"Claim validation failed: {e}")
            return {"validation_performed": False, "error": str(e)}

    def _generate_drafting_recommendations(self, validation_results: Dict[str, Any]) -> List[str]:
        """
        Generate drafting recommendations based on validation results
        """
        recommendations: List[str] = []

        overall_confidence = validation_results.get("overall_confidence", 0.0)

        if overall_confidence < 0.4:
            recommendations.append(
                "Consider strengthening claim allegations with additional supporting facts"
            )
            recommendations.append("Review recent case law to ensure claims are sufficiently pled")

        if overall_confidence > 0.8:
            recommendations.append("Claims appear well-supported by current legal landscape")
            recommendations.append("Monitor for recent developments that may impact these claims")

        # Check individual claim validations
        claim_results = validation_results.get("validation_results", {})
        weak_claims = [
            claim
            for claim, result in claim_results.items()
            if result.get("validation_score", 0) < 0.5
        ]

        if weak_claims:
            recommendations.append(
                f"Particular attention needed for claims: {', '.join(weak_claims)}"
            )

        return recommendations

    async def get_research_context_for_editing(
        self, claim_text: str, jurisdiction: str
    ) -> Dict[str, Any]:
        """
        Get research context for editing phase claim validation
        """
        if not self.tavily_integration:
            return {"research_available": False}

        try:
            # Search for recent developments related to the claim
            research_query = ResearchQuery(
                query_text=f"{claim_text} {jurisdiction} recent developments",
                legal_issues=[claim_text],
                jurisdiction=jurisdiction,
                preferred_sources=["news", "academic"],
                max_results=8,
                time_range="month",
            )

            research_result = await self.tavily_integration.comprehensive_research(research_query)

            return {
                "research_available": True,
                "claim_text": claim_text,
                "jurisdiction": jurisdiction,
                "research_findings": {
                    "content": research_result.content,
                    "sources": research_result.sources,
                    "citations": research_result.citations,
                    "confidence_score": research_result.confidence_score,
                },
                "validation_suggestions": self._generate_editing_suggestions(research_result),
                "timestamp": json.dumps({"timestamp": str(asyncio.get_event_loop().time())}),
            }

        except Exception as e:
            logger.error(f"Editing research context failed: {e}")
            return {"research_available": False, "error": str(e)}

    def _generate_editing_suggestions(self, research_result: Any) -> List[str]:
        """
        Generate editing suggestions based on research findings
        """
        suggestions: List[str] = []

        if hasattr(research_result, "content") and research_result.content:
            content_lower = research_result.content.lower()

            # Look for common legal editing suggestions
            if "recent case" in content_lower or "new decision" in content_lower:
                suggestions.append("Consider citing recent case law that may strengthen this claim")

            if "amended" in content_lower or "updated" in content_lower:
                suggestions.append(
                    "Review for any recent statutory amendments that may affect this claim"
                )

            if "settlement" in content_lower or "dismissal" in content_lower:
                suggestions.append("Consider whether recent settlements affect pleading strategy")

        if research_result.confidence_score < 0.6:
            suggestions.append(
                "Limited recent research found - consider traditional legal research"
            )

        return (
            suggestions if suggestions else ["No specific editing suggestions from recent research"]
        )


# Convenience functions for easy integration
async def generate_enhanced_outline(case_id: str, session_id: str) -> Dict[str, Any]:
    """
    Convenience function to generate enhanced outline with Tavily integration
    """
    try:
        from lawyerfactory.claims.matrix import ComprehensiveClaimsMatrixIntegration
        from lawyerfactory.kg.enhanced_graph import EnhancedKnowledgeGraph
        from lawyerfactory.phases.phaseA01_intake.evidence_routes import EvidenceAPI

        # Initialize components
        kg = EnhancedKnowledgeGraph()
        claims_matrix = ComprehensiveClaimsMatrixIntegration(kg)
        evidence_api = EvidenceAPI()

        # Create enhanced generator
        generator = EnhancedSkeletalOutlineGenerator(kg, claims_matrix, evidence_api)

        return await generator.generate_enhanced_outline(case_id, session_id)

    except Exception as e:
        logger.error(f"Enhanced outline generation failed: {e}")
        return {"error": str(e)}


async def validate_claims_for_drafting(claims: List[str], jurisdiction: str) -> Dict[str, Any]:
    """
    Convenience function for claim validation during drafting
    """
    try:
        # Initialize minimal generator for validation
        from lawyerfactory.kg.enhanced_graph import EnhancedKnowledgeGraph

        kg = EnhancedKnowledgeGraph()
        generator = EnhancedSkeletalOutlineGenerator(kg, None, None)

        return await generator.validate_claims_for_drafting(claims, jurisdiction)

    except Exception as e:
        logger.error(f"Claim validation failed: {e}")
        return {"validation_performed": False, "error": str(e)}


if __name__ == "__main__":
    # Example usage
    async def test_enhanced_generator():
        try:
            result = await generate_enhanced_outline("test_case_001", "test_session_001")
            print(f"Enhanced outline generated: {result.get('enhancement_metadata', {})}")

            # Test claim validation
            validation = await validate_claims_for_drafting(
                ["negligence", "breach of contract"], "California"
            )
            print(f"Claim validation: {validation.get('validation_performed', False)}")

        except Exception as e:
            print(f"Test failed: {e}")

    asyncio.run(test_enhanced_generator())
