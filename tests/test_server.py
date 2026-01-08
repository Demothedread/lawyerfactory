import sys
import tempfile
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from maestro.job_store import JobStore  # noqa: E402
from server import app  # noqa: E402


def setup_test_job_store():
    """Create a temporary JobStore for testing."""
    tmp_file = tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False)
    tmp_path = tmp_file.name
    tmp_file.close()
    return JobStore(job_store_path=tmp_path)


def test_health_endpoint():
    """Test the health check endpoint."""
    client = TestClient(app)
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_intake_endpoint_success():
    """Test successful job intake."""
    # Setup test job store
    test_job_store = setup_test_job_store()

    # Temporarily replace global job_store
    import server
    original_store = server.job_store
    server.job_store = test_job_store
    server.maestro.job_store = test_job_store

    try:
        client = TestClient(app)
        payload = {
            "documents": [
                {"name": "doc1.txt", "content": "Content of document 1"},
                {"name": "doc2.txt", "content": "Content of document 2"}
            ],
            "client_reference": "CLIENT-123",
            "topic": "contract dispute"
        }

        response = client.post("/api/jobs/intake", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert "job_id" in data
        assert data["status"] == "pending"
        assert data["current_stage"] is None
        assert len(data["stages"]) == 5
    finally:
        # Restore original job_store
        server.job_store = original_store
        server.maestro.job_store = original_store


def test_intake_endpoint_empty_documents():
    """Test intake endpoint rejects empty documents list."""
    client = TestClient(app)
    payload = {
        "documents": [],
        "topic": "contract dispute"
    }

    response = client.post("/api/jobs/intake", json=payload)
    assert response.status_code == 422  # Validation error


def test_intake_endpoint_empty_document_fields():
    """Test intake endpoint rejects empty document name or content."""
    client = TestClient(app)

    # Empty name
    payload = {
        "documents": [{"name": "", "content": "Content"}],
        "topic": "contract dispute"
    }
    response = client.post("/api/jobs/intake", json=payload)
    assert response.status_code == 422

    # Empty content
    payload = {
        "documents": [{"name": "doc.txt", "content": ""}],
        "topic": "contract dispute"
    }
    response = client.post("/api/jobs/intake", json=payload)
    assert response.status_code == 422


def test_job_status_endpoint():
    """Test retrieving job status."""
    test_job_store = setup_test_job_store()

    # Create a job
    documents = [{"name": "doc1.txt", "content": "content1"}]
    metadata = {"client_reference": "client123", "topic": "contract"}
    job_id = test_job_store.job_store_create_job(documents=documents, metadata=metadata)

    # Setup app with test job store
    import server
    original_store = server.job_store
    server.job_store = test_job_store

    try:
        client = TestClient(app)
        response = client.get(f"/api/jobs/{job_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["job_id"] == job_id
        assert data["status"] == "pending"
        assert len(data["stages"]) == 5
    finally:
        server.job_store = original_store


def test_job_status_endpoint_not_found():
    """Test retrieving status for non-existent job."""
    client = TestClient(app)
    response = client.get("/api/jobs/nonexistent-job-id")
    assert response.status_code == 404
    assert "Job not found" in response.json()["detail"]


def test_research_endpoint_requires_shotlist_completion():
    """Test research endpoint validates shotlist completion."""
    test_job_store = setup_test_job_store()

    # Create a job
    documents = [{"name": "doc1.txt", "content": "content1"}]
    metadata = {}
    job_id = test_job_store.job_store_create_job(
        documents=documents,
        metadata=metadata
    )

    # Setup app with test job store
    import server
    original_store = server.job_store
    server.job_store = test_job_store

    try:
        client = TestClient(app)

        # Try to start research without completing shotlist
        response = client.post(
            f"/api/jobs/{job_id}/research",
            json={"topic": "legal research"}
        )
        assert response.status_code == 400
        detail = response.json()["detail"]
        assert "shotlist stage must be completed first" in detail

        # Complete shotlist stage
        test_job_store.job_store_update_stage(
            job_id, "shotlist", "completed", {"summary": "test"}
        )

        # Now research should be allowed
        response = client.post(
            f"/api/jobs/{job_id}/research",
            json={"topic": "legal research"}
        )
        assert response.status_code == 200
    finally:
        server.job_store = original_store


def test_draft_endpoint_requires_research_completion():
    """Test draft endpoint validates research completion."""
    test_job_store = setup_test_job_store()

    # Create a job
    documents = [{"name": "doc1.txt", "content": "content1"}]
    metadata = {}
    job_id = test_job_store.job_store_create_job(documents=documents, metadata=metadata)

    # Setup app with test job store
    import server
    original_store = server.job_store
    server.job_store = test_job_store

    try:
        client = TestClient(app)

        # Try to start drafting without completing research
        response = client.post(
            f"/api/jobs/{job_id}/draft",
            json={"topic": "drafting"}
        )
        assert response.status_code == 400
        detail = response.json()["detail"]
        assert "research stage must be completed first" in detail

        # Complete research stage
        test_job_store.job_store_update_stage(
            job_id, "research", "completed", {"research": "test"}
        )

        # Now drafting should be allowed
        response = client.post(f"/api/jobs/{job_id}/draft", json={})
        assert response.status_code == 200
    finally:
        server.job_store = original_store


def test_research_endpoint_not_found():
    """Test research endpoint with non-existent job."""
    client = TestClient(app)
    response = client.post(
        "/api/jobs/nonexistent-job-id/research",
        json={"topic": "legal"}
    )
    assert response.status_code == 404
    assert "Job not found" in response.json()["detail"]


def test_draft_endpoint_not_found():
    """Test draft endpoint with non-existent job."""
    client = TestClient(app)
    response = client.post("/api/jobs/nonexistent-job-id/draft", json={})
    assert response.status_code == 404
    assert "Job not found" in response.json()["detail"]


def test_sections_endpoint():
    """Test retrieving job sections."""
    test_job_store = setup_test_job_store()

    # Create a job and add sections
    documents = [{"name": "doc1.txt", "content": "content1"}]
    metadata = {}
    job_id = test_job_store.job_store_create_job(
        documents=documents,
        metadata=metadata
    )

    test_job_store.job_store_add_section(
        job_id, "intro", "Introduction", "Intro content"
    )
    test_job_store.job_store_add_section(
        job_id, "analysis", "Analysis", "Analysis content"
    )

    # Setup app with test job store
    import server
    original_store = server.job_store
    server.job_store = test_job_store

    try:
        client = TestClient(app)
        response = client.get(f"/api/jobs/{job_id}/sections")
        assert response.status_code == 200

        data = response.json()
        assert data["job_id"] == job_id
        assert len(data["sections"]) == 2
        assert data["sections"][0]["section_key"] == "intro"
        assert data["sections"][0]["title"] == "Introduction"
        assert data["sections"][1]["section_key"] == "analysis"
    finally:
        server.job_store = original_store


def test_sections_endpoint_not_found():
    """Test sections endpoint with non-existent job."""
    client = TestClient(app)
    response = client.get("/api/jobs/nonexistent-job-id/sections")
    assert response.status_code == 404
    assert "Job not found" in response.json()["detail"]


def test_export_endpoint_success():
    """Test export endpoint when review is completed."""
    test_job_store = setup_test_job_store()

    # Create a job and complete review stage
    documents = [{"name": "doc1.txt", "content": "content1"}]
    metadata = {}
    job_id = test_job_store.job_store_create_job(
        documents=documents,
        metadata=metadata
    )

    # Complete review stage
    review_output = {"review": "Review notes", "export_ready": True}
    test_job_store.job_store_update_stage(
        job_id, "review", "completed", review_output
    )

    # Add sections
    test_job_store.job_store_add_section(
        job_id, "intro", "Introduction", "Intro content"
    )

    # Setup app with test job store
    import server
    original_store = server.job_store
    server.job_store = test_job_store

    try:
        client = TestClient(app)
        response = client.get(f"/api/jobs/{job_id}/export")
        assert response.status_code == 200

        data = response.json()
        assert data["job_id"] == job_id
        assert data["export_ready"] is True
        assert data["review"] == "Review notes"
        assert len(data["sections"]) == 1
    finally:
        server.job_store = original_store


def test_export_endpoint_review_not_ready():
    """Test export endpoint when review is not completed."""
    test_job_store = setup_test_job_store()

    # Create a job without completing review
    documents = [{"name": "doc1.txt", "content": "content1"}]
    metadata = {}
    job_id = test_job_store.job_store_create_job(documents=documents, metadata=metadata)

    # Setup app with test job store
    import server
    original_store = server.job_store
    server.job_store = test_job_store

    try:
        client = TestClient(app)
        response = client.get(f"/api/jobs/{job_id}/export")
        assert response.status_code == 409
        assert "Review output is not yet available" in response.json()["detail"]
    finally:
        server.job_store = original_store


def test_export_endpoint_not_found():
    """Test export endpoint with non-existent job."""
    client = TestClient(app)
    response = client.get("/api/jobs/nonexistent-job-id/export")
    assert response.status_code == 404
    assert "Job not found" in response.json()["detail"]
