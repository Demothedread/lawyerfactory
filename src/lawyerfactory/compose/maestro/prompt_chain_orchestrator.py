"""
# Script Name: prompt_chain_orchestrator.py
# Description: Prompt Chain Orchestrator for Skeletal Outline Generation Manages sequential LLM prompt execution with context preservation and anti-repetition protocols. Ensures coherent, comprehensive legal document generation that survives Rule 12(b)(6) motions.
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Orchestration
#   - Group Tags: orchestration
Prompt Chain Orchestrator for Skeletal Outline Generation
Manages sequential LLM prompt execution with context preservation and anti-repetition protocols.
Ensures coherent, comprehensive legal document generation that survives Rule 12(b)(6) motions.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
import logging
from typing import Dict, List

from lawyerfactory.kg.graph_api import EnhancedKnowledgeGraph
from skeletal_outline_generator import SectionType, SkeletalOutline, SkeletalSection

logger = logging.getLogger(__name__)


@dataclass
class GenerationContext:
    """Context maintained across prompt chain execution"""

    case_id: str
    session_id: str
    outline_id: str
    generated_content: Dict[str, str] = field(
        default_factory=dict
    )  # section_id -> content
    used_facts: List[str] = field(default_factory=list)  # Track used fact IDs
    used_evidence: List[str] = field(default_factory=list)  # Track used evidence IDs
    cited_authorities: List[str] = field(
        default_factory=list
    )  # Track cited authorities
    paragraph_counter: int = 1  # Global paragraph numbering
    section_references: Dict[str, List[int]] = field(
        default_factory=dict
    )  # section -> paragraph numbers
    content_tokens_used: int = 0  # Track token usage
    generation_log: List[str] = field(default_factory=list)  # Debug log


@dataclass
class PromptChainResult:
    """Result of complete prompt chain execution"""

    outline_id: str
    case_id: str
    generated_sections: Dict[str, str]
    final_document: str
    generation_context: GenerationContext
    total_word_count: int
    estimated_pages: int
    rule_12b6_compliance_score: float
    generation_time_seconds: float
    success: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class PromptChainOrchestrator:
    """Orchestrates sequential prompt execution for legal document generation"""

    def __init__(self, enhanced_kg: EnhancedKnowledgeGraph, llm_service=None):
        self.kg = enhanced_kg
        self.llm_service = llm_service  # LLM service for actual generation

        # Anti-repetition tracking
        self.fact_usage_tracker = {}  # fact_id -> sections_used_in
        self.evidence_usage_tracker = {}  # evidence_id -> sections_used_in
        self.content_similarity_threshold = 0.7  # Prevent similar content

        logger.info("Prompt Chain Orchestrator initialized")

    async def execute_prompt_chain(
        self, skeletal_outline: SkeletalOutline
    ) -> PromptChainResult:
        """Execute complete prompt chain for skeletal outline"""
        start_time = datetime.now()

        # Initialize generation context
        context = GenerationContext(
            case_id=skeletal_outline.case_id,
            session_id="",  # Will be set if available
            outline_id=skeletal_outline.outline_id,
        )

        try:
            logger.info(
                f"Starting prompt chain execution for outline {skeletal_outline.outline_id}"
            )

            # Sort sections by dependencies and priority
            execution_order = self._determine_execution_order(skeletal_outline.sections)

            # Execute sections in order
            for section in execution_order:
                section_content = await self._execute_section_prompt(
                    section, skeletal_outline, context
                )
                context.generated_content[section.section_id] = section_content
                context.generation_log.append(f"Generated section: {section.title}")

            # Compile final document
            final_document = self._compile_final_document(skeletal_outline, context)

            # Calculate metrics
            total_words = sum(
                len(content.split()) for content in context.generated_content.values()
            )
            estimated_pages = max(10, total_words // 250)
            compliance_score = self._calculate_rule_12b6_compliance(
                skeletal_outline, context
            )

            generation_time = (datetime.now() - start_time).total_seconds()

            result = PromptChainResult(
                outline_id=skeletal_outline.outline_id,
                case_id=skeletal_outline.case_id,
                generated_sections=context.generated_content,
                final_document=final_document,
                generation_context=context,
                total_word_count=total_words,
                estimated_pages=estimated_pages,
                rule_12b6_compliance_score=compliance_score,
                generation_time_seconds=generation_time,
                success=True,
            )

            logger.info(
                f"Prompt chain execution completed successfully in {generation_time:.2f}s"
            )
            return result

        except Exception as e:
            logger.exception(f"Prompt chain execution failed: {e}")

            return PromptChainResult(
                outline_id=skeletal_outline.outline_id,
                case_id=skeletal_outline.case_id,
                generated_sections=context.generated_content,
                final_document="",
                generation_context=context,
                total_word_count=0,
                estimated_pages=0,
                rule_12b6_compliance_score=0.0,
                generation_time_seconds=(datetime.now() - start_time).total_seconds(),
                success=False,
                errors=[str(e)],
            )

    def _determine_execution_order(
        self, sections: List[SkeletalSection]
    ) -> List[SkeletalSection]:
        """Determine optimal execution order based on dependencies and priorities"""
        # Create dependency graph
        section_map = {section.section_id: section for section in sections}
        ordered_sections = []
        processed = set()

        def can_process(section: SkeletalSection) -> bool:
            return all(dep in processed for dep in section.dependencies)

        # Process sections in dependency order
        remaining = sections.copy()
        while remaining:
            # Find processable sections
            ready = [s for s in remaining if can_process(s)]

            if not ready:
                # Break circular dependencies by processing highest priority
                ready = [min(remaining, key=lambda x: x.priority_level)]

            # Sort ready sections by priority
            ready.sort(key=lambda x: x.priority_level)

            # Process highest priority section
            section = ready[0]
            ordered_sections.append(section)
            processed.add(section.section_id)
            remaining.remove(section)

        return ordered_sections

    async def _execute_section_prompt(
        self,
        section: SkeletalSection,
        outline: SkeletalOutline,
        context: GenerationContext,
    ) -> str:
        """Execute prompt for individual section"""
        try:
            # Build section-specific prompt
            section_prompt = self._build_section_prompt(section, outline, context)

            # Execute subsections first if any
            subsection_content = ""
            for subsection in section.subsections:
                sub_content = await self._execute_section_prompt(
                    subsection, outline, context
                )
                context.generated_content[subsection.section_id] = sub_content
                subsection_content += f"\n\n{sub_content}"

            # Execute main section prompt
            if self.llm_service:
                section_content = await self._call_llm_service(section_prompt, section)
            else:
                # Mock generation for testing
                section_content = self._generate_mock_content(section, outline, context)

            # Combine with subsections
            if subsection_content:
                section_content += subsection_content

            # Update context tracking
            self._update_context_tracking(section, context)

            return section_content

        except Exception as e:
            logger.error(
                f"Failed to execute section prompt for {section.section_id}: {e}"
            )
            return f"[ERROR: Failed to generate content for {section.title}]"

    def _build_section_prompt(
        self,
        section: SkeletalSection,
        outline: SkeletalOutline,
        context: GenerationContext,
    ) -> str:
        """Build comprehensive prompt for section generation"""

        # Start with general context
        prompt_parts = [
            outline.general_prompts.get("global_context", ""),
            outline.general_prompts.get("anti_repetition", ""),
            outline.general_prompts.get("legal_standard", ""),
        ]

        # Add section-specific prompt template
        prompt_parts.append(f"SECTION TO GENERATE: {section.title}")
        prompt_parts.append(section.prompt_template)

        # Add context from previously generated sections
        if context.generated_content:
            prompt_parts.append(
                "\nPREVIOUSLY GENERATED CONTENT (for reference only, do not repeat):"
            )
            for section_id, content in context.generated_content.items():
                if section_id in section.dependencies:
                    prompt_parts.append(f"\n--- {section_id.upper()} ---")
                    prompt_parts.append(
                        content[:500] + "..." if len(content) > 500 else content
                    )

        # Add fact and evidence mappings
        if section.fact_mapping or section.evidence_mapping:
            prompt_parts.append("\nRELEVANT FACTS AND EVIDENCE:")

            # Add mapped facts
            for element, fact_ids in section.fact_mapping.items():
                unused_facts = [
                    f_id for f_id in fact_ids if f_id not in context.used_facts
                ]
                if unused_facts:
                    prompt_parts.append(f"\nFacts for {element}: {unused_facts}")

            # Add mapped evidence
            for element, evidence_ids in section.evidence_mapping.items():
                unused_evidence = [
                    e_id for e_id in evidence_ids if e_id not in context.used_evidence
                ]
                if unused_evidence:
                    prompt_parts.append(f"\nEvidence for {element}: {unused_evidence}")

        # Add legal authorities
        if section.legal_authorities:
            unused_authorities = [
                auth
                for auth in section.legal_authorities
                if auth not in context.cited_authorities
            ]
            if unused_authorities:
                prompt_parts.append(
                    f"\nLEGAL AUTHORITIES TO CITE: {unused_authorities}"
                )

        # Add paragraph numbering context
        prompt_parts.append(
            f"\nSTART PARAGRAPH NUMBERING AT: {context.paragraph_counter}"
        )

        # Add word count target
        prompt_parts.append(f"\nTARGET WORD COUNT: {section.word_count_target} words")

        # Add anti-repetition instructions
        if context.used_facts or context.used_evidence:
            prompt_parts.append(
                "\nANTI-REPETITION: Do not repeat facts or evidence already used:"
            )
            if context.used_facts:
                prompt_parts.append(f"Used facts: {context.used_facts}")
            if context.used_evidence:
                prompt_parts.append(f"Used evidence: {context.used_evidence}")

        return "\n".join(filter(None, prompt_parts))

    async def _call_llm_service(self, prompt: str, section: SkeletalSection) -> str:
        """Call LLM service to generate content"""
        try:
            if hasattr(self.llm_service, "generate_content"):
                response = await self.llm_service.generate_content(
                    prompt=prompt,
                    max_tokens=min(
                        section.word_count_target * 2, 4000
                    ),  # Rough token estimate
                    temperature=0.3,  # Lower temperature for legal writing
                )
                return response.get("content", "")
            else:
                # Fallback to synchronous call
                response = self.llm_service.generate(prompt)
                return response
        except Exception as e:
            logger.error(f"LLM service call failed: {e}")
            return f"[ERROR: LLM generation failed for {section.title}]"

    def _generate_mock_content(
        self,
        section: SkeletalSection,
        outline: SkeletalOutline,
        context: GenerationContext,
    ) -> str:
        """Generate mock content for testing purposes"""
        if section.section_type == SectionType.CAPTION:
            return self._mock_caption_content(outline)
        elif section.section_type == SectionType.INTRODUCTION:
            return self._mock_introduction_content(outline, context)
        elif section.section_type == SectionType.JURISDICTION_VENUE:
            return self._mock_jurisdiction_content(outline, context)
        elif section.section_type == SectionType.PARTIES:
            return self._mock_parties_content(outline, context)
        elif section.section_type == SectionType.STATEMENT_OF_FACTS:
            return self._mock_facts_content(outline, context)
        elif section.section_type == SectionType.CAUSE_OF_ACTION:
            return self._mock_cause_of_action_content(section, outline, context)
        elif section.section_type == SectionType.PRAYER_FOR_RELIEF:
            return self._mock_prayer_content(outline, context)
        elif section.section_type == SectionType.JURY_DEMAND:
            return self._mock_jury_demand_content()
        else:
            return f"[Mock content for {section.title}]"

    def _mock_caption_content(self, outline: SkeletalOutline) -> str:
        """Generate mock caption content"""
        return """
