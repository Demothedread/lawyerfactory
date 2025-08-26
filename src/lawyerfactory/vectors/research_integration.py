"""
Research Rounds Integration for LawyerFactory Vector Store

This module provides seamless integration between research phases and the vector storage system,
enabling the accumulation of knowledge across research iterations and providing enhanced
retrieval capabilities for drafting and analysis.

Features:
- Research round tracking and accumulation
- Knowledge synthesis across rounds
- Vector-enhanced research retrieval
- Research quality assessment
- Integration with LLM augmentation
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from .enhanced_vector_store import (
    EnhancedVectorStoreManager, VectorStoreType, ValidationType
)

logger = logging.getLogger(__name__)


class ResearchRound:
    """Represents a single research round with its findings and metadata"""

    def __init__(self, round_number: int, case_id: str, research_type: str):
        self.round_number = round_number
        self.case_id = case_id
        self.research_type = research_type
        self.findings: List[str] = []
        self.citations: List[Dict[str, Any]] = []
        self.questions_answered: List[str] = []
        self.new_questions_raised: List[str] = []
        self.confidence_score: float = 0.0
        self.vector_document_ids: List[str] = []
        self.created_at = datetime.now()
        self.metadata: Dict[str, Any] = {}

    def add_finding(self, finding: str, source: str = "", confidence: float = 0.8):
        """Add a research finding"""
        self.findings.append(finding)
        self.metadata[f"finding_{len(self.findings)}"] = {
            "content": finding,
            "source": source,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat()
        }

    def add_citation(self, citation: str, authority_level: str = "secondary",
                    relevance_score: float = 0.7):
        """Add a legal citation"""
        self.citations.append({
            "citation": citation,
            "authority_level": authority_level,
            "relevance_score": relevance_score,
            "added_in_round": self.round_number
        })

    def synthesize_content(self) -> str:
        """Synthesize all findings into a comprehensive research summary"""
        if not self.findings:
            return f"Research Round {self.round_number}: No findings recorded."

        synthesis = f"Research Round {self.round_number} - {self.research_type.upper()}\n\n"

        synthesis += "Key Findings:\n"
        for i, finding in enumerate(self.findings, 1):
            synthesis += f"{i}. {finding}\n"

        if self.citations:
            synthesis += f"\nSupporting Authorities ({len(self.citations)}):\n"
            for citation in self.citations:
                synthesis += f"- {citation['citation']} ({citation['authority_level']})\n"

        if self.questions_answered:
            synthesis += f"\nQuestions Answered ({len(self.questions_answered)}):\n"
            for question in self.questions_answered:
                synthesis += f"- {question}\n"

        if self.new_questions_raised:
            synthesis += f"\nNew Questions Raised ({len(self.new_questions_raised)}):\n"
            for question in self.new_questions_raised:
                synthesis += f"- {question}\n"

        synthesis += ".2f"
        return synthesis


class ResearchRoundsManager:
    """
    Manages research rounds integration with vector storage system
    """

    def __init__(self, vector_store_manager: Optional[EnhancedVectorStoreManager] = None):
        self.vector_store = vector_store_manager or EnhancedVectorStoreManager()
        self.active_research_rounds: Dict[str, ResearchRound] = {}
        self.completed_rounds: Dict[str, List[ResearchRound]] = {}
        self.research_accumulator: Dict[str, Dict[str, Any]] = {}

        # Research quality metrics
        self.quality_metrics = {
            "total_rounds_completed": 0,
            "average_confidence_score": 0.0,
            "total_findings_accumulated": 0,
            "total_citations_collected": 0
        }

    async def start_research_round(self, case_id: str, round_number: int,
                                 research_type: str = "general_legal_research") -> str:
        """
        Start a new research round

        Args:
            case_id: Unique case identifier
            round_number: Sequential round number
            research_type: Type of research being conducted

        Returns:
            Research round identifier
        """
        round_id = f"{case_id}_round_{round_number}"

        research_round = ResearchRound(round_number, case_id, research_type)
        self.active_research_rounds[round_id] = research_round

        # Initialize accumulator for this case if not exists
        if case_id not in self.research_accumulator:
            self.research_accumulator[case_id] = {
                "total_findings": 0,
                "total_citations": 0,
                "research_types_completed": set(),
                "knowledge_synthesis": "",
                "last_updated": datetime.now().isoformat()
            }

        logger.info(f"Started research round {round_id} for case {case_id}")
        return round_id

    async def add_research_finding(self, round_id: str, finding: str,
                                 source: str = "", confidence: float = 0.8):
        """
        Add a finding to the current research round

        Args:
            round_id: Research round identifier
            finding: Research finding content
            source: Source of the finding
            confidence: Confidence score (0-1)
        """
        if round_id not in self.active_research_rounds:
            logger.error(f"Research round {round_id} not found")
            return False

        research_round = self.active_research_rounds[round_id]
        research_round.add_finding(finding, source, confidence)

        # Update case accumulator
        case_id = research_round.case_id
        self.research_accumulator[case_id]["total_findings"] += 1
        self.research_accumulator[case_id]["last_updated"] = datetime.now().isoformat()

        logger.info(f"Added finding to research round {round_id}")
        return True

    async def add_research_citation(self, round_id: str, citation: str,
                                  authority_level: str = "secondary",
                                  relevance_score: float = 0.7):
        """
        Add a citation to the current research round

        Args:
            round_id: Research round identifier
            citation: Legal citation
            authority_level: Primary, secondary, persuasive
            relevance_score: Relevance to case (0-1)
        """
        if round_id not in self.active_research_rounds:
            logger.error(f"Research round {round_id} not found")
            return False

        research_round = self.active_research_rounds[round_id]
        research_round.add_citation(citation, authority_level, relevance_score)

        # Update case accumulator
        case_id = research_round.case_id
        self.research_accumulator[case_id]["total_citations"] += 1
        self.research_accumulator[case_id]["last_updated"] = datetime.now().isoformat()

        logger.info(f"Added citation to research round {round_id}")
        return True

    async def complete_research_round(self, round_id: str,
                                    questions_answered: List[str] = None,
                                    new_questions: List[str] = None) -> bool:
        """
        Complete a research round and store in vector system

        Args:
            round_id: Research round identifier
            questions_answered: List of questions answered in this round
            new_questions: List of new questions raised

        Returns:
            Success status
        """
        if round_id not in self.active_research_rounds:
            logger.error(f"Research round {round_id} not found")
            return False

        research_round = self.active_research_rounds[round_id]

        # Add questions
        if questions_answered:
            research_round.questions_answered.extend(questions_answered)
        if new_questions:
            research_round.new_questions_raised.extend(new_questions)

        # Calculate confidence score
        research_round.confidence_score = self._calculate_round_confidence(research_round)

        # Synthesize content
        synthesized_content = research_round.synthesize_content()

        # Store in vector system
        doc_id = await self.vector_store.add_research_round(
            research_content=synthesized_content,
            metadata={
                "case_id": research_round.case_id,
                "research_type": research_round.research_type,
                "round_number": research_round.round_number,
                "confidence_score": research_round.confidence_score,
                "findings_count": len(research_round.findings),
                "citations_count": len(research_round.citations),
                "questions_answered": research_round.questions_answered,
                "new_questions": research_round.new_questions_raised,
                "round_id": round_id
            },
            round_number=research_round.round_number
        )

        research_round.vector_document_ids.append(doc_id)

        # Move to completed rounds
        case_id = research_round.case_id
        if case_id not in self.completed_rounds:
            self.completed_rounds[case_id] = []
        self.completed_rounds[case_id].append(research_round)

        # Update accumulator
        self.research_accumulator[case_id]["research_types_completed"].add(research_round.research_type)
        self.research_accumulator[case_id]["knowledge_synthesis"] = await self._update_knowledge_synthesis(case_id)

        # Remove from active
        del self.active_research_rounds[round_id]

        # Update metrics
        self.quality_metrics["total_rounds_completed"] += 1
        self.quality_metrics["total_findings_accumulated"] += len(research_round.findings)
        self.quality_metrics["total_citations_collected"] += len(research_round.citations)

        logger.info(f"Completed research round {round_id} with confidence {research_round.confidence_score:.2f}")
        return True

    async def get_research_context(self, case_id: str, query: str = "",
                                 max_contexts: int = 5) -> Dict[str, Any]:
        """
        Get accumulated research context for a case

        Args:
            case_id: Case identifier
            query: Optional query to filter relevant research
            max_contexts: Maximum number of context chunks to return

        Returns:
            Research context with findings and citations
        """
        if case_id not in self.completed_rounds:
            return {"error": "No research rounds found for case"}

        completed_rounds = self.completed_rounds[case_id]

        # Get relevant research content
        if query:
            # Use vector search to find relevant research
            relevant_docs = await self.vector_store.semantic_search(
                query=query,
                store_type=VectorStoreType.GENERAL_RAG,
                top_k=max_contexts * 2
            )

            # Filter to only research documents for this case
            relevant_research = []
            for doc, score in relevant_docs:
                if (doc.metadata.get("case_id") == case_id and
                    doc.metadata.get("content_type") == "research_findings"):
                    relevant_research.append((doc, score))
        else:
            # Get all research documents for this case
            relevant_research = []
            for round_obj in completed_rounds:
                for doc_id in round_obj.vector_document_ids:
                    # Find document in vector store
                    for store in self.vector_store.vector_stores.values():
                        if doc_id in store:
                            doc = store[doc_id]
                            relevant_research.append((doc, 1.0))
                            break

        # Compile research context
        context = {
            "case_id": case_id,
            "total_rounds": len(completed_rounds),
            "research_types": list(self.research_accumulator[case_id]["research_types_completed"]),
            "total_findings": self.research_accumulator[case_id]["total_findings"],
            "total_citations": self.research_accumulator[case_id]["total_citations"],
            "relevant_findings": [],
            "supporting_citations": [],
            "research_summary": self.research_accumulator[case_id]["knowledge_synthesis"]
        }

        # Extract findings and citations from relevant research
        for doc, score in relevant_research[:max_contexts]:
            context["relevant_findings"].append({
                "content": doc.content,
                "confidence": doc.metadata.get("confidence_score", 0.8),
                "round_number": doc.metadata.get("round_number", 0),
                "research_type": doc.metadata.get("research_type", "unknown"),
                "relevance_score": score
            })

            # Extract citations if available
            citations = doc.metadata.get("citations", [])
            context["supporting_citations"].extend(citations)

        return context

    async def get_research_quality_metrics(self, case_id: Optional[str] = None) -> Dict[str, Any]:
        """Get research quality metrics"""
        if case_id:
            if case_id not in self.research_accumulator:
                return {"error": "Case not found"}

            accumulator = self.research_accumulator[case_id]
            rounds = self.completed_rounds.get(case_id, [])

            return {
                "case_id": case_id,
                "rounds_completed": len(rounds),
                "research_types": list(accumulator["research_types_completed"]),
                "total_findings": accumulator["total_findings"],
                "total_citations": accumulator["total_citations"],
                "average_confidence": sum(r.confidence_score for r in rounds) / max(len(rounds), 1),
                "last_updated": accumulator["last_updated"]
            }
        else:
            # Overall metrics
            return self.quality_metrics.copy()

    def _calculate_round_confidence(self, research_round: ResearchRound) -> float:
        """Calculate confidence score for a research round"""
        if not research_round.findings:
            return 0.0

        # Base confidence from findings
        base_confidence = len(research_round.findings) / 10.0  # Scale up to 10 findings

        # Citation authority boost
        authority_boost = 0.0
        for citation in research_round.citations:
            if citation["authority_level"] == "primary":
                authority_boost += 0.2
            elif citation["authority_level"] == "secondary":
                authority_boost += 0.1

        # Relevance boost
        relevance_boost = sum(c["relevance_score"] for c in research_round.citations) / max(len(research_round.citations), 1) * 0.1

        total_confidence = min(1.0, base_confidence + authority_boost + relevance_boost)
        return total_confidence

    async def _update_knowledge_synthesis(self, case_id: str) -> str:
        """Update the knowledge synthesis for a case"""
        if case_id not in self.completed_rounds:
            return "No research rounds completed."

        completed_rounds = self.completed_rounds[case_id]

        # Sort rounds by number
        sorted_rounds = sorted(completed_rounds, key=lambda r: r.round_number)

        synthesis = f"Knowledge Synthesis for Case {case_id}\n\n"

        for research_round in sorted_rounds:
            synthesis += f"Round {research_round.round_number} ({research_round.research_type}):\n"
            synthesis += f"Confidence: {research_round.confidence_score:.2f}\n"
            synthesis += f"Findings: {len(research_round.findings)}\n"
            synthesis += f"Citations: {len(research_round.citations)}\n\n"

        return synthesis

    async def cleanup_old_research(self, case_id: str, keep_rounds: int = 10):
        """Clean up old research rounds, keeping only the most recent"""
        if case_id not in self.completed_rounds:
            return

        completed_rounds = self.completed_rounds[case_id]

        if len(completed_rounds) <= keep_rounds:
            return

        # Sort by round number and keep most recent
        sorted_rounds = sorted(completed_rounds, key=lambda r: r.round_number, reverse=True)
        rounds_to_keep = sorted_rounds[:keep_rounds]
        rounds_to_remove = sorted_rounds[keep_rounds:]

        # Remove old rounds from vector store
        for old_round in rounds_to_remove:
            for doc_id in old_round.vector_document_ids:
                # Remove from all vector stores
                for store in self.vector_store.vector_stores.values():
                    if doc_id in store:
                        del store[doc_id]

        # Update completed rounds
        self.completed_rounds[case_id] = rounds_to_keep

        logger.info(f"Cleaned up {len(rounds_to_remove)} old research rounds for case {case_id}")


# Global instance for easy access
research_rounds_manager = ResearchRoundsManager()