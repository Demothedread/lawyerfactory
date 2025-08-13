"""
Agent registry and coordination system for the LawyerFactory orchestration.
Manages specialized bots and their lifecycle.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Type
from dataclasses import dataclass
from enum import Enum

from .workflow_models import WorkflowTask, WorkflowPhase, PhaseStatus

logger = logging.getLogger(__name__)


class AgentCapability(Enum):
    """Agent capabilities for task assignment"""
    DOCUMENT_INGESTION = "document_ingestion"
    TEXT_EXTRACTION = "text_extraction"
    LEGAL_RESEARCH = "legal_research"
    CASE_ANALYSIS = "case_analysis"
    LEGAL_WRITING = "legal_writing"
    DOCUMENT_REVIEW = "document_review"
    FORMATTING = "formatting"
    ORCHESTRATION = "orchestration"


@dataclass
class AgentConfig:
    """Configuration for agent instances"""
    agent_type: str
    max_concurrent: int = 1
    timeout_seconds: int = 300
    retry_attempts: int = 3
    capabilities: Optional[List[AgentCapability]] = None
    config: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = []
        if self.config is None:
            self.config = {}


class AgentInterface(ABC):
    """Base interface for all specialized agents"""

    def __init__(self, config: AgentConfig):
        self.config = config
        self.agent_type = config.agent_type
        self.is_busy = False
        self.current_task_id: Optional[str] = None

    @abstractmethod
    async def execute_task(self, task: WorkflowTask, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific task with given context"""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the agent is healthy and ready to process tasks"""
        pass

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the agent with required resources"""
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up agent resources"""
        pass

    async def can_handle_task(self, task: WorkflowTask) -> bool:
        """Check if this agent can handle the given task"""
        # Base implementation checks capabilities
        required_capability = self._get_required_capability(task)
        if not self.config.capabilities:
            return False
        return required_capability in self.config.capabilities

    def _get_required_capability(self, task: WorkflowTask) -> AgentCapability:
        """Map task to required capability"""
        capability_map = {
            WorkflowPhase.INTAKE: AgentCapability.DOCUMENT_INGESTION,
            WorkflowPhase.OUTLINE: AgentCapability.CASE_ANALYSIS,
            WorkflowPhase.RESEARCH: AgentCapability.LEGAL_RESEARCH,
            WorkflowPhase.DRAFTING: AgentCapability.LEGAL_WRITING,
            WorkflowPhase.LEGAL_REVIEW: AgentCapability.DOCUMENT_REVIEW,
            WorkflowPhase.EDITING: AgentCapability.DOCUMENT_REVIEW,
            WorkflowPhase.ORCHESTRATION: AgentCapability.ORCHESTRATION,
        }
        return capability_map.get(task.phase, AgentCapability.ORCHESTRATION)


class MockAgentInterface(AgentInterface):
    """Mock agent implementation for testing and development"""

    async def execute_task(self, task: WorkflowTask, context: Dict[str, Any]) -> Dict[str, Any]:
        """Mock task execution - returns a simulated result"""
        logger.info(f"Mock {self.agent_type} executing task {task.id}: {task.description}")
        
        # Simulate processing time
        await asyncio.sleep(1)
        
        # Return mock result based on task phase
        mock_results = {
            WorkflowPhase.INTAKE: {
                'entities_extracted': ['Tesla Inc.', 'SEC', 'Q3 2023'],
                'documents_processed': len(context.get('input_documents', [])),
                'knowledge_graph_updated': True
            },
            WorkflowPhase.OUTLINE: {
                'case_theory': 'Securities fraud based on misleading statements',
                'legal_claims': ['Securities Act violations', 'Rule 10b-5 violations'],
                'jurisdiction': 'Federal District Court'
            },
            WorkflowPhase.RESEARCH: {
                'cases_found': ['SEC v. Tesla (2018)', 'In re Tesla Securities Litigation'],
                'statutes_applicable': ['Securities Act of 1933', 'Securities Exchange Act of 1934'],
                'research_gaps': []
            },
            WorkflowPhase.DRAFTING: {
                'sections_completed': ['Introduction', 'Factual Background', 'Legal Claims'],
                'word_count': 2500,
                'citations_added': 15
            },
            WorkflowPhase.LEGAL_REVIEW: {
                'compliance_issues': [],
                'formatting_applied': True,
                'citations_verified': True
            },
            WorkflowPhase.EDITING: {
                'revisions_made': 8,
                'style_score': 85,
                'readability_score': 'Professional'
            },
            WorkflowPhase.ORCHESTRATION: {
                'workflow_status': 'progressing',
                'next_actions': ['Await human review']
            }
        }
        
        return mock_results.get(task.phase, {'status': 'completed'})

    async def health_check(self) -> bool:
        """Mock health check - always returns True"""
        return True

    async def initialize(self) -> None:
        """Mock initialization"""
        logger.info(f"Initialized mock {self.agent_type} agent")

    async def cleanup(self) -> None:
        """Mock cleanup"""
        logger.info(f"Cleaned up mock {self.agent_type} agent")


class AgentLoadBalancer:
    """Manages load balancing across agent instances"""

    def __init__(self):
        self.usage_metrics: Dict[str, int] = {}

    def select_agent(self, agents: List[AgentInterface]) -> AgentInterface:
        """Select the best available agent based on load"""
        if not agents:
            raise ValueError("No agents available")

        # Find the least busy agent
        available_agents = [agent for agent in agents if not agent.is_busy]
        if not available_agents:
            # If all busy, return the one with lowest usage
            return min(agents, key=lambda a: self.usage_metrics.get(a.agent_type, 0))

        # Return the least used available agent
        return min(available_agents, key=lambda a: self.usage_metrics.get(a.agent_type, 0))

    def record_usage(self, agent_type: str):
        """Record agent usage for load balancing"""
        self.usage_metrics[agent_type] = self.usage_metrics.get(agent_type, 0) + 1


class AgentRegistry:
    """Registry for managing specialized agents"""

    def __init__(self):
        self.agents: Dict[str, Dict[str, Any]] = {}
        self.agent_configs: Dict[str, AgentConfig] = {}
        self.load_balancer = AgentLoadBalancer()
        self._initialize_default_agents()

    def _initialize_default_agents(self):
        """Initialize default mock agents for all phases"""
        default_agents = [
            AgentConfig(
                agent_type="ReaderBot",
                capabilities=[AgentCapability.DOCUMENT_INGESTION, AgentCapability.TEXT_EXTRACTION],
                max_concurrent=2
            ),
            AgentConfig(
                agent_type="ParalegalBot",
                capabilities=[AgentCapability.CASE_ANALYSIS, AgentCapability.DOCUMENT_REVIEW],
                max_concurrent=3
            ),
            AgentConfig(
                agent_type="OutlinerBot",
                capabilities=[AgentCapability.CASE_ANALYSIS],
                max_concurrent=1
            ),
            AgentConfig(
                agent_type="ResearchBot",
                capabilities=[AgentCapability.LEGAL_RESEARCH],
                max_concurrent=2
            ),
            AgentConfig(
                agent_type="LegalResearcherBot",
                capabilities=[AgentCapability.LEGAL_RESEARCH],
                max_concurrent=2
            ),
            AgentConfig(
                agent_type="WriterBot",
                capabilities=[AgentCapability.LEGAL_WRITING],
                max_concurrent=1
            ),
            AgentConfig(
                agent_type="LegalFormatterBot",
                capabilities=[AgentCapability.FORMATTING, AgentCapability.DOCUMENT_REVIEW],
                max_concurrent=2
            ),
            AgentConfig(
                agent_type="LegalProcedureBot",
                capabilities=[AgentCapability.DOCUMENT_REVIEW],
                max_concurrent=1
            ),
            AgentConfig(
                agent_type="EditorBot",
                capabilities=[AgentCapability.DOCUMENT_REVIEW],
                max_concurrent=1
            ),
            AgentConfig(
                agent_type="MaestroBot",
                capabilities=[AgentCapability.ORCHESTRATION],
                max_concurrent=1
            ),
        ]

        for config in default_agents:
            self.register_agent(config.agent_type, MockAgentInterface, config)

    def register_agent(self, agent_type: str, agent_class: Type[AgentInterface], config: AgentConfig):
        """Register a new agent type"""
        self.agent_configs[agent_type] = config
        self.agents[agent_type] = {
            'class': agent_class,
            'instances': [],
            'max_concurrent': config.max_concurrent,
            'current_load': 0
        }
        logger.info(f"Registered agent type: {agent_type}")

    async def get_agent(self, agent_type: str) -> AgentInterface:
        """Get an available agent instance"""
        if agent_type not in self.agents:
            raise ValueError(f"Unknown agent type: {agent_type}")

        agent_info = self.agents[agent_type]
        config = self.agent_configs[agent_type]

        # Check if we can create a new instance
        if len(agent_info['instances']) < agent_info['max_concurrent']:
            instance = agent_info['class'](config)
            await instance.initialize()
            agent_info['instances'].append(instance)
            logger.info(f"Created new {agent_type} instance")
            return instance

        # Use load balancer to select best instance
        agent = self.load_balancer.select_agent(agent_info['instances'])
        self.load_balancer.record_usage(agent_type)
        return agent

    async def release_agent(self, agent: AgentInterface):
        """Release an agent after task completion"""
        agent.is_busy = False
        agent.current_task_id = None

    async def shutdown_all_agents(self):
        """Shutdown all agent instances"""
        for agent_type, agent_info in self.agents.items():
            for instance in agent_info['instances']:
                try:
                    await instance.cleanup()
                except Exception as e:
                    logger.error(f"Error cleaning up {agent_type}: {e}")
            agent_info['instances'].clear()
        logger.info("All agents shut down")

    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all registered agents"""
        status = {}
        for agent_type, agent_info in self.agents.items():
            status[agent_type] = {
                'instances': len(agent_info['instances']),
                'max_concurrent': agent_info['max_concurrent'],
                'current_load': agent_info['current_load'],
                'busy_instances': sum(1 for instance in agent_info['instances'] if instance.is_busy)
            }
        return status

    def get_agents_for_phase(self, phase: WorkflowPhase) -> List[str]:
        """Get list of agent types suitable for a specific phase"""
        # Agent assignment rules as defined in the specification
        phase_assignments = {
            WorkflowPhase.INTAKE: ['ReaderBot', 'ParalegalBot'],
            WorkflowPhase.OUTLINE: ['OutlinerBot', 'ParalegalBot'],
            WorkflowPhase.RESEARCH: ['ResearchBot', 'LegalResearcherBot'],
            WorkflowPhase.DRAFTING: ['WriterBot', 'ParalegalBot'],
            WorkflowPhase.LEGAL_REVIEW: ['LegalFormatterBot', 'LegalProcedureBot'],
            WorkflowPhase.EDITING: ['EditorBot'],
            WorkflowPhase.ORCHESTRATION: ['MaestroBot']
        }
        return phase_assignments.get(phase, [])


