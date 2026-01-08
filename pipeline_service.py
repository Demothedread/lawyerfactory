from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JobCreateRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    doc_type: Literal["business_proposal", "legal_claim", "white_paper"] = Field(
        ..., description="Document type to generate"
    )
    knobs: Optional[Dict[str, str]] = None


class JobLink(BaseModel):
    source: str
    target: str


class JobTask(BaseModel):
    id: str
    type: str
    stage: Optional[str]
    agent_id: Optional[str]
    status: str
    output: Optional[str]


class JobStage(BaseModel):
    id: str
    description: str
    status: str


class JobChecklistItem(BaseModel):
    id: str
    label: str
    source: str
    stage: str
    status: str
    note: Optional[str]


class JobTemplate(BaseModel):
    name: str
    sections: List[str]
    knobs: Dict[str, List[str]]


class JobResponse(BaseModel):
    id: str
    prompt: str
    doc_type: str
    status: str
    template: JobTemplate
    stages: List[JobStage]
    checklist: List[JobChecklistItem]
    tasks: List[JobTask]
    links: List[JobLink]


class JobSection(BaseModel):
    id: str
    title: str
    status: str
    content: Optional[str]
    agent_id: Optional[str]


class JobSectionsResponse(BaseModel):
    job_id: str
    sections: List[JobSection]


@dataclass
class JobRecord:
    job_id: str
    prompt: str
    doc_type: str
    created_at: datetime
    template: Dict[str, Any]
    stages: List[Dict[str, str]]
    checklist: List[Dict[str, str]]
    tasks: List[Dict[str, Optional[str]]]
    links: List[Dict[str, str]]
    timeline: Dict[str, Dict[str, float]]


DOC_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "business_proposal": {
        "name": "Business Proposal",
        "sections": [
            "Executive Summary",
            "Problem Statement",
            "Proposed Solution",
            "Market Analysis",
            "Team",
            "Financial Projections",
        ],
        "knobs": {
            "Tone": ["Persuasive", "Formal", "Visionary"],
            "Style": ["Standard", "Data-Driven", "Narrative"],
            "Length": ["Concise", "Standard", "Comprehensive"],
        },
        "stages": [
            {
                "id": "Shotlist Build",
                "description": "Outline deliverable from prompt and uploads.",
            },
            {"id": "Research", "description": "Gather references for drafting."},
            {"id": "Draft Sections", "description": "Write sections using research."},
            {"id": "Review & Export", "description": "Summarize output for delivery."},
        ],
        "checklist": [
            {
                "id": "outline",
                "label": "Outline sections from prompt and uploads",
                "source": "Shotlist Agent",
                "stage": "Shotlist Build",
            },
            {
                "id": "research",
                "label": "Collect references before drafting",
                "source": "Research Agent",
                "stage": "Research",
            },
        ],
    },
    "legal_claim": {
        "name": "Legal Claim",
        "sections": [
            "Caption",
            "Jurisdiction",
            "Statement of Facts",
            "Cause of Action: Breach of Contract",
            "Prayer for Relief",
        ],
        "knobs": {
            "Tone": ["Formal", "Assertive"],
            "Style": ["Procedural", "Argumentative"],
            "Length": ["Standard", "Detailed"],
        },
        "stages": [
            {
                "id": "OCR Intake",
                "description": "Recognize uploaded exhibits and normalize text.",
            },
            {
                "id": "Shotlist Build",
                "description": "Sequence facts and claims before research.",
            },
            {
                "id": "Legal Research",
                "description": "Break down statutes and find caselaw per element.",
            },
            {
                "id": "Draft Sections",
                "description": "Draft the pleading from validated claims.",
            },
            {
                "id": "Review & Export",
                "description": "Hand-off with citations and logged authorities.",
            },
        ],
        "checklist": [
            {
                "id": "ocr-intake",
                "label": "OCR and normalize uploaded material",
                "source": "Text recognition pipeline",
                "stage": "OCR Intake",
            },
            {
                "id": "shotlist-outline",
                "label": "Sequence facts and exhibits into a shotlist",
                "source": "Shotlist Agent (Lex Omnia GPT)",
                "stage": "Shotlist Build",
            },
            {
                "id": "statute-elements",
                "label": "Identify governing statute/rule and break into elements",
                "source": "LegiScan / jurisdiction rules",
                "stage": "Legal Research",
            },
            {
                "id": "caselaw-search",
                "label": "Search CourtListener by jurisdiction and element keywords",
                "source": "CourtListener filters and expansions",
                "stage": "Legal Research",
            },
            {
                "id": "claims-check",
                "label": (
                    "Map facts to each claim element (standing, venue, ripeness, etc.)"
                ),
                "source": "Statute + caselaw factors",
                "stage": "Legal Research",
            },
            {
                "id": "citation-log",
                "label": (
                    "Log statutes, caselaw, and articles for downstream SQL capture"
                ),
                "source": "Research agent event hooks",
                "stage": "Legal Research",
            },
            {
                "id": "draft-ready",
                "label": (
                    "Confirm claims checklist complete before drafting sections"
                ),
                "source": "Legal Research + Shotlist outputs",
                "stage": "Draft Sections",
            },
        ],
    },
    "white_paper": {
        "name": "White Paper",
        "sections": [
            "Abstract",
            "Introduction",
            "Background Analysis",
            "DeFi Lending Protocols",
            "Impact on Banking",
            "Conclusion",
        ],
        "knobs": {
            "Tone": ["Authoritative", "Academic", "Objective"],
            "Style": ["Technical", "Analytical", "Educational"],
            "Length": ["Standard", "In-Depth", "Exhaustive"],
        },
        "stages": [
            {
                "id": "Shotlist Build",
                "description": "Outline deliverable from prompt and uploads.",
            },
            {"id": "Research", "description": "Gather references for drafting."},
            {"id": "Draft Sections", "description": "Write sections using research."},
            {"id": "Review & Export", "description": "Summarize output for delivery."},
        ],
        "checklist": [
            {
                "id": "outline",
                "label": "Outline sections from prompt and uploads",
                "source": "Shotlist Agent",
                "stage": "Shotlist Build",
            },
            {
                "id": "research",
                "label": "Collect references before drafting",
                "source": "Research Agent",
                "stage": "Research",
            },
        ],
    },
}

