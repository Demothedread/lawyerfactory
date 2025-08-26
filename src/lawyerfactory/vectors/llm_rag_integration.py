"""
LLM RAG Integration for LawyerFactory Vector Stores

This module provides seamless integration between LLM services and vector stores,
enabling retrieval-augmented generation for legal document processing.

Features:
- Context retrieval from vector stores
- LLM-powered document generation with evidence
- IRAC/IR{C}C format integration
- Citation-aware generation
- Multi-turn conversation with vector memory
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from .enhanced_vector_store import (
    EnhancedVectorStoreManager, VectorStoreType, ValidationType
)
from .research_integration import ResearchRoundsManager

logger = logging.getLogger(__name__)


class RAGContext:
    """Container for RAG context and metadata"""

    def __init__(self, query: str, contexts: List[str], metadata: Dict[str, Any]):
        self.query = query
        self.contexts = contexts
        self.metadata = metadata
        self.created_at = datetime.now()
        self.context_hash = hash("".join(contexts))


class LegalDocumentGenerator:
    """
    LLM-powered legal document generator with RAG integration
    """

    def __init__(self, vector_store_manager: Optional[EnhancedVectorStoreManager] = None,
                 research_manager: Optional[ResearchRoundsManager] = None,
                 llm_service=None):
        self.vector_store = vector_store_manager or EnhancedVectorStoreManager()
        self.research_manager = research_manager or ResearchRoundsManager()
        self.llm_service = llm_service

        # Document generation templates
        self.templates = self._initialize_templates()

        # Generation history for context
        self.generation_history: List[Dict[str, Any]] = []

    def _initialize_templates(self) -> Dict[str, str]:
        """Initialize document generation templates"""
        return {
            "complaint_header": """
IN THE UNITED STATES DISTRICT COURT
FOR THE {jurisdiction}

{plaintiff_name},
Plaintiff,

v.

{DEFENDANT_NAME},
Defendant.

CASE NO. {case_number}

COMPLAINT FOR {cause_of_action}
""",

            "irac_issue": """
ISSUE {number}

{issue_statement}

""",

            "irac_rule": """
RULE

{legal_rule}

""",

            "irac_analysis": """
ANALYSIS

{legal_analysis}

""",

            "irac_conclusion": """
CONCLUSION

{legal_conclusion}

""",

            "irc_issue": """
ISSUE {number}

{issue_statement}

""",

            "irc_rule": """
RULE

{legal_rule}

""",

            "irc_conclusion": """
CONCLUSION

{legal_conclusion}

