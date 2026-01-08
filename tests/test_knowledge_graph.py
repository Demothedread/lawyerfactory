"""Tests for the knowledge_graph module."""

import json
import tempfile
from pathlib import Path

import pytest

from lawyerfactory.knowledge_graph import (
    KnowledgeGraph,
    add_entity,
    add_observation,
    add_relationship,
    load_graph,
    normalize_graph,
    save_graph,
)


class TestNormalizeGraph:
    """Test normalize_graph function."""

    def test_normalize_dict_entities(self):
        """Test that dict-format entities are preserved."""
        graph = {
            "entities": {"A": {"type": "test"}, "B": {"type": "test2"}},
            "relationships": [],
            "observations": [],
        }
        result = normalize_graph(graph)
        assert result["entities"] == {"A": {"type": "test"}, "B": {"type": "test2"}}
        assert result["relationships"] == []
        assert result["observations"] == []

    def test_normalize_list_entities(self):
        """Test that list-format entities are converted to dict format."""
        graph = {
            "entities": [
                {"id": "A", "type": "test"},
                {"id": "B", "type": "test2"},
            ],
            "relationships": [],
            "observations": [],
        }
        result = normalize_graph(graph)
        assert result["entities"] == {"A": {"type": "test"}, "B": {"type": "test2"}}

    def test_normalize_relationships_with_alternative_fields(self):
        """Test that relationships with from/to/type are normalized to
        source/target/relation."""
        graph = {
            "entities": {},
            "relationships": [
                {"from": "A", "to": "B", "type": "uses"},
                {"source": "C", "target": "D", "relation": "needs"},
            ],
            "observations": [],
        }
        result = normalize_graph(graph)
        assert len(result["relationships"]) == 2
        assert result["relationships"][0] == {
            "source": "A", "target": "B", "relation": "uses"
        }
        assert result["relationships"][1] == {
            "source": "C", "target": "D", "relation": "needs"
        }

    def test_normalize_malformed_input(self):
        """Test that malformed input is handled gracefully."""
        # Non-dict input
        result = normalize_graph("invalid")
        assert result == {"entities": {}, "relationships": [], "observations": []}

        # None input
        result = normalize_graph(None)
        assert result == {"entities": {}, "relationships": [], "observations": []}

    def test_normalize_handles_non_list_relationships(self):
        """Test that non-list relationships are converted to empty list."""
        graph = {
            "entities": {},
            "relationships": "invalid",
            "observations": [],
        }
        result = normalize_graph(graph)
        assert result["relationships"] == []

    def test_normalize_handles_non_list_observations(self):
        """Test that non-list observations are converted to empty list."""
        graph = {
            "entities": {},
            "relationships": [],
            "observations": "invalid",
        }
        result = normalize_graph(graph)
        assert result["observations"] == []

    def test_normalize_idempotent(self):
        """Test that normalizing already-normalized data returns equivalent data."""
        graph = {
            "entities": {"A": {"type": "test"}},
            "relationships": [{"source": "A", "target": "B", "relation": "uses"}],
            "observations": ["test"],
        }
        result1 = normalize_graph(graph)
        result2 = normalize_graph(result1)
        assert result1 == result2

    def test_normalize_filters_invalid_relationships(self):
        """Test that relationships without required fields are filtered out."""
        graph = {
            "entities": {},
            "relationships": [
                {"source": "A", "target": "B", "relation": "uses"},
                {"source": "A"},  # Missing target and relation
                "invalid",  # Not a dict
                {"source": "C", "target": None, "relation": "needs"},  # None target
            ],
            "observations": [],
        }
        result = normalize_graph(graph)
        assert len(result["relationships"]) == 1
        assert result["relationships"][0] == {
            "source": "A", "target": "B", "relation": "uses"
        }

    def test_normalize_handles_entities_without_id(self):
        """Test that list entities without id field are skipped."""
        graph = {
            "entities": [
                {"id": "A", "type": "test"},
                {"type": "no_id"},  # No id field
                {"id": "B", "type": "test2"},
            ],
            "relationships": [],
            "observations": [],
        }
        result = normalize_graph(graph)
        assert result["entities"] == {"A": {"type": "test"}, "B": {"type": "test2"}}


