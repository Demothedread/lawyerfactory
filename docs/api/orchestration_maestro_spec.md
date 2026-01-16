# Maestro Orchestration Engine Specification

## Overview

The Maestro Orchestration Engine is the central coordinator that manages the 7-phase workflow, coordinates specialized agents, maintains state across the lawsuit generation process, and ensures seamless data flow between components.

## Core Architecture

### Workflow State Management

```python
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import asyncio
import json

class WorkflowPhase(Enum):
    INTAKE = "intake"
    OUTLINE = "outline" 
    RESEARCH = "research"
    DRAFTING = "drafting"
    LEGAL_REVIEW = "legal_review"
    EDITING = "editing"
    ORCHESTRATION = "orchestration"

class PhaseStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    REQUIRES_HUMAN_REVIEW = "requires_human_review"
    PAUSED = "paused"

class TaskPriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

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
```

## Enhanced Maestro Implementation

```python
class EnhancedMaestro:
    """Advanced orchestration engine with state management and recovery"""
    
    def __init__(self, knowledge_graph, llm_service, agents_registry):
        self.knowledge_graph = knowledge_graph
        self.llm_service = llm_service
        self.agents = agents_registry
        self.state_manager = WorkflowStateManager()
        self.scheduler = TaskScheduler()
        self.event_bus = EventBus()
        self.checkpoint_manager = CheckpointManager()
        
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
            WorkflowPhase.ORCHESTRATION: ['MaestroBot']
        }
    
    async def start_workflow(self, case_name: str, input_documents: List[str], 
                           initial_context: Dict[str, Any]) -> str:
        """Initialize and start a new workflow"""
        session_id = self._generate_session_id()
        
        # Create workflow state
        workflow_state = WorkflowState(
            session_id=session_id,
            case_name=case_name,
            current_phase=WorkflowPhase.INTAKE,
            overall_status=PhaseStatus.PENDING,
            input_documents=input_documents,
            global_context=initial_context
        )
        
        # Initialize phase statuses
        for phase in WorkflowPhase:
            workflow_state.phases[phase] = PhaseStatus.PENDING
        
        # Generate initial task plan
        tasks = await self._generate_task_plan(workflow_state)
        for task in tasks:
            workflow_state.tasks[task.id] = task
        
        # Save initial state
        await self.state_manager.save_state(workflow_state)
        
        # Start execution
        await self._execute_workflow(session_id)
        
        return session_id
    
    async def _execute_workflow(self, session_id: str):
        """Main workflow execution loop"""
        workflow_state = await self.state_manager.load_state(session_id)
        
        while not self._is_workflow_complete(workflow_state):
            try:
                # Get next executable tasks
                ready_tasks = self._get_ready_tasks(workflow_state)
                
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
                await self._handle_workflow_error(workflow_state, e)
    
    async def _execute_tasks_batch(self, tasks: List[WorkflowTask], 
                                 workflow_state: WorkflowState):
        """Execute a batch of tasks concurrently"""
        
        # Group tasks by agent type for efficient resource usage
        agent_groups = {}
        for task in tasks:
            if task.agent_type not in agent_groups:
                agent_groups[task.agent_type] = []
            agent_groups[task.agent_type].append(task)
        
        # Execute each agent group
        execution_coroutines = []
        for agent_type, agent_tasks in agent_groups.items():
            coroutine = self._execute_agent_tasks(agent_type, agent_tasks, workflow_state)
            execution_coroutines.append(coroutine)
        
        # Wait for all agent executions to complete
        results = await asyncio.gather(*execution_coroutines, return_exceptions=True)
        
        # Process results and update task statuses
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                agent_type = list(agent_groups.keys())[i]
                await self._handle_agent_error(agent_type, result, workflow_state)
    
    async def _execute_agent_tasks(self, agent_type: str, tasks: List[WorkflowTask], 
                                 workflow_state: WorkflowState):
        """Execute tasks for a specific agent type"""
        agent = self.agents.get_agent(agent_type)
        
        for task in tasks:
            try:
                # Update task status
                task.status = PhaseStatus.IN_PROGRESS
                task.started_at = datetime.now()
                
                # Prepare task context
                task_context = self._prepare_task_context(task, workflow_state)
                
                # Execute the task
                result = await agent.execute_task(task, task_context)
                
                # Process result
                await self._process_task_result(task, result, workflow_state)
                
                # Update task completion
                task.status = PhaseStatus.COMPLETED
                task.completed_at = datetime.now()
                task.actual_duration = (task.completed_at - task.started_at).seconds
                
            except Exception as e:
                await self._handle_task_error(task, e, workflow_state)
    
    def _prepare_task_context(self, task: WorkflowTask, 
                            workflow_state: WorkflowState) -> Dict[str, Any]:
        """Prepare context for task execution"""
        context = {
            'session_id': workflow_state.session_id,
            'case_name': workflow_state.case_name,
            'current_phase': workflow_state.current_phase,
            'global_context': workflow_state.global_context,
            'task_input': task.input_data,
            'knowledge_graph': self.knowledge_graph,
            'previous_results': self._get_previous_task_results(task, workflow_state)
        }
        
        # Add phase-specific context
        if task.phase in self.phase_configs:
            context.update(self.phase_configs[task.phase].get('context', {}))
        
        return context
    
    async def _process_task_result(self, task: WorkflowTask, result: Any, 
                                 workflow_state: WorkflowState):
        """Process the result of a completed task"""
        
        # Store task output
        task.output_data = result if isinstance(result, dict) else {'result': result}
        
        # Update knowledge graph if applicable
        if hasattr(result, 'entities'):
            for entity in result.entities:
                await self.knowledge_graph.add_entity(entity)
        
        if hasattr(result, 'relationships'):
            for relationship in result.relationships:
                await self.knowledge_graph.add_relationship(relationship)
        
        # Update global context
        if hasattr(result, 'context_updates'):
            workflow_state.global_context.update(result.context_updates)
        
        # Trigger dependent tasks
        await self._trigger_dependent_tasks(task, workflow_state)
        
        # Emit event
        await self.event_bus.emit('task_completed', {
            'task_id': task.id,
            'session_id': workflow_state.session_id,
            'result': task.output_data
        })
    
    async def _check_phase_transitions(self, workflow_state: WorkflowState):
        """Check if workflow should transition to next phase"""
        current_phase = workflow_state.current_phase
        phase_tasks = [t for t in workflow_state.tasks.values() if t.phase == current_phase]
        
        # Check if all tasks in current phase are complete
        if all(t.status == PhaseStatus.COMPLETED for t in phase_tasks):
            
            # Check if human approval is required
            if self._requires_human_approval(current_phase):
                workflow_state.human_feedback_required = True
                workflow_state.pending_approvals.append(current_phase.value)
                return
            
            # Transition to next phase
            next_phase = self._get_next_phase(current_phase)
            if next_phase:
                workflow_state.current_phase = next_phase
                workflow_state.phases[next_phase] = PhaseStatus.IN_PROGRESS
                
                # Generate tasks for next phase
                next_phase_tasks = await self._generate_phase_tasks(next_phase, workflow_state)
                for task in next_phase_tasks:
                    workflow_state.tasks[task.id] = task
```

