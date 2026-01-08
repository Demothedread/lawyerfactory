import sys
import tempfile
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from maestro.job_store import JobStore  # noqa: E402


def test_job_store_create_and_get_job():
    """Test creating a job and retrieving it."""
    with tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False) as tmp_file:
        db_path = tmp_file.name

    job_store = JobStore(job_store_path=db_path)
    documents = [{"name": "doc1.txt", "content": "content1"}]
    metadata = {"client_reference": "client123", "topic": "contract"}

    job_id = job_store.job_store_create_job(documents=documents, metadata=metadata)

    assert job_id is not None
    assert len(job_id) > 0

    job_state = job_store.job_store_get_job(job_id)
    assert job_state is not None
    assert job_state["job_id"] == job_id
    assert job_state["status"] == "pending"
    assert job_state["current_stage"] is None
    assert job_state["metadata"]["client_reference"] == "client123"
    assert job_state["metadata"]["topic"] == "contract"
    assert len(job_state["stages"]) == 5  # ocr, shotlist, research, drafting, review

    # Verify all stages are initialized as pending
    for stage in job_state["stages"]:
        assert stage["status"] == "pending"
        assert stage["output"] is None


def test_job_store_update_stage():
    """Test updating stage status and output."""
    with tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False) as tmp_file:
        db_path = tmp_file.name

    job_store = JobStore(job_store_path=db_path)
    documents = [{"name": "doc1.txt", "content": "content1"}]
    metadata = {}

    job_id = job_store.job_store_create_job(documents=documents, metadata=metadata)

    # Update stage to in_progress
    job_store.job_store_update_stage(job_id, "ocr", "in_progress", None)
    job_state = job_store.job_store_get_job(job_id)
    ocr_stage = next(s for s in job_state["stages"] if s["stage"] == "ocr")
    assert ocr_stage["status"] == "in_progress"
    assert ocr_stage["started_at"] is not None
    assert ocr_stage["completed_at"] is None

    # Update stage to completed with output
    output = {"text": "extracted text", "documents": 1}
    job_store.job_store_update_stage(job_id, "ocr", "completed", output)
    job_state = job_store.job_store_get_job(job_id)
    ocr_stage = next(s for s in job_state["stages"] if s["stage"] == "ocr")
    assert ocr_stage["status"] == "completed"
    assert ocr_stage["output"] == output
    assert ocr_stage["completed_at"] is not None


def test_job_store_update_stage_failed():
    """Test updating stage to failed status with error output."""
    with tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False) as tmp_file:
        db_path = tmp_file.name

    job_store = JobStore(job_store_path=db_path)
    documents = [{"name": "doc1.txt", "content": "content1"}]
    metadata = {}

    job_id = job_store.job_store_create_job(documents=documents, metadata=metadata)

    # Update stage to failed with error output
    error_output = {"error": "Connection timeout", "error_type": "TimeoutError"}
    job_store.job_store_update_stage(job_id, "ocr", "failed", error_output)
    job_state = job_store.job_store_get_job(job_id)
    ocr_stage = next(s for s in job_state["stages"] if s["stage"] == "ocr")
    assert ocr_stage["status"] == "failed"
    assert ocr_stage["output"]["error"] == "Connection timeout"
    assert ocr_stage["output"]["error_type"] == "TimeoutError"


def test_job_store_stage_output():
    """Test retrieving stage output directly."""
    with tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False) as tmp_file:
        db_path = tmp_file.name

    job_store = JobStore(job_store_path=db_path)
    documents = [{"name": "doc1.txt", "content": "content1"}]
    metadata = {}

    job_id = job_store.job_store_create_job(documents=documents, metadata=metadata)

    # Initially no output
    output = job_store.job_store_stage_output(job_id, "ocr")
    assert output is None

    # Add output
    expected_output = {"text": "extracted text", "documents": 1}
    job_store.job_store_update_stage(job_id, "ocr", "completed", expected_output)

    # Retrieve output
    output = job_store.job_store_stage_output(job_id, "ocr")
    assert output == expected_output


