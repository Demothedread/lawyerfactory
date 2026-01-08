import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)

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
    # DEFAULT_GRAPH is already in canonical format, just deep copy it
    return json.loads(json.dumps(DEFAULT_GRAPH))


def save_graph(graph: Dict[str, Any], file_path: Optional[Path] = None) -> None:
    """Write the knowledge graph to disk."""
    path = file_path or KNOWLEDGE_GRAPH_PATH
    with path.open("w", encoding="utf-8") as fh:
        json.dump(normalize_graph(graph), fh, indent=2, ensure_ascii=False)


def normalize_graph(graph: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize entities, relationships, and observations to the canonical schema.

    This function operates directly on the provided dictionary to avoid the
    overhead of constructing a full KnowledgeGraph instance when only the
    serialized form is needed.
    """
    # Ensure we have a dictionary to work with
    if not isinstance(graph, dict):
        # Fall back to an empty graph structure if the input is invalid
        return {
            "entities": {},
            "relationships": [],
            "observations": [],
        }

    raw_entities = graph.get("entities", {})
    raw_relationships = graph.get("relationships", [])
    raw_observations = graph.get("observations", [])

    # Normalize entities: convert list format to dict format
    entities: Dict[str, Any]
    if isinstance(raw_entities, dict):
        # Already in dict format - use as-is (shallow copy to avoid mutation)
        entities = dict(raw_entities)
    elif isinstance(raw_entities, list):
        # Convert from list format: extract id field and use as key
        entities = {}
        for item in raw_entities:
            if isinstance(item, dict) and item.get("id"):
                entity_id = item["id"]
                entities[entity_id] = {
                    key: value for key, value in item.items() if key != "id"
                }
    else:
        entities = {}

    # Normalize relationships: ensure consistent schema
    relationships: List[Dict[str, Any]] = []
    if isinstance(raw_relationships, list):
        for rel in raw_relationships:
            if not isinstance(rel, dict):
                continue
            # Support multiple field names for source/target/relation
            # Use explicit None checks to avoid issues with falsy values
            source = (
                rel.get("source")
                if rel.get("source") is not None
                else rel.get("from")
            )
            target = (
                rel.get("target")
                if rel.get("target") is not None
                else rel.get("to")
            )
            relation = (
                rel.get("relation")
                if rel.get("relation") is not None
                else rel.get("type")
            )

            if source is not None and target is not None and relation is not None:
                relationships.append(
                    {"source": source, "target": target, "relation": relation}
                )

    # Normalize observations: ensure it's a list
    observations: List[str]
    if isinstance(raw_observations, list):
        observations = list(raw_observations)
    else:
        observations = []

    return {
        "entities": entities,
        "relationships": relationships,
        "observations": observations,
    }


def add_entity(
    graph: Dict[str, Any],
    entity_id: Union[str, Dict[str, Any]],
    payload: Optional[Dict[str, Any]] = None,
) -> None:
    """Add or update an entity in a graph dictionary.

    Supports both the current call style:
        add_entity(graph, "entity_id", {"key": "value"})

    and the legacy call style:
        add_entity(graph, {"id": "entity_id", "key": "value"})
    """
    # Backward-compatible handling for the legacy single-dict signature
    if isinstance(entity_id, dict) and payload is None:
        entity_dict = entity_id
        actual_id = entity_dict.get("id")
        if actual_id is None:
            raise ValueError(
                "add_entity requires an 'id' field when called with a dict, "
                "or provide entity_id as the second parameter."
            )
        actual_payload = {k: v for k, v in entity_dict.items() if k != "id"}
    else:
        actual_id = entity_id
        actual_payload = payload or {}

    entities = graph.setdefault("entities", {})
    if not isinstance(entities, dict):
        entities = normalize_graph(graph)["entities"]
        graph["entities"] = entities
    entities[actual_id] = actual_payload


def add_relationship(
    graph: Dict[str, Any],
    source: Union[str, Dict[str, Any]],
    target: Optional[str] = None,
    relation: Optional[str] = None,
) -> None:
    """Append a normalized relationship to the graph dictionary.

    Supports both the current call style:
        add_relationship(graph, "A", "B", "uses")

    and the legacy call style:
        add_relationship(graph, {"source": "A", "target": "B",
                                 "relation": "uses"})
    """
    # Backward-compatible handling for the legacy single-dict signature
    if isinstance(source, dict) and target is None and relation is None:
        rel_dict = source
        source_id = rel_dict.get("source")
        target_id = rel_dict.get("target")
        relation_type = rel_dict.get("relation")
    else:
        source_id = source
        target_id = target
        relation_type = relation

    if source_id is None or target_id is None or relation_type is None:
        raise ValueError(
            "add_relationship requires 'source', 'target', and 'relation' "
            "to be provided, either as separate arguments or within a "
            "relationship dict."
        )

    relationships = graph.setdefault("relationships", [])
    if not isinstance(relationships, list):
        logger.warning(
            "Discarding non-list relationships data (type: %s) and "
            "replacing with empty list",
            type(relationships).__name__
        )
        relationships = []
        graph["relationships"] = relationships
    relationships.append(
        {"source": source_id, "target": target_id, "relation": relation_type}
    )


def add_observation(graph: Dict[str, Any], observation: str) -> None:
    """Append an observation to a graph dictionary."""
    observations = graph.get("observations")
    if isinstance(observations, list):
        # Use the existing list as-is.
        pass
    elif observations is None:
        # No observations key yet; start a new list.
        observations = []
        graph["observations"] = observations
    else:
        # Preserve existing non-list value by wrapping it in a list.
        logger.warning(
            "Converting non-list observations (type: %s) to list by wrapping",
            type(observations).__name__
        )
        observations = [observations]
        graph["observations"] = observations
    observations.append(observation)