""",

            "citation_format": "[{authority_name}, {year}]",

            "evidence_reference": "See {document_type}: {document_title} (stored {date})"
        }

    async def generate_legal_document(self, document_type: str, case_data: Dict[str, Any],
                                    context_query: str = "", use_rag: bool = True) -> Dict[str, Any]:
        """
        Generate a legal document using RAG-enhanced LLM

        Args:
            document_type: Type of document to generate
            case_data: Case information and facts
            context_query: Query to find relevant context
            use_rag: Whether to use RAG for context

        Returns:
            Generated document with metadata
        """
        try:
            start_time = datetime.now()

            # Get RAG context if requested
            rag_context = None
            if use_rag and context_query:
                rag_context = await self._get_rag_context(context_query, case_data)

            # Get research context if available
            research_context = None
            case_id = case_data.get("case_id")
            if case_id:
                research_context = await self.research_manager.get_research_context(
                    case_id, context_query
                )

            # Generate document based on type
            if document_type == "complaint":
                content = await self._generate_complaint(case_data, rag_context, research_context)
            elif document_type == "brief":
                content = await self._generate_brief(case_data, rag_context, research_context)
            elif document_type == "motion":
                content = await self._generate_motion(case_data, rag_context, research_context)
            else:
                content = await self._generate_general_document(document_type, case_data, rag_context, research_context)

            # Calculate generation metrics
            generation_time = (datetime.now() - start_time).total_seconds()
            word_count = len(content.split())

            result = {
                "success": True,
                "document_type": document_type,
                "content": content,
                "word_count": word_count,
                "generation_time": generation_time,
                "rag_context_used": rag_context is not None,
                "research_context_used": research_context is not None,
                "context_sources": self._extract_context_sources(rag_context, research_context),
                "citations_found": self._count_citations(content),
                "generated_at": datetime.now().isoformat()
            }

            # Store generation in history
            self.generation_history.append({
                "document_type": document_type,
                "case_id": case_id,
                "word_count": word_count,
                "generation_time": generation_time,
                "timestamp": datetime.now().isoformat()
            })

            return result

        except Exception as e:
            logger.error(f"Error generating legal document: {e}")
            return {
                "success": False,
                "error": str(e),
                "document_type": document_type
            }

    async def _get_rag_context(self, query: str, case_data: Dict[str, Any]) -> RAGContext:
        """Get RAG context from vector stores"""
        try:
            # Get contexts from vector store
            contexts = await self.vector_store.rag_retrieve_context(
                query=query,
                max_contexts=5,
                context_window=1500
            )

            # Add metadata
            metadata = {
                "query": query,
                "context_count": len(contexts),
                "case_id": case_data.get("case_id"),
                "total_context_length": sum(len(ctx) for ctx in contexts)
            }

            return RAGContext(query, contexts, metadata)

        except Exception as e:
            logger.error(f"Error getting RAG context: {e}")
            return RAGContext(query, [], {"error": str(e)})

    async def _generate_complaint(self, case_data: Dict[str, Any],
                                rag_context: Optional[RAGContext],
                                research_context: Optional[Dict]) -> str:
        """Generate a complaint using RAG context"""
        try:
            # Build complaint structure
            complaint_parts = []

            # Header
            header = self.templates["complaint_header"].format(
                jurisdiction=case_data.get("jurisdiction", "NORTHERN DISTRICT OF CALIFORNIA"),
                plaintiff_name=case_data.get("plaintiff_name", "Plaintiff"),
                defendant_name=case_data.get("defendant_name", "Defendant"),
                case_number=case_data.get("case_number", "Case No. TBD"),
                cause_of_action=case_data.get("cause_of_action", "Damages")
            )
            complaint_parts.append(header)

            # Introduction
            introduction = self._generate_introduction(case_data, rag_context)
            complaint_parts.append(introduction)

            # Causes of action with IRAC structure
            causes_of_action = case_data.get("causes_of_action", ["Negligence"])
            for i, cause in enumerate(causes_of_action, 1):
                cause_section = await self._generate_cause_section(
                    cause, i, case_data, rag_context, research_context
                )
                complaint_parts.append(cause_section)

            # Prayer for relief
            prayer = self._generate_prayer_for_relief(case_data)
            complaint_parts.append(prayer)

            return "\n\n".join(complaint_parts)

        except Exception as e:
            logger.error(f"Error generating complaint: {e}")
            return f"Error generating complaint: {str(e)}"

    async def _generate_cause_section(self, cause_name: str, section_number: int,
                                    case_data: Dict[str, Any],
                                    rag_context: Optional[RAGContext],
                                    research_context: Optional[Dict]) -> str:
        """Generate a cause of action section using IRAC format"""
        try:
            section_parts = []

            # Issue
            issue = self.templates["irac_issue"].format(
                number=section_number,
                issue_statement=self._generate_issue_statement(cause_name, case_data)
            )
            section_parts.append(issue)

            # Rule
            rule = self.templates["irac_rule"].format(
                legal_rule=self._generate_legal_rule(cause_name, rag_context, research_context)
            )
            section_parts.append(rule)

            # Analysis
            analysis = self.templates["irac_analysis"].format(
                legal_analysis=self._generate_legal_analysis(cause_name, case_data, rag_context, research_context)
            )
            section_parts.append(analysis)

            # Conclusion
            conclusion = self.templates["irac_conclusion"].format(
                legal_conclusion=self._generate_legal_conclusion(cause_name, case_data)
            )
            section_parts.append(conclusion)

            return "\n".join(section_parts)

        except Exception as e:
            logger.error(f"Error generating cause section: {e}")
            return f"Error generating cause section for {cause_name}: {str(e)}"

    def _generate_introduction(self, case_data: Dict[str, Any],
                             rag_context: Optional[RAGContext]) -> str:
        """Generate complaint introduction"""
        plaintiff = case_data.get("plaintiff_name", "Plaintiff")
        defendant = case_data.get("defendant_name", "Defendant")
        claim_description = case_data.get("claim_description", "the claims alleged herein")

        introduction = f"""
