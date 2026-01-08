"""
Tests for the pipeline service API and core functions.
"""
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from pipeline_service import (
    app,
    build_agent_assignment,
    build_job_response,
    build_pipeline_tasks,
    build_timeline,
    task_status,
)


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


class TestBuildPipelineTasks:
    """Tests for the build_pipeline_tasks function."""

    def test_business_proposal_pipeline(self):
        """Test pipeline construction for business proposal document type."""
        sections = ["Executive Summary", "Problem Statement"]
        result = build_pipeline_tasks("business_proposal", sections)

        assert "tasks" in result
        assert "links" in result
        tasks = result["tasks"]
        links = result["links"]

        # Check for control nodes
        assert tasks[0]["id"] == "Start"
        assert tasks[-1]["id"] == "End"

        # Check for standard tasks
        task_ids = [t["id"] for t in tasks]
        assert "Shotlist Build" in task_ids
        assert "Research" in task_ids
        assert "Review & Export" in task_ids

        # Check sections are present
        assert "Executive Summary" in task_ids
        assert "Problem Statement" in task_ids

        # Verify links structure
        assert len(links) > 0
        # Each section should link to Review & Export
        section_to_review_links = [
            link for link in links
            if link["source"] in sections and link["target"] == "Review & Export"
        ]
        assert len(section_to_review_links) == len(sections)

    def test_legal_claim_pipeline(self):
        """Test pipeline construction for legal claim document type."""
        sections = ["Introduction", "Legal Arguments"]
        result = build_pipeline_tasks("legal_claim", sections)

        tasks = result["tasks"]
        task_ids = [t["id"] for t in tasks]

        # Legal claims should have OCR Intake
        assert "OCR Intake" in task_ids
        assert "Legal Research" in task_ids

    def test_sections_have_correct_stage(self):
        """Test that all section tasks are assigned to Draft Sections stage."""
        sections = ["Section A", "Section B", "Section C"]
        result = build_pipeline_tasks("business_proposal", sections)

        section_tasks = [
            t for t in result["tasks"]
            if t["id"] in sections
        ]

        for task in section_tasks:
            assert task["stage"] == "Draft Sections"
            assert task["type"] == "section"


class TestBuildTimeline:
    """Tests for the build_timeline function."""

    def test_simple_sequential_timeline(self):
        """Test timeline with sequential non-section tasks."""
        tasks = [
            {"id": "Start", "type": "control", "stage": None, "agent_id": None},
            {"id": "Task A", "type": "task", "stage": "Stage 1", "agent_id": "Agent1"},
            {"id": "Task B", "type": "task", "stage": "Stage 2", "agent_id": "Agent2"},
        ]
        timeline = build_timeline(tasks)

        # Control tasks should not be in timeline
        assert "Start" not in timeline

        # Sequential tasks should have increasing start times
        assert timeline["Task A"]["start"] == 0.0
        assert timeline["Task B"]["start"] > timeline["Task A"]["start"]

    def test_parallel_section_timeline(self):
        """Test that consecutive section tasks start at the same time."""
        tasks = [
            {
                "id": "Start",
                "type": "control",
                "stage": None,
                "agent_id": None
            },
            {
                "id": "Prep",
                "type": "task",
                "stage": "Stage 1",
                "agent_id": "Agent1"
            },
            {
                "id": "Section A",
                "type": "section",
                "stage": "Draft",
                "agent_id": "WriterA"
            },
            {
                "id": "Section B",
                "type": "section",
                "stage": "Draft",
                "agent_id": "WriterB"
            },
            {
                "id": "Section C",
                "type": "section",
                "stage": "Draft",
                "agent_id": "WriterC"
            },
            {
                "id": "Review",
                "type": "task",
                "stage": "Review",
                "agent_id": "Reviewer"
            },
        ]
        timeline = build_timeline(tasks)

        # All sections should start at the same time
        section_a_start = timeline["Section A"]["start"]
        assert timeline["Section B"]["start"] == section_a_start
        assert timeline["Section C"]["start"] == section_a_start

        # Review should start after all sections complete
        max_section_duration = max(
            timeline["Section A"]["duration"],
            timeline["Section B"]["duration"],
            timeline["Section C"]["duration"],
        )
        expected_review_start = section_a_start + max_section_duration
        assert timeline["Review"]["start"] == expected_review_start

    def test_duration_estimation(self):
        """Test that different task types get appropriate durations."""
        tasks = [
            {
                "id": "Legal Research",
                "type": "task",
                "stage": "Research",
                "agent_id": "LegalResearchAgent"
            },
            {
                "id": "Introduction",
                "type": "section",
                "stage": "Draft",
                "agent_id": "Writer"
            },
            {
                "id": "Detailed Analysis",
                "type": "section",
                "stage": "Draft",
                "agent_id": "Writer"
            },
        ]
        timeline = build_timeline(tasks)

        # Known task should use explicit duration
        assert timeline["Legal Research"]["duration"] == 4.0

        # Sections should have heuristic-based durations
        assert "Introduction" in timeline
        assert "Detailed Analysis" in timeline


