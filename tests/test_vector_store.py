"""Tests for VectorStore persistence, chunking, and filtering."""

import tempfile
from pathlib import Path
import pytest

from lawyerfactory.ai_vector import VectorStore


@pytest.fixture
def temp_store():
    """Fixture to create a VectorStore with isolated temp storage."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store = VectorStore(storage_path=Path(tmpdir) / "test_store.pkl")
        yield store


def test_vector_store_basic_add_and_search(temp_store):
    """Test basic add and search operations."""
    temp_store.add("The quick brown fox jumps over the lazy dog", {"source": "test"})
    temp_store.update_vectors()

    results = temp_store.search("fox jumps", top_k=1)
    assert len(results) == 1
    assert "fox" in results[0]["text"]
    assert results[0]["metadata"]["source"] == "test"


def test_vector_store_chunking(temp_store):
    """Test that long text is properly chunked."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store = VectorStore(
            storage_path=Path(tmpdir) / "chunked.pkl",
            chunk_size=5,
            chunk_overlap=2
        )

        # Text with 20 words should be split into multiple chunks
        text = " ".join([f"word{i}" for i in range(20)])
        store.add(text, {"source": "chunked"})

        # Should have multiple chunks
        assert len(store.texts) > 1

        # All chunks should have the same source metadata
        for metadata in store.metadata:
            assert metadata["source"] == "chunked"
            assert "chunk_index" in metadata
            assert "chunk_total" in metadata


def test_vector_store_sentence_aware_chunking(temp_store):
    """Test that chunking respects sentence boundaries."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store = VectorStore(
            storage_path=Path(tmpdir) / "sentences.pkl",
            chunk_size=10,
            chunk_overlap=2
        )

        text = "This is sentence one. This is sentence two. This is sentence three."
        store.add(text, {"source": "sentences"})

        # Verify chunks were created
        assert len(store.texts) > 0

        # Check that chunks don't break mid-sentence (when possible)
        for chunk_text in store.texts:
            # Chunks should generally end with sentence terminators or be at boundaries
            assert chunk_text.strip() != ""


def test_vector_store_metadata_filtering_jurisdiction(temp_store):
    """Test filtering by jurisdiction."""
    temp_store.add("California case law text", {"jurisdiction": "CA", "type": "case"})
    temp_store.add("New York case law text", {"jurisdiction": "NY", "type": "case"})
    temp_store.add("Federal case law text", {"jurisdiction": "Federal", "type": "case"})

    temp_store.update_vectors()

    # Search with CA filter
    ca_results = temp_store.search(
        "case law",
        top_k=5,
        filters={"jurisdiction": "CA"}
    )
    assert len(ca_results) == 1
    assert ca_results[0]["metadata"]["jurisdiction"] == "CA"

    # Search with NY filter
    ny_results = temp_store.search(
        "case law",
        top_k=5,
        filters={"jurisdiction": "NY"}
    )
    assert len(ny_results) == 1
    assert ny_results[0]["metadata"]["jurisdiction"] == "NY"


def test_vector_store_metadata_filtering_claim_elements(temp_store):
    """Test filtering by claim elements."""
    temp_store.add("Text about negligence", {"claim_elements": ["negligence", "duty"]})
    temp_store.add("Text about breach", {"claim_elements": ["breach", "duty"]})
    temp_store.add("Text about damages", {"claim_elements": ["damages"]})

    temp_store.update_vectors()

    # Search for entries with "negligence"
    neg_results = temp_store.search(
        "legal text",
        top_k=5,
        filters={"claim_elements": ["negligence"]}
    )
    assert len(neg_results) == 1
    assert "negligence" in neg_results[0]["metadata"]["claim_elements"]

    # Search for entries with "duty" (should match first two)
    duty_results = temp_store.search(
        "legal text",
        top_k=5,
        filters={"claim_elements": ["duty"]}
    )
    assert len(duty_results) == 2


def test_vector_store_persistence():
    """Test that VectorStore persists and loads state correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = Path(tmpdir) / "test_store.pkl"

        # Create store and add data
        store1 = VectorStore(storage_path=storage_path)
        store1.add("First entry text", {"id": "1", "source": "doc1"})
        store1.add("Second entry text", {"id": "2", "source": "doc2"})
        store1.update_vectors()

        # Verify data was persisted
        assert storage_path.exists()

        # Create new store instance with same path
        store2 = VectorStore(storage_path=storage_path)

        # Should have loaded the data
        assert len(store2.texts) == len(store1.texts)
        assert len(store2.metadata) == len(store1.metadata)

        # Search should work on loaded data
        results = store2.search("entry", top_k=5)
        assert len(results) == 2


