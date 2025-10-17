"""
IRAC Template System for Legal Document Drafting
Provides nested Issue-Rule-Application-Conclusion templates for structured legal writing.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class ElementAnalysis:
    """Analysis structure for a single legal element"""
    element_number: int
    element_name: str
    element_definition: str
    element_authority: str
    relevant_facts: List[str]
    application_analysis: str
    element_satisfied: bool
    confidence_score: float


@dataclass
class IRACSection:
    """Complete IRAC analysis for a cause of action"""
    cause_of_action_name: str
    issue_statement: str
    primary_authority: str
    citation: str
    elements: List[ElementAnalysis]
    overall_conclusion: str
    overall_confidence: float
    viable: bool
    missing_elements: List[str]
    uncertain_elements: List[str]


class IRACTemplateEngine:
    """Generates structured IRAC prompts for LLM drafting"""
    
    # Nested IRAC template for element-by-element analysis
    NESTED_IRAC_TEMPLATE = """
CAUSE OF ACTION: {cause_of_action_name}

I. ISSUE
{issue_statement}

II. RULE
Primary Legal Authority: {primary_authority}
Citation: {citation}

Elements Required:
{element_list}

III. APPLICATION (Element-by-Element Analysis)

{element_analyses}

IV. CONCLUSION
Based on the analysis of all elements, this cause of action is:

{conclusion_status}

Overall Confidence: {overall_confidence}%

{viability_assessment}
"""

    # Sub-template for individual element analysis
    ELEMENT_ANALYSIS_TEMPLATE = """
    Element {element_number}: {element_name}
    
    A. Sub-Issue
       Does the evidence satisfy the {element_name} requirement?
    
    B. Sub-Rule
       Definition: {element_definition}
       Authority: {element_authority}
    
    C. Sub-Application
       Facts from Evidence:
       {relevant_facts}
       
       Analysis:
       {application_analysis}
    
    D. Sub-Conclusion
       {element_conclusion}
       Confidence: {confidence_score}%
    
    {separator}
"""

    # Template for statement of facts (from shotlist)
    STATEMENT_OF_FACTS_TEMPLATE = """
STATEMENT OF FACTS

{fact_entries}

These facts are supported by the following evidence:
{evidence_citations}
"""

    # Template for prayer for relief
    PRAYER_TEMPLATE = """
PRAYER FOR RELIEF

WHEREFORE, Plaintiff respectfully requests that this Court:

{relief_requests}

Dated: {date}

Respectfully submitted,

_________________________
{attorney_name}
{bar_number}
Attorney for Plaintiff
"""

    @classmethod
    def generate_nested_irac_prompt(
        cls,
        irac_section: IRACSection,
        shotlist_facts: List[Dict[str, Any]],
        include_examples: bool = True
    ) -> str:
        """
        Generate a complete nested IRAC prompt for LLM drafting.
        
        Args:
            irac_section: Structured IRAC data from claims matrix
            shotlist_facts: Relevant facts from shotlist
            include_examples: Whether to include example language
            
        Returns:
            Formatted prompt string for LLM
        """
        # Format element list
        element_list = "\n".join([
            f"   {i+1}. {elem.element_name}"
            for i, elem in enumerate(irac_section.elements)
        ])
        
        # Generate element analyses
        element_analyses = []
        for elem in irac_section.elements:
            # Format relevant facts
            facts_text = "\n       ".join([
                f"- {fact}" for fact in elem.relevant_facts
            ])
            
            # Determine element conclusion text
            if elem.element_satisfied:
                elem_conclusion = f"✓ SATISFIED - The evidence clearly establishes {elem.element_name}."
            else:
                elem_conclusion = f"✗ NOT SATISFIED - Additional evidence needed for {elem.element_name}."
            
            # Generate analysis for this element
            analysis_text = cls.ELEMENT_ANALYSIS_TEMPLATE.format(
                element_number=elem.element_number,
                element_name=elem.element_name,
                element_definition=elem.element_definition,
                element_authority=elem.element_authority,
                relevant_facts=facts_text,
                application_analysis=elem.application_analysis,
                element_conclusion=elem_conclusion,
                confidence_score=int(elem.confidence_score * 100),
                separator="    " + "="*70
            )
            element_analyses.append(analysis_text)
        
        # Format conclusion status
        if irac_section.viable:
            conclusion_status = "[✓] VIABLE - All elements satisfied"
        elif irac_section.missing_elements:
            conclusion_status = f"[✗] NOT VIABLE - Missing element(s): {', '.join(irac_section.missing_elements)}"
        else:
            conclusion_status = f"[ ] UNCERTAIN - Requires additional discovery on: {', '.join(irac_section.uncertain_elements)}"
        
        # Viability assessment
        if irac_section.viable:
            viability_assessment = """