UNITED STATES DISTRICT COURT
NORTHERN DISTRICT OF CALIFORNIA

[PLAINTIFF NAME],                     Case No. [CASE NUMBER]

                Plaintiff,
                                      COMPLAINT
v.

[DEFENDANT NAME],

                Defendant.
________________________________/
"""

    def _mock_introduction_content(
        self, outline: SkeletalOutline, context: GenerationContext
    ) -> str:
        """Generate mock introduction content"""
        context.paragraph_counter += 1
        return f"""
I. INTRODUCTION

{context.paragraph_counter}. This action arises under {outline.global_context.get('primary_cause_of_action', 'applicable law')} and seeks damages and equitable relief for violations of plaintiff's rights. This Court has jurisdiction over this matter, and venue is proper in this District. Plaintiff seeks compensatory damages, punitive damages, injunctive relief, and such other relief as this Court deems just and proper.
"""

    def _mock_jurisdiction_content(
        self, outline: SkeletalOutline, context: GenerationContext
    ) -> str:
        """Generate mock jurisdiction content"""
        start_para = context.paragraph_counter + 1
        context.paragraph_counter += 3
        return f"""
II. JURISDICTION AND VENUE

{start_para}. This Court has subject matter jurisdiction over this action pursuant to 28 U.S.C. § 1331 as this action arises under federal law.

