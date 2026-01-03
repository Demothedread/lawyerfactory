"""Structured research artifacts with citations and query filters."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class ResearchFilters:
    """Query filters for jurisdiction and claim elements."""

    jurisdiction: str | None = None
    claim_elements: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "jurisdiction": self.jurisdiction,
            "claim_elements": list(self.claim_elements),
        }


@dataclass(frozen=True)
class ResearchSource:
    """Source item with citation data and content for retrieval."""

    source_id: str
    title: str
    citation: str
    content: str
    url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "title": self.title,
            "citation": self.citation,
            "content": self.content,
            "url": self.url,
        }


@dataclass(frozen=True)
class ResearchArtifact:
    """Container for structured research artifacts."""

    query: str
    summary: str
    filters: ResearchFilters
    sources: list[ResearchSource]
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "summary": self.summary,
            "filters": self.filters.to_dict(),
            "sources": [source.to_dict() for source in self.sources],
            "created_at": self.created_at,
        }

    def vector_entries(self) -> list[tuple[str, dict[str, Any]]]:
        entries: list[tuple[str, dict[str, Any]]] = []
        filters = self.filters.to_dict()
        for source in self.sources:
            metadata = {
                "query": self.query,
                "citation": source.citation,
                "source": source.title,
                "source_id": source.source_id,
                "url": source.url,
                **filters,
            }
            entries.append((source.content, metadata))
        if not entries:
            metadata = {
                "query": self.query,
                "citation": "Research summary",
                **filters,
            }
            entries.append((self.summary, metadata))
        return entries
