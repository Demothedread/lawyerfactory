import json
from pathlib import Path
from typing import Dict, Any, Optional

KGRAPH_FILE = Path(__file__).resolve().parent / "knowledge_graph.json"


def load_graph(file_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load the knowledge graph from a JSON file."""
    path = file_path or KGRAPH_FILE
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"entities": [], "relationships": [], "observations": []}


def save_graph(
    graph: Dict[str, Any], file_path: Optional[Path] = None
) -> None:
    """Save the knowledge graph to a JSON file."""
    path = file_path or KGRAPH_FILE
    with open(path, "w", encoding="utf-8") as f:
        json.dump(graph, f, indent=2, ensure_ascii=False)


def add_entity(graph: Dict[str, Any], entity: Dict[str, Any]) -> None:
    """Append an entity to the knowledge graph."""
    graph.setdefault("entities", []).append(entity)


def add_relationship(
    graph: Dict[str, Any], relationship: Dict[str, Any]
) -> None:
    """Append a relationship to the knowledge graph."""
    graph.setdefault("relationships", []).append(relationship)


def add_observation(graph: Dict[str, Any], observation: str) -> None:
    """Append an observation to the knowledge graph."""
    graph.setdefault("observations", []).append(observation)
