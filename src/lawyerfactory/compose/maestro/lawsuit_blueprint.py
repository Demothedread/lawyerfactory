"""Stage-based lawsuit assembly blueprint for multi-agent orchestration."""

from __future__ import annotations

import logging
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

from .prewriting_packets import PREWRITING_DELIVERABLE_IDS

logger = logging.getLogger(__name__)

EVIDENCE_TIERS = ("primary", "secondary", "tertiary")


@dataclass(frozen=True)
class AgentRole:
    """Defines a role in the multi-agent network for a phase."""

    role_id: str
    title: str
    responsibility: str


@dataclass(frozen=True)
class BlueprintPhase:
    """A discrete, combinable phase in the lawsuit assembly workflow."""

    phase_id: str
    label: str
    objective: str
    required_inputs: list[str]
    outputs: list[str]
    agents: list[AgentRole]
    can_iterate: bool = True


@dataclass
class EvidenceRecord:
    """Minimal evidence payload used for planning and tier categorization."""

    evidence_id: str
    summary: str
    source_type: str
    tier: str = field(default="secondary")

    def normalized_tier(self) -> str:
        normalized = (self.tier or "secondary").lower()
        return normalized if normalized in EVIDENCE_TIERS else "secondary"


def get_lawsuit_stage_blueprint() -> list[BlueprintPhase]:
    """Return ordered phases for evidence-to-lawsuit compilation.

    The first role in every phase is the Head Partner/Maestro/Architect, allowing
    a consistent supervisory control-plane with specialized worker agents.
    """

    head_partner = AgentRole(
        role_id="head_partner_maestro_architect",
        title="Head Partner / Maestro / Architect",
        responsibility="Direct phase sequencing, quality gates, and escalation.",
    )

    phases = [
        BlueprintPhase(
            phase_id="P01_evidence_rag_ingestion",
            label="Evidence Ingestion + RAG Indexing",
            objective=(
                "Ingest evidence, classify primary/secondary/tertiary tiers, and "
                "construct retrieval-ready chunks for downstream reasoning."
            ),
            required_inputs=["raw_evidence"],
            outputs=["tiered_evidence", "rag_index", "ingestion_audit_log"],
            agents=[
                head_partner,
                AgentRole(
                    role_id="evidence_intake_specialist",
                    title="Evidence Intake Specialist",
                    responsibility="Normalize uploads and extract canonical metadata.",
                ),
                AgentRole(
                    role_id="retrieval_engineer",
                    title="RAG Retrieval Engineer",
                    responsibility="Chunk, embed, and index evidence corpus.",
                ),
            ],
        ),
        BlueprintPhase(
            phase_id="P01b_prewriting_review",
            label="Pre-Writing Review",
            objective=(
                "Produce the three user-reviewable pre-writing deliverables before drafting."
            ),
            required_inputs=["tiered_evidence", "rag_index"],
            outputs=list(PREWRITING_DELIVERABLE_IDS) + ["prewriting_review_packet"],
            agents=[
                head_partner,
                AgentRole(
                    role_id="prewriting_packet_curator",
                    title="Pre-Writing Packet Curator",
                    responsibility="Consolidate evidence, issues, and claim theories for review.",
                ),
            ],
        ),
        BlueprintPhase(
            phase_id="P02_issue_spot",
            label="Issue Spotting",
            objective="Detect legal issues from tiered evidence and produce issue map.",
            required_inputs=["tiered_evidence", "rag_index"],
            outputs=["issue_map", "research_questions"],
            agents=[
                head_partner,
                AgentRole(
                    role_id="issue_spotter",
                    title="Issue Spotter",
                    responsibility="Surface potential claims, defenses, and procedural risks.",
                ),
            ],
        ),
        BlueprintPhase(
            phase_id="P03_analysis",
            label="Legal Analysis",
            objective="Analyze issues against law, jurisdiction, and burden elements.",
            required_inputs=["issue_map", "research_questions", "rag_index"],
            outputs=["analysis_memos", "element_gaps"],
            agents=[
                head_partner,
                AgentRole(
                    role_id="legal_analyst",
                    title="Legal Analyst",
                    responsibility="Apply rule statements and evaluate evidentiary sufficiency.",
                ),
            ],
        ),
        BlueprintPhase(
            phase_id="P04_fact_lists",
            label="Fact List Construction",
            objective="Convert analyzed evidence into admissibility-aware fact lists.",
            required_inputs=["analysis_memos", "tiered_evidence"],
            outputs=["fact_lists", "fact_citations"],
            agents=[
                head_partner,
                AgentRole(
                    role_id="fact_matrix_agent",
                    title="Fact Matrix Agent",
                    responsibility="Build numbered factual chronology with source attribution.",
                ),
            ],
        ),
        BlueprintPhase(
            phase_id="P05_causes_of_action",
            label="Cause of Action Assembly",
            objective="Map facts to causes of action and required legal elements.",
            required_inputs=["fact_lists", "analysis_memos"],
            outputs=["cause_of_action_matrix", "element_support_table"],
            agents=[
                head_partner,
                AgentRole(
                    role_id="claims_engine",
                    title="Cause of Action Specialist",
                    responsibility="Draft claim-by-claim element support and gap flags.",
                ),
            ],
        ),
        BlueprintPhase(
            phase_id="P06_top_sheet",
            label="Top Sheet Generation",
            objective="Create filing top sheet and litigation packet metadata.",
            required_inputs=["cause_of_action_matrix", "fact_lists"],
            outputs=["top_sheet", "filing_metadata"],
            agents=[
                head_partner,
                AgentRole(
                    role_id="filing_packet_specialist",
                    title="Filing Packet Specialist",
                    responsibility="Prepare court header data and relief summary.",
                ),
            ],
        ),
        BlueprintPhase(
            phase_id="P07_compile",
            label="Compilation",
            objective="Compile final lawsuit in modular sections into filing-ready package.",
            required_inputs=["top_sheet", "cause_of_action_matrix", "fact_lists"],
            outputs=["compiled_lawsuit", "quality_manifest"],
            agents=[
                head_partner,
                AgentRole(
                    role_id="compilation_editor",
                    title="Compilation Editor",
                    responsibility="Assemble sections, validate references, and finalize output.",
                ),
            ],
            can_iterate=False,
        ),
    ]
    logger.info(
        "Built lawsuit stage blueprint",
        extra={
            "phase_count": len(phases),
            "phase_ids": [phase.phase_id for phase in phases],
        },
    )
    return phases


def build_evidence_cycle(records: Iterable[EvidenceRecord]) -> dict[str, Any]:
    """Build an iteration cycle payload that drives repeated ingest/classify passes."""

    cycle: dict[str, Any] = {tier: [] for tier in EVIDENCE_TIERS}
    for record in records:
        tier = record.normalized_tier()
        cycle[tier].append(
            {
                "evidence_id": record.evidence_id,
                "summary": record.summary,
                "source_type": record.source_type,
            }
        )

    total_items = sum(len(items) for items in cycle.values())
    payload = {
        "evidence_cycle": cycle,
        "counts": {tier: len(items) for tier, items in cycle.items()},
        "total_items": total_items,
        "requires_additional_ingest": total_items == 0,
    }
    logger.info(
        "Built evidence cycle payload",
        extra={
            "total_items": total_items,
            "counts": payload["counts"],
            "requires_additional_ingest": payload["requires_additional_ingest"],
        },
    )
    return payload