def test_job_store_add_and_list_sections():
    """Test adding sections to a job and listing them."""
    with tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False) as tmp_file:
        db_path = tmp_file.name

    job_store = JobStore(job_store_path=db_path)
    documents = [{"name": "doc1.txt", "content": "content1"}]
    metadata = {}

    job_id = job_store.job_store_create_job(documents=documents, metadata=metadata)

    # Add sections
    job_store.job_store_add_section(
        job_id, "intro", "Introduction", "This is the intro."
    )
    job_store.job_store_add_section(
        job_id, "analysis", "Analysis", "This is the analysis."
    )
    job_store.job_store_add_section(
        job_id, "conclusion", "Conclusion", "This is the conclusion."
    )

    # List sections
    sections = job_store.job_store_list_sections(job_id)
    assert len(sections) == 3
    assert sections[0]["section_key"] == "intro"
    assert sections[0]["title"] == "Introduction"
    assert sections[0]["content"] == "This is the intro."
    assert sections[1]["section_key"] == "analysis"
    assert sections[2]["section_key"] == "conclusion"


def test_job_store_section_upsert():
    """Test that adding a section with the same key updates the existing one."""
    with tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False) as tmp_file:
        db_path = tmp_file.name

    job_store = JobStore(job_store_path=db_path)
    documents = [{"name": "doc1.txt", "content": "content1"}]
    metadata = {}

    job_id = job_store.job_store_create_job(documents=documents, metadata=metadata)

    # Add section
    job_store.job_store_add_section(
        job_id, "intro", "Introduction", "First version."
    )
    sections = job_store.job_store_list_sections(job_id)
    assert len(sections) == 1
    assert sections[0]["content"] == "First version."

    # Update section with same key
    job_store.job_store_add_section(
        job_id, "intro", "Introduction Updated", "Second version."
    )
    sections = job_store.job_store_list_sections(job_id)
    assert len(sections) == 1  # Still only 1 section
    assert sections[0]["title"] == "Introduction Updated"
    assert sections[0]["content"] == "Second version."


def test_job_store_update_job_status():
    """Test updating job status and current stage."""
    with tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False) as tmp_file:
        db_path = tmp_file.name

    job_store = JobStore(job_store_path=db_path)
    documents = [{"name": "doc1.txt", "content": "content1"}]
    metadata = {}

    job_id = job_store.job_store_create_job(documents=documents, metadata=metadata)

    # Update job status
    job_store.job_store_update_job(job_id, "in_progress", "ocr")
    job_state = job_store.job_store_get_job(job_id)
    assert job_state["status"] == "in_progress"
    assert job_state["current_stage"] == "ocr"

    # Update again
    job_store.job_store_update_job(job_id, "completed", "review")
    job_state = job_store.job_store_get_job(job_id)
    assert job_state["status"] == "completed"
    assert job_state["current_stage"] == "review"


def test_job_store_nonexistent_job():
    """Test retrieving a non-existent job returns None."""
    with tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False) as tmp_file:
        db_path = tmp_file.name

    job_store = JobStore(job_store_path=db_path)

    job_state = job_store.job_store_get_job("nonexistent-job-id")
    assert job_state is None


def test_job_store_foreign_key_cascade():
    """Test that deleting a job cascades to stages and sections."""
    with tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False) as tmp_file:
        db_path = tmp_file.name

    job_store = JobStore(job_store_path=db_path)
    documents = [{"name": "doc1.txt", "content": "content1"}]
    metadata = {}

    job_id = job_store.job_store_create_job(documents=documents, metadata=metadata)

    # Add stage output and sections
    job_store.job_store_update_stage(
        job_id, "ocr", "completed", {"text": "extracted"}
    )
    job_store.job_store_add_section(job_id, "intro", "Introduction", "Content")

    # Verify they exist
    job_state = job_store.job_store_get_job(job_id)
    assert job_state is not None
    sections = job_store.job_store_list_sections(job_id)
    assert len(sections) == 1

    # Delete the job
    with job_store._job_store_connect() as connection:
        connection.execute("DELETE FROM jobs WHERE job_id = ?", (job_id,))

    # Verify job, stages, and sections are deleted
    job_state = job_store.job_store_get_job(job_id)
    assert job_state is None
    sections = job_store.job_store_list_sections(job_id)
    assert len(sections) == 0