STAGE_OUTPUTS = {
    "OCR Intake": (
        "Uploaded files were scanned, text-normalized, and chunked for downstream "
        "agents."
    ),
    "Shotlist Build": (
        "Fact sequence created with linked exhibits and prompts to guide research."
    ),
    "Legal Research": (
        "Statute identified, elements extracted, and CourtListener/LegiScan queries "
        "queued."
    ),
    "Research": "Research notes collected and aligned with the outline for drafting.",
    "Review & Export": "Citations packaged and output prepared for delivery.",
}

SECTION_OUTPUTS = {
    "Executive Summary": (
        "ShipFast aligns AI-driven route optimization with rapid scale, positioning "
        "the platform for a $5M seed round."
    ),
    "Market Analysis": (
        "Logistics is a multi-trillion market; last-mile disruption creates a clear "
        "wedge for AI platforms."
    ),
    "Statement of Facts": (
        "Plaintiff John Doe contracted with MegaCorp for 10,000 units due March 31, "
        "2024, which were never delivered."
    ),
    "Cause of Action: Breach of Contract": (
        "Defendant's non-delivery constitutes a material breach of the January 1, "
        "2024 agreement."
    ),
    "Prayer for Relief": (
        "Plaintiff seeks compensatory damages, interest, costs, and further relief "
        "deemed proper."
    ),
    "Abstract": (
        "This paper assesses DeFi lending protocols and yield strategies reshaping "
        "traditional finance."
    ),
}


def build_agent_assignment(section: str) -> str:
    lowered = section.lower()
    if "market" in lowered:
        return "MarketAnalystAgent"
    if "financial" in lowered:
        return "FinancialModelerAgent"
    if any(
        keyword in lowered
        for keyword in [
            "legal",
            "claim",
            "fact",
            "action",
            "relief",
            "caption",
            "jurisdiction",
        ]
    ):
        return "LegalDrafterAgent"
    if "data" in lowered or "visualization" in lowered:
        return "DataVisualizationAgent"
    return "GeneralWriterAgent"