INTRODUCTION

1. {plaintiff} brings this action against {defendant} to recover damages arising from {claim_description}.

2. This Court has jurisdiction over this action pursuant to [jurisdictional basis].

3. Venue is proper in this Court pursuant to [venue basis].

4. The claims asserted herein are based on the following facts, which are alleged upon information and belief where the basis of knowledge is stated, and upon personal knowledge as to the remainder.
"""

        # Add RAG context if available
        if rag_context and rag_context.contexts:
            introduction += "\n5. The following evidence supports these allegations:\n"
            for i, context in enumerate(rag_context.contexts[:3], 1):
                # Truncate context for introduction
                truncated = context[:200] + "..." if len(context) > 200 else context
                introduction += f"   {i}. {truncated}\n"

        return introduction

    def _generate_issue_statement(self, cause_name: str, case_data: Dict[str, Any]) -> str:
        """Generate issue statement for IRAC"""
        if cause_name.lower() == "negligence":
            return f"Whether {case_data.get('defendant_name', 'Defendant')} was negligent in its actions that caused harm to {case_data.get('plaintiff_name', 'Plaintiff')}."
        elif cause_name.lower() == "breach of contract":
            return f"Whether {case_data.get('defendant_name', 'Defendant')} breached its contractual obligations to {case_data.get('plaintiff_name', 'Plaintiff')}."
        else:
            return f"Whether {case_data.get('defendant_name', 'Defendant')} is liable to {case_data.get('plaintiff_name', 'Plaintiff')} for {cause_name.lower()}."

    def _generate_legal_rule(self, cause_name: str, rag_context: Optional[RAGContext],
                           research_context: Optional[Dict]) -> str:
        """Generate legal rule section with citations"""
        base_rules = {
            "negligence": "To establish negligence, a plaintiff must prove: (1) duty of care, (2) breach of duty, (3) causation, and (4) damages.",
            "breach of contract": "To establish breach of contract, a plaintiff must prove: (1) existence of contract, (2) performance by plaintiff, (3) breach by defendant, and (4) damages."
        }

        rule = base_rules.get(cause_name.lower(), f"The elements of {cause_name} must be established.")

        # Add citations from research context
        if research_context and "supporting_citations" in research_context:
            citations = research_context["supporting_citations"][:3]  # Limit to 3 citations
            if citations:
                rule += "\n\nSupporting authorities include:"
                for citation in citations:
                    rule += f"\n- {citation}"

        return rule

    def _generate_legal_analysis(self, cause_name: str, case_data: Dict[str, Any],
                               rag_context: Optional[RAGContext],
                               research_context: Optional[Dict]) -> str:
        """Generate legal analysis section"""
        analysis = f"Analysis of the {cause_name.lower()} claim:\n\n"

        # Add case-specific facts
        claim_description = case_data.get("claim_description", "the incident in question")
        analysis += f"The plaintiff alleges that {claim_description}. "

        # Add evidence from RAG context
        if rag_context and rag_context.contexts:
            analysis += "Supporting evidence includes:\n"
            for context in rag_context.contexts[:2]:
                truncated = context[:300] + "..." if len(context) > 300 else context
                analysis += f"- {truncated}\n"

        # Add research findings
        if research_context and "relevant_findings" in research_context:
            analysis += "\nRelevant research findings:\n"
            for finding in research_context["relevant_findings"][:2]:
                analysis += f"- {finding['content'][:200]}...\n"

        return analysis

    def _generate_legal_conclusion(self, cause_name: str, case_data: Dict[str, Any]) -> str:
        """Generate legal conclusion"""
        plaintiff = case_data.get("plaintiff_name", "Plaintiff")
        defendant = case_data.get("defendant_name", "Defendant")

        return f"Based on the foregoing, {plaintiff} has established a valid claim for {cause_name.lower()} against {defendant}."

    def _generate_prayer_for_relief(self, case_data: Dict[str, Any]) -> str:
        """Generate prayer for relief"""
        claim_amount = case_data.get("claim_amount", 0)

        prayer = """
PRAYER FOR RELIEF

WHEREFORE, Plaintiff respectfully requests that this Court enter judgment in favor of Plaintiff and against Defendant as follows:

