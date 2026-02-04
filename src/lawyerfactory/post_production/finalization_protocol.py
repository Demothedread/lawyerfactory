"""
Finalization protocol for court-compliant post-production deliverables.

Builds cover sheets, evidence appendices, and tables of authorities using
prior phase outputs and jurisdiction defaults.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class CourtProfile:
    """Court rules and defaults for final deliverable generation."""

    jurisdiction: str
    court_name: str
    rules: Dict[str, Any] = field(default_factory=dict)
    cover_sheet_form: str = "CM-010"
    requires_cover_sheet: bool = True
    requires_table_of_authorities: bool = True
    requires_evidence_appendix: bool = True

    @classmethod
    def california_superior(cls) -> "CourtProfile":
        """Default to Superior Court of California when not specified."""
        return cls(
            jurisdiction="California",
            court_name="Superior Court of California",
            rules={
                "cover_sheet": "Civil Case Cover Sheet (CM-010)",
                "table_of_authorities": "Include cited cases and statutes",
                "evidence_appendix": "Attach exhibits with labels and descriptions",
            },
        )


class CoverSheetBuilder:
    """Construct court cover sheet content from case metadata."""

    def build(self, case_metadata: Dict[str, Any], court_profile: CourtProfile) -> Dict[str, Any]:
        """Build a structured cover sheet document."""
        parties = case_metadata.get("parties", {})
        plaintiff = parties.get("plaintiff", case_metadata.get("plaintiff", "Plaintiff"))
        defendant = parties.get("defendant", case_metadata.get("defendant", "Defendant"))

        return {
            "id": "cover_sheet",
            "type": "cover_sheet",
            "title": f"Civil Case Cover Sheet ({court_profile.cover_sheet_form})",
            "content": {
                "title": f"Civil Case Cover Sheet ({court_profile.cover_sheet_form})",
                "court": court_profile.court_name,
                "jurisdiction": court_profile.jurisdiction,
                "case_name": case_metadata.get("case_name", "Unnamed Case"),
                "case_number": case_metadata.get("case_number", "TBD"),
                "parties": [f"Plaintiff: {plaintiff}", f"Defendant: {defendant}"],
                "filing_category": case_metadata.get("case_category", "Unlimited Civil"),
                "relief_requested": case_metadata.get("relief_requested", "To be determined"),
                "cover_sheet_rules": [
                    "Ensure all mandatory fields are completed.",
                    "Confirm filing category and complex case designation if applicable.",
                ],
            },
            "format": "structured",
        }


class EvidenceCollator:
    """Create a supplemental evidence appendix from intake evidence items."""

    def build(self, evidence_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build a supplemental evidence appendix document."""
        items = evidence_data.get("items", [])
        appendix_entries = []
        for index, item in enumerate(items, 1):
            description = item.get("description", "Evidence item")
            source = item.get("source", "Unknown source")
            appendix_entries.append(f"Exhibit {index}: {description} ({source})")

        return {
            "id": "evidence_appendix",
            "type": "evidence_appendix",
            "title": "Supplemental Evidence Appendix",
            "content": {
                "title": "Supplemental Evidence Appendix",
                "summary": evidence_data.get("summary", "Evidence collated from intake."),
                "exhibits": appendix_entries or ["No evidence items provided."],
            },
            "format": "structured",
        }


class AuthorityTableBuilder:
    """Build a table of authorities from research outputs."""

    def build(self, research_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build a table of authorities document."""
        authorities = research_data.get("authorities", [])
        precedents = research_data.get("precedents", [])
        statutes = research_data.get("statutes", [])

        authority_entries = [
            self._format_authority(authority) for authority in authorities if authority
        ]
        precedent_entries = [self._format_authority(entry) for entry in precedents if entry]
        statute_entries = [self._format_authority(entry) for entry in statutes if entry]

        return {
            "id": "table_of_authorities",
            "type": "table_of_authorities",
            "title": "Table of Authorities",
            "content": {
                "title": "Table of Authorities",
                "cases": authority_entries or ["No case authorities provided."],
                "precedent_cases": precedent_entries or ["No precedent cases provided."],
                "statutes": statute_entries or ["No statutes provided."],
            },
            "format": "structured",
        }

    def _format_authority(self, authority: Any) -> str:
        """Normalize authority entries to a display string."""
        if isinstance(authority, dict):
            citation = authority.get("citation") or authority.get("name") or "Unknown authority"
            summary = authority.get("summary")
            return f"{citation} — {summary}" if summary else citation
        return str(authority)


class FinalizationProtocol:
    """Orchestrate final deliverables based on court rules and prior outputs."""

    def __init__(self, court_profile: Optional[CourtProfile] = None) -> None:
        self.court_profile = court_profile or CourtProfile.california_superior()
        self.cover_sheet_builder = CoverSheetBuilder()
        self.evidence_collator = EvidenceCollator()
        self.authority_table_builder = AuthorityTableBuilder()

    def build_post_production_deliverables(
        self,
        aggregated_data: Dict[str, Any],
        case_metadata: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Create post-production deliverables derived from prior phase outputs."""
        deliverables: List[Dict[str, Any]] = []
        phase_lineage = [entry.get("phase_id") for entry in aggregated_data.get("phase_lineage", [])]

        if self.court_profile.requires_cover_sheet:
            cover_sheet = self.cover_sheet_builder.build(case_metadata, self.court_profile)
            cover_sheet["metadata"] = {"builds_on": phase_lineage, "court_profile": self.court_profile.court_name}
            deliverables.append(cover_sheet)

        if self.court_profile.requires_evidence_appendix:
            evidence_doc = self.evidence_collator.build(aggregated_data.get("evidence", {}))
            evidence_doc["metadata"] = {"builds_on": phase_lineage, "source": "A01"}
            deliverables.append(evidence_doc)

        if self.court_profile.requires_table_of_authorities:
            authority_doc = self.authority_table_builder.build(aggregated_data.get("research", {}))
            authority_doc["metadata"] = {"builds_on": phase_lineage, "source": "A02"}
            deliverables.append(authority_doc)

        return deliverables
