"""Interactive one-click case package builder for LawyerFactory CLI."""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from lawyerfactory.post_production.deliverables import CourtPacketInputs, build_cover_sheet_text
from lawyerfactory.post_production.pdf_generator import (
    DocumentFormat,
    DocumentMetadata,
    LegalPDFGenerator,
)

PromptFn = Callable[[str], str]
PrintFn = Callable[[str], None]


@dataclass
class IntakeAnswers:
    """User-provided intake answers for case package generation."""

    plaintiff: str
    defendant: str
    venue: str
    jurisdiction: str
    intake_statement: str
    evidence_folder: str


@dataclass
class CaseBuildResult:
    """Result metadata for generated court-ready package."""

    case_id: str
    output_path: str
    evidence_count: int


def _prompt_non_empty(prompt: str, input_fn: PromptFn) -> str:
    """Collect a non-empty response from a prompt function."""
    while True:
        response = input_fn(prompt).strip()
        if response:
            return response


def _resolve_intake_statement(input_fn: PromptFn, print_fn: PrintFn) -> str:
    """Capture intake narrative either from direct text or from a file path."""
    source = _prompt_non_empty(
        "Provide intake statement directly (type 'direct') or from a file path (type 'file'): ",
        input_fn,
    ).lower()

    if source == "file":
        path = Path(_prompt_non_empty("Path to intake statement file: ", input_fn)).expanduser()
        if not path.exists() or not path.is_file():
            raise ValueError(f"Intake file not found: {path}")
        content = path.read_text(encoding="utf-8")
        if not content.strip():
            raise ValueError("Intake file is empty")
        print_fn(f"Loaded intake statement from: {path}")
        return content.strip()

    if source != "direct":
        print_fn("Unrecognized option; defaulting to direct statement mode.")

    return _prompt_non_empty("Intake statement: ", input_fn)


def _list_evidence_files(evidence_folder: Path) -> list[Path]:
    """Gather evidence files from a folder using stable alphabetical order."""
    files = [path for path in evidence_folder.iterdir() if path.is_file()]
    return sorted(files, key=lambda path: path.name.lower())


def collect_intake_answers(input_fn: PromptFn = input, print_fn: PrintFn = print) -> IntakeAnswers:
    """Collect interactive intake answers required for one-click generation."""
    evidence_folder = Path(_prompt_non_empty("Evidence folder path: ", input_fn)).expanduser()
    if not evidence_folder.exists() or not evidence_folder.is_dir():
        raise ValueError(f"Evidence folder not found: {evidence_folder}")

    intake_statement = _resolve_intake_statement(input_fn, print_fn)

    return IntakeAnswers(
        plaintiff=_prompt_non_empty("Plaintiff name: ", input_fn),
        defendant=_prompt_non_empty("Defendant name: ", input_fn),
        venue=_prompt_non_empty("Venue: ", input_fn),
        jurisdiction=_prompt_non_empty("Jurisdiction: ", input_fn),
        intake_statement=intake_statement,
        evidence_folder=str(evidence_folder),
    )


def _derive_claim_candidates(intake_statement: str) -> list[str]:
    """Derive simple claim suggestions from intake keywords."""
    lowered = intake_statement.lower()
    keyword_map = {
        "contract": "Breach of Contract",
        "fraud": "Fraud",
        "neglig": "Negligence",
        "defam": "Defamation",
        "retaliat": "Retaliation",
    }
    claims = [value for key, value in keyword_map.items() if key in lowered]
    return sorted(set(claims)) or ["General Civil Damages"]


def _build_statement_of_facts(intake_statement: str, evidence_files: Iterable[Path]) -> str:
    evidence_lines = [f"- {path.name}" for path in evidence_files]
    facts = [
        "STATEMENT OF FACTS",
        "",
        intake_statement.strip(),
        "",
        "EVIDENCE INDEX",
        *evidence_lines,
    ]
    return "\n".join(facts)


def _build_table_of_authorities(jurisdiction: str) -> str:
    authorities = [
        "TABLE OF AUTHORITIES",
        "",
        f"- {jurisdiction} Civil Procedure Rules",
        "- Federal Rules of Civil Procedure (as applicable)",
        "- Local court formatting and filing requirements",
    ]
    return "\n".join(authorities)


def _build_statement_of_claims(claims: list[str], plaintiff: str, defendant: str) -> str:
    lines = ["STATEMENT OF CLAIMS", ""]
    for index, claim in enumerate(claims, start=1):
        lines.append(f"{index}. {plaintiff} alleges {claim} against {defendant}.")
    return "\n".join(lines)


def _slugify_case_id(plaintiff: str, defendant: str) -> str:
    raw = f"{plaintiff}_v_{defendant}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    return re.sub(r"[^A-Za-z0-9_]+", "_", raw).strip("_")


async def build_case_package(
    answers: IntakeAnswers,
    output_dir: str = "output/cli",
) -> CaseBuildResult:
    """Generate a single PDF containing cover sheet and core case sections."""
    evidence_files = _list_evidence_files(Path(answers.evidence_folder))
    case_id = _slugify_case_id(answers.plaintiff, answers.defendant)

    cover_sheet = build_cover_sheet_text(
        CourtPacketInputs(
            case_id=case_id,
            case_name=f"{answers.plaintiff} v. {answers.defendant}",
            case_number="TBD",
            court=answers.venue,
            jurisdiction=answers.jurisdiction,
            parties={"plaintiff": answers.plaintiff, "defendant": answers.defendant},
        )
    )
    statement_of_facts = _build_statement_of_facts(answers.intake_statement, evidence_files)
    table_of_authorities = _build_table_of_authorities(answers.jurisdiction)
    statement_of_claims = _build_statement_of_claims(
        _derive_claim_candidates(answers.intake_statement),
        answers.plaintiff,
        answers.defendant,
    )

    merged_content = "\n\n".join(
        [cover_sheet, statement_of_facts, table_of_authorities, statement_of_claims]
    )

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    generator = LegalPDFGenerator(output_directory=str(output_path))
    result = await generator.generate_pdf(
        content=merged_content,
        metadata=DocumentMetadata(
            title="Ready-to-File Complaint Package",
            case_name=f"{answers.plaintiff} v. {answers.defendant}",
            court=answers.venue,
            case_number="TBD",
            document_type=DocumentFormat.COMPLAINT,
        ),
        output_filename=f"{case_id}_ready_to_file.pdf",
    )
    if not result.success or not result.file_path:
        error = result.error_message or "Unknown PDF generation error"
        raise RuntimeError(f"Failed to generate output package: {error}")

    return CaseBuildResult(
        case_id=case_id,
        output_path=result.file_path,
        evidence_count=len(evidence_files),
    )
