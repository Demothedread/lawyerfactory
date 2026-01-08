from typing import Any

from fastapi import BackgroundTasks, FastAPI, HTTPException  # 3P
from pydantic import BaseModel, Field  # 3P

from maestro.job_store import JobStore
from maestro.maestro import Maestro

app = FastAPI(title="LawyerFactory Maestro API")
job_store = JobStore()
maestro = Maestro(job_store=job_store)


class DocumentPayload(BaseModel):
    name: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)


class IntakeRequest(BaseModel):
    documents: list[DocumentPayload] = Field(..., min_length=1)
    client_reference: str | None = None
    topic: str | None = None


class ResearchKickoffRequest(BaseModel):
    topic: str = Field(default="legal research", min_length=1)


class DraftAssemblyRequest(BaseModel):
    topic: str | None = None


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    current_stage: str | None
    stages: list[dict[str, Any]]
    created_at: str
    updated_at: str


def _job_response(job_id: str) -> JobStatusResponse:
    job_state = job_store.job_store_get_job(job_id)
    if not job_state:
        raise HTTPException(status_code=404, detail="Job not found.")
    return JobStatusResponse(
        job_id=job_state["job_id"],
        status=job_state["status"],
        current_stage=job_state["current_stage"],
        stages=job_state["stages"],
        created_at=job_state["created_at"],
        updated_at=job_state["updated_at"],
    )


async def _pipeline_run(
    job_id: str,
    stage_start: str,
    stage_end: str,
    topic: str | None,
) -> None:
    await maestro.run_pipeline(
        job_id=job_id,
        stage_start=stage_start,
        stage_end=stage_end,
        topic=topic,
    )


@app.post("/api/jobs/intake", response_model=JobStatusResponse)
async def job_intake(
    request: IntakeRequest,
    background_tasks: BackgroundTasks,
) -> JobStatusResponse:
    metadata = {"client_reference": request.client_reference, "topic": request.topic}
    documents = [document.model_dump() for document in request.documents]
    job_id = job_store.job_store_create_job(
        documents=documents,
        metadata=metadata,
    )
    background_tasks.add_task(
        _pipeline_run,
        job_id,
        "ocr",
        "shotlist",
        request.topic,
    )
    return _job_response(job_id)


@app.post("/api/jobs/{job_id}/research", response_model=JobStatusResponse)
async def job_research_kickoff(
    job_id: str, request: ResearchKickoffRequest, background_tasks: BackgroundTasks
) -> JobStatusResponse:
    job_state = job_store.job_store_get_job(job_id)
    if not job_state:
        raise HTTPException(status_code=404, detail="Job not found.")
    # Validate that shotlist stage has completed
    shotlist_stage = next(
        (s for s in job_state["stages"] if s["stage"] == "shotlist"), None
    )
    if not shotlist_stage or shotlist_stage["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail="Cannot start research: shotlist stage must be completed first.",
        )
    background_tasks.add_task(
        _pipeline_run,
        job_id,
        "research",
        "research",
        request.topic,
    )
    return _job_response(job_id)


@app.post("/api/jobs/{job_id}/draft", response_model=JobStatusResponse)
async def job_draft_assembly(
    job_id: str, request: DraftAssemblyRequest, background_tasks: BackgroundTasks
) -> JobStatusResponse:
    job_state = job_store.job_store_get_job(job_id)
    if not job_state:
        raise HTTPException(status_code=404, detail="Job not found.")
    # Validate that research stage has completed
    research_stage = next(
        (s for s in job_state["stages"] if s["stage"] == "research"), None
    )
    if not research_stage or research_stage["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail="Cannot start drafting: research stage must be completed first.",
        )
    background_tasks.add_task(
        _pipeline_run,
        job_id,
        "drafting",
        "review",
        request.topic,
    )
    return _job_response(job_id)


@app.get("/api/jobs/{job_id}", response_model=JobStatusResponse)
async def job_status(job_id: str) -> JobStatusResponse:
    return _job_response(job_id)


@app.get("/api/jobs/{job_id}/sections")
async def job_sections(job_id: str) -> dict[str, Any]:
    job_state = job_store.job_store_get_job(job_id)
    if not job_state:
        raise HTTPException(status_code=404, detail="Job not found.")
    sections = job_store.job_store_list_sections(job_id)
    return {"job_id": job_id, "sections": sections}


@app.get("/api/jobs/{job_id}/export")
async def job_export(job_id: str) -> dict[str, Any]:
    job_state = job_store.job_store_get_job(job_id)
    if not job_state:
        raise HTTPException(status_code=404, detail="Job not found.")
    review_output = job_store.job_store_stage_output(job_id, "review")
    sections = job_store.job_store_list_sections(job_id)
    if not review_output:
        raise HTTPException(
            status_code=409,
            detail=(
                "Review output is not yet available for export. "
                "Check the job status at /api/jobs/{job_id} to confirm that the "
                "review stage has completed successfully, then try again."
            ),
        )
    return {
        "job_id": job_id,
        "export_ready": review_output.get("export_ready", False),
        "review": review_output.get("review"),
        "sections": sections,
    }


@app.get("/api/health")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
