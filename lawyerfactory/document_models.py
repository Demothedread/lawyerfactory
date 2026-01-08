"""Data model for representing structured lawsuit / complaint documents.

This module defines a small set of immutable dataclasses that together form an
in-memory schema for a civil lawsuit or similar pleading. Each class models a
distinct section or concept in the document, and validates its required
fields at construction time:

* ``Caption`` – court name, case title, and optional case number.
* ``Party`` – a party to the case, identified by ``party_id`` with a role
  such as ``"plaintiff"`` or ``"defendant"``.
* ``Jurisdiction`` – basis for jurisdiction and venue information.
* ``Fact`` – a factual allegation, associated with one or more party IDs.
* ``CauseOfAction`` – a legal claim, its elements, and supporting facts.
* ``Damages`` – a summary of alleged harm and optional itemized details.
* ``Prayer`` – the relief or remedies requested from the court.
* ``Verification`` – sworn statement verifying the facts.
* ``Attachment`` – supporting documents referenced in the pleading.
* ``LawsuitDocument`` – the top-level container for all sections.

Typical usage involves composing these objects into a higher-level lawsuit
representation that can later be rendered into natural-language pleadings or
analyzed by other components. For example:

    caption = Caption(
        court_name="Superior Court of California, County of San Francisco",
        case_title="Jane Doe v. Acme Corp.",
        case_number=None,
    )

    plaintiff = Party(party_id="P1", name="Jane Doe", role="plaintiff")
    defendant = Party(party_id="D1", name="Acme Corp.", role="defendant")

    fact = Fact(
        heading="Employment Relationship",
        summary="Jane Doe worked for Acme Corp. as a software engineer.",
        party_ids=["P1", "D1"],
    )

    cause = CauseOfAction(
        title="Wrongful Termination",
        elements=[
            "Existence of an employment relationship",
            "Termination of employment",
            "Termination in violation of public policy",
        ],
        supporting_facts=[fact.heading],
    )

The classes themselves do not enforce any particular container or storage
structure; they are intended to be simple, validated building blocks that
other parts of the system can assemble into complete document models.
"""
from dataclasses import dataclass, field
from typing import Sequence


def _validate_text(value: str, label: str) -> None:
    if not value or not value.strip():
        raise ValueError(f"{label} is required.")


def _validate_sequence(values: Sequence, label: str) -> None:
    if not values:
        raise ValueError(f"{label} is required.")


@dataclass(frozen=True)
class Caption:
    court_name: str
    case_title: str
    case_number: str | None = None

    def __post_init__(self) -> None:
        _validate_text(self.court_name, "caption.court_name")
        _validate_text(self.case_title, "caption.case_title")


@dataclass(frozen=True)
class Party:
    party_id: str
    name: str
    role: str
    description: str = ""

    def __post_init__(self) -> None:
        _validate_text(self.party_id, "party.party_id")
        _validate_text(self.name, "party.name")
        _validate_text(self.role, "party.role")


