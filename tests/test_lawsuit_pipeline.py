import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from lawyerfactory.lawsuit_pipeline import (  # noqa: E402
    LawsuitIntake,
    REQUIRED_LAWSUIT_SECTIONS,
    REQUIRED_METADATA_FIELDS,
    run_lawsuit_pipeline,
)


def test_lawsuit_pipeline_output_includes_schema_sections():
    intake = LawsuitIntake(
        title="Doe v. Acme Corp",
        jurisdiction="California Superior Court",
        parties=["Jane Doe", "Acme Corp"],
        facts=(
            "Plaintiff entered a service agreement with Defendant. "
            "Defendant failed to deliver services after payment."
        ),
        claims=["Breach of contract", "Unjust enrichment"],
        citations=["Cal. Civ. Code § 1550", "Cal. Civ. Code § 3300"],
    )

    output = run_lawsuit_pipeline(intake)
    sections = output["sections"]

    for section in REQUIRED_LAWSUIT_SECTIONS:
        assert section in sections


def test_lawsuit_pipeline_metadata_and_citations_present():
    intake = LawsuitIntake(
        title="Roe v. City",
        jurisdiction="New York Supreme Court",
        parties=["John Roe", "City of Gotham"],
        facts="Plaintiff was denied benefits after submitting documentation.",
        claims=["Due process violation"],
        citations=["42 U.S.C. § 1983"],
    )

    output = run_lawsuit_pipeline(intake)
    metadata = output["metadata"]

    for field in REQUIRED_METADATA_FIELDS:
        assert metadata.get(field)

    legal_arguments = output["sections"]["legal_arguments"]
    assert legal_arguments
    for argument in legal_arguments:
        assert argument["citations"]
