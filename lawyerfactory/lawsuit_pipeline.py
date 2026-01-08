from dataclasses import dataclass
from typing import Any, Dict, List

REQUIRED_LAWSUIT_SECTIONS = (
    "caption",
    "jurisdiction",
    "parties",
    "statement_of_facts",
    "causes_of_action",
    "legal_arguments",
    "prayer_for_relief",
)

REQUIRED_METADATA_FIELDS = ("jurisdiction", "parties")


@dataclass(frozen=True)
class LawsuitIntake:
    title: str
    jurisdiction: str
    parties: List[str]
    facts: str
    claims: List[str]
    citations: List[str]


def _build_caption(title: str, parties: List[str]) -> str:
    caption_parties = " v. ".join(parties) if parties else "Unknown Parties"
    return f"{title} — {caption_parties}"


def _build_causes_of_action(claims: List[str]) -> List[str]:
    if not claims:
        return ["Count 1: Placeholder claim"]
    return [f"Count {index + 1}: {claim}" for index, claim in enumerate(claims)]


def _build_legal_arguments(
    claims: List[str], citations: List[str]
) -> List[Dict[str, Any]]:
    argument_citations = citations or ["Citation pending"]
    arguments: List[Dict[str, Any]] = []
    for claim in claims or ["General liability"]:
        arguments.append(
            {
                "claim": claim,
                "argument": f"The facts support {claim.lower()} under the law.",
                "citations": argument_citations,
            }
        )
    return arguments


def _build_sections(intake: LawsuitIntake) -> Dict[str, Any]:
    return {
        "caption": _build_caption(intake.title, intake.parties),
        "jurisdiction": (
            f"This court has jurisdiction in {intake.jurisdiction}."
        ),
        "parties": intake.parties,
        "statement_of_facts": intake.facts,
        "causes_of_action": _build_causes_of_action(intake.claims),
        "legal_arguments": _build_legal_arguments(
            intake.claims, intake.citations
        ),
        "prayer_for_relief": "Plaintiff requests all relief deemed just.",
    }


def run_lawsuit_pipeline(intake: LawsuitIntake) -> Dict[str, Any]:
    metadata = {
        "title": intake.title,
        "jurisdiction": intake.jurisdiction,
        "parties": intake.parties,
    }
    return {
        "metadata": metadata,
        "sections": _build_sections(intake),
    }
