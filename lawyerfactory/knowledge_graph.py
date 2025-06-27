import json
from pathlib import Path
from typing import Dict, Any

KNOWLEDGE_GRAPH_PATH = Path("knowledge_graph.json")

DEFAULT_GRAPH: Dict[str, Any] = {
    "entities": {
        "Lawsuit": {
            "features": [
                "statement_of_facts",
                "description_of_parties",
                "cover_sheet",
            ]
        },
        "Workflow": {
            "stages": [
                "Preproduction Planning",
                "Research and Development",
                "Organization / Database Building",
                "1st Pass All Parts",
                "Combining",
                "Editing",
                "2nd Pass",
                "Human Feedback",
                "Final Draft",
            ]
        },
    },
    "relationships": {},
    "observations": ["Initial graph created."],
}


def load_graph() -> Dict[str, Any]:
    if KNOWLEDGE_GRAPH_PATH.exists():
        with KNOWLEDGE_GRAPH_PATH.open("r") as fh:
            return json.load(fh)
    return DEFAULT_GRAPH


def save_graph(graph: Dict[str, Any]) -> None:
    with KNOWLEDGE_GRAPH_PATH.open("w") as fh:
        json.dump(graph, fh, indent=2)


def add_observation(graph: Dict[str, Any], observation: str) -> None:
    graph.setdefault("observations", []).append(observation)
