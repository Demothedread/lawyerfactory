"""Pre-writing deliverable packets for user review before drafting."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

PREWRITING_DELIVERABLE_IDS = (
    "evidence_reliability_brief",
    "issue_fact_matrix",
    "claim_theory_strategy_sheet",
)


@dataclass(frozen=True)
class PreWritingDeliverable:
    """Single pre-writing deliverable payload."""

    deliverable_id: str
    title: str
    purpose: str
    sections: list[str]


def build_prewriting_deliverables() -> list[PreWritingDeliverable]:
    """Return 3 user-facing deliverables that gate drafting."""
    deliverables = [
        PreWritingDeliverable(
            deliverable_id="evidence_reliability_brief",
            title="Evidence Reliability Brief",
            purpose="Summarizes primary/secondary/tertiary evidence confidence and gaps.",
            sections=["tier_counts", "source_credibility", "missing_evidence_actions"],
        ),
        PreWritingDeliverable(
            deliverable_id="issue_fact_matrix",
            title="Issue-to-Fact Matrix",
            purpose="Maps spotted issues to supporting facts and citations.",
            sections=["issue_list", "supporting_facts", "open_questions"],
        ),
        PreWritingDeliverable(
            deliverable_id="claim_theory_strategy_sheet",
            title="Claim Theory Strategy Sheet",
            purpose="Defines each underlying claim and the legal theories that support it.",
            sections=["underlying_claims", "theory_variants", "element_support"],
        ),
    ]
    logger.debug(
        "Built pre-writing deliverables",
        extra={
            "deliverable_ids": [item.deliverable_id for item in deliverables],
            "deliverable_count": len(deliverables),
        },
    )
    return deliverables


def to_user_review_packet() -> dict[str, Any]:
    """Serialize deliverables for UI/API review checkpoint."""

    deliverables = build_prewriting_deliverables()
    packet = {
        "deliverable_count": len(deliverables),
        "deliverables": [item.__dict__ for item in deliverables],
        "ready_for_user_review": True,
    }
    logger.info(
        "Prepared pre-writing review packet",
        extra={
            "deliverable_count": packet["deliverable_count"],
            "ready_for_user_review": packet["ready_for_user_review"],
        },
    )
    return packet