@dataclass(frozen=True)
class Jurisdiction:
    basis: str
    venue: str
    court: str
    statutes: Sequence[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        _validate_text(self.basis, "jurisdiction.basis")
        _validate_text(self.venue, "jurisdiction.venue")
        _validate_text(self.court, "jurisdiction.court")


@dataclass(frozen=True)
class Fact:
    heading: str
    summary: str
    party_ids: Sequence[str]

    def __post_init__(self) -> None:
        _validate_text(self.heading, "fact.heading")
        _validate_text(self.summary, "fact.summary")
        _validate_sequence(self.party_ids, "fact.party_ids")
        for index, party_id in enumerate(self.party_ids):
            _validate_text(party_id, f"fact.party_ids[{index}]")


@dataclass(frozen=True)
class CauseOfAction:
    title: str
    elements: Sequence[str]
    supporting_facts: Sequence[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        _validate_text(self.title, "cause.title")
        _validate_sequence(self.elements, "cause.elements")


@dataclass(frozen=True)
class Damages:
    summary: str
    items: Sequence[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        _validate_text(self.summary, "damages.summary")


@dataclass(frozen=True)
class Prayer:
    requests: Sequence[str]

    def __post_init__(self) -> None:
        _validate_sequence(self.requests, "prayer.requests")


@dataclass(frozen=True)
class Verification:
    verifier_name: str
    verifier_role: str
    statement: str

    def __post_init__(self) -> None:
        _validate_text(self.verifier_name, "verification.verifier_name")
        _validate_text(self.verifier_role, "verification.verifier_role")
        _validate_text(self.statement, "verification.statement")


@dataclass(frozen=True)
class Attachment:
    title: str
    description: str
    reference: str

    def __post_init__(self) -> None:
        _validate_text(self.title, "attachment.title")
        _validate_text(self.description, "attachment.description")
        _validate_text(self.reference, "attachment.reference")


@dataclass(frozen=True)
class LawsuitDocument:
    """Top-level container for all sections of a lawsuit document.

    This class enforces validation rules to ensure document integrity:

    1. **Unique party_id values**: All parties must have unique identifiers.
    2. **Valid party references**: All party_ids referenced in facts must
       correspond to declared parties in the parties list.
    3. **All parties referenced**: Every declared party must be referenced
       in at least one fact to prevent orphaned party declarations.
    4. **Valid fact references**: All fact headings referenced in
       supporting_facts of causes of action must correspond to actual facts
       in the facts list.

    Raises:
        ValueError: If any validation rule is violated during construction.
    """
    caption: Caption
    parties: Sequence[Party]
    jurisdiction: Jurisdiction
    facts: Sequence[Fact]
    causes_of_action: Sequence[CauseOfAction]
    damages: Damages
    prayer: Prayer
    verification: Verification
    attachments: Sequence[Attachment]

    def __post_init__(self) -> None:
        _validate_sequence(self.parties, "parties")
        _validate_sequence(self.facts, "facts")
        _validate_sequence(self.causes_of_action, "causes_of_action")
        _validate_sequence(self.attachments, "attachments")
        self._validate_party_references()
        self._validate_fact_references()

    def _validate_party_references(self) -> None:
        party_ids = [party.party_id for party in self.parties]
        if len(set(party_ids)) != len(party_ids):
            raise ValueError("parties must have unique party_id values.")
        referenced_ids = set()
        for fact in self.facts:
            for party_id in fact.party_ids:
                if party_id not in party_ids:
                    raise ValueError(
                        (
                            f"fact '{fact.heading}' references unknown party_id "
                            f"'{party_id}'."
                        )
                    )
                referenced_ids.add(party_id)
        missing = sorted(set(party_ids) - referenced_ids)
        if missing:
            raise ValueError(
                "parties must be referenced in facts: " + ", ".join(missing)
            )

    def _validate_fact_references(self) -> None:
        fact_headings = {fact.heading for fact in self.facts}
        for cause in self.causes_of_action:
            for fact_heading in cause.supporting_facts:
                if fact_heading not in fact_headings:
                    raise ValueError(
                        (
                            f"cause of action '{cause.title}' references "
                            f"unknown fact heading '{fact_heading}'."
                        )
                    )

    def render_text(self) -> str:
        sections = [
            ("Caption", self._render_caption()),
            ("Parties", self._render_parties()),
            ("Jurisdiction", self._render_jurisdiction()),
            ("Facts", self._render_facts()),
            ("Causes of Action", self._render_causes()),
            ("Damages", self._render_damages()),
            ("Prayer", self._render_prayer()),
            ("Verification", self._render_verification()),
            ("Attachments", self._render_attachments()),
        ]
        return "\n\n".join(f"{title}\n{body}" for title, body in sections)

    def _render_caption(self) -> str:
        caption = self.caption
        case_number = caption.case_number or "TBD"
        return f"{caption.court_name}\n{caption.case_title}\nCase No. {case_number}"

    def _render_parties(self) -> str:
        return "\n".join(
            f"- {party.name} ({party.role})"
            + (f" {party.description}" if party.description else "")
            for party in self.parties
        )

    def _render_jurisdiction(self) -> str:
        statutes = ", ".join(self.jurisdiction.statutes) or "N/A"
        return (
            f"Basis: {self.jurisdiction.basis}\n"
            f"Venue: {self.jurisdiction.venue}\n"
            f"Court: {self.jurisdiction.court}\n"
            f"Statutes: {statutes}"
        )

    def _render_facts(self) -> str:
        return "\n".join(
            f"- {fact.heading}: {fact.summary}"
            f" (Parties: {', '.join(fact.party_ids)})"
            for fact in self.facts
        )

    def _render_causes(self) -> str:
        lines: list[str] = []
        for cause in self.causes_of_action:
            elements = "; ".join(cause.elements)
            supporting = ", ".join(cause.supporting_facts) or "N/A"
            lines.append(
                (
                    f"- {cause.title}\n"
                    f"  Elements: {elements}\n"
                    f"  Supporting Facts: {supporting}"
                )
            )
        return "\n".join(lines)

    def _render_damages(self) -> str:
        items = "\n".join(f"- {item}" for item in self.damages.items)
        items_text = items or "- None specified"
        return f"{self.damages.summary}\n{items_text}"

    def _render_prayer(self) -> str:
        return "\n".join(f"- {request}" for request in self.prayer.requests)

    def _render_verification(self) -> str:
        return (
            f"{self.verification.statement}\n"
            "Signed: "
            f"{self.verification.verifier_name}, {self.verification.verifier_role}"
        )

    def _render_attachments(self) -> str:
        return "\n".join(
            f"- {attachment.title}: {attachment.description}"
            f" (Ref: {attachment.reference})"
            for attachment in self.attachments
        )


def render_lawsuit_draft(document: LawsuitDocument) -> str:
    """Render a lawsuit document to human-readable plain text.

    Args:
        document: The LawsuitDocument instance to render.

    Returns:
        A formatted string containing all sections of the lawsuit document.

    Raises:
        TypeError: If document is not a LawsuitDocument instance.
    """
    if not isinstance(document, LawsuitDocument):
        raise TypeError("document must be a LawsuitDocument instance")
    return document.render_text()
