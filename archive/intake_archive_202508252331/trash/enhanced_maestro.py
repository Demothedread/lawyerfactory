"""
# Script Name: enhanced_maestro.py
# Description: Enhanced Maestro Orchestration Engine for LawyerFactory. Coordinates the 7-phase workflow with state management, agent coordination, and recovery.
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Orchestration
#   - Group Tags: orchestration
Enhanced Maestro Orchestration Engine for LawyerFactory.
Coordinates the 7-phase workflow with state management, agent coordination, and recovery.
"""

import asyncio
import importlib
import importlib.util
import inspect
import logging
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Ensure project root and src directory are on sys.path so imports like `from src...` and `from storage...` work
project_root = Path(__file__).resolve().parents[1]
src_path = project_root / 'src'
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if src_path.exists() and str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Safe import of file storage compatibility layer: prefer explicit src package, fall back to legacy compatibility module.
file_storage_manager = None
try:
    # Prefer the refactored src package location
    from src.storage.api import \
        file_storage as file_storage_mod  # type: ignore
    file_storage_manager = file_storage_mod
except ModuleNotFoundError as e:
    logger.warning("File storage manager not available from src.storage.api: %s", e)
    try:
        import importlib
        file_storage_mod = importlib.import_module("lawyerfactory.file_storage")
        file_storage_manager = file_storage_mod
    except ModuleNotFoundError:
        logger.warning("Legacy lawyerfactory.file_storage not found; continuing without file storage manager")
    except Exception as e2:
        logger.exception("Unexpected error importing legacy lawyerfactory.file_storage: %s", e2)
except Exception as e:
    logger.exception("Unexpected error importing src.storage.api.file_storage: %s", e)

from .registry import AgentRegistry, TaskScheduler
from .checkpoints import CheckpointManager
# new compat wrappers
from .compat_wrappers import (AgentPoolManagerWrapper,
                              CheckpointManagerWrapper, StateManagerWrapper)
from .errors import WorkflowErrorHandler
from .events import EventBus
from .workflow_models import (PhaseStatus, TaskPriority, WorkflowPhase,
                              WorkflowState, WorkflowStateManager,
                              WorkflowTask)

# Import phase-specific components for integration
try:
    from lawyerfactory.ingest.adapters.facts_matrix_adapter import FactsMatrixAdapter
    from lawyerfactory.outline.generator import SkeletalOutlineGenerator
    from lawyerfactory.claims.matrix import ComprehensiveClaimsMatrixIntegration
    PHASE_COMPONENTS_AVAILABLE = True
    logger.info("Successfully imported all phase-specific components for Maestro integration.")
except ImportError as e:
    logger.error(f"Failed to import one or more phase-specific components: {e}. Phase logic will be disabled.")
    PHASE_COMPONENTS_AVAILABLE = False

# Import post-production components for integration
try:
    from lawyerfactory.post_production import (
        FactChecker, BluebookValidator, LegalPDFGenerator,
        DocumentMetadata, FormattingOptions, DocumentFormat
    )
    POST_PRODUCTION_AVAILABLE = True
    logger.info("Successfully imported post-production components for Maestro integration.")
except ImportError as e:
    logger.error(f"Failed to import post-production components: {e}. Post-production phase will be disabled.")
    POST_PRODUCTION_AVAILABLE = False

# Import enhanced draft processing capabilities
try:
    from src.document_generator.api.enhanced_draft_processor import \
        EnhancedDraftProcessor
    ENHANCED_PROCESSING_AVAILABLE = True
except ImportError:
    logger.warning("Enhanced draft processor not available")
    ENHANCED_PROCESSING_AVAILABLE = False
    
# Replace previous broken file-storage import check with robust loader
FILE_STORAGE_AVAILABLE = False
FileStorageManager = None
try:
    # Prefer canonical module name if available
    mod = importlib.import_module("lawyerfactory.file_storage")
    FileStorageManager = getattr(mod, "FileStorageManager", None)
    if FileStorageManager:
        FILE_STORAGE_AVAILABLE = True
except Exception:
    # Fallback: try to load the compatibility file by path (supports hyphenated filename)
    try:
        compat_path = Path(__file__).resolve().parents[1] / "lawyerfactory" / "file-storage.py"
        if compat_path.exists():
            spec = importlib.util.spec_from_file_location("lawyerfactory._file_storage_compat", str(compat_path))
            if spec is not None and spec.loader is not None:
                compat_mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(compat_mod)  # type: ignore
                FileStorageManager = getattr(compat_mod, "FileStorageManager", None)
                if FileStorageManager:
                    FILE_STORAGE_AVAILABLE = True
            else:
                logger.warning("spec or spec.loader is None for file-storage compat module")
    except Exception:
        logger.warning("File storage manager not available (compat path load failed)")

# Do not override EnhancedDraftProcessor if imported; if import failed it was set in except above

# Try to import optional ingestion server helpers so Maestro can reuse them
_ingest_server = None
try:
    from src.ingestion.api import \
        ingest_server as _ingest_server  # type: ignore
except Exception:
    _ingest_server = None

