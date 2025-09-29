"""
# Script Name: workflow_models.py
# Description: Core workflow models for the LawyerFactory orchestration system. Based on the maestro_orchestration_spec.md specification.
# Relationships:
#   - Entity Type: Data Model
#   - Directory Group: Orchestration
#   - Group Tags: orchestration
Core workflow models for the LawyerFactory orchestration system.
Based on the maestro_orchestration_spec.md specification.
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
import json
import logging
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class WorkflowPhase(Enum):
    """8-phase workflow for lawsuit generation"""

    INTAKE = "intake"
    OUTLINE = "outline"
    RESEARCH = "research"
    DRAFTING = "drafting"
    LEGAL_REVIEW = "legal_review"
    EDITING = "editing"
    ORCHESTRATION = "orchestration"
    POST_PRODUCTION = "post_production"


class PhaseStatus(Enum):
    """Status of workflow phases and tasks"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    REQUIRES_HUMAN_REVIEW = "requires_human_review"
    PAUSED = "paused"


class TaskPriority(Enum):
    """Task execution priority levels"""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class WorkflowStatus(Enum):
    """Workflow-level status values"""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


@dataclass
class PhaseResult:
    """Result of a completed phase execution"""

    phase_id: str
    status: PhaseStatus
    output_data: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0
    timestamp: Optional[datetime] = None
    error_message: Optional[str] = None
    quality_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data["status"] = self.status.value
        if self.timestamp:
            data["timestamp"] = self.timestamp.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PhaseResult":
        """Create from dictionary for JSON deserialization"""
        data["status"] = PhaseStatus(data["status"])
        if data.get("timestamp"):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


@dataclass
class WorkflowTask:
    """Individual task within a workflow phase"""

    id: str
    phase: WorkflowPhase
    agent_type: str
    description: str
    priority: TaskPriority = TaskPriority.NORMAL
    status: PhaseStatus = PhaseStatus.PENDING

    # Input/Output
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)

    # Dependencies
    depends_on: List[str] = field(default_factory=list)
    blocks: List[str] = field(default_factory=list)

    # Execution metadata
    assigned_agent: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_duration: Optional[int] = None  # seconds
    actual_duration: Optional[int] = None

    # Error handling
    retry_count: int = 0
    max_retries: int = 3
    error_message: Optional[str] = None

    # Human review
    requires_human_approval: bool = False
    human_feedback: Optional[str] = None
    approved: Optional[bool] = None

    # Research loop support
    research_needed: bool = False
    research_questions: List[str] = field(default_factory=list)
    research_context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        # Convert enum values to strings
        data["phase"] = self.phase.value
        data["status"] = self.status.value
        data["priority"] = self.priority.value
        # Convert datetime objects to ISO strings
        if self.started_at:
            data["started_at"] = self.started_at.isoformat()
        if self.completed_at:
            data["completed_at"] = self.completed_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowTask":
        """Create from dictionary for JSON deserialization"""
        # Convert enum strings back to enums
        data["phase"] = WorkflowPhase(data["phase"])
        data["status"] = PhaseStatus(data["status"])
        data["priority"] = TaskPriority(data["priority"])
        # Convert ISO strings back to datetime objects
        if data.get("started_at"):
            data["started_at"] = datetime.fromisoformat(data["started_at"])
        if data.get("completed_at"):
            data["completed_at"] = datetime.fromisoformat(data["completed_at"])
        return cls(**data)


@dataclass
class WorkflowState:
    """Complete state of a lawsuit generation workflow"""

    session_id: str
    case_name: str
    current_phase: WorkflowPhase
    overall_status: PhaseStatus

    # Progress tracking
    phases: Dict[WorkflowPhase, PhaseStatus] = field(default_factory=dict)
    tasks: Dict[str, WorkflowTask] = field(default_factory=dict)
    completed_tasks: List[str] = field(default_factory=list)
    failed_tasks: List[str] = field(default_factory=list)

    # Context and data
    global_context: Dict[str, Any] = field(default_factory=dict)
    knowledge_graph_id: Optional[str] = None
    input_documents: List[str] = field(default_factory=list)

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

    # Research loop tracking
    research_loop_count: int = 0
    max_research_loops: int = 3
    pending_research_questions: List[str] = field(default_factory=list)
    research_loop_history: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        # Convert enum values to strings
        data["current_phase"] = self.current_phase.value
        data["overall_status"] = self.overall_status.value
        # Convert phases dict
        data["phases"] = {phase.value: status.value for phase, status in self.phases.items()}
        # Convert tasks dict
        data["tasks"] = {task_id: task.to_dict() for task_id, task in self.tasks.items()}
        # Convert datetime objects to ISO strings
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        if self.estimated_completion:
            data["estimated_completion"] = self.estimated_completion.isoformat()
        if self.last_checkpoint:
            data["last_checkpoint"] = self.last_checkpoint.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowState":
        """Create from dictionary for JSON deserialization"""
        # Convert enum strings back to enums
        data["current_phase"] = WorkflowPhase(data["current_phase"])
        data["overall_status"] = PhaseStatus(data["overall_status"])
        # Convert phases dict
        data["phases"] = {
            WorkflowPhase(phase): PhaseStatus(status) for phase, status in data["phases"].items()
        }
        # Convert tasks dict
        data["tasks"] = {
            task_id: WorkflowTask.from_dict(task_data)
            for task_id, task_data in data["tasks"].items()
        }
        # Convert ISO strings back to datetime objects
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        if data.get("estimated_completion"):
            data["estimated_completion"] = datetime.fromisoformat(data["estimated_completion"])
        if data.get("last_checkpoint"):
            data["last_checkpoint"] = datetime.fromisoformat(data["last_checkpoint"])
        return cls(**data)


