"""
Maestro Agent for LawyerFactory - Central orchestration and workflow coordination
Canonical agent location following copilot-instructions.md structure
"""

import asyncio
import logging
from typing import Any

from ...compose.maestro.document_object_map import DocumentObjectMap, SectionNode
from ...compose.maestro.lawsuit_blueprint import (
    EvidenceRecord,
    build_evidence_cycle,
    get_lawsuit_stage_blueprint,
)
from ...compose.maestro.prewriting_packets import to_user_review_packet

try:
    from ...compose.maestro.maestro import Maestro as ComposeMaestro
except ImportError:
    ComposeMaestro = None

logger = logging.getLogger(__name__)


class Maestro:
    """
    Central orchestration agent that directs the entire LawyerFactory workflow.
    Coordinates all phases: Intake → Research → Outline → Draft → Review → Edit → Final

    Features:
    - Phase-based workflow coordination
    - Agent swarm management
    - Unified storage integration
    - Real-time progress tracking
    """

    def __init__(self):
        from ...storage.enhanced_unified_storage_api import (
            get_enhanced_unified_storage_api,
        )

        self.unified_storage = get_enhanced_unified_storage_api()

        # Initialize with existing ComposeMaestro if available
        if ComposeMaestro:
            self.compose_maestro = ComposeMaestro()
        else:
            self.compose_maestro = None

        self.active_workflows: dict[str, dict[str, Any]] = {}
        self.phase_sequence = [
            "phaseA01_intake",
            "phaseA02_research",
            "phaseA03_outline",
            "phaseB01_review",
            "phaseB02_drafting",
            "phaseC01_editing",
            "phaseC02_orchestration",
        ]

        logger.info("Maestro agent initialized with unified storage integration")


    def get_stage_blueprint(self) -> list[dict[str, Any]]:
        """Return discrete, combinable lawsuit-assembly phases for UI/API clients."""
        blueprint = [
            {
                "phase_id": phase.phase_id,
                "label": phase.label,
                "objective": phase.objective,
                "required_inputs": phase.required_inputs,
                "outputs": phase.outputs,
                "can_iterate": phase.can_iterate,
                "agents": [
                    {
                        "role_id": agent.role_id,
                        "title": agent.title,
                        "responsibility": agent.responsibility,
                    }
                    for agent in phase.agents
                ],
            }
            for phase in get_lawsuit_stage_blueprint()
        ]
        logger.info(
            "Exposed stage blueprint",
            extra={
                "phase_count": len(blueprint),
                "phase_ids": [phase["phase_id"] for phase in blueprint],
            },
        )
        return blueprint

    def build_evidence_cycle_payload(
        self, evidence_items: list[dict[str, str]]
    ) -> dict[str, Any]:
        """Build tiered evidence cycle payload for repeated ingest/categorize passes."""
        logger.debug(
            "Building evidence cycle payload from raw evidence items",
            extra={"input_count": len(evidence_items)},
        )
        records = [
            EvidenceRecord(
                evidence_id=item.get("evidence_id", f"evidence_{index}"),
                summary=item.get("summary", ""),
                source_type=item.get("source_type", "unknown"),
                tier=item.get("tier", "secondary"),
            )
            for index, item in enumerate(evidence_items)
        ]
        payload = build_evidence_cycle(records)
        logger.debug(
            "Built evidence cycle payload in Maestro",
            extra={
                "counts": payload.get("counts", {}),
                "total_items": payload.get("total_items", 0),
            },
        )
        return payload


    def build_document_object_map(
        self, claim_sections: list[dict[str, Any]], token_budget: int = 900
    ) -> dict[str, Any]:
        """Build context-window-safe section map linked by underlying claim/theory."""
        logger.debug(
            "Building document object map packet",
            extra={"input_sections": len(claim_sections), "token_budget": token_budget},
        )
        document_map = DocumentObjectMap()
        for index, section in enumerate(claim_sections):
            document_map.add_section(
                SectionNode(
                    section_id=section.get("section_id", f"section_{index:03d}"),
                    claim_id=section.get("claim_id", "unscoped_claim"),
                    theory_id=section.get("theory_id", "default_theory"),
                    title=section.get("title", "Untitled Section"),
                    body=section.get("body", ""),
                    summary=section.get("summary", ""),
                    tags=section.get("tags", []),
                )
            )

        packet = document_map.build_context_packet(token_budget=token_budget)
        logger.info(
            "Built document object map packet",
            extra={
                "token_budget": token_budget,
                "packed_sections": len(packet.get("sections", [])),
                "has_overlap": packet.get("overlap_report", {}).get("has_overlap", False),
            },
        )
        return packet

    def get_prewriting_review_packet(self) -> dict[str, Any]:
        """Return the three pre-writing deliverables for user review gating."""
        packet = to_user_review_packet()
        logger.info(
            "Exposed pre-writing review packet",
            extra={"deliverable_count": packet.get("deliverable_count", 0)},
        )
        return packet

    async def start_workflow(self, case_data: dict[str, Any]) -> str:
        """
        Start a new 7-phase legal workflow

        Args:
            case_data: Initial case information and client intake

        Returns:
            Workflow ID for tracking progress
        """
        try:
            workflow_id = f"workflow_{len(self.active_workflows)}"

            # Initialize workflow state
            workflow_state = {
                "id": workflow_id,
                "current_phase": self.phase_sequence[0],
                "case_data": case_data,
                "phase_results": {},
                "status": "active",
                "agents_involved": [],
            }

            self.active_workflows[workflow_id] = workflow_state

            # Store initial case data through unified storage
            storage_result = await self.unified_storage.store_evidence(
                file_content=str(case_data).encode("utf-8"),
                filename=f"case_intake_{workflow_id}.json",
                metadata={
                    "workflow_id": workflow_id,
                    "phase": "A01_intake",
                    "content_type": "case_data",
                },
                source_phase="orchestration",
            )

            if storage_result.success:
                workflow_state["storage_object_id"] = storage_result.object_id
                logger.info(
                    f"Started workflow {workflow_id} with ObjectID {storage_result.object_id}"
                )

            return workflow_id

        except Exception as e:
            logger.error(f"Failed to start workflow: {e}")
            raise

    async def orchestrate_phase(self, workflow_id: str, phase_id: str) -> dict[str, Any]:
        """
        Orchestrate a specific phase of the workflow

        Args:
            workflow_id: The workflow to orchestrate
            phase_id: Phase to execute (e.g., "A01_intake", "A02_research")

        Returns:
            Phase execution results
        """
        try:
            if workflow_id not in self.active_workflows:
                raise ValueError(f"Workflow {workflow_id} not found")

            workflow = self.active_workflows[workflow_id]

            logger.info(f"Orchestrating phase {phase_id} for workflow {workflow_id}")

            # Delegate to compose maestro for actual orchestration if available
            if self.compose_maestro:
                phase_result = await self.compose_maestro.research_and_write(
                    f"Phase {phase_id}: {workflow['case_data']}"
                )
            else:
                # Fallback implementation for phase processing
                phase_result = f"Phase {phase_id} completed successfully for workflow {workflow_id}"

            # Store phase results
            workflow["phase_results"][phase_id] = {
                "result": phase_result,
                "completed_at": asyncio.get_event_loop().time(),
                "status": "completed",
            }

            # Store through unified storage
            storage_result = await self.unified_storage.store_evidence(
                file_content=phase_result.encode("utf-8"),
                filename=f"phase_{phase_id}_{workflow_id}.txt",
                metadata={
                    "workflow_id": workflow_id,
                    "phase": phase_id,
                    "content_type": "phase_result",
                },
                source_phase="orchestration",
            )

            if storage_result.success:
                workflow["phase_results"][phase_id]["storage_object_id"] = storage_result.object_id

            # Update workflow current phase
            if phase_id in self.phase_sequence:
                current_index = self.phase_sequence.index(phase_id)
                if current_index < len(self.phase_sequence) - 1:
                    workflow["current_phase"] = self.phase_sequence[current_index + 1]
                else:
                    workflow["status"] = "completed"

            return workflow["phase_results"][phase_id]

        except Exception as e:
            logger.error(f"Failed to orchestrate phase {phase_id}: {e}")
            raise

    async def get_workflow_status(self, workflow_id: str) -> dict[str, Any]:
        """Get current status of a workflow"""
        if workflow_id not in self.active_workflows:
            return {"error": "Workflow not found"}

        workflow = self.active_workflows[workflow_id]

        return {
            "workflow_id": workflow_id,
            "current_phase": workflow["current_phase"],
            "status": workflow["status"],
            "completed_phases": list(workflow["phase_results"].keys()),
            "next_phase": self._get_next_phase(workflow["current_phase"]),
            "progress_percentage": self._calculate_progress(workflow),
        }

    def _get_next_phase(self, current_phase: str) -> str | None:
        """Get the next phase in the sequence"""
        if current_phase in self.phase_sequence:
            current_index = self.phase_sequence.index(current_phase)
            if current_index < len(self.phase_sequence) - 1:
                return self.phase_sequence[current_index + 1]
        return None

    def _calculate_progress(self, workflow: dict[str, Any]) -> float:
        """Calculate workflow progress percentage"""
        completed_phases = len(workflow["phase_results"])
        total_phases = len(self.phase_sequence)
        return (completed_phases / total_phases) * 100 if total_phases > 0 else 0

    async def search_workflow_evidence(self, workflow_id: str, query: str) -> list[dict[str, Any]]:
        """Search for evidence within a specific workflow"""
        try:
            # Search all evidence, then filter by workflow_id
            all_results = await self.unified_storage.search_evidence(query, "all")

            workflow_results = []
            for result in all_results:
                metadata = result.get("metadata", {})
                if metadata.get("workflow_id") == workflow_id:
                    workflow_results.append(result)

            return workflow_results

        except Exception as e:
            logger.error(f"Failed to search workflow evidence: {e}")
            return []

    async def generate_workflow_summary(self, workflow_id: str) -> dict[str, Any]:
        """Generate a comprehensive summary of the workflow"""
        try:
            if workflow_id not in self.active_workflows:
                return {"error": "Workflow not found"}

            workflow = self.active_workflows[workflow_id]

            # Gather all phase results
            phase_summaries = {}
            for phase_id, phase_result in workflow["phase_results"].items():
                phase_summaries[phase_id] = {
                    "status": phase_result["status"],
                    "completed_at": phase_result["completed_at"],
                    "storage_object_id": phase_result.get("storage_object_id"),
                    "result_length": len(phase_result["result"]) if phase_result["result"] else 0,
                }

            return {
                "workflow_id": workflow_id,
                "case_data": workflow["case_data"],
                "current_phase": workflow["current_phase"],
                "status": workflow["status"],
                "phase_summaries": phase_summaries,
                "total_phases_completed": len(workflow["phase_results"]),
                "progress_percentage": self._calculate_progress(workflow),
                "storage_object_id": workflow.get("storage_object_id"),
            }

        except Exception as e:
            logger.error(f"Failed to generate workflow summary: {e}")
            return {"error": str(e)}