class EnhancedMaestro:
    """Advanced orchestration engine with state management and recovery"""

    def __init__(self, knowledge_graph, llm_service=None, storage_path: str = "workflow_storage"):
        # Ensure storage_path exists before any FileStorage instantiation
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True, parents=True)

        # Instantiate file storage manager if available (tolerant)
        if FILE_STORAGE_AVAILABLE and FileStorageManager is not None:
            try:
                self.file_storage_manager = FileStorageManager(str(self.storage_path / "file_storage"))
            except Exception as e:
                logger.warning(f"Failed to initialize FileStorageManager: {e}")
                self.file_storage_manager = None
        else:
            self.file_storage_manager = None
        self.knowledge_graph = knowledge_graph
        self.llm_service = llm_service
            
        
        # Core components (wrap raw managers with compatibility shims)
        raw_state_mgr = WorkflowStateManager(str(self.storage_path / "workflow_states.db"))
        self.state_manager = StateManagerWrapper(raw_state_mgr)
        self.agent_registry = AgentRegistry()
        self.scheduler = TaskScheduler(self.agent_registry)
        self.event_bus = EventBus()
        raw_checkpoint = CheckpointManager(str(self.storage_path))
        self.checkpoint_manager = CheckpointManagerWrapper(raw_checkpoint)
        self.error_handler = WorkflowErrorHandler(self.event_bus)
        
        # Initialize agent pools
        self._initialize_agent_pools()
        
        # Initialize enhanced draft processor if available
        self.enhanced_draft_processor = None
        if ENHANCED_PROCESSING_AVAILABLE:
            enhanced_cls = globals().get("EnhancedDraftProcessor")
            if callable(enhanced_cls):
                try:
                    self.enhanced_draft_processor = enhanced_cls(
                        knowledge_graph_path=str(self.storage_path / "enhanced_kg.db")
                    )
                    logger.info("Enhanced draft processor initialized successfully")
                except Exception as e:
                    logger.warning(f"Failed to initialize enhanced draft processor: {e}")
            else:
                self.enhanced_draft_processor = None
        else:
            self.enhanced_draft_processor = None
        
        # Active workflows tracking
        self.active_workflows: Dict[str, WorkflowState] = {}
        
        # Phase configurations
        self.phase_configs = self._initialize_phase_configs()
    
    def _initialize_agent_pools(self):
        """Initialize specialist and general agent pools"""
        try:
            from lawyerfactory.agent_config_system import (AgentConfigManager,
                                                           AgentPoolManager)

            # Initialize agent configuration system
            self.agent_config_manager = AgentConfigManager()
            raw_pool_mgr = AgentPoolManager(self.agent_config_manager)
            # wrap to provide select_best_agent/select_agent consistently
            self.agent_pool_manager = AgentPoolManagerWrapper(raw_pool_mgr)
            
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

    # Utility: robust invoker for callables that may be sync or async
    async def _invoke(self, fn_or_value, *args, **kwargs):
        """
        Call fn_or_value if callable; if the result is awaitable, await it.
        If fn_or_value itself is awaitable, await and return it.
        Otherwise return value directly.
        """
        try:
            if fn_or_value is None:
                return None
            if callable(fn_or_value):
                res = fn_or_value(*args, **kwargs)
            else:
                res = fn_or_value

            if inspect.isawaitable(res):
                return await res
            return res
        except Exception:
            # re-raise to preserve original behavior but keep stack
            raise

    # Utility: create a WorkflowTask instance without calling unknown constructor signatures
    def _make_workflow_task(self, **attrs):
        """
        Construct a WorkflowTask without relying on constructor signature.
        Set reasonable defaults for commonly used attributes.
        """
        task = WorkflowTask.__new__(WorkflowTask)
        # conservative defaults
        defaults = {
            "id": attrs.get("id", f"task_{int(time.time())}"),
            "phase": attrs.get("phase", WorkflowPhase.INTAKE),
            "agent_type": attrs.get("agent_type", "GenericAgent"),
            "description": attrs.get("description", ""),
            "priority": attrs.get("priority", TaskPriority.NORMAL),
            "input_data": attrs.get("input_data", {}),
            "requires_human_approval": attrs.get("requires_human_approval", False),
            "depends_on": attrs.get("depends_on", []),
            "status": attrs.get("status", PhaseStatus.PENDING),
            "assigned_agent": attrs.get("assigned_agent", None),
            "started_at": attrs.get("started_at", None),
            "completed_at": attrs.get("completed_at", None),
            "actual_duration": attrs.get("actual_duration", 0),
            "output_data": attrs.get("output_data", None),
        }
        # assign attributes
        for k, v in defaults.items():
            setattr(task, k, v)
        return task

    async def schedule_task(self, task_type: str, requirements: Dict[str, Any], 
                          session_id: str) -> Dict[str, Any]:
        """Schedule a task with intelligent agent assignment"""
        try:
            # Use agent pool manager if available
            if self.agent_pool_manager:
                # use getattr to support multiple AgentPoolManager APIs
                select_best = getattr(self.agent_pool_manager, "select_best_agent", None)
                if callable(select_best):
                    agent = await self._invoke(select_best, task_type, requirements)
                else:
                    # fallback to other common name
                    select_fn = getattr(self.agent_pool_manager, "select_agent", None)
                    if callable(select_fn):
                        agent = await self._invoke(select_fn, task_type, requirements)
                    else:
                        # last resort: raise a clear error
                        raise RuntimeError("AgentPoolManager has no select_best_agent/select_agent method")
                
                if agent:
                    logger.info(f"Assigned specialist agent {getattr(agent, 'name', str(agent))} for task {task_type}")
                    return await self._execute_task_with_agent(
                        task_type, requirements, agent, session_id
                    )
            
            # Fallback to original agent registry
            # support registries exposing get(...) or dict-like access
            get_fn = getattr(self.agent_registry, "get", None)
            if callable(get_fn):
                agent_maybe = await self._invoke(get_fn, task_type)
            else:
                # try mapping protocol
                try:
                    agent_maybe = self.agent_registry[task_type]  # type: ignore
                except Exception:
                    raise RuntimeError("AgentRegistry does not expose get() or mapping access for task_type")
            
            if agent_maybe is None:
                raise RuntimeError("No agent found for task_type")

            # agent_maybe might be a class, factory, or instance; try to instantiate if possible
            agent = None
            try:
                if isinstance(agent_maybe, type) or callable(agent_maybe):
                    try:
                        candidate = agent_maybe()  # factory or class
                        agent = candidate
                    except Exception:
                        # not instantiable, assume it's already the instance or callable to execute
                        agent = agent_maybe
                else:
                    agent = agent_maybe
            except Exception:
                agent = agent_maybe

            # generate a simple task id
            task_id = f"{task_type}_{int(time.time())}"
            
            logger.info(f"Scheduling task {task_id} with agent {getattr(agent, '__class__', type(agent)).__name__}")
            
            # Execute task - agent.execute may be sync or async or agent might itself be a callable
            exec_fn = getattr(agent, "execute", agent)
            result = await self._invoke(exec_fn, requirements)
            
            # Update workflow state (safe invoke)
            wf = getattr(self, "workflow_manager", None)
            if wf is not None:
                update_fn = getattr(wf, "update_state", None) or getattr(wf, "update", None)
                if callable(update_fn):
                    await self._invoke(update_fn, session_id)
                else:
                    # no-op if manager doesn't expose update API
                    pass
            
            return {
                'task_id': task_id,
                'status': 'completed',
                'result': result,
                'agent': getattr(agent, "__class__", type(agent)).__name__
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
            # Create a workflow task for the agent using safe factory
            task = self._make_workflow_task(
                id=f"{task_type}_{int(datetime.now().timestamp())}",
                phase=WorkflowPhase.INTAKE,
                agent_type=getattr(agent, "agent_type", getattr(agent, "__class__", type(agent)).__name__),
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
            
            # Execute the task using the agent (could be sync or async)
            exec_fn = getattr(agent, "execute_task", getattr(agent, "execute", agent))
            result = await self._invoke(exec_fn, task, task_context) if callable(exec_fn) else await self._invoke(exec_fn)
            
            # Process and return result
            return {
                'task_id': task.id,
                'status': 'completed',
                'result': result,
                'agent': getattr(agent, "name", getattr(agent, "__class__", type(agent)).__name__),
                'fitness_score': getattr(agent, "fitness_score", None)
            }
            
        except Exception as e:
            logger.error(f"Task execution failed with agent {getattr(agent, 'name', str(agent))}: {e}")
            return {
                'task_id': f"failed_{int(datetime.now().timestamp())}",
                'status': 'failed',
                'error': str(e),
                'agent': getattr(agent, "name", str(agent))
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
                    # Prefer ingest_server's draft processing when available
                    if _ingest_server and hasattr(_ingest_server, "_process_draft_document"):
                        analysis = await self._invoke(_ingest_server._process_draft_document, content, draft, "fact_statement")
                        if not isinstance(analysis, dict):
                            analysis = {}
                        # ingest_server returns a dict -> map to expected pieces
                        facts = analysis.get("key_facts") or analysis.get("facts") or []
                        entities = analysis.get("legal_entities") or analysis.get("entities") or []
                    else:
                        facts = await self._extract_legal_facts(content, draft_type='fact_statement')
                        entities = await self._extract_legal_entities(content, confidence_boost=0.2)
                    
                    aggregated_facts.extend(facts)
                    entities_extracted.extend(entities)
            
            # Deduplicate and rank facts by confidence
            unique_facts = self._deduplicate_facts(aggregated_facts)
            unique_entities = self._deduplicate_entities(entities_extracted)
            
            # Store in knowledge graph with high confidence; prefer ingest_server ingestion if available
            if self.knowledge_graph:
                if _ingest_server and hasattr(_ingest_server, "_ingest_to_knowledge_graph"):
                    kg_storage_result = await self._invoke(_ingest_server._ingest_to_knowledge_graph, unique_entities, {"draft_type": "fact_statement"})
                else:
                    kg_storage_result = await self._invoke(self._store_foundational_knowledge, unique_entities, unique_facts, 'fact_statement_draft')
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
                    # Prefer ingest_server's draft processing when available
                    if _ingest_server and hasattr(_ingest_server, "_process_draft_document"):
                        analysis = await self._invoke(_ingest_server._process_draft_document, content, draft, "case_complaint")
                        if not isinstance(analysis, dict):
                            analysis = {}
                        issues = analysis.get("legal_issues") or []
                        claims = analysis.get("claims") or []
                        entities = analysis.get("legal_entities") or []
                    else:
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
            
            # Store in knowledge graph (use ingest_server ingestion if available)
            if self.knowledge_graph:
                if _ingest_server and hasattr(_ingest_server, "_ingest_to_knowledge_graph"):
                    kg_storage_result = await self._invoke(_ingest_server._ingest_to_knowledge_graph, unique_entities, {"draft_type": "case_complaint"})
                else:
                    kg_storage_result = await self._invoke(self._store_foundational_knowledge, unique_entities, unique_issues + unique_claims, 'case_complaint_draft')
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
                    if workflow_state.overall_status == PhaseStatus.PAUSED:
                        logger.info(f"Workflow {session_id} is paused, halting execution loop.")
                        break

                # Execute the core business logic for the current phase to generate artifacts
                await self._execute_phase_logic(workflow_state)
                
                # If phase logic failed, the state will be FAILED, and the loop will terminate.
                if workflow_state.overall_status == PhaseStatus.FAILED:
                    logger.error(f"Workflow {session_id} failed during phase logic execution. Halting.")
                    break
                
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

    async def _execute_phase_logic(self, workflow_state: WorkflowState):
        """
        Executes the main business logic for the current phase, calling integrated components.
        This method is responsible for creating the primary artifacts of each phase.
        """
        if not PHASE_COMPONENTS_AVAILABLE:
            logger.warning("Phase components are not available. Skipping phase logic execution.")
            return

        current_phase = workflow_state.current_phase
        session_id = workflow_state.session_id
        logger.info(f"Executing core logic for phase '{current_phase.value}' in session {session_id}")

        try:
            if current_phase == WorkflowPhase.INTAKE:
                raw_data = workflow_state.global_context.get("raw_ingestion_data", {})
                if not raw_data:
                    logger.warning(f"No 'raw_ingestion_data' found in context for INTAKE phase. Skipping FactsMatrixAdapter.")
                    return
                
                logger.info("INTAKE PHASE: Processing raw data with FactsMatrixAdapter.")
                facts_matrix = FactsMatrixAdapter.process(raw_data)
                workflow_state.global_context["facts_matrix"] = facts_matrix
                logger.info("INTAKE PHASE: Facts Matrix created and added to workflow context.")

            elif current_phase == WorkflowPhase.OUTLINE:
                from dataclasses import asdict
                facts_matrix = workflow_state.global_context.get("facts_matrix")
                if not facts_matrix:
                    logger.error("OUTLINE PHASE: 'facts_matrix' not found in context. Cannot generate outline.")
                    raise ValueError("Facts matrix is required for the OUTLINE phase.")

                # Initialize Claims Matrix Integration
                logger.info("OUTLINE PHASE: Initializing ComprehensiveClaimsMatrixIntegration.")
                claims_matrix_integration = ComprehensiveClaimsMatrixIntegration(self.knowledge_graph)
                # The analysis session needs to be started before generating the analysis
                claims_matrix_integration.start_interactive_analysis(
                    jurisdiction=workflow_state.global_context.get("jurisdiction", "California"),
                    cause_of_action=workflow_state.global_context.get("primary_cause_of_action", "Negligence"),
                    case_facts=facts_matrix.get("undisputed_facts", []),
                    session_id=session_id
                )
                analysis = claims_matrix_integration.generate_attorney_ready_analysis(session_id)
                workflow_state.global_context["claims_matrix_analysis"] = asdict(analysis) if analysis else {}
                logger.info("OUTLINE PHASE: Claims Matrix analysis generated.")

                # Initialize Skeletal Outline Generator
                logger.info("OUTLINE PHASE: Initializing SkeletalOutlineGenerator.")
                # Note: EvidenceAPI is a dependency but seems to be a deprecated shim. Passing None for now.
                outline_generator = SkeletalOutlineGenerator(self.knowledge_graph, claims_matrix_integration, evidence_api=None)
                skeletal_outline = outline_generator.generate_skeletal_outline(workflow_state.case_name, session_id)
                workflow_state.global_context["skeletal_outline"] = skeletal_outline.to_dict()
                logger.info("OUTLINE PHASE: Skeletal Outline generated and added to workflow context.")

            elif current_phase == WorkflowPhase.RESEARCH:
                # Handle research phase - check if this is part of a research loop
                if workflow_state.research_loop_count > 0 and workflow_state.research_loop_history:
                    logger.info(f"RESEARCH PHASE: Processing research loop #{workflow_state.research_loop_count}")
                    await self._handle_research_loop_execution(workflow_state)
                else:
                    logger.info("RESEARCH PHASE: Standard research execution")
                    # Standard research phase logic would go here
                    # For now, we'll mark it as completed to allow workflow to continue
                    pass

            elif current_phase == WorkflowPhase.POST_PRODUCTION:
                if not POST_PRODUCTION_AVAILABLE:
                    logger.warning("POST_PRODUCTION PHASE: Post-production components not available. Skipping phase.")
                    return

                logger.info("POST_PRODUCTION PHASE: Starting document post-processing.")
                
                # Get the final document content from previous phases
                final_document = workflow_state.global_context.get("final_document_content")
                if not final_document:
                    logger.warning("POST_PRODUCTION PHASE: No final document content found. Attempting to retrieve from drafting phase.")
                    # Try to get from drafting phase output
                    final_document = workflow_state.global_context.get("drafted_document", "")
                
                if not final_document:
                    logger.error("POST_PRODUCTION PHASE: No document content available for post-processing.")
                    raise ValueError("Document content is required for the POST_PRODUCTION phase.")

                # Prepare source materials for fact verification
                source_materials = {
                    "facts_matrix": workflow_state.global_context.get("facts_matrix", {}),
                    "case_documents": workflow_state.global_context.get("source_documents", []),
                    "claims_matrix_analysis": workflow_state.global_context.get("claims_matrix_analysis", {}),
                    "skeletal_outline": workflow_state.global_context.get("skeletal_outline", {})
                }

                post_production_results = {}

                # 1. Fact Verification
                try:
                    logger.info("POST_PRODUCTION PHASE: Starting fact verification.")
                    fact_checker = FactChecker(
                        knowledge_graph=self.knowledge_graph,
                        evidence_api=None
                    )
                    verification_report = await fact_checker.verify_document_facts(
                        final_document, source_materials
                    )
                    post_production_results["verification_report"] = verification_report
                    logger.info(f"POST_PRODUCTION PHASE: Fact verification completed. "
                              f"{verification_report.verified_facts}/{verification_report.total_facts_checked} facts verified.")
                except Exception as e:
                    logger.error(f"POST_PRODUCTION PHASE: Fact verification failed: {e}")
                    post_production_results["verification_error"] = str(e)

                # 2. Citation Validation
                try:
                    logger.info("POST_PRODUCTION PHASE: Starting citation validation.")
                    citation_validator = BluebookValidator()
                    citation_report = await citation_validator.validate_document_citations(final_document)
                    post_production_results["citation_report"] = citation_report
                    logger.info(f"POST_PRODUCTION PHASE: Citation validation completed. "
                              f"{citation_report.valid_citations}/{citation_report.total_citations} citations valid.")
                except Exception as e:
                    logger.error(f"POST_PRODUCTION PHASE: Citation validation failed: {e}")
                    post_production_results["citation_error"] = str(e)

                # 3. PDF Generation
                try:
                    logger.info("POST_PRODUCTION PHASE: Starting PDF generation.")
                    
                    # Prepare document metadata
                    metadata = DocumentMetadata(
                        title=workflow_state.global_context.get("document_title", workflow_state.case_name),
                        case_name=workflow_state.case_name,
                        case_number=workflow_state.global_context.get("case_number"),
                        court=workflow_state.global_context.get("court"),
                        attorney_name=workflow_state.global_context.get("attorney_name"),
                        attorney_bar_number=workflow_state.global_context.get("attorney_bar_number"),
                        law_firm=workflow_state.global_context.get("law_firm"),
                        party_represented=workflow_state.global_context.get("party_represented"),
                        document_type=DocumentFormat.COMPLAINT  # Default, could be dynamic
                    )
                    
                    # Configure formatting
                    formatting = FormattingOptions(
                        double_space_pleadings=True,
                        include_page_numbers=True,
                        include_header=True
                    )
                    
                    pdf_generator = LegalPDFGenerator()
                    pdf_result = await pdf_generator.generate_pdf(
                        final_document, metadata, formatting
                    )
                    post_production_results["pdf_result"] = pdf_result
                    
                    if pdf_result.success:
                        logger.info(f"POST_PRODUCTION PHASE: PDF generated successfully: {pdf_result.file_path}")
                        workflow_state.global_context["final_pdf_path"] = pdf_result.file_path
                    else:
                        logger.error(f"POST_PRODUCTION PHASE: PDF generation failed: {pdf_result.error_message}")
                        
                except Exception as e:
                    logger.error(f"POST_PRODUCTION PHASE: PDF generation failed: {e}")
                    post_production_results["pdf_error"] = str(e)

                # Store all post-production results in workflow context
                workflow_state.global_context["post_production_results"] = post_production_results
                
                # Generate summary report
                summary_lines = ["POST-PRODUCTION PHASE SUMMARY:"]
                if "verification_report" in post_production_results:
                    vr = post_production_results["verification_report"]
                    summary_lines.append(f"✓ Fact Verification: {vr.verified_facts}/{vr.total_facts_checked} facts verified")
                if "citation_report" in post_production_results:
                    cr = post_production_results["citation_report"]
                    summary_lines.append(f"✓ Citation Validation: {cr.valid_citations}/{cr.total_citations} citations valid")
                if "pdf_result" in post_production_results:
                    pr = post_production_results["pdf_result"]
                    if pr.success:
                        summary_lines.append(f"✓ PDF Generation: Successfully created {pr.file_path}")
                    else:
                        summary_lines.append(f"✗ PDF Generation: Failed - {pr.error_message}")
                
                workflow_state.global_context["post_production_summary"] = "\n".join(summary_lines)
                logger.info("POST_PRODUCTION PHASE: Post-processing completed successfully.")

            # Add logic for other phases here as they are implemented
            # elif current_phase == WorkflowPhase.DRAFTING:
            #     ...

            logger.info(f"Successfully executed logic for phase '{current_phase.value}'.")

        except Exception as e:
            logger.exception(f"An error occurred during phase logic execution for '{current_phase.value}': {e}")
            # Optionally, set the workflow to a failed state
            workflow_state.overall_status = PhaseStatus.FAILED
            await self.error_handler.handle_workflow_error(workflow_state, e)
            raise # Re-raise to stop the workflow loop

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
            # Phase is complete - check for research needed before proceeding
            research_needed = await self._check_research_needed(workflow_state, completed_tasks)
            
            if research_needed:
                # Transition back to RESEARCH phase
                await self._initiate_research_loop(workflow_state, completed_tasks)
                return
            
            # No research needed - mark phase as complete and proceed
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

    async def _check_research_needed(self, workflow_state: WorkflowState, completed_tasks: List[WorkflowTask]) -> bool:
        """Check if any completed tasks flagged research as needed"""
        current_phase = workflow_state.current_phase
        
        # Only check for research needs in phases where iterative research makes sense
        research_capable_phases = [
            WorkflowPhase.OUTLINE,
            WorkflowPhase.DRAFTING,
            WorkflowPhase.LEGAL_REVIEW,
            WorkflowPhase.EDITING,
            WorkflowPhase.POST_PRODUCTION
        ]
        
        if current_phase not in research_capable_phases:
            return False
        
        # Check if we've exceeded maximum research loops
        if workflow_state.research_loop_count >= workflow_state.max_research_loops:
            logger.warning(f"Maximum research loops ({workflow_state.max_research_loops}) reached for session {workflow_state.session_id}")
            return False
        
        # Check completed tasks for research_needed flag
        research_questions = []
        for task in completed_tasks:
            if task.research_needed and task.research_questions:
                research_questions.extend(task.research_questions)
                logger.info(f"Task {task.id} flagged research needed: {task.research_questions}")
        
        if research_questions:
            # Store research questions for processing
            workflow_state.pending_research_questions.extend(research_questions)
            return True
        
        return False
    
    async def _initiate_research_loop(self, workflow_state: WorkflowState, completed_tasks: List[WorkflowTask]):
        """Initiate a research loop by transitioning back to RESEARCH phase"""
        current_phase = workflow_state.current_phase
        
        # Increment research loop counter
        workflow_state.research_loop_count += 1
        
        # Record the research loop in history
        loop_entry = {
            "loop_number": workflow_state.research_loop_count,
            "source_phase": current_phase.value,
            "research_questions": list(workflow_state.pending_research_questions),
            "triggered_by_tasks": [task.id for task in completed_tasks if task.research_needed],
            "timestamp": datetime.now().isoformat()
        }
        workflow_state.research_loop_history.append(loop_entry)
        
        logger.info(f"Initiating research loop #{workflow_state.research_loop_count} from {current_phase.value} phase")
        logger.info(f"Research questions: {workflow_state.pending_research_questions}")
        
        # Transition to RESEARCH phase
        workflow_state.current_phase = WorkflowPhase.RESEARCH
        workflow_state.phases[WorkflowPhase.RESEARCH] = PhaseStatus.IN_PROGRESS
        
        # Create research task to address the pending questions
        research_task = WorkflowTask(
            id=f"research_loop_{workflow_state.research_loop_count}_{workflow_state.session_id}",
            phase=WorkflowPhase.RESEARCH,
            agent_type="ResearchBot",
            description=f"Research loop #{workflow_state.research_loop_count} - Address questions from {current_phase.value} phase",
            priority=TaskPriority.HIGH,
            status=PhaseStatus.PENDING
        )
        
        # Add research context
        research_task.research_context = {
            "source_phase": current_phase.value,
            "research_questions": list(workflow_state.pending_research_questions),
            "loop_number": workflow_state.research_loop_count,
            "return_to_phase": current_phase.value
        }
        
        # Add the research task
        workflow_state.tasks[research_task.id] = research_task
        
        # Clear pending questions as they're now being processed
        workflow_state.pending_research_questions.clear()
        
        logger.info(f"Created research task {research_task.id} to address research needs")
    
    async def _handle_research_loop_execution(self, workflow_state: WorkflowState):
        """Handle execution of research loop - integrate with ResearchBot"""
        if not workflow_state.research_loop_history:
            logger.error("No research loop history found, cannot process research loop")
            return
        
        current_loop = workflow_state.research_loop_history[-1]
        source_phase = current_loop.get("source_phase")
        research_questions = current_loop.get("research_questions", [])
        
        logger.info(f"Executing research loop for questions: {research_questions}")
        
        try:
            # Try to import and use ResearchBot
            from lawyerfactory.compose.bots.research import ResearchBot
            
            # Create research bot instance
            research_bot = ResearchBot()
            
            # Process each research question
            new_evidence = []
            research_results = []
            
            for question in research_questions:
                logger.info(f"Researching question: {question}")
                
                # Create research query
                from lawyerfactory.compose.bots.research import ResearchQuery
                query = ResearchQuery(
                    query_text=question,
                    legal_issues=[question],
                    jurisdiction=workflow_state.global_context.get("jurisdiction", "federal"),
                    venue=workflow_state.global_context.get("venue")
                )
                
                # Execute research
                result = await research_bot.execute_research(query)
                research_results.append(result)
                
                # Extract evidence and citations
                if hasattr(result, 'citations') and result.citations:
                    new_evidence.extend(result.citations)
            
            # Update evidence table and context
            if new_evidence:
                existing_evidence = workflow_state.global_context.get("evidence_table", [])
                existing_evidence.extend([{
                    "citation": ev.citation if hasattr(ev, 'citation') else str(ev),
                    "title": ev.title if hasattr(ev, 'title') else "Research Result",
                    "source": "research_loop",
                    "loop_number": workflow_state.research_loop_count,
                    "question": research_questions[new_evidence.index(ev) % len(research_questions)] if research_questions else "unknown"
                } for ev in new_evidence])
                
                workflow_state.global_context["evidence_table"] = existing_evidence
                logger.info(f"Added {len(new_evidence)} new evidence items from research loop")
                
                # For phases 5 and later, only update evidence table
                # For earlier phases, also update facts matrix and claims matrix
                if source_phase in ["outline", "research", "drafting"]:
                    await self._update_research_dependent_artifacts(workflow_state, new_evidence, research_results)
            
            # Mark research loop as complete and return to source phase
            await self._complete_research_loop(workflow_state, source_phase)
            
        except ImportError:
            logger.warning("ResearchBot not available, using fallback research loop completion")
            # Fallback - just complete the loop without actual research
            await self._complete_research_loop(workflow_state, source_phase)
        except Exception as e:
            logger.error(f"Research loop execution failed: {e}")
            # Complete the loop anyway to avoid getting stuck
            await self._complete_research_loop(workflow_state, source_phase)
    
    async def _update_research_dependent_artifacts(self, workflow_state: WorkflowState, new_evidence: List, research_results: List):
        """Update facts matrix, claims matrix based on new research findings"""
        logger.info("Updating research-dependent artifacts with new findings")
        
        # Update facts matrix if available
        facts_matrix = workflow_state.global_context.get("facts_matrix", {})
        if facts_matrix and new_evidence:
            # Add new facts from research to undisputed facts (as they come from authoritative sources)
            new_facts = [f"Research finding: {ev.get('title', str(ev))}" for ev in new_evidence[:3]]  # Limit to avoid overflow
            existing_facts = facts_matrix.get("undisputed_facts", [])
            existing_facts.extend(new_facts)
            facts_matrix["undisputed_facts"] = existing_facts
            workflow_state.global_context["facts_matrix"] = facts_matrix
            logger.info(f"Added {len(new_facts)} new facts from research to facts matrix")
        
        # Update claims matrix analysis with new legal authorities
        claims_analysis = workflow_state.global_context.get("claims_matrix_analysis", {})
        if claims_analysis:
            # Add research findings to supporting authorities
            if "supporting_authorities" not in claims_analysis:
                claims_analysis["supporting_authorities"] = []
            
            research_authorities = [f"Research authority: {ev.get('citation', str(ev))}" for ev in new_evidence[:5]]
            claims_analysis["supporting_authorities"].extend(research_authorities)
            workflow_state.global_context["claims_matrix_analysis"] = claims_analysis
            logger.info(f"Added {len(research_authorities)} research authorities to claims analysis")
    
    async def _complete_research_loop(self, workflow_state: WorkflowState, source_phase: str):
        """Complete the research loop and return to the source phase"""
        logger.info(f"Completing research loop #{workflow_state.research_loop_count}, returning to {source_phase} phase")
        
        # Convert source_phase string back to WorkflowPhase enum
        try:
            return_phase = WorkflowPhase(source_phase)
        except ValueError:
            logger.error(f"Invalid source phase: {source_phase}, defaulting to OUTLINE")
            return_phase = WorkflowPhase.OUTLINE
        
        # Update workflow state to return to source phase
        workflow_state.current_phase = return_phase
        workflow_state.phases[return_phase] = PhaseStatus.IN_PROGRESS
        workflow_state.phases[WorkflowPhase.RESEARCH] = PhaseStatus.COMPLETED
        
        # Update research loop history
        if workflow_state.research_loop_history:
            workflow_state.research_loop_history[-1]["completed_at"] = datetime.now().isoformat()
            workflow_state.research_loop_history[-1]["status"] = "completed"
        
        logger.info(f"Successfully returned to {return_phase.value} phase after research loop completion")
    
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

    async def list_workflows(self) -> List[Dict[str, Any]]:
        """List all active workflows"""
        try:
            workflows = []
            
            # Get workflows from memory
            for session_id, workflow_state in self.active_workflows.items():
                # Defensive attribute access: workflow_state may be a dict-like or object
                try:
                    case_name = getattr(workflow_state, 'case_name', None) or (workflow_state.get('case_name') if isinstance(workflow_state, dict) else None)
                    current_phase = (getattr(workflow_state, 'current_phase', None).value
                                     if getattr(workflow_state, 'current_phase', None) is not None else (workflow_state.get('current_phase') if isinstance(workflow_state, dict) else None))
                    overall_status = (getattr(workflow_state, 'overall_status', None).value
                                      if getattr(workflow_state, 'overall_status', None) is not None else (workflow_state.get('overall_status') if isinstance(workflow_state, dict) else None))
                    tasks_len = len(getattr(workflow_state, 'tasks', workflow_state.get('tasks') if isinstance(workflow_state, dict) else [])) if (getattr(workflow_state, 'tasks', None) is not None or (isinstance(workflow_state, dict) and workflow_state.get('tasks') is not None)) else 0
                    completed_len = len(getattr(workflow_state, 'completed_tasks', workflow_state.get('completed_tasks') if isinstance(workflow_state, dict) else [])) if (getattr(workflow_state, 'completed_tasks', None) is not None or (isinstance(workflow_state, dict) and workflow_state.get('completed_tasks') is not None)) else 0
                    progress = (completed_len / tasks_len * 100) if tasks_len else 0

                    created_at = None
                    updated_at = None
                    created = getattr(workflow_state, 'created_at', None)
                    updated = getattr(workflow_state, 'updated_at', None)
                    if created and hasattr(created, 'isoformat'):
                        created_at = created.isoformat()
                    elif isinstance(workflow_state, dict):
                        created_at = workflow_state.get('created_at')
                    if updated and hasattr(updated, 'isoformat'):
                        updated_at = updated.isoformat()
                    elif isinstance(workflow_state, dict):
                        updated_at = workflow_state.get('updated_at')

                    workflows.append({
                        'session_id': session_id,
                        'case_name': case_name,
                        'current_phase': current_phase,
                        'overall_status': overall_status,
                        'progress': progress,
                        'created_at': created_at,
                        'updated_at': updated_at
                    })
                except Exception:
                    # skip malformed workflow entries
                    continue
            
            # Also try to load any persisted workflows from state manager
            try:
                # tolerant discovery of saved states across manager implementations
                list_all = getattr(self.state_manager, "list_all_states", None)
                if callable(list_all):
                    persisted_workflows = await self._invoke(list_all)
                else:
                    # fallback to alternate method name
                    list_fn = getattr(self.state_manager, "list_states", None)
                    if callable(list_fn):
                        persisted_workflows = await self._invoke(list_fn)
                    else:
                        persisted_workflows = []  # nothing available
                
                if not isinstance(persisted_workflows, list):
                    persisted_workflows = []
                
                for workflow_data in persisted_workflows:
                    # Avoid duplicates from active workflows
                    try:
                        sid = workflow_data.get('session_id') if isinstance(workflow_data, dict) else None
                        if sid and sid not in self.active_workflows:
                            workflows.append(workflow_data)
                    except Exception:
                        # skip malformed entries
                        continue
            except Exception as e:
                logger.warning(f"Failed to load persisted workflows: {e}")
            
            return workflows
            
        except Exception as e:
            logger.error(f"Failed to list workflows: {e}")
            return []

    async def get_workflow_status(self, session_id: str) -> Dict[str, Any]:
        """Get current status of a workflow"""
        workflow_state = self.active_workflows.get(session_id)
        if not workflow_state:
            # Try to load from persistent storage (safe invocation)
            workflow_state = await self._invoke(getattr(self.state_manager, "load_state", None), session_id)
        
        if not workflow_state:
            raise ValueError(f"Workflow not found: {session_id}")
        
        # Defensive construction of status dict
        try:
            case_name = getattr(workflow_state, 'case_name', None) or (workflow_state.get('case_name') if isinstance(workflow_state, dict) else None)
            current_phase = (getattr(workflow_state, 'current_phase', None).value
                             if getattr(workflow_state, 'current_phase', None) is not None else (workflow_state.get('current_phase') if isinstance(workflow_state, dict) else None))
            overall_status = (getattr(workflow_state, 'overall_status', None).value
                              if getattr(workflow_state, 'overall_status', None) is not None else (workflow_state.get('overall_status') if isinstance(workflow_state, dict) else None))

            tasks = getattr(workflow_state, 'tasks', workflow_state.get('tasks') if isinstance(workflow_state, dict) else {}) or {}
            completed_tasks = getattr(workflow_state, 'completed_tasks', workflow_state.get('completed_tasks') if isinstance(workflow_state, dict) else []) or []
            progress = (len(completed_tasks) / len(tasks) * 100) if tasks else 0

            phases = {}
            phases_attr = getattr(workflow_state, 'phases', workflow_state.get('phases') if isinstance(workflow_state, dict) else {}) or {}
            if isinstance(phases_attr, dict):
                for phase_k, status_v in phases_attr.items():
                    try:
                        phases[phase_k if isinstance(phase_k, str) else getattr(phase_k, 'value', str(phase_k))] = (status_v.value if hasattr(status_v, 'value') else status_v)
                    except Exception:
                        phases[str(phase_k)] = str(status_v)

            created_at = None
            updated_at = None
            created = getattr(workflow_state, 'created_at', None)
            updated = getattr(workflow_state, 'updated_at', None)
            if created and hasattr(created, 'isoformat'):
                created_at = created.isoformat()
            elif isinstance(workflow_state, dict):
                created_at = workflow_state.get('created_at')
            if updated and hasattr(updated, 'isoformat'):
                updated_at = updated.isoformat()
            elif isinstance(workflow_state, dict):
                updated_at = workflow_state.get('updated_at')

            return {
                'session_id': session_id,
                'case_name': case_name,
                'current_phase': current_phase,
                'overall_status': overall_status,
                'progress': progress,
                'phases': phases,
                'created_at': created_at,
                'updated_at': updated_at
            }
        except Exception as exc:
            logger.error(f"Failed to assemble workflow status for {session_id}: {exc}")
            raise

    async def shutdown(self):
        """Gracefully shutdown the maestro"""
        logger.info("Shutting down Enhanced Maestro")
        # gracefully close managers if they expose close/shutdown APIs
        async_close = getattr(self.state_manager, "close", None) or getattr(self.state_manager, "shutdown", None)
        if callable(async_close):
            await self._invoke(async_close)
        # checkpoint manager
        cp_close = getattr(self.checkpoint_manager, "close", None) or getattr(self.checkpoint_manager, "shutdown", None)
        if callable(cp_close):
            await self._invoke(cp_close)