## Agent Registry and Management

```python
class AgentRegistry:
    """Registry for managing specialized agents"""
    
    def __init__(self):
        self.agents = {}
        self.agent_configs = {}
        self.load_balancer = AgentLoadBalancer()
    
    def register_agent(self, agent_type: str, agent_class, config: Dict[str, Any]):
        """Register a new agent type"""
        self.agent_configs[agent_type] = config
        self.agents[agent_type] = {
            'class': agent_class,
            'instances': [],
            'max_concurrent': config.get('max_concurrent', 1),
            'current_load': 0
        }
    
    async def get_agent(self, agent_type: str):
        """Get an available agent instance"""
        if agent_type not in self.agents:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        agent_info = self.agents[agent_type]
        
        # Check if we can create a new instance
        if len(agent_info['instances']) < agent_info['max_concurrent']:
            instance = agent_info['class'](self.agent_configs[agent_type])
            agent_info['instances'].append(instance)
            return instance
        
        # Use load balancer to select best instance
        return self.load_balancer.select_agent(agent_info['instances'])

class TaskScheduler:
    """Intelligent task scheduling with dependency management"""
    
    def __init__(self):
        self.dependency_graph = DependencyGraph()
        self.resource_manager = ResourceManager()
    
    def get_ready_tasks(self, workflow_state: WorkflowState) -> List[WorkflowTask]:
        """Get tasks that are ready to execute"""
        ready_tasks = []
        
        for task in workflow_state.tasks.values():
            if task.status == PhaseStatus.PENDING:
                if self._are_dependencies_satisfied(task, workflow_state):
                    if self._are_resources_available(task):
                        ready_tasks.append(task)
        
        # Sort by priority and phase order
        ready_tasks.sort(key=lambda t: (t.phase.value, -t.priority.value))
        
        return ready_tasks
    
    def _are_dependencies_satisfied(self, task: WorkflowTask, 
                                  workflow_state: WorkflowState) -> bool:
        """Check if all task dependencies are satisfied"""
        for dependency_id in task.depends_on:
            if dependency_id in workflow_state.tasks:
                dep_task = workflow_state.tasks[dependency_id]
                if dep_task.status != PhaseStatus.COMPLETED:
                    return False
        return True
```

