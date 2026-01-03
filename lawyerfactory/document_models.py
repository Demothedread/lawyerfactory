from dataclasses import dataclass, field
from typing import Sequence


def _require_text(value: str, label: str) -> str:
    if not value or not value.strip():
        raise ValueError(f"{label} is required.")
    return value


def _require_sequence(values: Sequence, label: str) -> Sequence:
    if not values:
        raise ValueError(f"{label} is required.")
    return values


@dataclass(frozen=True)
class Caption:
    court_name: str
    case_title: str
    case_number: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.court_name, "caption.court_name")
        _require_text(self.case_title, "caption.case_title")


@dataclass(frozen=True)
class Party:
    party_id: str
    name: str
    role: str
    description: str = ""

    def __post_init__(self) -> None:
        _require_text(self.party_id, "party.party_id")
        _require_text(self.name, "party.name")
        _require_text(self.role, "party.role")


@dataclass(frozen=True)
class Jurisdiction:
    basis: str
    venue: str
    court: str
    statutes: Sequence[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        _require_text(self.basis, "jurisdiction.basis")
        _require_text(self.venue, "jurisdiction.venue")
        _require_text(self.court, "jurisdiction.court")


@dataclass(frozen=True)
class Fact:
    heading: str
    summary: str
    party_ids: Sequence[str]

    def __post_init__(self) -> None:
        _require_text(self.heading, "fact.heading")
        _require_text(self.summary, "fact.summary")
        _require_sequence(self.party_ids, "fact.party_ids")


@dataclass(frozen=True)
class CauseOfAction:
    title: str
    elements: Sequence[str]
    supporting_facts: Sequence[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        _require_text(self.title, "cause.title")
        _require_sequence(self.elements, "cause.elements")


@dataclass(frozen=True)
class Damages:
    summary: str
    items: Sequence[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        _require_text(self.summary, "damages.summary")


@dataclass(frozen=True)
class Prayer:
    requests: Sequence[str]

    def __post_init__(self) -> None:
        _require_sequence(self.requests, "prayer.requests")


@dataclass(frozen=True)
class Verification:
    verifier_name: str
    verifier_role: str
    statement: str

    def __post_init__(self) -> None:
        _require_text(self.verifier_name, "verification.verifier_name")
        _require_text(self.verifier_role, "verification.verifier_role")
        _require_text(self.statement, "verification.statement")


@dataclass(frozen=True)
class Attachment:
    title: str
    description: str
    reference: str

    def __post_init__(self) -> None:
        _require_text(self.title, "attachment.title")
        _require_text(self.description, "attachment.description")
        _require_text(self.reference, "attachment.reference")


@dataclass(frozen=True)
class LawsuitDocument:
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
        _require_sequence(self.parties, "parties")
        _require_sequence(self.facts, "facts")
        _require_sequence(self.causes_of_action, "causes_of_action")
        _require_sequence(self.attachments, "attachments")
        self._validate_party_references()

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
            f"- {party.name} ({party.role}) {party.description}".rstrip()
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
            f"- {fact.heading}: {fact.summary} "
            f"(Parties: {', '.join(fact.party_ids)})"
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
            f"- {attachment.title}: {attachment.description} "
            f"(Ref: {attachment.reference})"
            for attachment in self.attachments
        )


def render_lawsuit_draft(document: LawsuitDocument) -> str:
    return document.render_text()