1. Award compensatory damages in an amount to be determined at trial;
2. Award punitive damages in an amount to be determined at trial;
3. Award pre-judgment and post-judgment interest at the maximum rate allowed by law;
4. Award costs of suit and reasonable attorney's fees; and
5. Grant such other and further relief as the Court deems just and proper.
"""

        if claim_amount > 0:
            prayer = prayer.replace("to be determined at trial", f"no less than ${claim_amount:,}")

        return prayer

    def _generate_brief(self, case_data: Dict[str, Any],
                       rag_context: Optional[RAGContext],
                       research_context: Optional[Dict]) -> str:
        """Generate a legal brief"""
        # Simplified brief generation - in production would be more comprehensive
        brief = f"""
LEGAL BRIEF

Case: {case_data.get('case_name', 'Unknown Case')}

TABLE OF CONTENTS

I. INTRODUCTION
II. STATEMENT OF FACTS
III. LEGAL ARGUMENT
IV. CONCLUSION

I. INTRODUCTION

This brief addresses the legal issues in the above-referenced matter.

II. STATEMENT OF FACTS

{case_data.get('claim_description', 'Facts to be developed.')}

III. LEGAL ARGUMENT

[Legal arguments would be developed here using IRAC format]

IV. CONCLUSION

[Conclusion would be provided here]
"""
        return brief

    def _generate_motion(self, case_data: Dict[str, Any],
                        rag_context: Optional[RAGContext],
                        research_context: Optional[Dict]) -> str:
        """Generate a legal motion"""
        motion = f"""
NOTICE OF MOTION AND MOTION FOR [RELIEF]

{case_data.get('plaintiff_name', 'Plaintiff')}, by and through counsel, hereby gives notice that on [date], at [time], or as soon thereafter as the matter may be heard, Plaintiff will move this Court for an order [relief requested].

This motion is based on the following memorandum of points and authorities, the declarations filed herewith, and the records and files in this case.
"""
        return motion

    async def _generate_general_document(self, document_type: str, case_data: Dict[str, Any],
                                       rag_context: Optional[RAGContext],
                                       research_context: Optional[Dict]) -> str:
        """Generate a general legal document"""
        return f"""
{document_type.upper()}

Generated for Case: {case_data.get('case_name', 'Unknown Case')}

[Content would be generated based on document type: {document_type}]

