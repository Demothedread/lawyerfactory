"""
Phase Orchestrator - Unified Phase Management System

Central coordinator for all LawyerFactory phases with real-time communication,
progress tracking, and integrated workflow management.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

from ..storage.enhanced_unified_storage_api import get_enhanced_unified_storage_api
from .phaseA01_intake.background_research_integration import BackgroundResearchIntegration
from ..agents.orchestration.maestro import Maestro

logger = logging.getLogger(__name__)


class PhaseStatus(Enum):
    """Phase execution status"""
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class WorkflowStatus(Enum):
    """Overall workflow status"""
    INITIALIZING = "initializing"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class PhaseResult:
    """Result of a phase execution"""
    phase_id: str
    status: PhaseStatus
    output_data: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    execution_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class WorkflowSession:
    """Active workflow session"""
    session_id: str
    case_id: Optional[str] = None
    current_phase: Optional[str] = None
    status: WorkflowStatus = WorkflowStatus.INITIALIZING
    phase_results: Dict[str, PhaseResult] = field(default_factory=dict)
    session_data: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


class PhaseOrchestrator:
    """
    Unified phase orchestration system that coordinates all LawyerFactory phases
    with real-time updates, progress tracking, and integrated communication.
    """

    def __init__(self):
        self.storage_api = get_enhanced_unified_storage_api()
        self.background_research = BackgroundResearchIntegration()
        self.maestro = Maestro()

        # Active sessions
        self.active_sessions: Dict[str, WorkflowSession] = {}

        # Phase definitions with dependencies
        self.phase_definitions = self._load_phase_definitions()

        # Event callbacks
        self.event_callbacks: Dict[str, List[Callable]] = {}

        # Socket.IO integration (will be set by server)
        self.socketio = None

        logger.info("Phase Orchestrator initialized")

    def _load_phase_definitions(self) -> Dict[str, Dict[str, Any]]:
        """Load phase definitions with dependencies and requirements"""
        return {
            "A01": {
                "name": "Document Intake",
                "description": "Upload and categorize legal documents",
                "type": "preproduction",
                "dependencies": [],
                "inputs": ["client_info", "documents"],
                "outputs": ["categorized_docs", "extracted_facts", "evidence_table"],
                "estimated_duration": 300,  # 5 minutes
            },
            "A02": {
                "name": "Legal Research",
                "description": "Automated legal research and authority gathering",
                "type": "preproduction",
                "dependencies": ["A01"],
                "inputs": ["case_facts", "jurisdiction", "legal_issues"],
                "outputs": ["legal_authorities", "precedent_cases", "research_notes"],
                "estimated_duration": 600,  # 10 minutes
            },
            "A03": {
                "name": "Case Outline",
                "description": "Structure case claims and arguments",
                "type": "preproduction",
                "dependencies": ["A01", "A02"],
                "inputs": ["research_results", "evidence", "legal_theories"],
                "outputs": ["case_outline", "claims_matrix", "argument_structure"],
                "estimated_duration": 450,  # 7.5 minutes
            },
            "B01": {
                "name": "Quality Review",
                "description": "Validate research and outline quality",
                "type": "production",
                "dependencies": ["A03"],
                "inputs": ["case_outline", "research_quality", "evidence_strength"],
                "outputs": ["quality_assessment", "missing_elements", "recommendations"],
                "estimated_duration": 300,  # 5 minutes
            },
            "B02": {
                "name": "Document Drafting",
                "description": "Generate professional legal documents",
                "type": "production",
                "dependencies": ["B01"],
                "inputs": ["approved_outline", "templates", "legal_standards"],
                "outputs": ["draft_documents", "legal_pleadings", "supporting_briefs"],
                "estimated_duration": 900,  # 15 minutes
            },
            "C01": {
                "name": "Document Editing",
                "description": "Refine formatting and citations",
                "type": "production",
                "dependencies": ["B02"],
                "inputs": ["draft_documents", "citation_rules", "format_standards"],
                "outputs": ["formatted_documents", "proper_citations", "final_review"],
                "estimated_duration": 600,  # 10 minutes
            },
            "C02": {
                "name": "Final Orchestration",
                "description": "Coordinate and finalize all deliverables",
                "type": "production",
                "dependencies": ["C01"],
                "inputs": ["all_phase_outputs", "quality_checks", "client_review"],
                "outputs": ["court_ready_documents", "filing_package", "case_summary"],
                "estimated_duration": 300,  # 5 minutes
            },
        }

    def set_socketio(self, socketio_instance):
        """Set Socket.IO instance for real-time communication"""
        self.socketio = socketio_instance
        logger.info("Socket.IO integration configured")

    def add_event_callback(self, event_type: str, callback: Callable):
        """Add callback for specific events"""
        if event_type not in self.event_callbacks:
            self.event_callbacks[event_type] = []
        self.event_callbacks[event_type].append(callback)

    def _emit_event(self, event_type: str, data: Dict[str, Any], session_id: str = None):
        """Emit event to registered callbacks and Socket.IO"""
        # Call registered callbacks
        if event_type in self.event_callbacks:
            for callback in self.event_callbacks[event_type]:
                try:
                    callback(data, session_id)
                except Exception as e:
                    logger.error(f"Event callback error: {e}")

        # Emit to Socket.IO if available
        if self.socketio and session_id:
            try:
                self.socketio.emit(event_type, {
                    "session_id": session_id,
                    "data": data,
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Socket.IO emit error: {e}")

    async def start_workflow(self, intake_data: Dict[str, Any], session_id: str) -> str:
        """
        Start a new workflow session with intake data

        Args:
            intake_data: Initial case intake data
            session_id: Unique session identifier

        Returns:
            Case ID for the workflow
        """
        try:
            # Create new session
            session = WorkflowSession(
                session_id=session_id,
                status=WorkflowStatus.ACTIVE,
                session_data={"intake_data": intake_data}
            )
            self.active_sessions[session_id] = session

            # Generate case ID
            case_id = f"CASE-{session_id}-{datetime.now().strftime('%Y%m%d')}"
            session.case_id = case_id

            # Emit workflow started event
            self._emit_event("workflow_started", {
                "case_id": case_id,
                "phase_definitions": self.phase_definitions
            }, session_id)

            # Start with A01 phase
            await self._start_phase("A01", session)

            logger.info(f"Workflow started: {case_id} (session: {session_id})")
            return case_id

        except Exception as e:
            logger.error(f"Failed to start workflow: {e}")
            self._emit_event("workflow_error", {
                "error": str(e),
                "phase": "initialization"
            }, session_id)
            raise

    async def _start_phase(self, phase_id: str, session: WorkflowSession):
        """Start execution of a specific phase"""
        try:
            session.current_phase = phase_id
            session.status = WorkflowStatus.ACTIVE

            # Check dependencies
            if not self._check_dependencies(phase_id, session):
                logger.warning(f"Dependencies not met for phase {phase_id}")
                return

            # Emit phase started event
            self._emit_event("phase_started", {
                "phase_id": phase_id,
                "phase_name": self.phase_definitions[phase_id]["name"],
                "estimated_duration": self.phase_definitions[phase_id]["estimated_duration"]
            }, session.session_id)

            # Execute phase
            result = await self._execute_phase(phase_id, session)

            # Store result
            session.phase_results[phase_id] = result

            # Handle completion
            if result.status == PhaseStatus.COMPLETED:
                await self._handle_phase_completion(phase_id, session)
            else:
                await self._handle_phase_failure(phase_id, session, result.error_message)

        except Exception as e:
            logger.error(f"Phase execution error for {phase_id}: {e}")
            await self._handle_phase_failure(phase_id, session, str(e))

    async def _execute_phase(self, phase_id: str, session: WorkflowSession) -> PhaseResult:
        """Execute a specific phase"""
        start_time = datetime.now()

        try:
            if phase_id == "A01":
                result = await self._execute_a01_intake(session)
            elif phase_id == "A02":
                result = await self._execute_a02_research(session)
            elif phase_id == "A03":
                result = await self._execute_a03_outline(session)
            else:
                # Placeholder for other phases
                result = await self._execute_placeholder_phase(phase_id, session)

            result.execution_time = (datetime.now() - start_time).total_seconds()
            return result

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return PhaseResult(
                phase_id=phase_id,
                status=PhaseStatus.FAILED,
                error_message=str(e),
                execution_time=execution_time
            )

    async def _execute_a01_intake(self, session: WorkflowSession) -> PhaseResult:
        """Execute A01 Document Intake phase"""
        intake_data = session.session_data.get("intake_data", {})

        try:
            # Perform background research integration
            research_result = await self.background_research.perform_background_research(
                intake_data, session.session_id
            )

            # Store intake data in unified storage
            storage_result = await self.storage_api.store_evidence(
                file_content=json.dumps(intake_data).encode(),
                filename="intake_data.json",
                metadata={"phase": "A01", "session_id": session.session_id},
                source_phase="A01"
            )

            output_data = {
                "research_result": research_result,
                "storage_result": {
                    "object_id": storage_result.object_id,
                    "evidence_id": storage_result.evidence_id
                },
                "intake_processed": True
            }

            return PhaseResult(
                phase_id="A01",
                status=PhaseStatus.COMPLETED,
                output_data=output_data
            )

        except Exception as e:
            logger.error(f"A01 execution failed: {e}")
            return PhaseResult(
                phase_id="A01",
                status=PhaseStatus.FAILED,
                error_message=str(e)
            )

    async def _execute_a02_research(self, session: WorkflowSession) -> PhaseResult:
        """Execute A02 Legal Research phase"""
        try:
            # Get data from previous phases
            a01_result = session.phase_results.get("A01")
            if not a01_result or a01_result.status != PhaseStatus.COMPLETED:
                raise ValueError("A01 phase must be completed before A02")

            intake_data = session.session_data.get("intake_data", {})

            # Perform legal research (placeholder - would integrate with research agents)
            research_output = {
                "jurisdiction": intake_data.get("jurisdiction", "Unknown"),
                "case_type": intake_data.get("case_type", "General Civil"),
                "research_completed": True,
                "authorities_found": 5,  # Placeholder
                "precedents_identified": 3  # Placeholder
            }

            return PhaseResult(
                phase_id="A02",
                status=PhaseStatus.COMPLETED,
                output_data=research_output
            )

        except Exception as e:
            logger.error(f"A02 execution failed: {e}")
            return PhaseResult(
                phase_id="A02",
                status=PhaseStatus.FAILED,
                error_message=str(e)
            )

    async def _execute_a03_outline(self, session: WorkflowSession) -> PhaseResult:
        """Execute A03 Case Outline phase"""
        try:
            # Get data from previous phases
            a01_result = session.phase_results.get("A01")
            a02_result = session.phase_results.get("A02")

            if not (a01_result and a02_result and
                    a01_result.status == PhaseStatus.COMPLETED and
                    a02_result.status == PhaseStatus.COMPLETED):
                raise ValueError("A01 and A02 phases must be completed before A03")

            intake_data = session.session_data.get("intake_data", {})

            # Generate case outline (placeholder - would integrate with outline agents)
            outline_output = {
                "case_theory": intake_data.get("claim_description", ""),
                "causes_of_action": intake_data.get("selected_causes", []),
                "outline_sections": [
                    "I. Introduction",
                    "II. Factual Background",
                    "III. Causes of Action",
                    "IV. Legal Arguments",
                    "V. Prayer for Relief"
                ],
                "outline_completed": True
            }

            return PhaseResult(
                phase_id="A03",
                status=PhaseStatus.COMPLETED,
                output_data=outline_output
            )

        except Exception as e:
            logger.error(f"A03 execution failed: {e}")
            return PhaseResult(
                phase_id="A03",
                status=PhaseStatus.FAILED,
                error_message=str(e)
            )

    async def _execute_placeholder_phase(self, phase_id: str, session: WorkflowSession) -> PhaseResult:
        """Placeholder execution for unimplemented phases"""
        # Simulate phase execution
        await asyncio.sleep(2)

        return PhaseResult(
            phase_id=phase_id,
            status=PhaseStatus.COMPLETED,
            output_data={"placeholder": True, "message": f"Phase {phase_id} executed (placeholder)"}
        )

    def _check_dependencies(self, phase_id: str, session: WorkflowSession) -> bool:
        """Check if phase dependencies are met"""
        dependencies = self.phase_definitions[phase_id]["dependencies"]

        for dep in dependencies:
            if dep not in session.phase_results:
                return False
            if session.phase_results[dep].status != PhaseStatus.COMPLETED:
                return False

        return True

    async def _handle_phase_completion(self, phase_id: str, session: WorkflowSession):
        """Handle successful phase completion"""
        # Emit completion event
        self._emit_event("phase_completed", {
            "phase_id": phase_id,
            "phase_name": self.phase_definitions[phase_id]["name"],
            "result": session.phase_results[phase_id].output_data
        }, session.session_id)

        # Determine next phase
        next_phase = self._get_next_phase(phase_id, session)

        if next_phase:
            # Auto-start next phase
            await self._start_phase(next_phase, session)
        else:
            # Workflow completed
            await self._handle_workflow_completion(session)

    async def _handle_phase_failure(self, phase_id: str, session: WorkflowSession, error: str):
        """Handle phase execution failure"""
        session.status = WorkflowStatus.FAILED

        self._emit_event("phase_failed", {
            "phase_id": phase_id,
            "phase_name": self.phase_definitions[phase_id]["name"],
            "error": error
        }, session.session_id)

        # Could implement retry logic or manual intervention here

    async def _handle_workflow_completion(self, session: WorkflowSession):
        """Handle overall workflow completion"""
        session.status = WorkflowStatus.COMPLETED

        # Compile final results
        final_results = {
            "case_id": session.case_id,
            "total_phases": len(session.phase_results),
            "completed_phases": len([r for r in session.phase_results.values() if r.status == PhaseStatus.COMPLETED]),
            "total_execution_time": sum(r.execution_time for r in session.phase_results.values()),
            "phase_results": {pid: {
                "status": result.status.value,
                "execution_time": result.execution_time,
                "output_summary": str(result.output_data)[:200] + "..." if len(str(result.output_data)) > 200 else str(result.output_data)
            } for pid, result in session.phase_results.items()}
        }

        self._emit_event("workflow_completed", final_results, session.session_id)

        logger.info(f"Workflow completed: {session.case_id}")

    def _get_next_phase(self, current_phase: str, session: WorkflowSession) -> Optional[str]:
        """Determine the next phase to execute"""
        phase_order = ["A01", "A02", "A03", "B01", "B02", "C01", "C02"]

        try:
            current_index = phase_order.index(current_phase)
            if current_index + 1 < len(phase_order):
                next_phase = phase_order[current_index + 1]

                # Check if next phase dependencies are met
                if self._check_dependencies(next_phase, session):
                    return next_phase
        except ValueError:
            pass

        return None

    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a workflow session"""
        if session_id not in self.active_sessions:
            return None

        session = self.active_sessions[session_id]

        return {
            "session_id": session_id,
            "case_id": session.case_id,
            "status": session.status.value,
            "current_phase": session.current_phase,
            "phase_results": {
                pid: {
                    "status": result.status.value,
                    "execution_time": result.execution_time,
                    "timestamp": result.timestamp.isoformat()
                }
                for pid, result in session.phase_results.items()
            },
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat()
        }

    def get_workflow_progress(self, session_id: str) -> Dict[str, Any]:
        """Get detailed workflow progress information"""
        if session_id not in self.active_sessions:
            return {"error": "Session not found"}

        session = self.active_sessions[session_id]

        total_phases = len(self.phase_definitions)
        completed_phases = len([r for r in session.phase_results.values() if r.status == PhaseStatus.COMPLETED])
        progress_percentage = (completed_phases / total_phases) * 100

        return {
            "session_id": session_id,
            "case_id": session.case_id,
            "overall_progress": progress_percentage,
            "current_phase": session.current_phase,
            "phase_status": {
                pid: {
                    "name": self.phase_definitions[pid]["name"],
                    "status": session.phase_results.get(pid, PhaseResult(pid, PhaseStatus.PENDING)).status.value,
                    "estimated_duration": self.phase_definitions[pid]["estimated_duration"]
                }
                for pid in self.phase_definitions.keys()
            },
            "total_execution_time": sum(r.execution_time for r in session.phase_results.values()),
            "session_status": session.status.value
        }


# Global instance
_phase_orchestrator_instance = None

def get_phase_orchestrator() -> PhaseOrchestrator:
    """Get the global phase orchestrator instance"""
    global _phase_orchestrator_instance
    if _phase_orchestrator_instance is None:
        _phase_orchestrator_instance = PhaseOrchestrator()
    return _phase_orchestrator_instance