Recommendation: PROCEED WITH THIS CLAIM
This cause of action has strong evidentiary support and meets all required elements.
The complaint should include this claim with the analysis above.
"""
        elif irac_section.missing_elements:
            viability_assessment = f"""
Recommendation: ADDITIONAL DISCOVERY REQUIRED
Before including this claim, obtain evidence for: {', '.join(irac_section.missing_elements)}
Consider whether discovery will yield sufficient evidence to satisfy missing elements.
"""
        else:
            viability_assessment = f"""
Recommendation: CONDITIONAL INCLUSION
This claim may be viable pending clarification on: {', '.join(irac_section.uncertain_elements)}
Include in complaint but flag for additional development during discovery.
"""
        
        # Generate complete prompt
        return cls.NESTED_IRAC_TEMPLATE.format(
            cause_of_action_name=irac_section.cause_of_action_name,
            issue_statement=irac_section.issue_statement,
            primary_authority=irac_section.primary_authority,
            citation=irac_section.citation,
            element_list=element_list,
            element_analyses="\n".join(element_analyses),
            conclusion_status=conclusion_status,
            overall_confidence=int(irac_section.overall_confidence * 100),
            viability_assessment=viability_assessment
        )
    
    @classmethod
    def generate_statement_of_facts(
        cls,
        shotlist_facts: List[Dict[str, Any]],
        chronological: bool = True
    ) -> str:
        """
        Generate Statement of Facts section from shotlist.
        
        Args:
            shotlist_facts: List of fact entries from shotlist
            chronological: Whether to order chronologically (default True)
            
        Returns:
            Formatted statement of facts
        """
        if chronological:
            # Sort by timestamp
            sorted_facts = sorted(
                shotlist_facts,
                key=lambda x: x.get('timestamp', '')
            )
        else:
            sorted_facts = shotlist_facts
        
        # Generate numbered fact entries
        fact_entries = []
        citations = []
        
        for i, fact in enumerate(sorted_facts, 1):
            summary = fact.get('summary', '')
            timestamp = fact.get('timestamp', 'Unknown date')
            entities = fact.get('entities', [])
            cite = fact.get('citations', '')
            
            # Format fact entry
            fact_text = f"{i}. On {timestamp}, {summary}"
            fact_entries.append(fact_text)
            
            # Collect citations
            if cite:
                citations.append(f"[{i}] {cite}")
        
        fact_text = "\n".join(fact_entries)
        citation_text = "\n".join(citations) if citations else "See attached evidence."
        
        return cls.STATEMENT_OF_FACTS_TEMPLATE.format(
            fact_entries=fact_text,
            evidence_citations=citation_text
        )
    
    @classmethod
    def generate_prayer_for_relief(
        cls,
        relief_requests: List[str],
        attorney_name: str,
        bar_number: str,
        date: str
    ) -> str:
        """
        Generate Prayer for Relief section.
        
        Args:
            relief_requests: List of relief items requested
            attorney_name: Attorney's name
            bar_number: Bar number
            date: Filing date
            
        Returns:
            Formatted prayer for relief
        """
        # Format relief requests as numbered list
        formatted_requests = "\n".join([
            f"{i}. {request}"
            for i, request in enumerate(relief_requests, 1)
        ])
        
        return cls.PRAYER_TEMPLATE.format(
            relief_requests=formatted_requests,
            date=date,
            attorney_name=attorney_name,
            bar_number=bar_number
        )
    
    @classmethod
    def build_section_prompt(
        cls,
        section_type: str,
        section_data: Dict[str, Any],
        shotlist_facts: List[Dict[str, Any]],
        claims_matrix: Dict[str, Any],
        rag_context: Optional[List[str]] = None
    ) -> str:
        """
        Build a complete drafting prompt for a specific section.
        
        Args:
            section_type: Type of section (e.g., 'cause_of_action', 'statement_of_facts')
            section_data: Section-specific data from skeletal outline
            shotlist_facts: Relevant facts from shotlist
            claims_matrix: Claims matrix data
            rag_context: Optional similar document examples
            
        Returns:
            Complete prompt for LLM drafting
        """
        prompt_parts = []
        
        # Add system context
        prompt_parts.append("""
You are an expert legal writer drafting a court complaint. Use the IRAC method 
(Issue-Rule-Application-Conclusion) for legal analysis. Draft in clear, 
professional legal language following Federal Rules of Civil Procedure (FRCP).
""")
        
        # Add section-specific instructions
        if section_type == "cause_of_action":
            # Build IRAC analysis for this cause of action
            cause_name = section_data.get('cause_of_action_name', 'Unknown Claim')
            
            prompt_parts.append(f"""
