"""Tests for Maestro orchestration and research workflow."""

import tempfile
from pathlib import Path
import pytest

from maestro.maestro import Maestro
from maestro.database import Database
from lawyerfactory.ai_vector import VectorStore
from lawyerfactory.research_artifacts import (
    ResearchArtifact,
    ResearchFilters,
    ResearchSource
)


def test_database_add_and_retrieve():
    """Test Database can store and retrieve items."""
    db = Database()

    item1 = {"id": "1", "data": "test1"}
    item2 = {"id": "2", "data": "test2"}

    db.add(item1)
    db.add(item2)

    all_items = db.all()
    assert len(all_items) == 2
    assert item1 in all_items
    assert item2 in all_items


def test_maestro_initialization():
    """Test Maestro initializes with required components."""
    maestro = Maestro()

    assert maestro.db is not None
    assert maestro.vector_store is not None
    assert maestro.planner_bot is not None
    assert maestro.research_bot is not None
    assert maestro.editor_bot is not None
    assert maestro.writer_bot is not None


def test_maestro_store_research_artifact():
    """Test that Maestro stores research artifacts correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        maestro = Maestro()
        # Override vector store to use temp directory
        maestro.vector_store = VectorStore(
            storage_path=Path(tmpdir) / "test_store.pkl"
        )

        # Create a research artifact
        filters = ResearchFilters(jurisdiction="CA")
        sources = [
            ResearchSource(
                source_id="test-1",
                title="Test Case",
                citation="Test Citation",
                content="This is test content for the case."
            )
        ]

        artifact = ResearchArtifact(
            query="test query",
            summary="test summary",
            filters=filters,
            sources=sources
        )

        # Store the artifact
        maestro._store_research_artifact(artifact)

        # Check database has the artifact
        db_items = maestro.db.all()
        assert len(db_items) == 1
        assert db_items[0]["query"] == "test query"

        # Check vector store has the entries
        maestro.vector_store.update_vectors()
        assert len(maestro.vector_store.texts) > 0

        # Search should return results
        results = maestro.vector_store.search("test content", top_k=5)
        assert len(results) > 0


def test_maestro_format_retrieved():
    """Test that Maestro formats retrieved chunks with citations."""
    maestro = Maestro()

    retrieved = [
        {
            "text": "First chunk of text",
            "metadata": {"citation": "Citation 1"},
            "score": 0.9
        },
        {
            "text": "Second chunk of text",
            "metadata": {"citation": "Citation 2"},
            "score": 0.8
        }
    ]

    formatted = maestro._format_retrieved(retrieved)

    assert "First chunk of text (Citation 1)" in formatted
    assert "Second chunk of text (Citation 2)" in formatted


def test_maestro_format_retrieved_with_missing_citation():
    """Test formatting handles missing citation metadata."""
    maestro = Maestro()

    retrieved = [
        {
            "text": "Text without citation",
            "metadata": {},
            "score": 0.5
        }
    ]

    formatted = maestro._format_retrieved(retrieved)

    # Should use default citation
    assert "Text without citation (Unknown citation)" in formatted


@pytest.mark.asyncio
async def test_maestro_research_and_write():
    """Test the full research_and_write workflow."""
    with tempfile.TemporaryDirectory() as tmpdir:
        maestro = Maestro()
        # Override vector store to use temp directory
        maestro.vector_store = VectorStore(
            storage_path=Path(tmpdir) / "test_workflow.pkl"
        )

        # Run the workflow
        result = await maestro.research_and_write("contract law")

        # Should return a string result
        assert isinstance(result, str)
        assert len(result) > 0

        # Database should have research artifact
        db_items = maestro.db.all()
        assert len(db_items) > 0

        # Vector store should have indexed content
        maestro.vector_store.update_vectors()
        assert len(maestro.vector_store.texts) > 0


@pytest.mark.asyncio
async def test_maestro_research_workflow_with_filtering():
    """Test that research workflow applies filters correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        maestro = Maestro()
        maestro.vector_store = VectorStore(
            storage_path=Path(tmpdir) / "test_filtering.pkl"
        )

        # Create multiple artifacts with different jurisdictions
        artifact1 = ResearchArtifact(
            query="CA case",
            summary="CA summary",
            filters=ResearchFilters(jurisdiction="CA"),
            sources=[
                ResearchSource(
                    source_id="ca-1",
                    title="CA Case",
                    citation="CA Citation",
                    content="California case content"
                )
            ]
        )

        artifact2 = ResearchArtifact(
            query="NY case",
            summary="NY summary",
            filters=ResearchFilters(jurisdiction="NY"),
            sources=[
                ResearchSource(
                    source_id="ny-1",
                    title="NY Case",
                    citation="NY Citation",
                    content="New York case content"
                )
            ]
        )

        # Store both artifacts
        maestro._store_research_artifact(artifact1)
        maestro._store_research_artifact(artifact2)
        maestro.vector_store.update_vectors()

        # Search with CA filter
        ca_results = maestro.vector_store.search(
            "case content",
            top_k=5,
            filters={"jurisdiction": "CA"}
        )

        # Should only get CA results
        assert len(ca_results) == 1
        assert ca_results[0]["metadata"]["jurisdiction"] == "CA"


@pytest.mark.asyncio
async def test_maestro_handles_empty_sources():
    """Test Maestro handles artifacts with no sources."""
    with tempfile.TemporaryDirectory() as tmpdir:
        maestro = Maestro()
        maestro.vector_store = VectorStore(
            storage_path=Path(tmpdir) / "test_empty.pkl"
        )

        # Artifact with no sources
        artifact = ResearchArtifact(
            query="test",
            summary="This is just a summary with no sources",
            filters=ResearchFilters(),
            sources=[]
        )

        # Should not crash
        maestro._store_research_artifact(artifact)
        maestro.vector_store.update_vectors()

        # Database should have the artifact
        assert len(maestro.db.all()) == 1

        # Vector store should have the summary
        assert len(maestro.vector_store.texts) > 0


@pytest.mark.asyncio
async def test_maestro_preserves_metadata_through_workflow():
    """Test that metadata is preserved through the workflow."""
    with tempfile.TemporaryDirectory() as tmpdir:
        maestro = Maestro()
        maestro.vector_store = VectorStore(
            storage_path=Path(tmpdir) / "test_metadata.pkl"
        )

        # Create artifact with specific metadata
        artifact = ResearchArtifact(
            query="specific query",
            summary="summary",
            filters=ResearchFilters(
                jurisdiction="Federal",
                claim_elements=("negligence", "damages")
            ),
            sources=[
                ResearchSource(
                    source_id="src-1",
                    title="Source Title",
                    citation="Source Citation",
                    content="Source content here",
                    url="http://example.com"
                )
            ]
        )

        maestro._store_research_artifact(artifact)
        maestro.vector_store.update_vectors()

        # Retrieve and check metadata
        results = maestro.vector_store.search("content", top_k=1)
        assert len(results) == 1

        metadata = results[0]["metadata"]
        assert metadata["query"] == "specific query"
        assert metadata["jurisdiction"] == "Federal"
        assert metadata["claim_elements"] == ["negligence", "damages"]
        assert metadata["citation"] == "Source Citation"
        assert metadata["source"] == "Source Title"
        assert metadata["source_id"] == "src-1"
        assert metadata["url"] == "http://example.com"


def test_maestro_format_retrieved_empty_list():
    """Test formatting handles empty results list."""
    maestro = Maestro()

    formatted = maestro._format_retrieved([])

    # Should return empty string
    assert formatted == ""
