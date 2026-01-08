import pytest

from lawyerfactory.document_models import (
    Attachment,
    Caption,
    CauseOfAction,
    Damages,
    Fact,
    Jurisdiction,
    LawsuitDocument,
    Party,
    Prayer,
    Verification,
    render_lawsuit_draft,
)


def build_document() -> LawsuitDocument:
    return LawsuitDocument(
        caption=Caption(
            court_name="Superior Court of Example County",
            case_title="Acme Corp. v. Doe",
            case_number="2024-CV-1001",
        ),
        parties=[
            Party(
                party_id="plaintiff",
                name="Acme Corp.",
                role="Plaintiff",
                description="A Delaware corporation.",
            ),
            Party(
                party_id="defendant",
                name="John Doe",
                role="Defendant",
                description="An individual resident of Example County.",
            ),
        ],
        jurisdiction=Jurisdiction(
            basis="Diversity jurisdiction under 28 U.S.C. § 1332.",
            venue="Venue is proper in Example County.",
            court="Superior Court of Example County",
            statutes=["28 U.S.C. § 1332"],
        ),
        facts=[
            Fact(
                heading="Contract formation",
                summary="Plaintiff and Defendant executed a services agreement.",
                party_ids=["plaintiff", "defendant"],
            )
        ],
        causes_of_action=[
            CauseOfAction(
                title="Breach of Contract",
                elements=["Valid contract", "Breach", "Damages"],
                supporting_facts=["Contract formation"],
            )
        ],
        damages=Damages(
            summary="Plaintiff suffered economic damages.",
            items=["Lost profits", "Out-of-pocket expenses"],
        ),
        prayer=Prayer(
            requests=[
                "Award compensatory damages.",
                "Award costs and fees.",
            ]
        ),
        verification=Verification(
            verifier_name="Jane Smith",
            verifier_role="Authorized representative",
            statement="I declare under penalty of perjury that the foregoing is true.",
        ),
        attachments=[
            Attachment(
                title="Exhibit A",
                description="Executed services agreement.",
                reference="Attachment-1",
            )
        ],
    )


def test_render_lawsuit_draft_includes_required_sections() -> None:
    document = build_document()
    draft = render_lawsuit_draft(document)
    assert "Caption" in draft
    assert "Parties" in draft
    assert "Jurisdiction" in draft
    assert "Facts" in draft
    assert "Causes of Action" in draft
    assert "Damages" in draft
    assert "Prayer" in draft
    assert "Verification" in draft
    assert "Attachments" in draft


def test_facts_require_known_parties() -> None:
    with pytest.raises(
        ValueError,
        match=r"fact 'Incident' references unknown party_id 'defendant'\."
    ):
        LawsuitDocument(
            caption=Caption(
                court_name="Superior Court of Example County",
                case_title="Acme Corp. v. Doe",
            ),
            parties=[
                Party(
                    party_id="plaintiff",
                    name="Acme Corp.",
                    role="Plaintiff",
                )
            ],
            jurisdiction=Jurisdiction(
                basis="Diversity jurisdiction.",
                venue="Venue is proper.",
                court="Superior Court of Example County",
            ),
            facts=[
                Fact(
                    heading="Incident",
                    summary="Defendant failed to perform.",
                    party_ids=["defendant"],
                )
            ],
            causes_of_action=[
                CauseOfAction(
                    title="Breach of Contract",
                    elements=["Contract", "Breach", "Damages"],
                )
            ],
            damages=Damages(summary="Damages to be proven."),
            prayer=Prayer(requests=["Award damages."]),
            verification=Verification(
                verifier_name="Jane Smith",
                verifier_role="Authorized representative",
                statement="I declare under penalty of perjury.",
            ),
            attachments=[
                Attachment(
                    title="Exhibit A",
                    description="Agreement.",
                    reference="Attachment-1",
                )
            ],
        )


def test_duplicate_party_ids_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="parties must have unique party_id values"
    ):
        LawsuitDocument(
            caption=Caption(
                court_name="Superior Court of Example County",
                case_title="Acme Corp. v. Doe",
            ),
            parties=[
                Party(
                    party_id="plaintiff",
                    name="Acme Corp.",
                    role="Plaintiff",
                ),
                Party(
                    party_id="plaintiff",
                    name="Another Corp.",
                    role="Co-Plaintiff",
                ),
            ],
            jurisdiction=Jurisdiction(
                basis="Diversity jurisdiction.",
                venue="Venue is proper.",
                court="Superior Court of Example County",
            ),
            facts=[
                Fact(
                    heading="Incident",
                    summary="Something happened.",
                    party_ids=["plaintiff"],
                )
            ],
            causes_of_action=[
                CauseOfAction(
                    title="Breach of Contract",
                    elements=["Contract", "Breach", "Damages"],
                )
            ],
            damages=Damages(summary="Damages to be proven."),
            prayer=Prayer(requests=["Award damages."]),
            verification=Verification(
                verifier_name="Jane Smith",
                verifier_role="Authorized representative",
                statement="I declare under penalty of perjury.",
            ),
            attachments=[
                Attachment(
                    title="Exhibit A",
                    description="Agreement.",
                    reference="Attachment-1",
                )
            ],
        )