TASK: Draft a complete cause of action section for {cause_name}.

REQUIREMENTS:
1. State the legal issue clearly
2. Cite primary legal authority
3. Analyze each element with supporting facts
4. Conclude whether the claim is viable

Use the following structure:
""")
            
            # Add IRAC template (simplified version for prompt)
            prompt_parts.append("""
I. ISSUE
   [State the legal question]

II. RULE
   [Primary authority and citation]
   [List required elements]

III. APPLICATION
   [For each element:]
   - Define the element
   - Apply facts to element
   - Conclude if satisfied

IV. CONCLUSION
   [Overall viability assessment]
""")
        
        elif section_type == "statement_of_facts":
            prompt_parts.append("""
TASK: Draft a Statement of Facts section.

REQUIREMENTS:
1. Present facts chronologically
2. Use numbered paragraphs
3. Include specific dates and entities
4. Cite evidence sources
5. Be objective and factual (no legal conclusions)

FACTS TO INCLUDE:
""")
            prompt_parts.append(
                cls.generate_statement_of_facts(shotlist_facts)
            )
        
        # Add RAG context if provided
        if rag_context:
            prompt_parts.append("\n\nREFERENCE EXAMPLES FROM SIMILAR COMPLAINTS:")
            for i, example in enumerate(rag_context, 1):
                prompt_parts.append(f"\n--- Example {i} ---\n{example}\n")
        
        # Add final instructions
        prompt_parts.append("""
\nOUTPUT FORMAT:
- Use clear headings and subheadings
- Number all paragraphs
- Include proper legal citations
- Draft in past tense for facts, present tense for legal arguments
- Be concise but thorough
- Aim for 300-500 words per section

Now draft this section:
""")
        
        return "\n".join(prompt_parts)


# Utility function to convert claims matrix to IRAC structure
def claims_matrix_to_irac(
    claim_data: Dict[str, Any],
    shotlist_facts: List[Dict[str, Any]]
) -> IRACSection:
    """
    Convert claims matrix data to IRAC structure.
    
    Args:
        claim_data: Claim data from ComprehensiveClaimsMatrixIntegration
        shotlist_facts: Facts from shotlist
        
    Returns:
        IRACSection object
    """
    # Extract elements from claim data
    elements = []
    element_analysis = claim_data.get('element_analysis', {})
    
    for elem_name, elem_data in element_analysis.items():
        # Get relevant facts for this element
        elem_facts = [
            fact.get('summary', '')
            for fact in shotlist_facts
            if elem_name.lower() in fact.get('summary', '').lower()
        ][:5]  # Limit to top 5 relevant facts
        
        breakdown = elem_data.get('breakdown', {})
        
        element = ElementAnalysis(
            element_number=len(elements) + 1,
            element_name=elem_name.replace('_', ' ').title(),
            element_definition=breakdown.get('definition', ''),
            element_authority=breakdown.get('authority', ''),
            relevant_facts=elem_facts,
            application_analysis=breakdown.get('analysis', ''),
            element_satisfied=elem_data.get('decision_outcome', {}).get('satisfied', False),
            confidence_score=elem_data.get('decision_outcome', {}).get('confidence', 0.5)
        )
        elements.append(element)
    
    # Determine overall viability
    satisfied_elements = [e for e in elements if e.element_satisfied]
    viable = len(satisfied_elements) == len(elements)
    missing = [e.element_name for e in elements if not e.element_satisfied]
    
    # Calculate overall confidence
    if elements:
        overall_confidence = sum(e.confidence_score for e in elements) / len(elements)
    else:
        overall_confidence = 0.0
    
    # Build IRAC section
    header = claim_data.get('header', {})
    legal_def = claim_data.get('legal_definition', {})
    
    return IRACSection(
        cause_of_action_name=header.get('cause_of_action', 'Unknown Claim'),
        issue_statement=f"Whether the evidence establishes all elements of {header.get('cause_of_action', 'this claim')}.",
        primary_authority=legal_def.get('primary_definition', ''),
        citation=legal_def.get('authority_citations', [''])[0] if legal_def.get('authority_citations') else '',
        elements=elements,
        overall_conclusion=claim_data.get('executive_summary', {}).get('case_strength', {}).get('overall_strength', 'Unknown'),
        overall_confidence=overall_confidence,
        viable=viable,
        missing_elements=missing,
        uncertain_elements=[]
    )