Generated using RAG context: {len(rag_context.contexts) if rag_context else 0} sources
Research rounds integrated: {len(research_context.get('relevant_findings', [])) if research_context else 0} findings
"""

    def _extract_context_sources(self, rag_context: Optional[RAGContext],
                               research_context: Optional[Dict]) -> List[str]:
        """Extract sources used for context"""
        sources = []

        if rag_context:
            sources.extend([f"RAG: {len(rag_context.contexts)} contexts"])

        if research_context:
            findings = research_context.get('relevant_findings', [])
            citations = research_context.get('supporting_citations', [])
            sources.extend([
                f"Research: {len(findings)} findings",
                f"Citations: {len(citations)} authorities"
            ])

        return sources

    def _count_citations(self, content: str) -> int:
        """Count legal citations in content"""
        # Simple citation counting - in production would use more sophisticated detection
        citation_patterns = [
            r'\d+\s+Cal\.\s+\d+',  # California citations
            r'\d+\s+U\.S\.\s+\d+',  # US Supreme Court
            r'\d+\s+F\.\s+\d+',    # Federal Reporter
        ]

        total_citations = 0
        for pattern in citation_patterns:
            import re
            total_citations += len(re.findall(pattern, content))

        return total_citations

    def get_generation_stats(self) -> Dict[str, Any]:
        """Get document generation statistics"""
        if not self.generation_history:
            return {"total_generations": 0}

        total_words = sum(h.get("word_count", 0) for h in self.generation_history)
        total_time = sum(h.get("generation_time", 0) for h in self.generation_history)

        return {
            "total_generations": len(self.generation_history),
            "total_words_generated": total_words,
            "average_words_per_generation": total_words / len(self.generation_history),
            "total_generation_time": total_time,
            "average_generation_time": total_time / len(self.generation_history),
            "document_types_generated": list(set(h.get("document_type") for h in self.generation_history))
        }


class LLMConversationManager:
    """
    Manages multi-turn conversations with LLM using vector store memory
    """

    def __init__(self, vector_store_manager: Optional[EnhancedVectorStoreManager] = None,
                 document_generator: Optional[LegalDocumentGenerator] = None):
        self.vector_store = vector_store_manager or EnhancedVectorStoreManager()
        self.document_generator = document_generator or LegalDocumentGenerator()

        # Conversation history
        self.conversations: Dict[str, List[Dict[str, Any]]] = {}

    async def process_legal_query(self, query: str, conversation_id: str = "default",
                                case_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a legal query with vector-enhanced LLM response

        Args:
            query: User's legal question
            conversation_id: Conversation identifier
            case_context: Case-specific context

        Returns:
            LLM response with sources
        """
        try:
            # Get conversation history
            if conversation_id not in self.conversations:
                self.conversations[conversation_id] = []

            history = self.conversations[conversation_id]

            # Get relevant context from vector stores
            context_query = f"{query} {' '.join(case_context.values()) if case_context else ''}"
            rag_context = await self.vector_store.rag_retrieve_context(
                query=context_query,
                max_contexts=3,
                context_window=1000
            )

            # Build prompt with context
            prompt = self._build_legal_prompt(query, rag_context, history, case_context)

            # Generate response (simplified - would use actual LLM)
            response = await self._generate_llm_response(prompt)

            # Store conversation
            conversation_entry = {
                "query": query,
                "response": response,
                "context_sources": len(rag_context) if rag_context else 0,
                "timestamp": datetime.now().isoformat()
            }
            history.append(conversation_entry)

            # Keep conversation history manageable
            if len(history) > 50:
                history = history[-50:]
                self.conversations[conversation_id] = history

            return {
                "success": True,
                "response": response,
                "context_sources": len(rag_context) if rag_context else 0,
                "conversation_length": len(history)
            }

        except Exception as e:
            logger.error(f"Error processing legal query: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _build_legal_prompt(self, query: str, rag_context: List[str],
                          history: List[Dict[str, Any]], case_context: Dict[str, Any]) -> str:
        """Build a legal-focused prompt with context"""
        prompt_parts = []

        # System instruction
        prompt_parts.append("""
You are an expert legal assistant with access to comprehensive legal knowledge and case-specific information.
Provide accurate, well-reasoned legal analysis based on the provided context and your legal expertise.
""")

        # Case context
        if case_context:
            prompt_parts.append(f"\nCase Context: {case_context}")

        # RAG context
        if rag_context:
            prompt_parts.append("\nRelevant Legal Information:")
            for i, context in enumerate(rag_context, 1):
                prompt_parts.append(f"{i}. {context}")

        # Conversation history
        if history:
            prompt_parts.append("\nRecent Conversation:")
            for entry in history[-3:]:  # Last 3 exchanges
                prompt_parts.append(f"Q: {entry['query']}")
                prompt_parts.append(f"A: {entry['response'][:200]}...")

        # Current query
        prompt_parts.append(f"\nCurrent Query: {query}")
        prompt_parts.append("\nProvide a comprehensive legal analysis:")

        return "\n".join(prompt_parts)

    async def _generate_llm_response(self, prompt: str) -> str:
        """Generate LLM response (placeholder - would integrate with actual LLM)"""
        # This would integrate with the actual LLM service
        # For now, return a structured legal response

        response = f"""
Based on the legal information provided and my analysis:

**Legal Analysis:**

The query raises important legal considerations that require careful examination of the applicable law and facts.

**Key Legal Principles:**

1. **Relevant Legal Framework:** The analysis must consider the governing legal principles and statutory framework.

2. **Case-Specific Application:** The specific facts and circumstances of this case are critical to the legal determination.

**Recommendations:**

1. **Immediate Steps:** Consider consulting with legal counsel to assess the specific legal implications.
2. **Documentation:** Ensure all relevant evidence and documentation are properly preserved.
3. **Further Research:** Additional legal research may be necessary to fully address the query.

**Disclaimer:** This analysis is for informational purposes only and does not constitute legal advice.

---
*Response generated using vector-enhanced legal analysis with {len(prompt.split())} context tokens.*
"""
        return response


# Global instances for easy access
legal_document_generator = LegalDocumentGenerator()
llm_conversation_manager = LLMConversationManager()