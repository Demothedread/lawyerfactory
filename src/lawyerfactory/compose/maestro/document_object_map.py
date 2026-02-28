"""Document object map utilities for long-form modular drafting."""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


def _fingerprint(text: str) -> str:
    return hashlib.sha1(text.strip().lower().encode("utf-8")).hexdigest()[:12]


def _token_estimate(text: str) -> int:
    # Fast approximation for context-window packing.
    return max(1, len(text.split()))


@dataclass(frozen=True)
class SectionLink:
    """Link between an underlying claim and one of its theory sections."""

    claim_id: str
    theory_id: str
    section_id: str


@dataclass
class SectionNode:
    """Single document section tracked in the object map."""

    section_id: str
    claim_id: str
    theory_id: str
    title: str
    body: str
    summary: str
    tags: list[str] = field(default_factory=list)

    @property
    def body_fingerprint(self) -> str:
        return _fingerprint(self.body)


@dataclass
class DocumentObjectMap:
    """Tracks section locations, overlap detection, and context compression."""

    sections: list[SectionNode] = field(default_factory=list)

    def add_section(self, section: SectionNode) -> None:
        self.sections.append(section)
        logger.debug(
            "Added section to document object map",
            extra={
                "section_id": section.section_id,
                "claim_id": section.claim_id,
                "theory_id": section.theory_id,
                "total_sections": len(self.sections),
            },
        )

    def linked_sections(self) -> list[SectionLink]:
        return [
            SectionLink(
                claim_id=section.claim_id,
                theory_id=section.theory_id,
                section_id=section.section_id,
            )
            for section in self.sections
        ]

    def overlap_report(self) -> dict[str, Any]:
        seen: dict[str, str] = {}
        duplicates: list[dict[str, str]] = []
        for section in self.sections:
            fingerprint = section.body_fingerprint
            if fingerprint in seen:
                duplicates.append(
                    {
                        "section_id": section.section_id,
                        "duplicates_section_id": seen[fingerprint],
                    }
                )
            else:
                seen[fingerprint] = section.section_id
        report = {
            "has_overlap": len(duplicates) > 0,
            "duplicate_pairs": duplicates,
            "section_count": len(self.sections),
        }
        if report["has_overlap"]:
            logger.warning(
                "Detected overlapping section content in document object map",
                extra={
                    "duplicate_count": len(duplicates),
                    "section_count": len(self.sections),
                },
            )
        else:
            logger.debug(
                "No overlaps detected in document object map",
                extra={"section_count": len(self.sections)},
            )
        return report

    def build_context_packet(self, token_budget: int = 900) -> dict[str, Any]:
        ordered = sorted(self.sections, key=lambda item: item.section_id)
        packed_sections: list[dict[str, Any]] = []
        consumed = 0

        for section in ordered:
            summary_tokens = _token_estimate(section.summary)
            if consumed + summary_tokens > token_budget:
                break
            consumed += summary_tokens
            packed_sections.append(
                {
                    "section_id": section.section_id,
                    "claim_id": section.claim_id,
                    "theory_id": section.theory_id,
                    "title": section.title,
                    "summary": section.summary,
                    "tags": sorted(set(section.tags)),
                }
            )

        packet = {
            "token_budget": token_budget,
            "consumed_tokens": consumed,
            "sections": packed_sections,
            "overlap_report": self.overlap_report(),
            "links": [link.__dict__ for link in self.linked_sections()],
        }
        logger.info(
            "Built document context packet",
            extra={
                "token_budget": token_budget,
                "consumed_tokens": consumed,
                "packed_sections": len(packed_sections),
                "total_sections": len(self.sections),
            },
        )
        return packet
