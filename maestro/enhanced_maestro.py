"""
Enhanced Maestro Orchestration Engine for LawyerFactory.
Coordinates the 7-phase workflow with state management, agent coordination, and recovery.
"""

import asyncio
import logging
import uuid
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
        
        # Phase configurations
        self.phase_configs = self._initialize_phase_configs()
        
        # Active workflows tracking
        self.active_workflows: Dict[str, WorkflowState] = {}

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
        suitable_agents = self.agent_registry.get_agents_for_phase(phase)
        
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
            
            # Entity extraction task
            if workflow_state.input_documents:
                task = WorkflowTask(
                    id=f"extraction_{uuid.uuid4().hex[:8]}",
                    phase=phase,
                    agent_type="ParalegalBot",
                    description="Extract entities and relationships",
                    priority=TaskPriority.NORMAL,
                    depends_on=[t.id for t in tasks],  # Depends on document processing
                    requires_human_approval=False
                )
                tasks.append(task)
                
            # AI Case Classification task - runs in parallel with traditional processing
            ai_classification_task = WorkflowTask(
                id=f"ai_case_classification_{uuid.uuid4().hex[:8]}",
                phase=phase,
                agent_type="AIDocumentAgent",
                description="AI case classification and analysis",
                priority=TaskPriority.NORMAL,
                input_data={'task_type': 'ai_case_classification'},
                requires_human_approval=False
            )
            tasks.append(ai_classification_task)
        
        elif phase == WorkflowPhase.OUTLINE:
            task = WorkflowTask(
                id=f"outline_{uuid.uuid4().hex[:8]}",
                phase=phase,
                agent_type="OutlinerBot",
                description="Create case outline and legal theory",
                priority=TaskPriority.HIGH,
                requires_human_approval=True
            )
            tasks.append(task)
        
        elif phase == WorkflowPhase.RESEARCH:
            # Legal research tasks
            research_areas = ["case_law", "statutes", "regulations"]
            for area in research_areas:
                task = WorkflowTask(
                    id=f"research_{area}_{uuid.uuid4().hex[:8]}",
                    phase=phase,
                    agent_type="ResearchBot",
                    description=f"Research {area.replace('_', ' ')}",
                    priority=TaskPriority.NORMAL,
                    input_data={'research_area': area}
                )
                tasks.append(task)
        
        elif phase == WorkflowPhase.DRAFTING:
            # Professional complaint drafting using templates and AI modules
            professional_complaint_task = WorkflowTask(
                id=f"professional_complaint_{uuid.uuid4().hex[:8]}",
                phase=phase,
                agent_type="WriterBot",
                description="Generate professional complaint using Jinja2 templates and AI modules",
                priority=TaskPriority.HIGH,
                input_data={
                    'content_type': 'complaint',
                    'use_professional_templates': True,
                    'ai_synthesis': True
                },
                requires_human_approval=False
            )
            tasks.append(professional_complaint_task)
            
            # Professional motion drafting
            professional_motion_task = WorkflowTask(
                id=f"professional_motion_{uuid.uuid4().hex[:8]}",
                phase=phase,
                agent_type="WriterBot",
                description="Generate professional motion using legal theory mapping",
                priority=TaskPriority.NORMAL,
                input_data={
                    'content_type': 'motion',
                    'motion_type': 'Motion for Summary Judgment',
                    'use_professional_templates': True
                },
                depends_on=[professional_complaint_task.id],
                requires_human_approval=False
            )
            tasks.append(professional_motion_task)
            
            # AI Document Generation tasks - PDF forms (parallel track)
            ai_form_selection_task = WorkflowTask(
                id=f"ai_form_selection_{uuid.uuid4().hex[:8]}",
                phase=phase,
                agent_type="AIDocumentAgent",
                description="AI-powered PDF form processing and selection",
                priority=TaskPriority.HIGH,
                input_data={'task_type': 'pdf_form_processing'},
                requires_human_approval=False
            )
            tasks.append(ai_form_selection_task)
            
            ai_field_mapping_task = WorkflowTask(
                id=f"ai_field_mapping_{uuid.uuid4().hex[:8]}",
                phase=phase,
                agent_type="AIDocumentAgent",
                description="Automated field mapping for court forms",
                priority=TaskPriority.NORMAL,
                input_data={'task_type': 'automated_field_mapping'},
                depends_on=[ai_form_selection_task.id],
                requires_human_approval=False
            )
            tasks.append(ai_field_mapping_task)
            
            ai_form_generation_task = WorkflowTask(
                id=f"ai_form_generation_{uuid.uuid4().hex[:8]}",
                phase=phase,
                agent_type="AIDocumentAgent",
                description="Generate filled court forms using AI",
                priority=TaskPriority.HIGH,
                input_data={'task_type': 'court_form_generation'},
                depends_on=[ai_field_mapping_task.id],
                requires_human_approval=True  # Forms should be reviewed before filing
            )
            tasks.append(ai_form_generation_task)
        
        elif phase == WorkflowPhase.LEGAL_REVIEW:
            # Professional compliance review using AI modules
            compliance_review_task = WorkflowTask(
                id=f"compliance_review_{uuid.uuid4().hex[:8]}",
                phase=phase,
                agent_type="LegalEditorBot",
                description="Rule 12(b)(6) compliance and citation validation",
                priority=TaskPriority.CRITICAL,
                input_data={
                    'review_type': 'compliance',
                    'check_rule_12b6': True,
                    'validate_citations': True
                },
                requires_human_approval=True
            )
            tasks.append(compliance_review_task)
            
            # Professional brief structure review
            brief_structure_task = WorkflowTask(
                id=f"brief_structure_{uuid.uuid4().hex[:8]}",
                phase=phase,
                agent_type="LegalEditorBot",
                description="Professional legal brief structure and formatting review",
                priority=TaskPriority.HIGH,
                input_data={
                    'review_type': 'legal_brief',
                    'check_professional_standards': True
                },
                depends_on=[compliance_review_task.id],
                requires_human_approval=False
            )
            tasks.append(brief_structure_task)
        
        elif phase == WorkflowPhase.EDITING:
            # Comprehensive professional review combining all checks
            comprehensive_review_task = WorkflowTask(
                id=f"comprehensive_review_{uuid.uuid4().hex[:8]}",
                phase=phase,
                agent_type="LegalEditorBot",
                description="Comprehensive professional review and final formatting",
                priority=TaskPriority.HIGH,
                input_data={
                    'review_type': 'comprehensive',
                    'final_review': True
                },
                requires_human_approval=False
            )
            tasks.append(comprehensive_review_task)
            
            # Final formatting and citation review
            final_format_task = WorkflowTask(
                id=f"final_format_{uuid.uuid4().hex[:8]}",
                phase=phase,
                agent_type="LegalEditorBot",
                description="Final formatting and citation review for court filing",
                priority=TaskPriority.NORMAL,
                input_data={
                    'review_type': 'formatting',
                    'prepare_for_filing': True
                },
                depends_on=[comprehensive_review_task.id],
                requires_human_approval=False
            )
            tasks.append(final_format_task)
        
        elif phase == WorkflowPhase.ORCHESTRATION:
            task = WorkflowTask(
                id=f"orchestration_{uuid.uuid4().hex[:8]}",
                phase=phase,
                agent_type="MaestroBot",
                description="Final assembly and output generation",
                priority=TaskPriority.CRITICAL,
                requires_human_approval=True
            )
            tasks.append(task)
        
        return tasks

    async def _execute_workflow(self, session_id: str):
        """Main workflow execution loop"""
        try:
            workflow_state = self.active_workflows.get(session_id)
            if not workflow_state:
                workflow_state = await self.state_manager.load_state(session_id)
                self.active_workflows[session_id] = workflow_state
            
            logger.info(f"Starting workflow execution for session {session_id}")
            
            while not self._is_workflow_complete(workflow_state):
                try:
                    # Get next executable tasks
                    ready_tasks = self.scheduler.get_ready_tasks(workflow_state)
                    
                    if not ready_tasks:
                        if workflow_state.human_feedback_required:
                            logger.info(f"Workflow {session_id} waiting for human input")
                            await self._wait_for_human_input(workflow_state)
                            continue
                        else:
                            logger.info(f"No more tasks ready for execution in workflow {session_id}")
                            break
                    
                    # Execute tasks concurrently (where possible)
                    await self._execute_tasks_batch(ready_tasks, workflow_state)
                    
                    # Update workflow state
                    await self._update_workflow_progress(workflow_state)
                    
                    # Create checkpoint
                    await self.checkpoint_manager.create_checkpoint(workflow_state)
                    
                    # Check for phase transitions
                    await self._check_phase_transitions(workflow_state)
                    
                    # Save updated state
                    await self.state_manager.save_state(workflow_state)
                    
                except Exception as e:
                    await self.error_handler.handle_workflow_error(workflow_state, e)
            
            # Mark workflow as completed
            workflow_state.overall_status = PhaseStatus.COMPLETED
            await self.state_manager.save_state(workflow_state)
            
            await self.event_bus.emit('workflow_completed', {
                'session_id': session_id,
                'case_name': workflow_state.case_name,
                'completion_time': datetime.now().isoformat()
            })
            
            logger.info(f"Workflow {session_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Critical error in workflow {session_id}: {e}")
            await self.event_bus.emit('workflow_failed', {
                'session_id': session_id,
                'error': str(e)
            })

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
        for dependency_id in task.depends_on:
            if dependency_id in workflow_state.tasks:
                dep_task = workflow_state.tasks[dependency_id]
                if dep_task.status == PhaseStatus.COMPLETED:
                    results[dependency_id] = dep_task.output_data
        return results

    async def _process_task_result(self, task: WorkflowTask, result: Any, workflow_state: WorkflowState):
        """Process the result of a completed task"""
        # Store task output
        task.output_data = result if isinstance(result, dict) else {'result': result}
        
        # Update knowledge graph if applicable
        if isinstance(result, dict):
            if 'entities' in result:
                for entity in result['entities']:
                    try:
                        await self.knowledge_graph.add_entity(entity)
                    except Exception as e:
                        logger.warning(f"Failed to add entity to knowledge graph: {e}")
            
            if 'relationships' in result:
                for relationship in result['relationships']:
                    try:
                        await self.knowledge_graph.add_relationship(relationship)
                    except Exception as e:
                        logger.warning(f"Failed to add relationship to knowledge graph: {e}")
            
            # Update global context
            if 'context_updates' in result:
                workflow_state.global_context.update(result['context_updates'])
        
        # Trigger dependent tasks
        await self._trigger_dependent_tasks(task, workflow_state)
        
        # Emit event
        await self.event_bus.emit('task_completed', {
            'task_id': task.id,
            'session_id': workflow_state.session_id,
            'phase': task.phase.value,
            'agent_type': task.agent_type,
            'result': task.output_data
        })

    async def _trigger_dependent_tasks(self, completed_task: WorkflowTask, workflow_state: WorkflowState):
        """Trigger tasks that depend on the completed task"""
        for task in workflow_state.tasks.values():
            if completed_task.id in task.depends_on and task.status == PhaseStatus.PENDING:
                # Check if all dependencies are now satisfied
                dependencies_met = all(
                    dep_id in workflow_state.tasks and
                    workflow_state.tasks[dep_id].status == PhaseStatus.COMPLETED
                    for dep_id in task.depends_on
                )
                if dependencies_met:
                    logger.info(f"Task {task.id} is now ready to execute")

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
                logger.info(f"Phase {current_phase.value} requires human approval")
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
                
                logger.info(f"Transitioned from {current_phase.value} to {next_phase.value}")
                
                await self.event_bus.emit('phase_transition', {
                    'session_id': workflow_state.session_id,
                    'from_phase': current_phase.value,
                    'to_phase': next_phase.value,
                    'new_tasks': len(next_phase_tasks)
                })

    def _requires_human_approval(self, phase: WorkflowPhase) -> bool:
        """Check if a phase requires human approval before proceeding"""
        return self.phase_configs.get(phase, {}).get('requires_human_approval', False)

    def _get_next_phase(self, current_phase: WorkflowPhase) -> Optional[WorkflowPhase]:
        """Get the next phase in the workflow sequence"""
        phases = list(WorkflowPhase)
        try:
            current_index = phases.index(current_phase)
            if current_index < len(phases) - 1:
                return phases[current_index + 1]
        except ValueError:
            pass
        return None

    def _is_workflow_complete(self, workflow_state: WorkflowState) -> bool:
        """Check if the workflow is complete"""
        return (workflow_state.current_phase == WorkflowPhase.ORCHESTRATION and 
                workflow_state.phases[WorkflowPhase.ORCHESTRATION] == PhaseStatus.COMPLETED)

    async def _wait_for_human_input(self, workflow_state: WorkflowState):
        """Wait for human input before proceeding"""
        # In a real implementation, this would wait for user interface input
        # For now, we'll just wait a short time and continue
        await asyncio.sleep(5)
        workflow_state.human_feedback_required = False

    async def _update_workflow_progress(self, workflow_state: WorkflowState):
        """Update overall workflow progress metrics"""
        workflow_state.updated_at = datetime.now()
        
        # Calculate completion percentage
        total_tasks = len(workflow_state.tasks)
        completed_tasks = len(workflow_state.completed_tasks)
        
        if total_tasks > 0:
            progress = (completed_tasks / total_tasks) * 100
            workflow_state.global_context['progress_percentage'] = progress

    def _generate_session_id(self) -> str:
        """Generate a unique session ID"""
        return f"session_{uuid.uuid4().hex[:12]}"

    async def get_workflow_status(self, session_id: str) -> Dict[str, Any]:
        """Get the current status of a workflow"""
        if session_id in self.active_workflows:
            workflow_state = self.active_workflows[session_id]
        else:
            workflow_state = await self.state_manager.load_state(session_id)
        
        return {
            'session_id': workflow_state.session_id,
            'case_name': workflow_state.case_name,
            'current_phase': workflow_state.current_phase.value,
            'overall_status': workflow_state.overall_status.value,
            'progress_percentage': workflow_state.global_context.get('progress_percentage', 0),
            'tasks_completed': len(workflow_state.completed_tasks),
            'tasks_total': len(workflow_state.tasks),
            'human_feedback_required': workflow_state.human_feedback_required,
            'pending_approvals': workflow_state.pending_approvals,
            'created_at': workflow_state.created_at.isoformat(),
            'updated_at': workflow_state.updated_at.isoformat()
        }

    async def list_workflows(self) -> List[Dict[str, Any]]:
        """List all workflows"""
        return await self.state_manager.list_sessions()

    async def shutdown(self):
        """Shutdown the maestro and clean up resources"""
        logger.info("Shutting down Enhanced Maestro")
        await self.agent_registry.shutdown_all_agents()
        self.active_workflows.clear()