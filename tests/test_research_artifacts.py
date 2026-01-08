"""Tests for ResearchArtifact and related dataclasses."""

from lawyerfactory.research_artifacts import (
    ResearchArtifact,
    ResearchSource,
    ResearchFilters
)


def test_research_filters_creation():
    """Test ResearchFilters can be created with defaults."""
    filters = ResearchFilters()
    assert filters.jurisdiction is None
    assert filters.claim_elements == ()


def test_research_filters_with_values():
    """Test ResearchFilters with jurisdiction and claim elements."""
    filters = ResearchFilters(
        jurisdiction="CA",
        claim_elements=("negligence", "duty", "breach")
    )
    assert filters.jurisdiction == "CA"
    assert filters.claim_elements == ("negligence", "duty", "breach")


def test_research_filters_immutability():
    """Test that ResearchFilters is frozen (immutable)."""
    filters = ResearchFilters(jurisdiction="CA")

    # Should not be able to modify fields
    try:
        filters.jurisdiction = "NY"
        assert False, "Should not be able to modify frozen dataclass"
    except AttributeError:
        pass  # Expected


def test_research_filters_to_dict():
    """Test ResearchFilters.to_dict() conversion."""
    filters = ResearchFilters(
        jurisdiction="NY",
        claim_elements=("damages", "causation")
    )

    result = filters.to_dict()
    assert result == {
        "jurisdiction": "NY",
        "claim_elements": ["damages", "causation"]
    }


def test_research_source_creation():
    """Test ResearchSource creation."""
    source = ResearchSource(
        source_id="case-123",
        title="Smith v. Jones",
        citation="123 F.3d 456 (9th Cir. 2020)",
        content="The court held that...",
        url="https://example.com/case/123"
    )

    assert source.source_id == "case-123"
    assert source.title == "Smith v. Jones"
    assert source.citation == "123 F.3d 456 (9th Cir. 2020)"
    assert source.content == "The court held that..."
    assert source.url == "https://example.com/case/123"


def test_research_source_to_dict():
    """Test ResearchSource.to_dict() conversion."""
    source = ResearchSource(
        source_id="doc-1",
        title="Legal Document",
        citation="Doc. 1",
        content="Content here",
        url=None
    )

    result = source.to_dict()
    assert result == {
        "source_id": "doc-1",
        "title": "Legal Document",
        "citation": "Doc. 1",
        "content": "Content here",
        "url": None
    }


def test_research_artifact_creation():
    """Test ResearchArtifact creation with sources."""
    filters = ResearchFilters(jurisdiction="CA")
    sources = [
        ResearchSource(
            source_id="case-1",
            title="Case One",
            citation="Citation 1",
            content="Case one content"
        )
    ]

    artifact = ResearchArtifact(
        query="negligence cases",
        summary="Summary of negligence cases",
        filters=filters,
        sources=sources
    )

    assert artifact.query == "negligence cases"
    assert artifact.summary == "Summary of negligence cases"
    assert artifact.filters == filters
    assert len(artifact.sources) == 1
    assert artifact.created_at  # Should have timestamp


def test_research_artifact_to_dict():
    """Test ResearchArtifact.to_dict() conversion."""
    filters = ResearchFilters(jurisdiction="Federal")
    sources = [
        ResearchSource(
            source_id="s1",
            title="Source 1",
            citation="Cite 1",
            content="Content 1"
        )
    ]

    artifact = ResearchArtifact(
        query="test query",
        summary="test summary",
        filters=filters,
        sources=sources
    )

    result = artifact.to_dict()
    assert result["query"] == "test query"
    assert result["summary"] == "test summary"
    assert result["filters"]["jurisdiction"] == "Federal"
    assert len(result["sources"]) == 1
    assert result["sources"][0]["source_id"] == "s1"
    assert "created_at" in result


def test_research_artifact_vector_entries_with_sources():
    """Test vector_entries() generates correct entries from sources."""
    filters = ResearchFilters(
        jurisdiction="NY",
        claim_elements=("negligence", "duty")
    )

    sources = [
        ResearchSource(
            source_id="case-1",
            title="First Case",
            citation="1 F.3d 1",
            content="First case content with important details.",
            url="http://example.com/1"
        ),
        ResearchSource(
            source_id="case-2",
            title="Second Case",
            citation="2 F.3d 2",
            content="Second case content with more details.",
            url="http://example.com/2"
        )
    ]

    artifact = ResearchArtifact(
        query="duty and negligence",
        summary="Summary of duty cases",
        filters=filters,
        sources=sources
    )

    entries = artifact.vector_entries()

    # Should have one entry per source
    assert len(entries) == 2

    # Check first entry
    text1, metadata1 = entries[0]
    assert text1 == "First case content with important details."
    assert metadata1["query"] == "duty and negligence"
    assert metadata1["citation"] == "1 F.3d 1"
    assert metadata1["source"] == "First Case"
    assert metadata1["source_id"] == "case-1"
    assert metadata1["url"] == "http://example.com/1"
    assert metadata1["jurisdiction"] == "NY"
    assert metadata1["claim_elements"] == ["negligence", "duty"]

    # Check second entry
    text2, metadata2 = entries[1]
    assert text2 == "Second case content with more details."
    assert metadata2["citation"] == "2 F.3d 2"
    assert metadata2["source_id"] == "case-2"


def test_research_artifact_vector_entries_without_sources():
    """Test vector_entries() falls back to summary when no sources."""
    filters = ResearchFilters(jurisdiction="CA")

    artifact = ResearchArtifact(
        query="contract law",
        summary="This is a summary of contract law principles.",
        filters=filters,
        sources=[]  # No sources
    )

    entries = artifact.vector_entries()

    # Should have one entry with the summary
    assert len(entries) == 1

    text, metadata = entries[0]
    assert text == "This is a summary of contract law principles."
    assert metadata["query"] == "contract law"
    assert metadata["citation"] == "Research summary"
    assert metadata["jurisdiction"] == "CA"
    assert "source" not in metadata
    assert "source_id" not in metadata


def test_research_artifact_vector_entries_empty_sources():
    """Test vector_entries() handles empty sources list."""
    artifact = ResearchArtifact(
        query="test",
        summary="test summary",
        filters=ResearchFilters(),
        sources=[]
    )

    entries = artifact.vector_entries()
    assert len(entries) == 1
    assert entries[0][0] == "test summary"


def test_research_filters_claim_elements_are_tuple():
    """Test that claim_elements is truly immutable (tuple, not list)."""
    filters = ResearchFilters(claim_elements=("elem1", "elem2"))

    # Should be a tuple
    assert isinstance(filters.claim_elements, tuple)

    # Tuples are immutable
    try:
        filters.claim_elements[0] = "new_value"
        assert False, "Tuples should be immutable"
    except TypeError:
        pass  # Expected
