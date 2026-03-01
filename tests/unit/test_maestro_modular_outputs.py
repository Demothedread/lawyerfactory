from lawyerfactory.agents.orchestration.maestro import Maestro


def test_maestro_prewriting_packet_and_stage_blueprint_exposed():
    maestro = object.__new__(Maestro)

    packet = maestro.get_prewriting_review_packet()
    phases = maestro.get_stage_blueprint()

    assert packet["deliverable_count"] == 3
    assert phases[1]["phase_id"] == "P01b_prewriting_review"


def test_maestro_document_object_map_links_claim_and_theory():
    maestro = object.__new__(Maestro)
    result = maestro.build_document_object_map(
        [
            {
                "section_id": "S-101",
                "claim_id": "claim-fraud",
                "theory_id": "theory-concealment",
                "title": "Fraud by Concealment",
                "body": "Body text",
                "summary": "Condensed summary",
                "tags": ["fraud"],
            }
        ],
        token_budget=20,
    )

    assert result["sections"][0]["section_id"] == "S-101"
    assert result["links"][0]["claim_id"] == "claim-fraud"
