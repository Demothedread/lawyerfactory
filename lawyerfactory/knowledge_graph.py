import json
from pathlib import Path
from typing import Any, Dict, List, Optional

KNOWLEDGE_GRAPH_PATH = Path("knowledge_graph.json")

DEFAULT_GRAPH: Dict[str, Any] = {
    "entities": {
        "Lawsuit": {
            "type": "document",
            "features": [
                "statement_of_facts",
                "description_of_parties",
                "cover_sheet",
            ],
        },
        "Workflow": {
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
    },
    "relationships": [],
    "observations": ["Initial graph created."],
}

EMPTY_GRAPH: Dict[str, Any] = {"entities": {}, "relationships": [], "observations": []}


class KnowledgeGraph:
    """Lightweight in-memory knowledge graph with optional persistence."""

    def __init__(
        self,
        path: Optional[Path] = None,
        seed: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.path = path or KNOWLEDGE_GRAPH_PATH
        initial_source = seed if seed is not None else DEFAULT_GRAPH
        initial = json.loads(json.dumps(initial_source))
        entities = initial.get("entities", {})
        relationships = initial.get("relationships", [])
        observations = initial.get("observations", [])

        self.entities: Dict[str, Any] = self._normalize_entities(entities)
        self.relationships: List[Dict[str, Any]] = self._normalize_relationships(
            relationships
        )
        self.observations: List[str] = (
            observations if isinstance(observations, list) else []
        )

    def _normalize_entities(self, entities: Any) -> Dict[str, Any]:
        """Convert entities from list-or-dict into a keyed dictionary."""

        if isinstance(entities, dict):
            return entities

        normalized: Dict[str, Any] = {}
        if isinstance(entities, list):
            for item in entities:
                if isinstance(item, dict) and item.get("id"):
                    entity_id = item["id"]
                    normalized[entity_id] = {
                        key: value for key, value in item.items() if key != "id"
                    }
        return normalized

    def _normalize_relationships(self, relationships: Any) -> List[Dict[str, Any]]:
        """Ensure relationships use a consistent schema."""

        if not isinstance(relationships, list):
            return []

        normalized: List[Dict[str, Any]] = []
        for rel in relationships:
            if not isinstance(rel, dict):
                continue
            source = rel.get("source") or rel.get("from")
            target = rel.get("target") or rel.get("to")
            relation = rel.get("relation") or rel.get("type")

            if source and target and relation:
                normalized.append(
                    {"source": source, "target": target, "relation": relation}
                )
        return normalized

    def add_entity(self, entity: str, data: Any = None) -> None:
        """Add or update an entity payload."""
        self.entities[entity] = data or {}

    def get_entity(self, entity: str) -> Any:
        """Fetch an entity payload by key."""
        return self.entities.get(entity)

    def add_relationship(self, source: str, target: str, relation: str) -> None:
        """Store a relationship triple."""
        self.relationships.append(
            {
                "source": source,
                "target": target,
                "relation": relation,
            }
        )

    def get_relationships(self) -> List[Dict[str, Any]]:
        """Return all relationships."""
        return self.relationships

    def add_observation(self, observation: str) -> None:
        """Record a descriptive note."""
        self.observations.append(observation)

    def to_dict(self) -> Dict[str, Any]:
        """Materialize the graph to a serializable dictionary."""
        return {
            "entities": self.entities,
            "relationships": self.relationships,
            "observations": self.observations,
        }

    def save(self) -> None:
        """Persist the graph to its configured path."""
        save_graph(self.to_dict(), self.path)


def load_graph(file_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load the knowledge graph from disk if present."""
    path = file_path or KNOWLEDGE_GRAPH_PATH
    if path.exists():
        with path.open("r", encoding="utf-8") as fh:
            return normalize_graph(json.load(fh))
    return normalize_graph(json.loads(json.dumps(DEFAULT_GRAPH)))


def save_graph(graph: Dict[str, Any], file_path: Optional[Path] = None) -> None:
    """Write the knowledge graph to disk."""
    path = file_path or KNOWLEDGE_GRAPH_PATH
    with path.open("w", encoding="utf-8") as fh:
        json.dump(normalize_graph(graph), fh, indent=2, ensure_ascii=False)


def normalize_graph(graph: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize entities and relationships to the canonical schema."""
    normalized = KnowledgeGraph(seed=graph)
    return {
        "entities": normalized.entities,
        "relationships": normalized.relationships,
        "observations": normalized.observations,
    }


def add_entity(
    graph: Dict[str, Any],
    entity_id: str,
    payload: Optional[Dict[str, Any]] = None,
) -> None:
    """Add or update an entity in a graph dictionary."""
    entities = graph.setdefault("entities", {})
    if not isinstance(entities, dict):
        entities = normalize_graph(graph)["entities"]
        graph["entities"] = entities
    entities[entity_id] = payload or {}


def add_relationship(
    graph: Dict[str, Any],
    source: str,
    target: str,
    relation: str,
) -> None:
    """Append a normalized relationship to the graph dictionary."""
    relationships = graph.setdefault("relationships", [])
    if not isinstance(relationships, list):
        relationships = []
        graph["relationships"] = relationships
    relationships.append({"source": source, "target": target, "relation": relation})


def add_observation(graph: Dict[str, Any], observation: str) -> None:
    """Append an observation to a graph dictionary."""
    observations = graph.setdefault("observations", [])
    if not isinstance(observations, list):
        observations = []
        graph["observations"] = observations
    observations.append(observation)