def test_unreferenced_parties_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="parties must be referenced in facts: defendant"
    ):
        LawsuitDocument(
            caption=Caption(
                court_name="Superior Court of Example County",
                case_title="Acme Corp. v. Doe",
            ),
            parties=[
                Party(
                    party_id="plaintiff",
                    name="Acme Corp.",
                    role="Plaintiff",
                ),
                Party(
                    party_id="defendant",
                    name="John Doe",
                    role="Defendant",
                ),
            ],
            jurisdiction=Jurisdiction(
                basis="Diversity jurisdiction.",
                venue="Venue is proper.",
                court="Superior Court of Example County",
            ),
            facts=[
                Fact(
                    heading="Incident",
                    summary="Plaintiff performed services.",
                    party_ids=["plaintiff"],
                )
            ],
            causes_of_action=[
                CauseOfAction(
                    title="Breach of Contract",
                    elements=["Contract", "Breach", "Damages"],
                )
            ],
            damages=Damages(summary="Damages to be proven."),
            prayer=Prayer(requests=["Award damages."]),
            verification=Verification(
                verifier_name="Jane Smith",
                verifier_role="Authorized representative",
                statement="I declare under penalty of perjury.",
            ),
            attachments=[
                Attachment(
                    title="Exhibit A",
                    description="Agreement.",
                    reference="Attachment-1",
                )
            ],
        )


def test_empty_party_id_rejected() -> None:
    with pytest.raises(ValueError, match="party.party_id is required"):
        Party(party_id="", name="Test", role="Plaintiff")


def test_whitespace_only_party_id_rejected() -> None:
    with pytest.raises(ValueError, match="party.party_id is required"):
        Party(party_id="   ", name="Test", role="Plaintiff")


def test_empty_sequence_party_ids_in_fact_rejected() -> None:
    with pytest.raises(ValueError, match="fact.party_ids is required"):
        Fact(
            heading="Test",
            summary="Test summary",
            party_ids=[]
        )


def test_empty_string_in_party_ids_rejected() -> None:
    with pytest.raises(ValueError, match=r"fact\.party_ids\[0\] is required"):
        Fact(
            heading="Test",
            summary="Test summary",
            party_ids=[""]
        )


def test_invalid_fact_reference_in_cause_of_action() -> None:
    with pytest.raises(
        ValueError,
        match=(
            r"cause of action 'Breach of Contract' references "
            r"unknown fact heading 'Nonexistent Fact'\."
        )
    ):
        LawsuitDocument(
            caption=Caption(
                court_name="Superior Court of Example County",
                case_title="Acme Corp. v. Doe",
            ),
            parties=[
                Party(
                    party_id="plaintiff",
                    name="Acme Corp.",
                    role="Plaintiff",
                )
            ],
            jurisdiction=Jurisdiction(
                basis="Diversity jurisdiction.",
                venue="Venue is proper.",
                court="Superior Court of Example County",
            ),
            facts=[
                Fact(
                    heading="Contract formation",
                    summary="Plaintiff and Defendant executed a services agreement.",
                    party_ids=["plaintiff"],
                )
            ],
            causes_of_action=[
                CauseOfAction(
                    title="Breach of Contract",
                    elements=["Contract", "Breach", "Damages"],
                    supporting_facts=["Nonexistent Fact"],
                )
            ],
            damages=Damages(summary="Damages to be proven."),
            prayer=Prayer(requests=["Award damages."]),
            verification=Verification(
                verifier_name="Jane Smith",
                verifier_role="Authorized representative",
                statement="I declare under penalty of perjury.",
            ),
            attachments=[
                Attachment(
                    title="Exhibit A",
                    description="Agreement.",
                    reference="Attachment-1",
                )
            ],
        )


def test_render_lawsuit_draft_with_invalid_type() -> None:
    with pytest.raises(
        TypeError,
        match="document must be a LawsuitDocument instance"
    ):
        render_lawsuit_draft("not a document")