class TestAddEntity:
    """Test add_entity helper function."""

    def test_add_entity_current_style(self):
        """Test adding entity with current call style."""
        graph = {"entities": {}}
        add_entity(graph, "test_entity", {"key": "value"})
        assert graph["entities"]["test_entity"] == {"key": "value"}

    def test_add_entity_legacy_style(self):
        """Test adding entity with legacy call style (single dict)."""
        graph = {"entities": {}}
        add_entity(graph, {"id": "test_entity", "key": "value"})
        assert graph["entities"]["test_entity"] == {"key": "value"}

    def test_add_entity_legacy_style_without_id_raises(self):
        """Test that legacy style without id raises ValueError."""
        graph = {"entities": {}}
        with pytest.raises(ValueError, match="requires an 'id' field"):
            add_entity(graph, {"key": "value"})

    def test_add_entity_normalizes_non_dict_entities(self):
        """Test that non-dict entities are normalized."""
        graph = {"entities": [{"id": "A", "type": "test"}]}
        add_entity(graph, "B", {"type": "test2"})
        # Should convert list to dict and add new entity
        assert isinstance(graph["entities"], dict)
        assert "A" in graph["entities"]
        assert "B" in graph["entities"]

    def test_add_entity_creates_entities_if_missing(self):
        """Test that entities key is created if missing."""
        graph = {}
        add_entity(graph, "test", {"key": "value"})
        assert graph["entities"] == {"test": {"key": "value"}}

    def test_add_entity_with_none_payload(self):
        """Test adding entity with None payload creates empty dict."""
        graph = {"entities": {}}
        add_entity(graph, "test", None)
        assert graph["entities"]["test"] == {}


class TestAddRelationship:
    """Test add_relationship helper function."""

    def test_add_relationship_current_style(self):
        """Test adding relationship with current call style."""
        graph = {"relationships": []}
        add_relationship(graph, "A", "B", "uses")
        expected = [{"source": "A", "target": "B", "relation": "uses"}]
        assert graph["relationships"] == expected

    def test_add_relationship_legacy_style(self):
        """Test adding relationship with legacy call style (single dict)."""
        graph = {"relationships": []}
        add_relationship(
            graph, {"source": "A", "target": "B", "relation": "uses"}
        )
        expected = [{"source": "A", "target": "B", "relation": "uses"}]
        assert graph["relationships"] == expected

    def test_add_relationship_legacy_style_incomplete_raises(self):
        """Test that legacy style without required fields raises
        ValueError."""
        graph = {"relationships": []}
        with pytest.raises(
            ValueError, match="requires 'source', 'target', and 'relation'"
        ):
            add_relationship(graph, {"source": "A", "target": "B"})

    def test_add_relationship_current_style_incomplete_raises(self):
        """Test that current style with None values raises ValueError."""
        graph = {"relationships": []}
        with pytest.raises(
            ValueError, match="requires 'source', 'target', and 'relation'"
        ):
            add_relationship(graph, "A", None, "uses")

    def test_add_relationship_normalizes_non_list(self):
        """Test that non-list relationships are replaced with empty list."""
        graph = {"relationships": "invalid"}
        add_relationship(graph, "A", "B", "uses")
        expected = [{"source": "A", "target": "B", "relation": "uses"}]
        assert graph["relationships"] == expected

    def test_add_relationship_creates_key_if_missing(self):
        """Test that relationships key is created if missing."""
        graph = {}
        add_relationship(graph, "A", "B", "uses")
        expected = [{"source": "A", "target": "B", "relation": "uses"}]
        assert graph["relationships"] == expected


class TestAddObservation:
    """Test add_observation helper function."""

    def test_add_observation_to_list(self):
        """Test adding observation to existing list."""
        graph = {"observations": ["first"]}
        add_observation(graph, "second")
        assert graph["observations"] == ["first", "second"]

    def test_add_observation_creates_list_if_missing(self):
        """Test that observations list is created if missing."""
        graph = {}
        add_observation(graph, "test")
        assert graph["observations"] == ["test"]

    def test_add_observation_wraps_non_list(self):
        """Test that non-list observation is wrapped in list."""
        graph = {"observations": "single_string"}
        add_observation(graph, "new")
        assert graph["observations"] == ["single_string", "new"]