class WorkflowStateManager:
    """Manages persistence and retrieval of workflow states"""

    def __init__(self, db_path: str = "workflow_states.db"):
        self.db_path = Path(db_path)
        self._initialize_db()

    def _initialize_db(self):
        """Initialize the SQLite database for workflow state storage"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS workflow_states (
                    session_id TEXT PRIMARY KEY,
                    case_name TEXT NOT NULL,
                    current_phase TEXT NOT NULL,
                    overall_status TEXT NOT NULL,
                    state_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS workflow_checkpoints (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    checkpoint_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES workflow_states (session_id)
                )
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_workflow_session 
                ON workflow_states (session_id)
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_checkpoint_session 
                ON workflow_checkpoints (session_id, created_at)
            """
            )

            conn.commit()

    async def save_state(self, workflow_state: WorkflowState) -> None:
        """Save workflow state to database"""
        try:
            workflow_state.updated_at = datetime.now()
            state_json = json.dumps(workflow_state.to_dict(), indent=2)

            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO workflow_states 
                    (session_id, case_name, current_phase, overall_status, state_data, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        workflow_state.session_id,
                        workflow_state.case_name,
                        workflow_state.current_phase.value,
                        workflow_state.overall_status.value,
                        state_json,
                        workflow_state.updated_at.isoformat(),
                    ),
                )
                conn.commit()

            logger.info(f"Saved workflow state for session {workflow_state.session_id}")

        except Exception as e:
            logger.error(f"Failed to save workflow state: {e}")
            raise

    async def load_state(self, session_id: str) -> WorkflowState:
        """Load workflow state from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT state_data FROM workflow_states WHERE session_id = ?",
                    (session_id,),
                )
                row = cursor.fetchone()

                if not row:
                    raise ValueError(f"No workflow state found for session {session_id}")

                state_data = json.loads(row[0])
                workflow_state = WorkflowState.from_dict(state_data)

                logger.info(f"Loaded workflow state for session {session_id}")
                return workflow_state

        except Exception as e:
            logger.error(f"Failed to load workflow state: {e}")
            raise

    async def list_sessions(self) -> List[Dict[str, Any]]:
        """List all workflow sessions"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT session_id, case_name, current_phase, overall_status, 
                           created_at, updated_at
                    FROM workflow_states
                    ORDER BY updated_at DESC
                """
                )

                sessions = []
                for row in cursor.fetchall():
                    sessions.append(
                        {
                            "session_id": row[0],
                            "case_name": row[1],
                            "current_phase": row[2],
                            "overall_status": row[3],
                            "created_at": row[4],
                            "updated_at": row[5],
                        }
                    )

                return sessions

        except Exception as e:
            logger.error(f"Failed to list sessions: {e}")
            raise

    async def create_checkpoint(self, workflow_state: WorkflowState) -> None:
        """Create a checkpoint for the workflow"""
        try:
            checkpoint_data = {
                "timestamp": datetime.now().isoformat(),
                "session_id": workflow_state.session_id,
                "current_phase": workflow_state.current_phase.value,
                "completed_tasks": workflow_state.completed_tasks.copy(),
                "global_context": workflow_state.global_context.copy(),
            }

            checkpoint_json = json.dumps(checkpoint_data, indent=2)

            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO workflow_checkpoints (session_id, checkpoint_data)
                    VALUES (?, ?)
                """,
                    (workflow_state.session_id, checkpoint_json),
                )
                conn.commit()

            workflow_state.last_checkpoint = datetime.now()
            workflow_state.checkpoint_data = checkpoint_data

            logger.info(f"Created checkpoint for session {workflow_state.session_id}")

        except Exception as e:
            logger.error(f"Failed to create checkpoint: {e}")
            raise

    async def restore_from_checkpoint(
        self, session_id: str, checkpoint_id: Optional[int] = None
    ) -> WorkflowState:
        """Restore workflow from a specific checkpoint"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                if checkpoint_id:
                    cursor = conn.execute(
                        """
                        SELECT checkpoint_data FROM workflow_checkpoints 
                        WHERE session_id = ? AND id = ?
                    """,
                        (session_id, checkpoint_id),
                    )
                else:
                    cursor = conn.execute(
                        """
                        SELECT checkpoint_data FROM workflow_checkpoints 
                        WHERE session_id = ?
                        ORDER BY created_at DESC
                        LIMIT 1
                    """,
                        (session_id,),
                    )

                row = cursor.fetchone()
                if not row:
                    raise ValueError(f"No checkpoint found for session {session_id}")

                checkpoint_data = json.loads(row[0])

                # Load the current workflow state and apply checkpoint data
                workflow_state = await self.load_state(session_id)
                workflow_state.global_context.update(checkpoint_data.get("global_context", {}))
                workflow_state.checkpoint_data = checkpoint_data

                logger.info(f"Restored workflow from checkpoint for session {session_id}")
                return workflow_state

        except Exception as e:
            logger.error(f"Failed to restore from checkpoint: {e}")
            raise
