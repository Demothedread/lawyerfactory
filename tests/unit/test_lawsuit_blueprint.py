from lawyerfactory.compose.maestro.lawsuit_blueprint import (
    EvidenceRecord,
    build_evidence_cycle,
    get_lawsuit_stage_blueprint,
)


def test_lawsuit_stage_blueprint_contains_required_pipeline_steps():
    phases = get_lawsuit_stage_blueprint()
    phase_ids = [phase.phase_id for phase in phases]

    assert phase_ids == [
        "P01_evidence_rag_ingestion",
        "P01b_prewriting_review",
        "P02_issue_spot",
        "P03_analysis",
        "P04_fact_lists",
        "P05_causes_of_action",
        "P06_top_sheet",
        "P07_compile",
    ]

    for phase in phases:
        assert phase.agents[0].role_id == "head_partner_maestro_architect"


def test_build_evidence_cycle_normalizes_unknown_tiers_to_secondary():
    cycle_payload = build_evidence_cycle(
        [
            EvidenceRecord("E1", "Contract", "document", "primary"),
            EvidenceRecord("E2", "Summary", "note", "unsupported"),
            EvidenceRecord("E3", "Witness", "interview", "tertiary"),
        ]
    )

    assert cycle_payload["counts"] == {"primary": 1, "secondary": 1, "tertiary": 1}
    assert cycle_payload["total_items"] == 3
    assert cycle_payload["requires_additional_ingest"] is False
