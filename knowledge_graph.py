import json
from pathlib import Path
from typing import Any, Dict, Optional

KGRAPH_FILE = Path("knowledge_graph.json")

DEFAULT_GRAPH: Dict[str, Any] = {
    "entities": [
        {
            "id": "Lawsuit",
            "type": "document",
            "features": [
                "statement_of_facts",
                "description_of_parties",
                "cover_sheet",
            ],
        },
        {
            "id": "Workflow",
            "type": "meta",
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
            ],
        },
    ],
    "relationships": [],
    "observations": ["Initial graph created."],
}


def load_graph(file_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load the knowledge graph JSON or return a default scaffold."""

    path = file_path or KGRAPH_FILE
    if path.exists():
        with path.open("r", encoding="utf-8") as graph_file:
            return json.load(graph_file)
    return json.loads(json.dumps(DEFAULT_GRAPH))


def save_graph(graph: Dict[str, Any], file_path: Optional[Path] = None) -> None:
    """Persist the knowledge graph to disk."""

    path = file_path or KGRAPH_FILE
    with path.open("w", encoding="utf-8") as graph_file:
        json.dump(graph, graph_file, indent=2, ensure_ascii=False)


def add_entity(graph: Dict[str, Any], entity: Dict[str, Any]) -> None:
    """Append an entity node to the graph in-memory."""

    graph.setdefault("entities", []).append(entity)


def add_relationship(graph: Dict[str, Any], relationship: Dict[str, Any]) -> None:
    """Append a relationship to the graph in-memory."""

    graph.setdefault("relationships", []).append(relationship)


def add_observation(graph: Dict[str, Any], observation: str) -> None:
    """Append a textual observation to the graph in-memory."""

    graph.setdefault("observations", []).append(observation)


if __name__ == "__main__":
    import sys

    graph_state = load_graph()
    if len(sys.argv) > 1:
        add_observation(graph_state, " ".join(sys.argv[1:]))
        save_graph(graph_state)
    else:
        print(json.dumps(graph_state, indent=2))