class TaskScheduler:
    """Intelligent task scheduling with dependency management"""

    def __init__(self, agent_registry: AgentRegistry):
        self.agent_registry = agent_registry

    def get_ready_tasks(self, workflow_state) -> List:
        """Get tasks that are ready to execute"""
        from .workflow_models import WorkflowState, WorkflowTask  # Import here to avoid circular imports
        
        ready_tasks = []
        
        for task in workflow_state.tasks.values():
            if task.status == PhaseStatus.PENDING:
                if self._are_dependencies_satisfied(task, workflow_state):
                    if self._are_resources_available(task):
                        ready_tasks.append(task)

        # Sort by priority and phase order
        ready_tasks.sort(key=lambda t: (t.phase.value, -t.priority.value))
        
        return ready_tasks

    def _are_dependencies_satisfied(self, task, workflow_state) -> bool:
        """Check if all task dependencies are satisfied"""
        for dependency_id in task.depends_on:
            if dependency_id in workflow_state.tasks:
                dep_task = workflow_state.tasks[dependency_id]
                if dep_task.status != PhaseStatus.COMPLETED:
                    return False
        return True

    def _are_resources_available(self, task) -> bool:
        """Check if resources are available for the task"""
        # Check if appropriate agents are available for the task
        suitable_agents = self.agent_registry.get_agents_for_phase(task.phase)
        if not suitable_agents:
            return False
        
        # For now, assume resources are available if agents exist
        # In a more sophisticated implementation, this would check actual availability
        return True