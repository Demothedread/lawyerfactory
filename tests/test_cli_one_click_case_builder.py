from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import patch

from apps.cli.one_click_case_builder import (
    IntakeAnswers,
    build_case_package,
    collect_intake_answers,
)


def test_build_case_package_generates_output(tmp_path: Path):
    evidence_dir = tmp_path / "evidence"
    evidence_dir.mkdir()
    (evidence_dir / "invoice.pdf").write_text("fake pdf", encoding="utf-8")
    (evidence_dir / "email.txt").write_text("demand email", encoding="utf-8")

    answers = IntakeAnswers(
        plaintiff="Alice",
        defendant="Bob Corp",
        venue="Superior Court of California, County of Alameda",
        jurisdiction="California",
        intake_statement="Defendant breached the contract and caused damages.",
        evidence_folder=str(evidence_dir),
    )

    result = asyncio.run(build_case_package(answers, output_dir=str(tmp_path)))

    assert result.case_id.startswith("Alice_v_Bob_Corp")
    assert result.evidence_count == 2
    assert Path(result.output_path).exists()


def test_collect_intake_answers_supports_file_intake(tmp_path: Path):
    evidence_dir = tmp_path / "evidence"
    evidence_dir.mkdir()
    intake_file = tmp_path / "intake.txt"
    intake_file.write_text("Narrative from file", encoding="utf-8")

    responses = iter(
        [
            str(evidence_dir),
            "file",
            str(intake_file),
            "Jane Roe",
            "Acme LLC",
            "Superior Court",
            "California",
        ]
    )

    answers = collect_intake_answers(
        input_fn=lambda _prompt: next(responses),
        print_fn=lambda _m: None,
    )

    assert answers.plaintiff == "Jane Roe"
    assert answers.defendant == "Acme LLC"
    assert answers.intake_statement == "Narrative from file"


def test_build_case_package_fallback_produces_txt(tmp_path: Path):
    """When ReportLab is unavailable the generator writes a .txt file."""
    evidence_dir = tmp_path / "evidence"
    evidence_dir.mkdir()
    (evidence_dir / "doc.txt").write_text("evidence content", encoding="utf-8")

    answers = IntakeAnswers(
        plaintiff="Alice",
        defendant="Bob Corp",
        venue="Superior Court",
        jurisdiction="California",
        intake_statement="Defendant breached the contract.",
        evidence_folder=str(evidence_dir),
    )

    pdf_gen_module = "lawyerfactory.post_production.pdf_generator"
    with patch(f"{pdf_gen_module}.REPORTLAB_AVAILABLE", False):
        result = asyncio.run(build_case_package(answers, output_dir=str(tmp_path)))

    output_path = Path(result.output_path)
    assert output_path.exists()
    assert output_path.suffix == ".txt", f"Expected .txt fallback, got {output_path.suffix}"
    assert output_path.stat().st_size > 0
