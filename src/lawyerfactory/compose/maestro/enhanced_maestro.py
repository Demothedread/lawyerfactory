"""
# Script Name: enhanced_maestro.py
# Description: Enhanced orchestration engine with state management and recovery. Implements the
#              EnhancedMaestro specification from orchestration_maestro_spec.md.
# Relationships:
#   - Entity Type: Engine
#   - Directory Group: Orchestration
#   - Group Tags: orchestration
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
import uuid

from .checkpoints import CheckpointManager
from .events import EventBus
from .workflow_models import PhaseStatus, TaskPriority, WorkflowPhase, WorkflowTask

logger = logging.getLogger(__name__)


@dataclass
class WorkflowState:
    """Complete workflow state for a lawsuit generation session"""
    
    session_id: str
    case_name: str
    current_phase: WorkflowPhase = WorkflowPhase.INTAKE
    overall_status: PhaseStatus = PhaseStatus.PENDING
    
    # Phase tracking
    phases: Dict[WorkflowPhase, PhaseStatus] = field(default_factory=dict)
    phase_outputs: Dict[WorkflowPhase, Dict[str, Any]] = field(default_factory=dict)
    
    # Task management
    tasks: Dict[str, WorkflowTask] = field(default_factory=dict)
    completed_tasks: List[str] = field(default_factory=list)
    failed_tasks: List[str] = field(default_factory=list)
    
    # Context and state
    global_context: Dict[str, Any] = field(default_factory=dict)
    input_documents: List[str] = field(default_factory=list)
    generated_documents: List[str] = field(default_factory=list)
    
    # Knowledge graph integration
    knowledge_graph_id: Optional[str] = None
    
    # Timing
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    estimated_completion: Optional[datetime] = None
    
    # Human interaction
    pending_approvals: List[str] = field(default_factory=list)
    human_feedback_required: bool = False
    
    # Checkpoints for recovery
    last_checkpoint: Optional[datetime] = None
    checkpoint_data: Dict[str, Any] = field(default_factory=dict)


class WorkflowStateManager:
    """Manages workflow state persistence"""
    
    def __init__(self, storage_path: str = "workflow_storage"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        self.states: Dict[str, WorkflowState] = {}
    
    async def save_state(self, state: WorkflowState) -> None:
        """Save workflow state"""
        state.updated_at = datetime.now()
        self.states[state.session_id] = state
        logger.debug(f"Saved state for session {state.session_id}")
    
    async def load_state(self, session_id: str) -> Optional[WorkflowState]:
        """Load workflow state by session ID"""
        return self.states.get(session_id)
    
    async def delete_state(self, session_id: str) -> None:
        """Delete workflow state"""
        if session_id in self.states:
            del self.states[session_id]


class TaskScheduler:
    """Schedules and prioritizes workflow tasks"""
    
    def __init__(self):
        self.task_queue: List[WorkflowTask] = []
    
    def add_task(self, task: WorkflowTask) -> None:
        """Add a task to the queue"""
        self.task_queue.append(task)
        # Sort by priority (higher priority first)
        self.task_queue.sort(key=lambda t: t.priority.value if hasattr(t, 'priority') else 0, reverse=True)
    
    def get_next_task(self) -> Optional[WorkflowTask]:
        """Get the next task to execute"""
        if self.task_queue:
            return self.task_queue.pop(0)
        return None
    
    def get_ready_tasks(self, max_count: int = 5) -> List[WorkflowTask]:
        """Get ready tasks for parallel execution"""
        ready = []
        remaining = []
        for task in self.task_queue:
            if len(ready) < max_count:
                ready.append(task)
            else:
                remaining.append(task)
        self.task_queue = remaining
        return ready


class EnhancedMaestro:
    """Advanced orchestration engine with state management and recovery"""
    
    def __init__(
        self,
        knowledge_graph=None,
        llm_service=None,
        agents_registry=None,
        storage_path: str = "workflow_storage"
    ):
        self.knowledge_graph = knowledge_graph
        self.llm_service = llm_service
        self.agents = agents_registry or {}
        self.storage_path = storage_path
        
        self.state_manager = WorkflowStateManager(storage_path)
        self.scheduler = TaskScheduler()
        self.event_bus = EventBus()
        self.checkpoint_manager = CheckpointManager(storage_path)
        
        # Phase configurations
        self.phase_configs = self._initialize_phase_configs()
        
        # Agent assignment rules
        self.agent_assignments = {
            WorkflowPhase.INTAKE: ['ReaderBot', 'ParalegalBot'],
            WorkflowPhase.OUTLINE: ['OutlinerBot', 'ParalegalBot'],
            WorkflowPhase.RESEARCH: ['ResearchBot', 'LegalResearcherBot'],
            WorkflowPhase.DRAFTING: ['WriterBot', 'ParalegalBot'],
            WorkflowPhase.LEGAL_REVIEW: ['LegalFormatterBot', 'LegalProcedureBot'],
            WorkflowPhase.EDITING: ['EditorBot'],
            WorkflowPhase.ORCHESTRATION: ['MaestroBot'],
            WorkflowPhase.POST_PRODUCTION: ['FormatterBot'],
        }
    
    def _initialize_phase_configs(self) -> Dict[WorkflowPhase, Dict[str, Any]]:
        """Initialize phase-specific configurations"""
        return {
            WorkflowPhase.INTAKE: {
                "timeout": 1800,  # 30 minutes
                "retry_count": 3,
                "requires_human_approval": False,
            },
            WorkflowPhase.OUTLINE: {
                "timeout": 3600,
                "retry_count": 2,
                "requires_human_approval": True,
            },
            WorkflowPhase.RESEARCH: {
                "timeout": 7200,
                "retry_count": 3,
                "requires_human_approval": False,
            },
            WorkflowPhase.DRAFTING: {
                "timeout": 7200,
                "retry_count": 2,
                "requires_human_approval": True,
            },
            WorkflowPhase.LEGAL_REVIEW: {
                "timeout": 3600,
                "retry_count": 2,
                "requires_human_approval": True,
            },
            WorkflowPhase.EDITING: {
                "timeout": 1800,
                "retry_count": 3,
                "requires_human_approval": False,
            },
            WorkflowPhase.ORCHESTRATION: {
                "timeout": 1800,
                "retry_count": 2,
                "requires_human_approval": False,
            },
            WorkflowPhase.POST_PRODUCTION: {
                "timeout": 1800,
                "retry_count": 2,
                "requires_human_approval": True,
            },
        }
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID"""
        return str(uuid.uuid4())
    
    async def start_workflow(
        self,
        case_name: str,
        input_documents: List[str],
        initial_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Initialize and start a new workflow"""
        session_id = self._generate_session_id()
        
        # Create workflow state
        workflow_state = WorkflowState(
            session_id=session_id,
            case_name=case_name,
            current_phase=WorkflowPhase.INTAKE,
            overall_status=PhaseStatus.PENDING,
            input_documents=input_documents,
            global_context=initial_context or {}
        )
        
        # Initialize phase statuses
        for phase in WorkflowPhase:
            workflow_state.phases[phase] = PhaseStatus.PENDING
        
        # Generate initial task plan
        tasks = await self._generate_task_plan(workflow_state)
        for task in tasks:
            workflow_state.tasks[task.task_id] = task
            self.scheduler.add_task(task)
        
        # Save initial state
        await self.state_manager.save_state(workflow_state)
        
        # Emit workflow started event
        await self.event_bus.emit("workflow_started", {
            "session_id": session_id,
            "case_name": case_name,
            "input_documents": input_documents,
        })
        
        return session_id
    
    async def _generate_task_plan(self, workflow_state: WorkflowState) -> List[WorkflowTask]:
        """Generate the initial task plan based on workflow state"""
        tasks = []
        
        # Create intake tasks
        task_id = f"task_{workflow_state.session_id}_intake_1"
        tasks.append(WorkflowTask(
            task_id=task_id,
            phase=WorkflowPhase.INTAKE,
            name="Document Ingestion",
            description="Process and analyze input documents",
            assigned_agents=self.agent_assignments.get(WorkflowPhase.INTAKE, []),
            priority=TaskPriority.HIGH,
            status=PhaseStatus.PENDING,
        ))
        
        return tasks
    
    async def execute_workflow(self, session_id: str) -> None:
        """Main workflow execution loop"""
        workflow_state = await self.state_manager.load_state(session_id)
        if not workflow_state:
            raise ValueError(f"No workflow found for session {session_id}")
        
        workflow_state.overall_status = PhaseStatus.IN_PROGRESS
        await self.state_manager.save_state(workflow_state)
        
        while not self._is_workflow_complete(workflow_state):
            try:
                # Get next executable tasks
                ready_tasks = self.scheduler.get_ready_tasks()
                
                if not ready_tasks:
                    if workflow_state.human_feedback_required:
                        await self._wait_for_human_input(workflow_state)
                        continue
                    else:
                        break  # No more tasks to execute
                
                # Execute tasks concurrently (where possible)
                await self._execute_tasks_batch(ready_tasks, workflow_state)
                
                # Update workflow state
                await self._update_workflow_progress(workflow_state)
                
                # Create checkpoint
                await self.checkpoint_manager.create_checkpoint(workflow_state)
                
                # Check for phase transitions
                await self._check_phase_transitions(workflow_state)
                
            except Exception as e:
                logger.error(f"Workflow execution error: {e}")
                workflow_state.overall_status = PhaseStatus.FAILED
                await self.state_manager.save_state(workflow_state)
                await self.event_bus.emit("workflow_failed", {
                    "session_id": session_id,
                    "error": str(e),
                })
                raise
        
        # Mark workflow complete
        workflow_state.overall_status = PhaseStatus.COMPLETED
        await self.state_manager.save_state(workflow_state)
        await self.event_bus.emit("workflow_completed", {
            "session_id": session_id,
            "case_name": workflow_state.case_name,
        })
    
    def _is_workflow_complete(self, workflow_state: WorkflowState) -> bool:
        """Check if workflow is complete"""
        return (
            workflow_state.overall_status in [PhaseStatus.COMPLETED, PhaseStatus.FAILED]
            or all(
                status in [PhaseStatus.COMPLETED, PhaseStatus.FAILED]
                for status in workflow_state.phases.values()
            )
        )
    
    async def _execute_tasks_batch(
        self,
        tasks: List[WorkflowTask],
        workflow_state: WorkflowState
    ) -> None:
        """Execute a batch of tasks"""
        for task in tasks:
            try:
                task.status = PhaseStatus.IN_PROGRESS
                task.started_at = datetime.now()
                
                # Execute task (placeholder for actual execution logic)
                result = await self._execute_task(task, workflow_state)
                
                task.status = PhaseStatus.COMPLETED
                task.completed_at = datetime.now()
                task.output = result
                workflow_state.completed_tasks.append(task.task_id)
                
                await self.event_bus.emit("task_completed", {
                    "task_id": task.task_id,
                    "phase": task.phase.value,
                    "result": result,
                })
                
            except Exception as e:
                task.status = PhaseStatus.FAILED
                task.error = str(e)
                workflow_state.failed_tasks.append(task.task_id)
                logger.error(f"Task {task.task_id} failed: {e}")
    
    async def _execute_task(
        self,
        task: WorkflowTask,
        workflow_state: WorkflowState
    ) -> Dict[str, Any]:
        """Execute a single task"""
        # Placeholder for actual task execution
        logger.info(f"Executing task: {task.name}")
        await asyncio.sleep(0.1)  # Simulate work
        return {"status": "success", "task_id": task.task_id}
    
    async def _update_workflow_progress(self, workflow_state: WorkflowState) -> None:
        """Update workflow progress metrics"""
        total_tasks = len(workflow_state.tasks)
        completed = len(workflow_state.completed_tasks)
        
        if total_tasks > 0:
            progress = (completed / total_tasks) * 100
            workflow_state.global_context["progress_percentage"] = progress
        
        await self.state_manager.save_state(workflow_state)
    
    async def _check_phase_transitions(self, workflow_state: WorkflowState) -> None:
        """Check and handle phase transitions"""
        current_phase = workflow_state.current_phase
        
        # Check if current phase is complete
        phase_tasks = [
            t for t in workflow_state.tasks.values()
            if t.phase == current_phase
        ]
        
        all_complete = all(
            t.status == PhaseStatus.COMPLETED for t in phase_tasks
        )
        
        if all_complete and phase_tasks:
            workflow_state.phases[current_phase] = PhaseStatus.COMPLETED
            
            # Get next phase
            phases_list = list(WorkflowPhase)
            current_index = phases_list.index(current_phase)
            
            if current_index < len(phases_list) - 1:
                next_phase = phases_list[current_index + 1]
                workflow_state.current_phase = next_phase
                workflow_state.phases[next_phase] = PhaseStatus.IN_PROGRESS
                
                await self.event_bus.emit("phase_transition", {
                    "session_id": workflow_state.session_id,
                    "from_phase": current_phase.value,
                    "to_phase": next_phase.value,
                })
    
    async def _wait_for_human_input(self, workflow_state: WorkflowState) -> None:
        """Wait for human input/approval"""
        logger.info(f"Waiting for human input on session {workflow_state.session_id}")
        await asyncio.sleep(1)  # Polling interval
    
    async def get_workflow_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current workflow status"""
        workflow_state = await self.state_manager.load_state(session_id)
        if not workflow_state:
            return None
        
        return {
            "session_id": session_id,
            "case_name": workflow_state.case_name,
            "current_phase": workflow_state.current_phase.value,
            "overall_status": workflow_state.overall_status.value,
            "phases": {
                phase.value: status.value
                for phase, status in workflow_state.phases.items()
            },
            "completed_tasks": workflow_state.completed_tasks,
            "failed_tasks": workflow_state.failed_tasks,
            "progress": workflow_state.global_context.get("progress_percentage", 0),
        }
    
    async def pause_workflow(self, session_id: str) -> bool:
        """Pause a workflow"""
        workflow_state = await self.state_manager.load_state(session_id)
        if workflow_state:
            workflow_state.overall_status = PhaseStatus.PAUSED
            await self.state_manager.save_state(workflow_state)
            return True
        return False
    
    async def resume_workflow(self, session_id: str) -> bool:
        """Resume a paused workflow"""
        workflow_state = await self.state_manager.load_state(session_id)
        if workflow_state and workflow_state.overall_status == PhaseStatus.PAUSED:
            workflow_state.overall_status = PhaseStatus.IN_PROGRESS
            await self.state_manager.save_state(workflow_state)
            return True
        return False
