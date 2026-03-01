from lawyerfactory.compose.maestro.document_object_map import DocumentObjectMap, SectionNode


def test_document_map_detects_duplicates_and_builds_links():
    document_map = DocumentObjectMap()
    document_map.add_section(
        SectionNode(
            section_id="S1",
            claim_id="C1",
            theory_id="T1",
            title="Claim One",
            body="Repeated body text",
            summary="Summary one",
            tags=["claim"],
        )
    )
    document_map.add_section(
        SectionNode(
            section_id="S2",
            claim_id="C1",
            theory_id="T2",
            title="Claim One Theory Two",
            body="Repeated body text",
            summary="Summary two",
            tags=["theory"],
        )
    )

    packet = document_map.build_context_packet(token_budget=50)

    assert packet["overlap_report"]["has_overlap"] is True
    assert len(packet["links"]) == 2
    assert packet["sections"][0]["claim_id"] == "C1"


def test_document_map_respects_token_budget():
    document_map = DocumentObjectMap(
        sections=[
            SectionNode("S1", "C1", "T1", "A", "Body", "one two three"),
            SectionNode("S2", "C2", "T2", "B", "Body", "four five six"),
        ]
    )

    packet = document_map.build_context_packet(token_budget=3)
    assert len(packet["sections"]) == 1