class TestTaskStatus:
    """Tests for the task_status function."""

    def test_pending_status(self):
        """Test that task is pending before its start time."""
        timeline = {"Task A": {"start": 10.0, "duration": 5.0}}
        status = task_status(5.0, timeline, "Task A")
        assert status == "pending"

    def test_active_status(self):
        """Test that task is active during its execution window."""
        timeline = {"Task A": {"start": 10.0, "duration": 5.0}}
        status = task_status(12.0, timeline, "Task A")
        assert status == "active"

    def test_complete_status(self):
        """Test that task is complete after its end time."""
        timeline = {"Task A": {"start": 10.0, "duration": 5.0}}
        status = task_status(20.0, timeline, "Task A")
        assert status == "complete"

    def test_missing_task(self):
        """Test that missing task returns pending status."""
        timeline = {"Task A": {"start": 10.0, "duration": 5.0}}
        status = task_status(10.0, timeline, "Task B")
        assert status == "pending"


class TestBuildAgentAssignment:
    """Tests for the build_agent_assignment function."""

    def test_legal_section_assignment(self):
        """Test agent assignment for legal-related sections."""
        agent = build_agent_assignment("Legal Arguments")
        assert agent == "LegalDrafterAgent"

        agent = build_agent_assignment("Jurisdiction")
        assert agent == "LegalDrafterAgent"

    def test_financial_section_assignment(self):
        """Test agent assignment for financial sections."""
        agent = build_agent_assignment("Financial Projections")
        assert agent == "FinancialModelerAgent"

        agent = build_agent_assignment("Financial Analysis")
        assert agent == "FinancialModelerAgent"

    def test_market_section_assignment(self):
        """Test agent assignment for market-related sections."""
        agent = build_agent_assignment("Market Analysis")
        assert agent == "MarketAnalystAgent"

        agent = build_agent_assignment("Market Overview")
        assert agent == "MarketAnalystAgent"

    def test_default_assignment(self):
        """Test default agent assignment for general sections."""
        agent = build_agent_assignment("General Content")
        assert agent == "GeneralWriterAgent"