class TestKnowledgeGraphToDict:
    """Test KnowledgeGraph.to_dict method."""

    def test_to_dict_returns_dict_keyed_entities(self):
        """Test that to_dict returns entities as dict keyed by ID."""
        seed = {"entities": {}, "relationships": [], "observations": []}
        kg = KnowledgeGraph(seed=seed)
        kg.add_entity("A", {"type": "test"})
        kg.add_entity("B", {"type": "test2"})
        result = kg.to_dict()

        assert isinstance(result["entities"], dict)
        assert "A" in result["entities"]
        assert "B" in result["entities"]
        assert result["entities"]["A"] == {"type": "test"}
        assert result["entities"]["B"] == {"type": "test2"}

    def test_to_dict_roundtrip(self):
        """Test that to_dict output can be loaded back correctly."""
        seed = {"entities": {}, "relationships": [], "observations": []}
        kg = KnowledgeGraph(seed=seed)
        kg.add_entity("A", {"type": "test"})
        kg.add_relationship("A", "B", "uses")
        kg.add_observation("test observation")

        serialized = kg.to_dict()
        kg2 = KnowledgeGraph(seed=serialized)

        assert kg2.entities == kg.entities
        assert kg2.relationships == kg.relationships
        assert kg2.observations == kg.observations


class TestLoadSaveGraph:
    """Test load_graph and save_graph functions."""

    def test_save_and_load_roundtrip(self):
        """Test that saving and loading preserves the graph."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test_graph.json"

            graph = {
                "entities": {"A": {"type": "test"}},
                "relationships": [{"source": "A", "target": "B", "relation": "uses"}],
                "observations": ["test"],
            }

            save_graph(graph, path)
            loaded = load_graph(path)

            assert loaded["entities"] == graph["entities"]
            assert loaded["relationships"] == graph["relationships"]
            assert loaded["observations"] == graph["observations"]

    def test_load_nonexistent_returns_default(self):
        """Test that loading nonexistent file returns DEFAULT_GRAPH."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "nonexistent.json"
            loaded = load_graph(path)

            # Should return a copy of DEFAULT_GRAPH
            assert "entities" in loaded
            assert "relationships" in loaded
            assert "observations" in loaded

    def test_save_normalizes_graph(self):
        """Test that save_graph normalizes the graph before saving."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test_graph.json"

            # Graph with list-format entities
            graph = {
                "entities": [{"id": "A", "type": "test"}],
                "relationships": [],
                "observations": [],
            }

            save_graph(graph, path)

            # Load the raw JSON to verify it was normalized
            with path.open("r") as f:
                saved = json.load(f)

            # Should be converted to dict format
            assert isinstance(saved["entities"], dict)
            assert "A" in saved["entities"]


class TestKnowledgeGraphNormalization:
    """Test KnowledgeGraph class normalization."""

    def test_kg_normalizes_list_entities_on_init(self):
        """Test that KnowledgeGraph normalizes list-format entities on
        initialization."""
        kg = KnowledgeGraph(
            seed={
                "entities": [{"id": "A", "type": "test"}],
                "relationships": [],
                "observations": [],
            }
        )
        assert isinstance(kg.entities, dict)
        assert "A" in kg.entities
        assert kg.entities["A"] == {"type": "test"}

    def test_kg_normalizes_relationships_with_alternative_fields(self):
        """Test that KnowledgeGraph normalizes relationships with
        from/to/type."""
        kg = KnowledgeGraph(
            seed={
                "entities": {},
                "relationships": [{"from": "A", "to": "B", "type": "uses"}],
                "observations": [],
            }
        )
        assert len(kg.relationships) == 1
        expected = {"source": "A", "target": "B", "relation": "uses"}
        assert kg.relationships[0] == expected