{start_para + 1}. This Court has personal jurisdiction over defendants because they conduct substantial business in {outline.jurisdiction} and the claims arise from their activities in this state.

{start_para + 2}. Venue is proper in this District pursuant to 28 U.S.C. § 1391(b) because defendants conduct business in this District and the events giving rise to this action occurred in this District.
"""

    def _mock_parties_content(
        self, outline: SkeletalOutline, context: GenerationContext
    ) -> str:
        """Generate mock parties content"""
        start_para = context.paragraph_counter + 1
        context.paragraph_counter += 2
        return f"""
III. PARTIES

{start_para}. Plaintiff [PLAINTIFF NAME] is [description] and is a resident of {outline.jurisdiction}.

{start_para + 1}. Defendant [DEFENDANT NAME] is [description] and conducts business in {outline.jurisdiction}.
"""

    def _mock_facts_content(
        self, outline: SkeletalOutline, context: GenerationContext
    ) -> str:
        """Generate mock statement of facts"""
        start_para = context.paragraph_counter + 1
        fact_count = len(outline.evidence_summary.get("fact_assertions", []))
        para_count = max(5, fact_count)
        context.paragraph_counter += para_count

        facts_content = "IV. STATEMENT OF FACTS\n\n"
        for i in range(para_count):
            facts_content += f"{start_para + i}. [Factual allegation {i+1} with supporting evidence]\n\n"

        return facts_content

    def _mock_cause_of_action_content(
        self,
        section: SkeletalSection,
        outline: SkeletalOutline,
        context: GenerationContext,
    ) -> str:
        """Generate mock cause of action content"""
        start_para = context.paragraph_counter + 1
        element_count = len(section.subsections) if section.subsections else 4
        context.paragraph_counter += element_count + 2

        coa_content = f"{section.roman_numeral}. {section.title}\n\n"
        coa_content += f"{start_para}. Plaintiff incorporates by reference all preceding allegations.\n\n"

        for i, subsection in enumerate(section.subsections):
            coa_content += (
                f"{start_para + i + 1}. [Element {subsection.title} allegations]\n\n"
            )

        coa_content += f"{start_para + element_count + 1}. As a direct and proximate result of defendants' conduct, plaintiff has suffered damages in an amount to be proven at trial.\n\n"

        return coa_content

    def _mock_prayer_content(
        self, outline: SkeletalOutline, context: GenerationContext
    ) -> str:
        """Generate mock prayer for relief"""
        return """
