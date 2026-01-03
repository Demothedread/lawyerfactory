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
    with pytest.raises(ValueError, match="unknown party_id"):
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