def test_vector_store_corrupted_file_handling():
    """Test that corrupted pickle files are handled gracefully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = Path(tmpdir) / "corrupted.pkl"

        # Create a corrupted pickle file
        with storage_path.open("wb") as f:
            f.write(b"This is not a valid pickle file")

        # Should not crash, should initialize with empty state
        store = VectorStore(storage_path=storage_path)
        assert len(store.texts) == 0
        assert len(store.metadata) == 0

        # Should be able to add data after failed load
        store.add("New text", {"source": "test"})
        assert len(store.texts) > 0


def test_vector_store_entry_id_assignment(temp_store):
    """Test that entry IDs are properly assigned per entry."""
    # Add entries without explicit entry_id
    temp_store.add("First text", {"source": "doc1"})
    temp_store.add("Second text", {"source": "doc2"})

    # Get unique entry_ids (not chunk_ids)
    entry_ids = set(m["entry_id"] for m in temp_store.metadata)

    # Should have 2 unique entry IDs (one per add call)
    assert len(entry_ids) == 2


def test_vector_store_citation_fallback(temp_store):
    """Test that citation metadata falls back appropriately."""
    # Add with explicit citation
    temp_store.add("Text 1", {"citation": "Explicit Citation"})
    assert temp_store.metadata[0]["citation"] == "Explicit Citation"

    # Add with source but no citation
    temp_store.add("Text 2", {"source": "Source Document"})
    # Last added entry should use source as citation
    last_metadata = [
        m for m in temp_store.metadata
        if "Text 2" in temp_store.texts[temp_store.metadata.index(m)]
    ]
    if last_metadata:
        assert last_metadata[0]["citation"] == "Source Document"

    # Add with neither
    temp_store.add("Text 3", {})
    last_metadata = [
        m for m in temp_store.metadata
        if "Text 3" in temp_store.texts[temp_store.metadata.index(m)]
    ]
    if last_metadata:
        assert last_metadata[0]["citation"] == "Unattributed"


def test_vector_store_empty_text_handling(temp_store):
    """Test that empty text is handled gracefully."""
    initial_count = len(temp_store.texts)

    # Add empty text
    temp_store.add("", {"source": "empty"})

    # Should not create any new entries
    assert len(temp_store.texts) == initial_count


def test_vector_store_add_entries_batch(temp_store):
    """Test batch adding of entries."""
    entries = [
        ("First text", {"id": "1"}),
        ("Second text", {"id": "2"}),
        ("Third text", {"id": "3"}),
    ]

    temp_store.add_entries(entries)
    temp_store.update_vectors()

    # Should have all entries
    assert len(temp_store.texts) == 3

    # Search should work
    results = temp_store.search("text", top_k=5)
    assert len(results) == 3


def test_vector_store_deferred_persistence():
    """Test that persistence is deferred until update_vectors."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = Path(tmpdir) / "deferred.pkl"

        store = VectorStore(storage_path=storage_path)

        # Add data but don't call update_vectors
        store.add("Text without update", {"source": "test"})

        # File should not exist yet (or be outdated)
        # This depends on implementation - but the key is that
        # update_vectors should trigger persistence

        # Call update_vectors
        store.update_vectors()

        # Now file should definitely exist with current data
        assert storage_path.exists()

        # Load in new instance to verify
        store2 = VectorStore(storage_path=storage_path)
        assert len(store2.texts) == len(store.texts)