class TestAPIEndpoints:
    """Tests for the FastAPI endpoints."""

    def test_create_job_business_proposal(self, client):
        """Test creating a business proposal job."""
        payload = {
            "prompt": "Create a proposal for AI consulting services",
            "doc_type": "business_proposal"
        }
        response = client.post("/jobs", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["doc_type"] == "business_proposal"
        assert data["prompt"] == payload["prompt"]
        assert "template" in data
        assert "stages" in data
        assert "tasks" in data
        assert "links" in data

    def test_create_job_legal_claim(self, client):
        """Test creating a legal claim job."""
        payload = {
            "prompt": "Draft a complaint for breach of contract",
            "doc_type": "legal_claim"
        }
        response = client.post("/jobs", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["doc_type"] == "legal_claim"

    def test_create_job_white_paper(self, client):
        """Test creating a white paper job."""
        payload = {
            "prompt": "Write about blockchain technology",
            "doc_type": "white_paper"
        }
        response = client.post("/jobs", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["doc_type"] == "white_paper"

    def test_create_job_invalid_doc_type(self, client):
        """Test that invalid document type returns 422 (validation error)."""
        payload = {
            "prompt": "Test prompt",
            "doc_type": "invalid_type"
        }
        response = client.post("/jobs", json=payload)

        # Pydantic validation should reject this before it reaches the endpoint
        assert response.status_code == 422

    def test_get_job(self, client):
        """Test fetching an existing job."""
        # Create a job first
        create_payload = {
            "prompt": "Test job",
            "doc_type": "business_proposal"
        }
        create_response = client.post("/jobs", json=create_payload)
        job_id = create_response.json()["id"]

        # Fetch the job
        response = client.get(f"/jobs/{job_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == job_id
        assert data["prompt"] == create_payload["prompt"]

    def test_get_nonexistent_job(self, client):
        """Test fetching a job that doesn't exist."""
        response = client.get("/jobs/nonexistent_id")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_sections(self, client):
        """Test fetching sections for an existing job."""
        # Create a job first
        create_payload = {
            "prompt": "Test job",
            "doc_type": "legal_claim"
        }
        create_response = client.post("/jobs", json=create_payload)
        job_id = create_response.json()["id"]

        # Fetch sections
        response = client.get(f"/jobs/{job_id}/sections")
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["job_id"] == job_id
        assert "sections" in data
        assert isinstance(data["sections"], list)

    def test_get_sections_nonexistent_job(self, client):
        """Test fetching sections for a nonexistent job."""
        response = client.get("/jobs/nonexistent_id/sections")
        assert response.status_code == 404

    def test_job_status_progression(self, client):
        """Test that job status changes over time (simulated)."""
        # Create a job
        create_payload = {
            "prompt": "Test progression",
            "doc_type": "business_proposal"
        }
        create_response = client.post("/jobs", json=create_payload)
        job_id = create_response.json()["id"]

        # Immediately after creation, status should be "running"
        response = client.get(f"/jobs/{job_id}")
        data = response.json()

        # At least some tasks should be pending or active
        task_statuses = [task["status"] for task in data["tasks"]]
        assert "pending" in task_statuses or "active" in task_statuses


class TestJobResponse:
    """Tests for the build_job_response function."""

    def test_stage_status_all_complete(self):
        """Test stage status when all tasks are complete."""
        from pipeline_service import DOC_TEMPLATES, JobRecord

        template = DOC_TEMPLATES["business_proposal"]
        pipeline = build_pipeline_tasks("business_proposal", template["sections"])

        # Create a job that started in the past so all tasks are complete
        job = JobRecord(
            job_id="test_123",
            prompt="Test",
            doc_type="business_proposal",
            created_at=datetime(2020, 1, 1, tzinfo=timezone.utc),
            template=template,
            stages=template["stages"],
            checklist=template["checklist"],
            tasks=pipeline["tasks"],
            links=pipeline["links"],
            timeline=build_timeline(pipeline["tasks"]),
        )

        response = build_job_response(job)

        # All stages should be complete
        assert all(stage.status == "complete" for stage in response.stages)
        assert response.status == "complete"

    def test_stage_status_with_active_tasks(self):
        """Test stage status when some tasks are active."""
        from pipeline_service import DOC_TEMPLATES, JobRecord

        template = DOC_TEMPLATES["business_proposal"]
        pipeline = build_pipeline_tasks("business_proposal", template["sections"])

        # Create a job that just started
        job = JobRecord(
            job_id="test_456",
            prompt="Test",
            doc_type="business_proposal",
            created_at=datetime.now(timezone.utc),
            template=template,
            stages=template["stages"],
            checklist=template["checklist"],
            tasks=pipeline["tasks"],
            links=pipeline["links"],
            timeline=build_timeline(pipeline["tasks"]),
        )

        response = build_job_response(job)

        # Job should be running (not complete)
        assert response.status == "running"

        # At least one stage should be pending or active
        stage_statuses = [stage.status for stage in response.stages]
        assert "pending" in stage_statuses or "active" in stage_statuses