## Workflow Recovery and Checkpointing

```python
class CheckpointManager:
    """Manages workflow checkpoints for recovery"""
    
    def __init__(self, storage_path: str):
        self.storage_path = storage_path
        self.checkpoint_interval = 300  # 5 minutes
    
    async def create_checkpoint(self, workflow_state: WorkflowState):
        """Create a workflow checkpoint"""
        checkpoint_data = {
            'timestamp': datetime.now().isoformat(),
            'session_id': workflow_state.session_id,
            'current_phase': workflow_state.current_phase.value,
            'completed_tasks': workflow_state.completed_tasks.copy(),
            'global_context': workflow_state.global_context.copy(),
            'knowledge_graph_state': await self._capture_kg_state(workflow_state),
        }
        
        checkpoint_file = f"{self.storage_path}/checkpoint_{workflow_state.session_id}.json"
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint_data, f, indent=2)
        
        workflow_state.last_checkpoint = datetime.now()
        workflow_state.checkpoint_data = checkpoint_data
    
    async def restore_workflow(self, session_id: str) -> WorkflowState:
        """Restore workflow from checkpoint"""
        checkpoint_file = f"{self.storage_path}/checkpoint_{session_id}.json"
        
        if not os.path.exists(checkpoint_file):
            raise FileNotFoundError(f"No checkpoint found for session {session_id}")
        
        with open(checkpoint_file, 'r') as f:
            checkpoint_data = json.load(f)
        
        # Restore workflow state
        workflow_state = await self._reconstruct_workflow_state(checkpoint_data)
        
        # Restore knowledge graph state
        await self._restore_kg_state(checkpoint_data['knowledge_graph_state'])
        
        return workflow_state

class EventBus:
    """Event system for workflow coordination"""
    
    def __init__(self):
        self.subscribers = {}
        self.event_history = []
    
    async def emit(self, event_type: str, data: Dict[str, Any]):
        """Emit an event to all subscribers"""
        event = {
            'type': event_type,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }
        
        self.event_history.append(event)
        
        if event_type in self.subscribers:
            for callback in self.subscribers[event_type]:
                try:
                    await callback(event)
                except Exception as e:
                    print(f"Error in event handler: {e}")
    
    def subscribe(self, event_type: str, callback):
        """Subscribe to an event type"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)
```

## Human Interaction Management

```python
class HumanInteractionManager:
    """Manages human review and feedback in the workflow"""
    
    def __init__(self):
        self.pending_reviews = {}
        self.feedback_handlers = {}
    
    async def request_human_review(self, session_id: str, phase: WorkflowPhase, 
                                 content: Dict[str, Any]) -> str:
        """Request human review for a workflow phase"""
        review_id = f"{session_id}_{phase.value}_{datetime.now().timestamp()}"
        
        review_request = {
            'id': review_id,
            'session_id': session_id,
            'phase': phase,
            'content': content,
            'requested_at': datetime.now(),
            'status': 'pending'
        }
        
        self.pending_reviews[review_id] = review_request
        
        # Emit event for UI notification
        await self.event_bus.emit('human_review_requested', {
            'review_id': review_id,
            'session_id': session_id,
            'phase': phase.value,
            'content': content
        })
        
        return review_id
    
    async def submit_human_feedback(self, review_id: str, 
                                  approved: bool, feedback: str) -> bool:
        """Submit human feedback for a pending review"""
        if review_id not in self.pending_reviews:
            return False
        
        review = self.pending_reviews[review_id]
        review['approved'] = approved
        review['feedback'] = feedback
        review['reviewed_at'] = datetime.now()
        review['status'] = 'completed'
        
        # Resume workflow
        await self._resume_workflow_after_review(review)
        
        return True
```

This specification provides the foundation for a robust workflow orchestration system that can manage complex multi-phase lawsuit generation with proper state management, recovery capabilities, and human interaction points.