def build_pipeline_tasks(doc_type: str, sections: List[str]) -> Dict[str, Any]:
    is_legal = doc_type == "legal_claim"
    tasks: List[Dict[str, Optional[str]]] = [
        {"id": "Start", "type": "control", "stage": None, "agent_id": None},
    ]
    links: List[Dict[str, str]] = []
    last_task = "Start"

    def append_task(task_id: str, stage: str, agent_id: str) -> None:
        nonlocal last_task
        tasks.append(
            {
                "id": task_id,
                "type": "task",
                "stage": stage,
                "agent_id": agent_id,
            }
        )
        links.append({"source": last_task, "target": task_id})
        last_task = task_id

    if is_legal:
        append_task("OCR Intake", "OCR Intake", "ShotlistAgent")
    append_task("Shotlist Build", "Shotlist Build", "ShotlistAgent")
    append_task(
        "Legal Research" if is_legal else "Research",
        "Legal Research" if is_legal else "Research",
        "LegalResearchAgent" if is_legal else "WebResearchAgent",
    )

    for section in sections:
        tasks.append(
            {
                "id": section,
                "type": "section",
                "stage": "Draft Sections",
                "agent_id": build_agent_assignment(section),
            }
        )
        links.append({"source": last_task, "target": section})
        links.append({"source": section, "target": "Review & Export"})

    tasks.append(
        {
            "id": "Review & Export",
            "type": "task",
            "stage": "Review & Export",
            "agent_id": "EditorAgent",
        }
    )
    tasks.append(
        {"id": "End", "type": "control", "stage": None, "agent_id": None}
    )
    links.append({"source": "Review & Export", "target": "End"})

    return {"tasks": tasks, "links": links}


def build_timeline(
    tasks: List[Dict[str, Optional[str]]],
) -> Dict[str, Dict[str, float]]:
    """
    Build a timeline that assigns start times and durations to tasks.

    Section tasks execute in parallel (all start at the same time after
    their prerequisites), while non-section tasks execute sequentially.
    """
    timeline: Dict[str, Dict[str, float]] = {}
    cursor = 0.0

    # Known task durations
    durations = {
        "OCR Intake": 3.0,
        "Shotlist Build": 3.0,
        "Legal Research": 4.0,
        "Research": 4.0,
        "Review & Export": 3.0,
    }

    def estimate_duration(task: Dict[str, Optional[str]]) -> float:
        """
        Estimate the duration of a task based on its type and ID.
        """
        # Magic numbers for duration estimation
        SECTION_NAME_LENGTH_DIVISOR = 40.0

        task_id = task.get("id")
        task_type = task.get("type")

        # Use explicit configuration when available
        if task_id is not None and task_id in durations:
            return durations[task_id]

        # Apply heuristic for section tasks
        if task_type == "section":
            name = (str(task_id) if task_id is not None else "").lower()
            base = 3.0
            if "introduction" in name or "summary" in name:
                base = 2.0
            elif "analysis" in name or "argument" in name:
                base = 4.0
            elif "damages" in name or "relief" in name:
                base = 3.5
            # Add slight variability based on name length
            length_factor = min(
                len(str(task_id)) / SECTION_NAME_LENGTH_DIVISOR, 1.0
            )
            return base + length_factor

        # Default for unclassified tasks
        return 3.0

    # Process tasks, treating consecutive sections as parallel
    i = 0
    n = len(tasks)
    while i < n:
        task = tasks[i]
        if task["type"] == "control":
            i += 1
            continue

        # Group consecutive section tasks for parallel execution
        if task["type"] == "section":
            section_group: List[Dict[str, Optional[str]]] = []
            while i < n and tasks[i]["type"] == "section":
                section_group.append(tasks[i])
                i += 1

            # All sections in the group start at the same time
            max_duration = 0.0
            for section_task in section_group:
                duration = estimate_duration(section_task)
                task_id = section_task["id"]
                if task_id is not None:
                    timeline[task_id] = {
                        "start": cursor,
                        "duration": duration,
                    }
                if duration > max_duration:
                    max_duration = duration

            # Move cursor forward by the longest section duration
            cursor += max_duration
            continue

        # Non-section tasks execute sequentially
        duration = estimate_duration(task)
        task_id = task["id"]
        if task_id is not None:
            timeline[task_id] = {
                "start": cursor,
                "duration": duration,
            }
        cursor += duration
        i += 1

    return timeline


def task_status(
    elapsed: float,
    timeline: Dict[str, Dict[str, float]],
    task_id: str,
) -> str:
    if task_id not in timeline:
        return "pending"
    start = timeline[task_id]["start"]
    duration = timeline[task_id]["duration"]
    if elapsed < start:
        return "pending"
    if elapsed < start + duration:
        return "active"
    return "complete"


