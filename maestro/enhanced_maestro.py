"""
Enhanced Maestro Orchestration Engine for LawyerFactory.
Coordinates the 7-phase workflow with state management, agent coordination, and recovery.
"""

import asyncio
import logging
import uuid
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from .agent_registry import AgentRegistry, TaskScheduler
from .checkpoint_manager import CheckpointManager
from .error_handling import WorkflowErrorHandler
from .event_system import EventBus
from .workflow_models import (PhaseStatus, TaskPriority, WorkflowPhase,
                              WorkflowState, WorkflowStateManager,
                              WorkflowTask)

logger = logging.getLogger(__name__)


class EnhancedMaestro:
    """Advanced orchestration engine with state management and recovery"""

    def __init__(self, knowledge_graph, llm_service=None, storage_path: str = "workflow_storage"):
        self.knowledge_graph = knowledge_graph
        self.llm_service = llm_service
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        
        # Core components
        self.state_manager = WorkflowStateManager(str(self.storage_path / "workflow_states.db"))
        self.agent_registry = AgentRegistry()
        self.scheduler = TaskScheduler(self.agent_registry)
        self.event_bus = EventBus()
        self.checkpoint_manager = CheckpointManager(str(self.storage_path))
        self.error_handler = WorkflowErrorHandler(self.event_bus)
        
        # Initialize agent pools
        self._initialize_agent_pools()
        
        # Active workflows tracking
        self.active_workflows: Dict[str, WorkflowState] = {}
        
        # Phase configurations
        self.phase_configs = self._initialize_phase_configs()
    
    def _initialize_agent_pools(self):
        """Initialize specialist and general agent pools"""
        try:
            from lawyerfactory.agent_config_system import AgentConfigManager, AgentPoolManager
            
            # Initialize agent configuration system
            self.agent_config_manager = AgentConfigManager()
            self.agent_pool_manager = AgentPoolManager(self.agent_config_manager)
            
            logger.info("Agent pools initialized successfully")
            
        except ImportError as e:
            logger.warning(f"Agent configuration system not available: {e}")
            self.agent_config_manager = None
            self.agent_pool_manager = None

    def _initialize_phase_configs(self) -> Dict[WorkflowPhase, Dict[str, Any]]:
        """Initialize configuration for each workflow phase"""
        return {
            WorkflowPhase.INTAKE: {
                'requires_human_approval': False,
                'estimated_duration': 300,  # 5 minutes
                'context': {'focus': 'document_processing'},
                'parallel_execution': True
            },
            WorkflowPhase.OUTLINE: {
                'requires_human_approval': True,
                'estimated_duration': 600,  # 10 minutes
                'context': {'focus': 'case_analysis'},
                'parallel_execution': False
            },
            WorkflowPhase.RESEARCH: {
                'requires_human_approval': False,
                'estimated_duration': 1800,  # 30 minutes
                'context': {'focus': 'legal_research'},
                'parallel_execution': True
            },
            WorkflowPhase.DRAFTING: {
                'requires_human_approval': True,
                'estimated_duration': 2400,  # 40 minutes
                'context': {'focus': 'content_generation'},
                'parallel_execution': True
            },
            WorkflowPhase.LEGAL_REVIEW: {
                'requires_human_approval': True,
                'estimated_duration': 900,  # 15 minutes
                'context': {'focus': 'compliance_review'},
                'parallel_execution': False
            },
            WorkflowPhase.EDITING: {
                'requires_human_approval': False,
                'estimated_duration': 600,  # 10 minutes
                'context': {'focus': 'content_refinement'},
                'parallel_execution': False
            },
            WorkflowPhase.ORCHESTRATION: {
                'requires_human_approval': True,
                'estimated_duration': 300,  # 5 minutes
                'context': {'focus': 'final_assembly'},
                'parallel_execution': False
            }
        }

    async def schedule_task(self, task_type: str, requirements: Dict[str, Any], 
                          session_id: str) -> Dict[str, Any]:
        """Schedule a task with intelligent agent assignment"""
        try:
            # Use agent pool manager if available
            if self.agent_pool_manager:
                agent = await self.agent_pool_manager.select_best_agent(
                    task_type, requirements
                )
                if agent:
                    logger.info(f"Assigned specialist agent {agent.name} for task {task_type}")
                    return await self._execute_task_with_agent(
                        task_type, requirements, agent, session_id
                    )
            
            # Fallback to original agent registry
            agent_class = self.agent_registry.get(task_type)
            if not agent_class:
                raise ValueError(f"No agent available for task type: {task_type}")
            
            agent = agent_class()
            task_id = f"{task_type}_{int(time.time())}"
            
            logger.info(f"Scheduling task {task_id} with agent {agent.__class__.__name__}")
            
            # Execute task
            result = await agent.execute(requirements)
            
            # Update workflow state
            if hasattr(self, 'workflow_manager'):
                await self.workflow_manager.update_state(session_id)
            
            return {
                'task_id': task_id,
                'status': 'completed',
                'result': result,
                'agent': agent.__class__.__name__
            }
            
        except Exception as e:
            logger.error(f"Task scheduling failed: {e}")
            return {
                'task_id': f"failed_{int(time.time())}",
                'status': 'failed',
                'error': str(e)
            }

    async def _execute_task_with_agent(self, task_type: str, requirements: Dict[str, Any], 
                                     agent, session_id: str) -> Dict[str, Any]:
        """Execute a task with a specific agent from the agent pool"""
        try:
            # Create a workflow task for the agent
            task = WorkflowTask(
                id=f"{task_type}_{int(datetime.now().timestamp())}",
                phase=WorkflowPhase.INTAKE,  # Default phase
                agent_type=agent.agent_type,
                description=f"Execute {task_type} task",
                priority=TaskPriority.NORMAL,
                input_data=requirements,
                requires_human_approval=False
            )
            
            # Get workflow state for the session
            workflow_state = self.active_workflows.get(session_id)
            if not workflow_state:
                # Create a minimal workflow state if none exists
                workflow_state = WorkflowState(
                    session_id=session_id,
                    case_name="ad_hoc_task",
                    current_phase=WorkflowPhase.INTAKE,
                    overall_status=PhaseStatus.IN_PROGRESS
                )
                self.active_workflows[session_id] = workflow_state
            
            # Prepare task context
            task_context = self._prepare_task_context(task, workflow_state)
            
            # Execute the task using the agent
            result = await agent.execute_task(task, task_context)
            
            # Process and return result
            return {
                'task_id': task.id,
                'status': 'completed',
                'result': result,
                'agent': agent.name,
                'fitness_score': agent.fitness_score
            }
            
        except Exception as e:
            logger.error(f"Task execution failed with agent {agent.name}: {e}")
            return {
                'task_id': f"failed_{int(datetime.now().timestamp())}",
                'status': 'failed',
                'error': str(e),
                'agent': agent.name
            }

    def _prepare_task_context(self, task: WorkflowTask, workflow_state: WorkflowState) -> Dict[str, Any]:
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

    def _get_previous_task_results(self, task: WorkflowTask, workflow_state: WorkflowState) -> Dict[str, Any]:
        """Get results from previous tasks that this task depends on"""
        results = {}
        for dep_task_id in task.depends_on:
            if dep_task_id in workflow_state.tasks:
                dep_task = workflow_state.tasks[dep_task_id]
                if dep_task.status == PhaseStatus.COMPLETED:
                    results[dep_task_id] = dep_task.output_data
        return results

    async def start_workflow(self, case_name: str, session_id: str, input_documents: List[str],
                           initial_context: Optional[Dict[str, Any]] = None) -> str:
        """Initialize and start a new workflow"""
        
        if initial_context is None:
            initial_context = {}
        
        logger.info(f"Starting new workflow for case: {case_name}, session: {session_id}")
        
        # Create workflow state
        workflow_state = WorkflowState(
            session_id,
            case_name,
            WorkflowPhase.INTAKE,
            PhaseStatus.PENDING
        )
        workflow_state.input_documents = input_documents
        workflow_state.global_context = initial_context or {}
        
        # Initialize phase statuses
        for phase in WorkflowPhase:
            workflow_state.phases[phase] = PhaseStatus.PENDING
        workflow_state.phases[WorkflowPhase.INTAKE] = PhaseStatus.IN_PROGRESS
        
        # Generate initial task plan
        tasks = await self._generate_task_plan(workflow_state)
        for task in tasks:
            workflow_state.tasks[task.id] = task
        
        # Save initial state
        await self.state_manager.save_state(workflow_state)
        self.active_workflows[session_id] = workflow_state
        
        # Emit workflow started event
        await self.event_bus.emit('workflow_started', {
            'session_id': session_id,
            'case_name': case_name,
            'initial_tasks': len(tasks)
        })
        
        # Start execution in background
        asyncio.create_task(self._execute_workflow(session_id))
        
        return session_id

    async def _generate_task_plan(self, workflow_state: WorkflowState) -> List[WorkflowTask]:
        """Generate the initial task plan for the workflow"""
        tasks = []
        
        # Start with INTAKE phase tasks
        intake_tasks = await self._generate_phase_tasks(WorkflowPhase.INTAKE, workflow_state)
        tasks.extend(intake_tasks)
        
        return tasks

    async def _generate_phase_tasks(self, phase: WorkflowPhase, workflow_state: WorkflowState) -> List[WorkflowTask]:
        """Generate tasks for a specific workflow phase"""
        tasks = []
        
        if phase == WorkflowPhase.INTAKE:
            # Document ingestion and processing
            for i, doc in enumerate(workflow_state.input_documents):
                task = WorkflowTask(
                    id=f"intake_{i}_{uuid.uuid4().hex[:8]}",
                    phase=phase,
                    agent_type="ReaderBot",
                    description=f"Process document: {Path(doc).name}",
                    priority=TaskPriority.HIGH,
                    input_data={'document_path': doc},
                    requires_human_approval=False
                )
                tasks.append(task)
        
        return tasks

    async def _execute_workflow(self, session_id: str):
        """Main workflow execution loop"""
        workflow_state = self.active_workflows.get(session_id)
        if not workflow_state:
            logger.error(f"Workflow state not found for session: {session_id}")
            return
        
        try:
            logger.info(f"Starting workflow execution for session: {session_id}")
            
            while not self._is_workflow_complete(workflow_state):
                # Check for human approval requirements
                if workflow_state.human_feedback_required:
                    await self._wait_for_human_input(workflow_state)
                    continue
                
                # Get ready tasks for current phase
                ready_tasks = [
                    task for task in workflow_state.tasks.values()
                    if task.status == PhaseStatus.PENDING and task.phase == workflow_state.current_phase
                ]
                
                if ready_tasks:
                    await self._execute_tasks_batch(ready_tasks, workflow_state)
                    await self._update_workflow_progress(workflow_state)
                
                # Check for phase transitions
                await self._check_phase_transitions(workflow_state)
                
                # Small delay to prevent busy waiting
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Workflow execution failed for session {session_id}: {e}")
            workflow_state.overall_status = PhaseStatus.FAILED
            await self.state_manager.save_state(workflow_state)

    async def _execute_tasks_batch(self, tasks: List[WorkflowTask], workflow_state: WorkflowState):
        """Execute a batch of tasks concurrently"""
        logger.info(f"Executing batch of {len(tasks)} tasks for session {workflow_state.session_id}")
        
        # Group tasks by agent type for efficient resource usage
        agent_groups = {}
        for task in tasks:
            if task.agent_type not in agent_groups:
                agent_groups[task.agent_type] = []
            agent_groups[task.agent_type].append(task)
        
        # Execute each agent group sequentially
        for agent_type, agent_tasks in agent_groups.items():
            try:
                await self._execute_agent_tasks(agent_type, agent_tasks, workflow_state)
            except Exception as e:
                await self.error_handler.handle_agent_error(agent_type, e, workflow_state)

    async def _execute_agent_tasks(self, agent_type: str, tasks: List[WorkflowTask], 
                                 workflow_state: WorkflowState):
        """Execute tasks for a specific agent type"""
        agent = await self.agent_registry.get_agent(agent_type)
        
        for task in tasks:
            try:
                # Update task status
                task.status = PhaseStatus.IN_PROGRESS
                task.started_at = datetime.now()
                task.assigned_agent = agent.agent_type
                
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
                workflow_state.completed_tasks.append(task.id)
                
                logger.info(f"Completed task {task.id} in {task.actual_duration}s")
                
            except Exception as e:
                await self.error_handler.handle_task_error(task, e, workflow_state)
            finally:
                await self.agent_registry.release_agent(agent)

    async def _process_task_result(self, task: WorkflowTask, result: Any, workflow_state: WorkflowState):
        """Process the result of a completed task"""
        task.output_data = result
        
        # Update knowledge graph if applicable
        if hasattr(result, 'entities') and result.entities:
            try:
                await self.knowledge_graph.add_entities(result.entities)
            except Exception as e:
                logger.warning(f"Failed to update knowledge graph: {e}")
        
        # Update global context if result contains context updates
        if hasattr(result, 'context_updates') and result.context_updates:
            try:
                workflow_state.global_context.update(result.context_updates)
            except Exception as e:
                logger.warning(f"Failed to update global context: {e}")
        
        # Save state after each task completion
        await self.state_manager.save_state(workflow_state)
        
        # Trigger dependent tasks
        await self._trigger_dependent_tasks(task, workflow_state)

    async def _trigger_dependent_tasks(self, completed_task: WorkflowTask, workflow_state: WorkflowState):
        """Check and trigger tasks that depend on the completed task"""
        for task in workflow_state.tasks.values():
            if (completed_task.id in task.depends_on and 
                task.status == PhaseStatus.PENDING and
                all(dep_id in workflow_state.completed_tasks for dep_id in task.depends_on)):
                
                # All dependencies are satisfied, task can be scheduled
                task.status = PhaseStatus.PENDING
                logger.info(f"Task {task.id} dependencies satisfied, ready for execution")

    async def _check_phase_transitions(self, workflow_state: WorkflowState):
        """Check if current phase is complete and transition to next phase"""
        current_phase = workflow_state.current_phase
        phase_tasks = [
            task for task in workflow_state.tasks.values()
            if task.phase == current_phase
        ]
        
        # Check if all tasks in current phase are complete
        completed_tasks = [task for task in phase_tasks if task.status == PhaseStatus.COMPLETED]
        failed_tasks = [task for task in phase_tasks if task.status == PhaseStatus.FAILED]
        
        if len(completed_tasks) + len(failed_tasks) == len(phase_tasks):
            # Phase is complete
            workflow_state.phases[current_phase] = PhaseStatus.COMPLETED
            
            # Move to next phase
            next_phase = self._get_next_phase(current_phase)
            if next_phase:
                workflow_state.current_phase = next_phase
                workflow_state.phases[next_phase] = PhaseStatus.IN_PROGRESS
                
                # Generate tasks for next phase
                next_phase_tasks = await self._generate_phase_tasks(next_phase, workflow_state)
                for task in next_phase_tasks:
                    workflow_state.tasks[task.id] = task
                
                logger.info(f"Transitioned from {current_phase.value} to {next_phase.value}")
            else:
                # Workflow complete
                workflow_state.overall_status = PhaseStatus.COMPLETED
                logger.info(f"Workflow completed for session: {workflow_state.session_id}")

    def _get_next_phase(self, current_phase: WorkflowPhase) -> Optional[WorkflowPhase]:
        """Get the next phase in the workflow sequence"""
        phase_order = list(WorkflowPhase)
        try:
            current_index = phase_order.index(current_phase)
            if current_index < len(phase_order) - 1:
                return phase_order[current_index + 1]
        except ValueError:
            pass
        return None

    def _is_workflow_complete(self, workflow_state: WorkflowState) -> bool:
        """Check if the workflow is complete"""
        return workflow_state.overall_status in [PhaseStatus.COMPLETED, PhaseStatus.FAILED]

    async def _wait_for_human_input(self, workflow_state: WorkflowState):
        """Wait for human input/approval"""
        logger.info(f"Waiting for human input for session: {workflow_state.session_id}")
        # Implementation would depend on UI integration
        await asyncio.sleep(5)  # Placeholder

    async def _update_workflow_progress(self, workflow_state: WorkflowState):
        """Update workflow progress and emit events"""
        # Calculate progress metrics
        total_tasks = len(workflow_state.tasks)
        completed_tasks = len(workflow_state.completed_tasks)
        progress_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        # Emit progress update event
        await self.event_bus.emit('workflow_progress', {
            'session_id': workflow_state.session_id,
            'progress': progress_percentage,
            'current_phase': workflow_state.current_phase.value,
            'completed_tasks': completed_tasks,
            'total_tasks': total_tasks
        })

    async def get_workflow_status(self, session_id: str) -> Dict[str, Any]:
        """Get current status of a workflow"""
        workflow_state = self.active_workflows.get(session_id)
        if not workflow_state:
            # Try to load from persistent storage
            workflow_state = await self.state_manager.load_state(session_id)
        
        if not workflow_state:
            raise ValueError(f"Workflow not found: {session_id}")
        
        return {
            'session_id': session_id,
            'case_name': workflow_state.case_name,
            'current_phase': workflow_state.current_phase.value,
            'overall_status': workflow_state.overall_status.value,
            'progress': len(workflow_state.completed_tasks) / len(workflow_state.tasks) * 100 if workflow_state.tasks else 0,
            'phases': {phase.value: status.value for phase, status in workflow_state.phases.items()},
            'created_at': workflow_state.created_at.isoformat(),
            'updated_at': workflow_state.updated_at.isoformat()
        }

    async def shutdown(self):
        """Gracefully shutdown the maestro"""
        logger.info("Shutting down Enhanced Maestro")
        await self.state_manager.close()
        await self.checkpoint_manager.close()