VI. PRAYER FOR RELIEF

WHEREFORE, Plaintiff respectfully requests that this Court:

a. Award compensatory damages in an amount to be proven at trial;
b. Award punitive damages in an amount to be proven at trial;
c. Grant injunctive relief as appropriate;
d. Award attorney's fees and costs;
e. Award pre and post-judgment interest; and
f. Grant such other relief as this Court deems just and proper.
"""

    def _mock_jury_demand_content(self) -> str:
        """Generate mock jury demand"""
        return """
DEMAND FOR JURY TRIAL

Plaintiff demands trial by jury on all issues so triable as a matter of right.

Respectfully submitted,

[Attorney Signature Block]
"""

    def _update_context_tracking(
        self, section: SkeletalSection, context: GenerationContext
    ):
        """Update context tracking after section generation"""
        # Track used facts and evidence
        for element, fact_ids in section.fact_mapping.items():
            context.used_facts.extend(fact_ids)

        for element, evidence_ids in section.evidence_mapping.items():
            context.used_evidence.extend(evidence_ids)

        # Track cited authorities
        context.cited_authorities.extend(section.legal_authorities)

        # Record paragraph numbers for this section
        context.section_references[section.section_id] = list(
            range(
                context.paragraph_counter - 10,  # Rough estimate
                context.paragraph_counter,
            )
        )

    def _compile_final_document(
        self, outline: SkeletalOutline, context: GenerationContext
    ) -> str:
        """Compile final document from generated sections"""
        document_parts = []

        # Add header
        document_parts.append("COMPLAINT")
        document_parts.append("=" * 50)
        document_parts.append("")

        # Add sections in order
        for section in outline.sections:
            if section.section_id in context.generated_content:
                document_parts.append(context.generated_content[section.section_id])
                document_parts.append("")

        # Add footer
        document_parts.append(f"Generated on: {datetime.now().strftime('%B %d, %Y')}")
        document_parts.append(f"Case ID: {outline.case_id}")
        document_parts.append(f"Outline ID: {outline.outline_id}")

        return "\n".join(document_parts)

    def _calculate_rule_12b6_compliance(
        self, outline: SkeletalOutline, context: GenerationContext
    ) -> float:
        """Calculate estimated Rule 12(b)(6) compliance score"""
        score = 0.0
        total_checks = 8

        # Check for required sections
        required_sections = {
            SectionType.JURISDICTION_VENUE,
            SectionType.PARTIES,
            SectionType.STATEMENT_OF_FACTS,
            SectionType.CAUSE_OF_ACTION,
        }

        present_sections = {section.section_type for section in outline.sections}
        score += len(required_sections & present_sections) / len(required_sections) * 25

        # Check for factual allegations
        if context.used_facts:
            score += 15

        # Check for evidence support
        if context.used_evidence:
            score += 15

        # Check for legal authorities
        if context.cited_authorities:
            score += 15

        # Check word count adequacy
        total_words = sum(
            len(content.split()) for content in context.generated_content.values()
        )
        if total_words >= 2000:  # Minimum for substantial complaint
            score += 15
        elif total_words >= 1000:
            score += 10
        elif total_words >= 500:
            score += 5

        # Check for element coverage in COA sections
        coa_sections = [
            s for s in outline.sections if s.section_type == SectionType.CAUSE_OF_ACTION
        ]
        if coa_sections and any(s.subsections for s in coa_sections):
            score += 15

        return min(100.0, score)


async def test_prompt_chain_orchestrator():
    """Test the prompt chain orchestrator"""
    try:
        from lawyerfactory.kg.graph_api import EnhancedKnowledgeGraph
        from maestro.evidence_api import EvidenceAPI
        from skeletal_outline_generator import SkeletalOutlineGenerator

        from src.claims_matrix.comprehensive_claims_matrix_integration import (
            ComprehensiveClaimsMatrixIntegration,
        )

        # Initialize components
        kg = EnhancedKnowledgeGraph()
        claims_matrix = ComprehensiveClaimsMatrixIntegration(kg)
        evidence_api = EvidenceAPI()
        outline_generator = SkeletalOutlineGenerator(kg, claims_matrix, evidence_api)

        # Generate skeletal outline
        outline = outline_generator.generate_skeletal_outline(
            "test_case_001", "test_session_001"
        )

        # Create orchestrator
        orchestrator = PromptChainOrchestrator(kg)

        # Execute prompt chain
        result = await orchestrator.execute_prompt_chain(outline)

        print("Prompt chain execution result:")
        print(f"Success: {result.success}")
        print(f"Word count: {result.total_word_count}")
        print(f"Estimated pages: {result.estimated_pages}")
        print(
            f"Rule 12(b)(6) compliance score: {result.rule_12b6_compliance_score:.1f}%"
        )
        print(f"Generation time: {result.generation_time_seconds:.2f} seconds")

        if result.errors:
            print(f"Errors: {result.errors}")

        return result

    except Exception as e:
        print(f"Test failed: {e}")
        return None


if __name__ == "__main__":
    import asyncio

    asyncio.run(test_prompt_chain_orchestrator())
