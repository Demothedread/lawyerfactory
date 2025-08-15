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
import sys
import os

# Add project root to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .agent_registry import AgentRegistry, TaskScheduler
from .checkpoint_manager import CheckpointManager
from .error_handling import WorkflowErrorHandler
from .event_system import EventBus
from .workflow_models import (PhaseStatus, TaskPriority, WorkflowPhase,
                              WorkflowState, WorkflowStateManager,
                              WorkflowTask)

# Import enhanced draft processing capabilities
try:
    from enhanced_draft_processor import EnhancedDraftProcessor
    ENHANCED_PROCESSING_AVAILABLE = True
except ImportError:
    logger.warning("Enhanced draft processor not available")
    ENHANCED_PROCESSING_AVAILABLE = False

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
        
        # Initialize enhanced draft processor if available
        self.enhanced_draft_processor = None
        if ENHANCED_PROCESSING_AVAILABLE:
            try:
                self.enhanced_draft_processor = EnhancedDraftProcessor(
                    knowledge_graph_path=str(self.storage_path / "enhanced_kg.db")
                )
                logger.info("Enhanced draft processor initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize enhanced draft processor: {e}")
        
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

    async def process_draft_documents(self, draft_documents: List[Dict[str, Any]], session_id: str) -> Dict[str, Any]:
        """Process draft documents with priority before general evidence processing"""
        try:
            logger.info(f"Processing {len(draft_documents)} draft documents for session {session_id}")
            
            fact_drafts = [doc for doc in draft_documents if doc.get('draft_type') == 'fact_statement']
            case_drafts = [doc for doc in draft_documents if doc.get('draft_type') == 'case_complaint']
            
            processing_results = {
                'fact_drafts_processed': len(fact_drafts),
                'case_drafts_processed': len(case_drafts),
                'foundational_entities': [],
                'high_confidence_facts': [],
                'draft_analysis': {}
            }
            
            # Process fact statement drafts first (highest priority)
            if fact_drafts:
                fact_result = await self._process_fact_statement_drafts(fact_drafts, session_id)
                processing_results['fact_analysis'] = fact_result
                processing_results['foundational_entities'].extend(fact_result.get('entities', []))
                processing_results['high_confidence_facts'].extend(fact_result.get('facts', []))
            
            # Process case/complaint drafts second
            if case_drafts:
                case_result = await self._process_case_complaint_drafts(case_drafts, session_id)
                processing_results['case_analysis'] = case_result
                processing_results['foundational_entities'].extend(case_result.get('entities', []))
                processing_results['high_confidence_facts'].extend(case_result.get('legal_issues', []))
            
            # Update workflow state with foundational information
            if session_id in self.active_workflows:
                workflow_state = self.active_workflows[session_id]
                workflow_state.global_context.update({
                    'foundational_entities': processing_results['foundational_entities'],
                    'high_confidence_facts': processing_results['high_confidence_facts'],
                    'draft_processing_complete': True
                })
            
            logger.info(f"Draft document processing complete: {processing_results['fact_drafts_processed']} fact drafts, {processing_results['case_drafts_processed']} case drafts")
            return processing_results
            
        except Exception as e:
            logger.error(f"Draft document processing failed: {e}")
            return {"error": str(e), "draft_processing_complete": False}

    async def _process_fact_statement_drafts(self, fact_drafts: List[Dict[str, Any]], session_id: str) -> Dict[str, Any]:
        """Process fact statement drafts with aggregation and knowledge graph integration"""
        try:
            # Aggregate multiple fact drafts if present
            aggregated_facts = []
            entities_extracted = []
            
            for draft in fact_drafts:
                content = draft.get('content', '')
                if content:
                    # Extract structured facts and entities
                    facts = await self._extract_legal_facts(content, draft_type='fact_statement')
                    entities = await self._extract_legal_entities(content, confidence_boost=0.2)
                    
                    aggregated_facts.extend(facts)
                    entities_extracted.extend(entities)
            
            # Deduplicate and rank facts by confidence
            unique_facts = self._deduplicate_facts(aggregated_facts)
            unique_entities = self._deduplicate_entities(entities_extracted)
            
            # Store in knowledge graph with high confidence
            if self.knowledge_graph:
                kg_storage_result = await self._store_foundational_knowledge(
                    unique_entities, unique_facts, source_type='fact_statement_draft'
                )
            else:
                kg_storage_result = {"status": "knowledge_graph_unavailable"}
            
            return {
                'facts': unique_facts,
                'entities': unique_entities,
                'confidence_level': 'high',
                'source_type': 'fact_statement_draft',
                'knowledge_graph_storage': kg_storage_result
            }
            
        except Exception as e:
            logger.error(f"Fact statement processing failed: {e}")
            return {"error": str(e)}

    async def _process_case_complaint_drafts(self, case_drafts: List[Dict[str, Any]], session_id: str) -> Dict[str, Any]:
        """Process case/complaint drafts with legal issue extraction"""
        try:
            # Aggregate multiple case drafts if present
            legal_issues = []
            entities_extracted = []
            claims_identified = []
            
            for draft in case_drafts:
                content = draft.get('content', '')
                if content:
                    # Extract legal issues and claims
                    issues = await self._extract_legal_issues(content)
                    claims = await self._extract_legal_claims(content)
                    entities = await self._extract_legal_entities(content, confidence_boost=0.2)
                    
                    legal_issues.extend(issues)
                    claims_identified.extend(claims)
                    entities_extracted.extend(entities)
            
            # Deduplicate and categorize
            unique_issues = self._deduplicate_legal_issues(legal_issues)
            unique_claims = self._deduplicate_claims(claims_identified)
            unique_entities = self._deduplicate_entities(entities_extracted)
            
            # Store in knowledge graph
            if self.knowledge_graph:
                kg_storage_result = await self._store_foundational_knowledge(
                    unique_entities, unique_issues + unique_claims, source_type='case_complaint_draft'
                )
            else:
                kg_storage_result = {"status": "knowledge_graph_unavailable"}
            
            return {
                'legal_issues': unique_issues,
                'claims': unique_claims,
                'entities': unique_entities,
                'confidence_level': 'high',
                'source_type': 'case_complaint_draft',
                'knowledge_graph_storage': kg_storage_result
            }
            
        except Exception as e:
            logger.error(f"Case complaint processing failed: {e}")
            return {"error": str(e)}

    async def _extract_legal_facts(self, content: str, draft_type: str) -> List[Dict[str, Any]]:
        """Extract structured legal facts from draft content"""
        # This would use NLP/LLM processing to extract facts
        # For now, return a simplified extraction
        facts = []
        sentences = content.split('.')
        for i, sentence in enumerate(sentences[:10]):  # Process first 10 sentences
            if len(sentence.strip()) > 20:  # Only meaningful sentences
                facts.append({
                    'fact_id': f"{draft_type}_fact_{i}",
                    'content': sentence.strip(),
                    'confidence': 0.9,
                    'source_type': draft_type,
                    'foundational': True
                })
        return facts

    async def _extract_legal_entities(self, content: str, confidence_boost: float = 0.0) -> List[Dict[str, Any]]:
        """Extract legal entities with enhanced confidence for draft documents"""
        # Simplified entity extraction - in production would use NER
        entities = []
        
        # Basic pattern matching for legal entities
        import re
        
        # Find potential parties (capitalized words/phrases)
        party_pattern = r'\b[A-Z][a-zA-Z\s]+(?:Inc\.|Corp\.|LLC|Ltd\.)\b'
        parties = re.findall(party_pattern, content)
        
        for party in parties[:5]:  # Limit to first 5
            entities.append({
                'type': 'PARTY',
                'name': party.strip(),
                'confidence': 0.8 + confidence_boost,
                'foundational': True
            })
        
        # Find dates
        date_pattern = r'\b\d{1,2}/\d{1,2}/\d{4}\b|\b\w+ \d{1,2}, \d{4}\b'
        dates = re.findall(date_pattern, content)
        
        for date in dates[:3]:  # Limit to first 3
            entities.append({
                'type': 'DATE',
                'name': date,
                'confidence': 0.9 + confidence_boost,
                'foundational': True
            })
        
        return entities

    async def _extract_legal_issues(self, content: str) -> List[Dict[str, Any]]:
        """Extract legal issues from case/complaint drafts"""
        issues = []
        # Simplified extraction - look for common legal terms
        legal_terms = ['breach of contract', 'negligence', 'fraud', 'defamation', 'copyright infringement']
        
        content_lower = content.lower()
        for term in legal_terms:
            if term in content_lower:
                issues.append({
                    'issue_type': term.replace(' ', '_').upper(),
                    'description': term,
                    'confidence': 0.8,
                    'foundational': True
                })
        
        return issues

    async def _extract_legal_claims(self, content: str) -> List[Dict[str, Any]]:
        """Extract legal claims from complaint drafts"""
        claims = []
        # Look for numbered claims or causes of action
        import re
        
        claim_pattern = r'(?:Claim|Count|Cause of Action)\s+(\d+|I+|One|Two|Three)'
        matches = re.findall(claim_pattern, content, re.IGNORECASE)
        
        for i, match in enumerate(matches[:5]):  # Limit to 5 claims
            claims.append({
                'claim_id': f"claim_{i+1}",
                'claim_number': match,
                'confidence': 0.9,
                'foundational': True
            })
        
        return claims

    def _deduplicate_facts(self, facts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate facts based on content similarity"""
        unique_facts = []
        seen_content = set()
        
        for fact in facts:
            content = fact.get('content', '').lower().strip()
            if content and content not in seen_content:
                seen_content.add(content)
                unique_facts.append(fact)
        
        return unique_facts

    def _deduplicate_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate entities based on name and type"""
        unique_entities = []
        seen_entities = set()
        
        for entity in entities:
            key = (entity.get('type', ''), entity.get('name', '').lower())
            if key not in seen_entities:
                seen_entities.add(key)
                unique_entities.append(entity)
        
        return unique_entities

    def _deduplicate_legal_issues(self, issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate legal issues"""
        unique_issues = []
        seen_issues = set()
        
        for issue in issues:
            issue_type = issue.get('issue_type', '')
            if issue_type and issue_type not in seen_issues:
                seen_issues.add(issue_type)
                unique_issues.append(issue)
        
        return unique_issues

    def _deduplicate_claims(self, claims: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate claims"""
        unique_claims = []
        seen_claims = set()
        
        for claim in claims:
            claim_id = claim.get('claim_id', '')
            if claim_id and claim_id not in seen_claims:
                seen_claims.add(claim_id)
                unique_claims.append(claim)
        
        return unique_claims

    async def _store_foundational_knowledge(self, entities: List[Dict[str, Any]],
                                          facts: List[Dict[str, Any]], source_type: str) -> Dict[str, Any]:
        """Store foundational knowledge in the knowledge graph with high confidence"""
        try:
            if not self.knowledge_graph:
                return {"status": "no_knowledge_graph"}
            
            stored_entities = 0
            stored_facts = 0
            
            # Store entities
            for entity in entities:
                try:
                    # Add entity to knowledge graph (implementation depends on KG interface)
                    # This is a simplified version
                    stored_entities += 1
                except Exception as e:
                    logger.warning(f"Failed to store entity: {e}")
            
            # Store facts as observations or separate entities
            for fact in facts:
                try:
                    # Store fact in knowledge graph
                    stored_facts += 1
                except Exception as e:
                    logger.warning(f"Failed to store fact: {e}")
            
            return {
                "status": "success",
                "entities_stored": stored_entities,
                "facts_stored": stored_facts,
                "source_type": source_type
            }
            
        except Exception as e:
            logger.error(f"Knowledge graph storage failed: {e}")
            return {"status": "error", "error": str(e)}

    async def start_workflow(self, case_name: str, session_id: str, input_documents: List[str],
                           initial_context: Optional[Dict[str, Any]] = None) -> str:
        """Initialize and start a new workflow with draft document processing"""
        
        if initial_context is None:
            initial_context = {}
        
        logger.info(f"Starting new workflow for case: {case_name}, session: {session_id}")
        
        # Check for draft documents in initial context and process them first
        draft_documents = initial_context.get('draft_documents', [])
        if draft_documents:
            logger.info(f"Processing {len(draft_documents)} draft documents before workflow start")
            draft_results = await self.process_draft_documents(draft_documents, session_id)
            initial_context['draft_processing_results'] = draft_results
        
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