def build_job_response(job: JobRecord) -> JobResponse:
    now = datetime.now(timezone.utc)
    elapsed = (now - job.created_at).total_seconds()
    tasks: List[JobTask] = []
    task_statuses = {}

    for task in job.tasks:
        status = task_status(elapsed, job.timeline, task["id"])
        task_statuses[task["id"]] = status
        output = None
        if status == "complete":
            output = SECTION_OUTPUTS.get(task["id"], STAGE_OUTPUTS.get(task["id"]))
        tasks.append(
            JobTask(
                id=task["id"],
                type=task["type"] or "task",
                stage=task["stage"],
                agent_id=task["agent_id"],
                status=status,
                output=output,
            )
        )

    stages: List[JobStage] = []
    for stage in job.stages:
        stage_tasks = [t for t in tasks if t.stage == stage["id"]]
        if not stage_tasks:
            # Stage has no tasks - mark as skipped or n/a
            status = "pending"
        elif all(task.status == "complete" for task in stage_tasks):
            status = "complete"
        elif any(task.status == "active" for task in stage_tasks):
            status = "active"
        else:
            status = "pending"
        stages.append(
            JobStage(
                id=stage["id"],
                description=stage["description"],
                status=status,
            )
        )

    checklist: List[JobChecklistItem] = []
    for item in job.checklist:
        stage_status = next(
            (s.status for s in stages if s.id == item["stage"]),
            "pending",
        )
        note = None
        if stage_status == "active" and item["stage"] == "Legal Research":
            note = "Breaking statutes into elements and searching caselaw."
        if stage_status == "complete" and item["stage"] == "Draft Sections":
            note = "Sections drafted with validated claims."
        checklist.append(
            JobChecklistItem(
                id=item["id"],
                label=item["label"],
                source=item["source"],
                stage=item["stage"],
                status=stage_status,
                note=note,
            )
        )

    job_status = (
        "complete"
        if all(t.status == "complete" for t in tasks if t.type != "control")
        else "running"
    )

    return JobResponse(
        id=job.job_id,
        prompt=job.prompt,
        doc_type=job.doc_type,
        status=job_status,
        template=JobTemplate(
            name=job.template["name"],
            sections=job.template["sections"],
            knobs=job.template["knobs"],
        ),
        stages=stages,
        checklist=checklist,
        tasks=tasks,
        links=[
            JobLink(source=link["source"], target=link["target"])
            for link in job.links
        ],
    )


def build_sections_response(job: JobRecord) -> JobSectionsResponse:
    response = build_job_response(job)
    sections: List[JobSection] = []
    for task in response.tasks:
        if task.type != "section":
            continue
        sections.append(
            JobSection(
                id=task.id,
                title=task.id,
                status=task.status,
                content=task.output if task.status == "complete" else None,
                agent_id=task.agent_id,
            )
        )
    return JobSectionsResponse(job_id=job.job_id, sections=sections)


app = FastAPI(title="Pipeline Service", version="1.0")

# Configure CORS origins via environment variable for security
# Default to "*" for development, but should be restricted in production
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

JOBS: Dict[str, JobRecord] = {}


@app.post("/jobs", response_model=JobResponse)
def create_job(payload: JobCreateRequest) -> JobResponse:
    if payload.doc_type not in DOC_TEMPLATES:
        supported_types = ", ".join(DOC_TEMPLATES.keys())
        error_msg = (
            f"Unsupported document type '{payload.doc_type}'. "
            f"Supported types: {supported_types}"
        )
        logger.error(f"Job creation failed: {error_msg}")
        raise HTTPException(status_code=400, detail=error_msg)
    template = DOC_TEMPLATES[payload.doc_type]
    pipeline = build_pipeline_tasks(payload.doc_type, template["sections"])
    job_id = uuid4().hex
    job = JobRecord(
        job_id=job_id,
        prompt=payload.prompt,
        doc_type=payload.doc_type,
        created_at=datetime.now(timezone.utc),
        template=template,
        stages=template["stages"],
        checklist=template["checklist"],
        tasks=pipeline["tasks"],
        links=pipeline["links"],
        timeline=build_timeline(pipeline["tasks"]),
    )
    JOBS[job_id] = job
    logger.info(f"Job created: {job_id} (type: {payload.doc_type})")
    return build_job_response(job)


@app.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: str) -> JobResponse:
    job = JOBS.get(job_id)
    if not job:
        logger.error(f"Job not found: {job_id}")
        raise HTTPException(
            status_code=404, detail=f"Job not found: {job_id}"
        )
    return build_job_response(job)


@app.get("/jobs/{job_id}/sections", response_model=JobSectionsResponse)
def get_sections(job_id: str) -> JobSectionsResponse:
    job = JOBS.get(job_id)
    if not job:
        logger.error(f"Job not found for sections request: {job_id}")
        raise HTTPException(
            status_code=404, detail=f"Job not found: {job_id}"
        )
    return build_sections_response(job)
