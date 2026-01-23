"""
# Script Name: deliverables.py
# Description: Post-production deliverables builder for court-ready packets.
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Core
#   - Group Tags: null
Post-production deliverables builder for court-ready packets.
"""

import json
import zipfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

DEFAULT_COURT = "Superior Court of California"
DEFAULT_JURISDICTION = "California"


@dataclass
class CourtPacketArtifacts:
    """Paths and metadata produced by the post-production protocol."""

    cover_sheet_path: str | None = None
    supplemental_evidence_path: str | None = None
    table_of_authorities_path: str | None = None
    manifest_path: str | None = None
    package_zip_path: str | None = None
    warnings: list[str] = field(default_factory=list)


@dataclass
class CourtPacketInputs:
    """Inputs for generating court-ready packet assets."""

    case_id: str
    case_name: str = "Unknown Case"
    case_number: str = "TBD"
    court: str = DEFAULT_COURT
    jurisdiction: str = DEFAULT_JURISDICTION
    parties: dict[str, str] = field(default_factory=dict)


class PostProductionProtocol:
    """
    Build court-ready post-production deliverables.

    Produces: cover sheet, table of authorities, supplemental evidence index, and
    a packaged ZIP including existing document artifacts.
    """

    def __init__(self, output_dir: str = "output/post_production"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def build_court_packet(
        self,
        inputs: CourtPacketInputs,
        documents: list[dict[str, Any]],
        authorities: list[dict[str, Any]],
        evidence_items: list[dict[str, Any]],
        phase_chain: list[dict[str, Any]],
    ) -> CourtPacketArtifacts:
        """Generate court-ready packet artifacts and a package ZIP."""
        artifacts = CourtPacketArtifacts()

        cover_sheet_text = build_cover_sheet_text(inputs)
        artifacts.cover_sheet_path = write_text_asset(
            self.output_dir, f"{inputs.case_id}_cover_sheet.txt", cover_sheet_text
        )

        toa_text = build_table_of_authorities(authorities)
        artifacts.table_of_authorities_path = write_text_asset(
            self.output_dir, f"{inputs.case_id}_table_of_authorities.txt", toa_text
        )

        evidence_text = build_supplemental_evidence_index(evidence_items)
        artifacts.supplemental_evidence_path = write_text_asset(
            self.output_dir, f"{inputs.case_id}_supplemental_evidence.txt", evidence_text
        )

        artifacts.manifest_path = write_manifest(
            self.output_dir,
            inputs,
            documents,
            phase_chain,
            artifacts,
        )

        artifacts.package_zip_path = create_document_package_zip(
            self.output_dir,
            inputs.case_id,
            documents,
            artifacts,
            artifacts.warnings,
        )

        return artifacts


def build_cover_sheet_text(inputs: CourtPacketInputs) -> str:
    """Build a court cover sheet using default Superior Court of California rules."""
    plaintiff = inputs.parties.get("plaintiff", "Plaintiff")
    defendant = inputs.parties.get("defendant", "Defendant")
    caption_lines = [
        inputs.court,
        f"{inputs.jurisdiction}",
        "",
        f"{plaintiff},",
        "    Plaintiff,",
        "",
        "v.",
        "",
        f"{defendant},",
        "    Defendant.",
        "____________________________________)",
        ")",
        f") Case No. {inputs.case_number}",
        ")",
        ") COMPLAINT FOR DAMAGES AND",
        ") INJUNCTIVE RELIEF",
        ")",
        ") JURY TRIAL DEMANDED",
        ")",
        "____________________________________)",
    ]
    return "\n".join(caption_lines)


def build_table_of_authorities(authorities: list[dict[str, Any]]) -> str:
    """Create a table of authorities from research outputs."""
    header = ["TABLE OF AUTHORITIES", ""]
    if not authorities:
        return "\n".join(header + ["No authorities provided."])

    entries = []
    for authority in authorities:
        name = authority.get("authority_name") or authority.get("name") or "Unknown Authority"
        citation = authority.get("citation") or authority.get("bluebook") or ""
        court = authority.get("court") or authority.get("jurisdiction") or ""
        year = authority.get("year") or authority.get("date") or ""
        entry = " | ".join(part for part in [name, citation, court, str(year)] if part)
        entries.append(f"- {entry}")

    return "\n".join(header + entries)


def build_supplemental_evidence_index(evidence_items: list[dict[str, Any]]) -> str:
    """Create a supplemental evidence index from intake outputs."""
    header = ["SUPPLEMENTAL EVIDENCE INDEX", ""]
    if not evidence_items:
        return "\n".join(header + ["No supplemental evidence listed."])

    lines = []
    for idx, item in enumerate(evidence_items, start=1):
        label = item.get("title") or item.get("filename") or item.get("name") or "Evidence"
        description = item.get("summary") or item.get("description") or ""
        lines.append(f"{idx}. {label} {description}".strip())

    return "\n".join(header + lines)


def write_text_asset(output_dir: Path, filename: str, content: str) -> str:
    """Write a text asset to the output directory."""
    output_path = output_dir / filename
    output_path.write_text(content, encoding="utf-8")
    return str(output_path)


def write_manifest(
    output_dir: Path,
    inputs: CourtPacketInputs,
    documents: list[dict[str, Any]],
    phase_chain: list[dict[str, Any]],
    artifacts: CourtPacketArtifacts,
) -> str:
    """Write a JSON manifest describing the packet contents."""
    manifest = {
        "case_id": inputs.case_id,
        "case_name": inputs.case_name,
        "case_number": inputs.case_number,
        "court": inputs.court,
        "jurisdiction": inputs.jurisdiction,
        "generated_at": datetime.now().isoformat(),
        "documents": documents,
        "phase_chain": phase_chain,
        "artifacts": {
            "cover_sheet": artifacts.cover_sheet_path,
            "table_of_authorities": artifacts.table_of_authorities_path,
            "supplemental_evidence": artifacts.supplemental_evidence_path,
        },
    }
    manifest_path = output_dir / f"{inputs.case_id}_court_packet_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return str(manifest_path)


def create_document_package_zip(
    output_dir: Path,
    case_id: str,
    documents: list[dict[str, Any]],
    artifacts: CourtPacketArtifacts,
    warnings: list[str],
) -> str:
    """Package deliverables into a single ZIP archive."""
    package_path = output_dir / f"{case_id}_court_packet.zip"
    with zipfile.ZipFile(package_path, "w", compression=zipfile.ZIP_DEFLATED) as zip_file:
        _add_artifact(zip_file, artifacts.cover_sheet_path, warnings)
        _add_artifact(zip_file, artifacts.table_of_authorities_path, warnings)
        _add_artifact(zip_file, artifacts.supplemental_evidence_path, warnings)
        _add_artifact(zip_file, artifacts.manifest_path, warnings)

        for document in documents:
            document_path = document.get("file_path") or document.get("path")
            if document_path:
                _add_artifact(zip_file, document_path, warnings)
            else:
                warnings.append(f"Missing file_path for document: {document.get('title')}")

    return str(package_path)


def _add_artifact(zip_file: zipfile.ZipFile, path: str | None, warnings: list[str]) -> None:
    """Add an artifact to the zip file if present."""
    if not path:
        return
    artifact_path = Path(path)
    if artifact_path.exists():
        zip_file.write(artifact_path, arcname=artifact_path.name)
    else:
        warnings.append(f"Artifact missing on disk: {path}")
