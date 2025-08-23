"""
# Script Name: agent_config_shared.py
# Description: YAML-based Agent Configuration System for LawyerFactory Provides dynamic agent specialization and configuration management. Supports both general and specialist agent pools with skill-based assignment.
# Relationships:
#   - Entity Type: Configuration
#   - Directory Group: Core
#   - Group Tags: null
YAML-based Agent Configuration System for LawyerFactory
Provides dynamic agent specialization and configuration management.
Supports both general and specialist agent pools with skill-based assignment.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

import yaml

logger = logging.getLogger(__name__)


class AgentType(Enum):
    """Types of agents in the system"""
    GENERAL = "general"
    SPECIALIST = "specialist"
    SUPERVISOR = "supervisor"
    RESEARCHER = "researcher"
    WRITER = "writer"
    REVIEWER = "reviewer"
    LEGAL_EXPERT = "legal_expert"
    TECHNICAL_EXPERT = "technical_expert"


class SkillLevel(Enum):
    """Skill proficiency levels"""
    NOVICE = 1
    INTERMEDIATE = 2
    ADVANCED = 3
    EXPERT = 4
    MASTER = 5


class WorkflowPhaseType(Enum):
    """Workflow phases for agent assignment"""
    INTAKE = "intake"
    OUTLINE = "outline"
    RESEARCH = "research"
    DRAFTING = "drafting"
    LEGAL_REVIEW = "legal_review"
    EDITING = "editing"
    ORCHESTRATION = "orchestration"


@dataclass
class AgentSkill:
    """Represents a specific skill an agent possesses"""
    name: str
    level: SkillLevel
    domain: str
    description: str = ""
    keywords: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    
    def matches_requirement(self, required_skill: str, min_level: SkillLevel = SkillLevel.INTERMEDIATE) -> bool:
        """Check if this skill matches a requirement"""
        return (
            self.name.lower() == required_skill.lower() and 
            self.level.value >= min_level.value
        ) or any(keyword.lower() in required_skill.lower() for keyword in self.keywords)


@dataclass
class AgentCapability:
    """Represents an agent's capability in a specific area"""
    name: str
    confidence: float  # 0.0 to 1.0
    experience_count: int = 0
    success_rate: float = 1.0
    last_used: Optional[datetime] = None
    specialization_tags: List[str] = field(default_factory=list)


@dataclass
class AgentConfiguration:
    """Complete configuration for an agent"""
    id: str
    name: str
    agent_type: AgentType
    skills: List[AgentSkill] = field(default_factory=list)
    capabilities: List[AgentCapability] = field(default_factory=list)
    preferred_phases: List[WorkflowPhaseType] = field(default_factory=list)
    max_concurrent_tasks: int = 3
    availability: bool = True
    priority: int = 1  # Higher numbers = higher priority
    load_balancing_weight: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_skill_level(self, skill_name: str) -> Optional[SkillLevel]:
        """Get the level for a specific skill"""
        for skill in self.skills:
            if skill.name.lower() == skill_name.lower():
                return skill.level
        return None
    
    def has_capability(self, capability_name: str, min_confidence: float = 0.5) -> bool:
        """Check if agent has a capability with minimum confidence"""
        for cap in self.capabilities:
            if cap.name.lower() == capability_name.lower() and cap.confidence >= min_confidence:
                return True
        return False
    
    def can_handle_phase(self, phase: WorkflowPhaseType) -> bool:
        """Check if agent can handle a specific workflow phase"""
        return phase in self.preferred_phases or not self.preferred_phases
    
    def calculate_fitness_score(self, required_skills: List[str], 
                              phase: WorkflowPhaseType,
                              task_complexity: float = 0.5) -> float:
        """Calculate fitness score for a task assignment"""
        score = 0.0
        
        # Base priority score
        score += self.priority * 0.2
        
        # Availability bonus
        if self.availability:
            score += 0.3
        
        # Phase preference bonus
        if self.can_handle_phase(phase):
            score += 0.2
        
        # Skills matching
        skill_matches = 0
        for req_skill in required_skills:
            for skill in self.skills:
                if skill.matches_requirement(req_skill):
                    skill_matches += skill.level.value * 0.1
        
        score += min(skill_matches, 0.3)  # Cap at 0.3
        
        # Load balancing factor
        score *= self.load_balancing_weight
        
        return min(score, 1.0)


class AgentConfigManager:
    """Manages agent configurations and dynamic assignments"""
    
    def __init__(self, config_directory: str = "configs/agents"):
        self.config_directory = Path(config_directory)
        self.config_directory.mkdir(parents=True, exist_ok=True)
        
        self.agents: Dict[str, AgentConfiguration] = {}
        self.agent_pools: Dict[AgentType, List[str]] = {}
        self.skill_registry: Dict[str, Set[str]] = {}  # skill_name -> agent_ids
        self.task_assignments: Dict[str, str] = {}  # task_id -> agent_id
        
        self._initialize_default_configs()
    
    def _initialize_default_configs(self):
        """Initialize default agent configurations"""
        default_configs = [
            self._create_general_agent_config(),
            self._create_legal_specialist_config(),
            self._create_research_specialist_config(),
            self._create_writing_specialist_config(),
            self._create_technical_specialist_config()
        ]
        
        for config in default_configs:
            self.register_agent(config)
    
    def _create_general_agent_config(self) -> AgentConfiguration:
        """Create a general-purpose agent configuration"""
        return AgentConfiguration(
            id="general_agent_001",
            name="General Purpose Agent",
            agent_type=AgentType.GENERAL,
            skills=[
                AgentSkill("document_processing", SkillLevel.ADVANCED, "general", 
                          keywords=["pdf", "docx", "text", "parsing"]),
                AgentSkill("content_analysis", SkillLevel.INTERMEDIATE, "general",
                          keywords=["analysis", "extraction", "summarization"]),
                AgentSkill("workflow_coordination", SkillLevel.ADVANCED, "general",
                          keywords=["orchestration", "coordination", "management"])
            ],
            capabilities=[
                AgentCapability("task_routing", 0.8),
                AgentCapability("content_summarization", 0.7),
                AgentCapability("workflow_management", 0.9)
            ],
            preferred_phases=[WorkflowPhaseType.INTAKE, WorkflowPhaseType.ORCHESTRATION],
            max_concurrent_tasks=5,
            priority=2
        )
    
    def _create_legal_specialist_config(self) -> AgentConfiguration:
        """Create a legal specialist agent configuration"""
        return AgentConfiguration(
            id="legal_specialist_001",
            name="Legal Document Specialist",
            agent_type=AgentType.LEGAL_EXPERT,
            skills=[
                AgentSkill("legal_research", SkillLevel.EXPERT, "legal",
                          keywords=["case_law", "statutes", "regulations", "precedents"]),
                AgentSkill("legal_writing", SkillLevel.EXPERT, "legal",
                          keywords=["briefs", "motions", "complaints", "legal_documents"]),
                AgentSkill("citation_formatting", SkillLevel.MASTER, "legal",
                          keywords=["bluebook", "citations", "legal_formatting"]),
                AgentSkill("contract_analysis", SkillLevel.ADVANCED, "legal",
                          keywords=["contracts", "agreements", "terms"])
            ],
            capabilities=[
                AgentCapability("legal_document_generation", 0.95),
                AgentCapability("case_law_research", 0.9),
                AgentCapability("legal_compliance_review", 0.85),
                AgentCapability("legal_argument_construction", 0.9)
            ],
            preferred_phases=[WorkflowPhaseType.RESEARCH, WorkflowPhaseType.DRAFTING, 
                            WorkflowPhaseType.LEGAL_REVIEW],
            max_concurrent_tasks=3,
            priority=5
        )
    
    def _create_research_specialist_config(self) -> AgentConfiguration:
        """Create a research specialist agent configuration"""
        return AgentConfiguration(
            id="research_specialist_001",
            name="Research & Analysis Specialist",
            agent_type=AgentType.RESEARCHER,
            skills=[
                AgentSkill("information_retrieval", SkillLevel.EXPERT, "research",
                          keywords=["search", "databases", "sources", "retrieval"]),
                AgentSkill("data_analysis", SkillLevel.ADVANCED, "research",
                          keywords=["statistics", "trends", "patterns", "analysis"]),
                AgentSkill("fact_verification", SkillLevel.EXPERT, "research",
                          keywords=["verification", "fact_checking", "validation"]),
                AgentSkill("source_evaluation", SkillLevel.ADVANCED, "research",
                          keywords=["credibility", "reliability", "authority"])
            ],
            capabilities=[
                AgentCapability("comprehensive_research", 0.9),
                AgentCapability("fact_extraction", 0.85),
                AgentCapability("source_citation", 0.8),
                AgentCapability("research_synthesis", 0.88)
            ],
            preferred_phases=[WorkflowPhaseType.RESEARCH, WorkflowPhaseType.OUTLINE],
            max_concurrent_tasks=4,
            priority=4
        )
    
    def _create_writing_specialist_config(self) -> AgentConfiguration:
        """Create a writing specialist agent configuration"""
        return AgentConfiguration(
            id="writing_specialist_001",
            name="Technical Writing Specialist", 
            agent_type=AgentType.WRITER,
            skills=[
                AgentSkill("technical_writing", SkillLevel.EXPERT, "writing",
                          keywords=["documentation", "technical", "clarity", "structure"]),
                AgentSkill("content_organization", SkillLevel.ADVANCED, "writing",
                          keywords=["structure", "organization", "flow", "hierarchy"]),
                AgentSkill("editing", SkillLevel.EXPERT, "writing",
                          keywords=["proofreading", "revision", "refinement"]),
                AgentSkill("style_adaptation", SkillLevel.ADVANCED, "writing",
                          keywords=["tone", "style", "audience", "adaptation"])
            ],
            capabilities=[
                AgentCapability("document_drafting", 0.9),
                AgentCapability("content_editing", 0.95),
                AgentCapability("style_consistency", 0.85),
                AgentCapability("readability_optimization", 0.8)
            ],
            preferred_phases=[WorkflowPhaseType.DRAFTING, WorkflowPhaseType.EDITING],
            max_concurrent_tasks=3,
            priority=4
        )
    
    def _create_technical_specialist_config(self) -> AgentConfiguration:
        """Create a technical specialist agent configuration"""
        return AgentConfiguration(
            id="technical_specialist_001",
            name="Technical Systems Specialist",
            agent_type=AgentType.TECHNICAL_EXPERT,
            skills=[
                AgentSkill("system_integration", SkillLevel.EXPERT, "technical",
                          keywords=["apis", "integration", "systems", "architecture"]),
                AgentSkill("data_processing", SkillLevel.ADVANCED, "technical",
                          keywords=["etl", "transformation", "processing", "pipelines"]),
                AgentSkill("automation", SkillLevel.EXPERT, "technical",
                          keywords=["workflow", "automation", "scripting", "orchestration"]),
                AgentSkill("quality_assurance", SkillLevel.ADVANCED, "technical",
                          keywords=["testing", "validation", "quality", "verification"])
            ],
            capabilities=[
                AgentCapability("workflow_automation", 0.9),
                AgentCapability("system_optimization", 0.85),
                AgentCapability("technical_validation", 0.88),
                AgentCapability("integration_management", 0.92)
            ],
            preferred_phases=[WorkflowPhaseType.INTAKE, WorkflowPhaseType.ORCHESTRATION],
            max_concurrent_tasks=4,
            priority=3
        )
    
    def register_agent(self, agent_config: AgentConfiguration):
        """Register a new agent configuration"""
        self.agents[agent_config.id] = agent_config
        
        # Update agent pools
        agent_type = agent_config.agent_type
        if agent_type not in self.agent_pools:
            self.agent_pools[agent_type] = []
        self.agent_pools[agent_type].append(agent_config.id)
        
        # Update skill registry
        for skill in agent_config.skills:
            if skill.name not in self.skill_registry:
                self.skill_registry[skill.name] = set()
            self.skill_registry[skill.name].add(agent_config.id)
        
        logger.info(f"Registered agent: {agent_config.name} ({agent_config.id})")
    
    def save_agent_config(self, agent_id: str):
        """Save agent configuration to YAML file"""
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not found")
        
        config = self.agents[agent_id]
        config_file = self.config_directory / f"{agent_id}.yaml"
        
        # Convert to serializable format
        config_data = {
            'id': config.id,
            'name': config.name,
            'agent_type': config.agent_type.value,
            'skills': [
                {
                    'name': skill.name,
                    'level': skill.level.value,
                    'domain': skill.domain,
                    'description': skill.description,
                    'keywords': skill.keywords,
                    'prerequisites': skill.prerequisites
                }
                for skill in config.skills
            ],
            'capabilities': [
                {
                    'name': cap.name,
                    'confidence': cap.confidence,
                    'experience_count': cap.experience_count,
                    'success_rate': cap.success_rate,
                    'specialization_tags': cap.specialization_tags
                }
                for cap in config.capabilities
            ],
            'preferred_phases': [phase.value for phase in config.preferred_phases],
            'max_concurrent_tasks': config.max_concurrent_tasks,
            'availability': config.availability,
            'priority': config.priority,
            'load_balancing_weight': config.load_balancing_weight,
            'metadata': config.metadata
        }
        
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f, default_flow_style=False, indent=2)
        
        logger.info(f"Saved agent configuration: {config_file}")
    
    def load_agent_config(self, config_file: Union[str, Path]) -> AgentConfiguration:
        """Load agent configuration from YAML file"""
        config_file = Path(config_file)
        
        with open(config_file, 'r') as f:
            config_data = yaml.safe_load(f)
        
        # Reconstruct agent configuration
        skills = [
            AgentSkill(
                name=skill_data['name'],
                level=SkillLevel(skill_data['level']),
                domain=skill_data['domain'],
                description=skill_data.get('description', ''),
                keywords=skill_data.get('keywords', []),
                prerequisites=skill_data.get('prerequisites', [])
            )
            for skill_data in config_data.get('skills', [])
        ]
        
        capabilities = [
            AgentCapability(
                name=cap_data['name'],
                confidence=cap_data['confidence'],
                experience_count=cap_data.get('experience_count', 0),
                success_rate=cap_data.get('success_rate', 1.0),
                specialization_tags=cap_data.get('specialization_tags', [])
            )
            for cap_data in config_data.get('capabilities', [])
        ]
        
        preferred_phases = [
            WorkflowPhaseType(phase) for phase in config_data.get('preferred_phases', [])
        ]
        
        return AgentConfiguration(
            id=config_data['id'],
            name=config_data['name'],
            agent_type=AgentType(config_data['agent_type']),
            skills=skills,
            capabilities=capabilities,
            preferred_phases=preferred_phases,
            max_concurrent_tasks=config_data.get('max_concurrent_tasks', 3),
            availability=config_data.get('availability', True),
            priority=config_data.get('priority', 1),
            load_balancing_weight=config_data.get('load_balancing_weight', 1.0),
            metadata=config_data.get('metadata', {})
        )
    
    def find_best_agent(self, required_skills: List[str], 
                       phase: WorkflowPhaseType,
                       task_complexity: float = 0.5,
                       agent_type_preference: Optional[AgentType] = None) -> Optional[str]:
        """Find the best agent for a task based on requirements"""
        
        candidates = []
        
        # Filter agents by type preference if specified
        if agent_type_preference:
            candidate_ids = self.agent_pools.get(agent_type_preference, [])
        else:
            candidate_ids = list(self.agents.keys())
        
        # Filter by availability
        available_agents = [
            agent_id for agent_id in candidate_ids
            if self.agents[agent_id].availability
        ]
        
        if not available_agents:
            logger.warning("No available agents found")
            return None
        
        # Calculate fitness scores
        for agent_id in available_agents:
            agent = self.agents[agent_id]
            fitness_score = agent.calculate_fitness_score(required_skills, phase, task_complexity)
            candidates.append((agent_id, fitness_score))
        
        # Sort by fitness score
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        if candidates:
            best_agent_id = candidates[0][0]
            logger.info(f"Selected agent {best_agent_id} with fitness score {candidates[0][1]:.3f}")
            return best_agent_id
        
        return None
    
    def assign_task(self, task_id: str, agent_id: str):
        """Assign a task to an agent"""
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not found")
        
        self.task_assignments[task_id] = agent_id
        logger.info(f"Assigned task {task_id} to agent {agent_id}")
    
    def get_agent_workload(self, agent_id: str) -> int:
        """Get current workload for an agent"""
        return sum(1 for assigned_agent in self.task_assignments.values() 
                  if assigned_agent == agent_id)
    
    def get_agents_by_skill(self, skill_name: str, min_level: SkillLevel = SkillLevel.INTERMEDIATE) -> List[str]:
        """Get agents that have a specific skill at minimum level"""
        matching_agents = []
        
        for agent_id in self.skill_registry.get(skill_name, set()):
            agent = self.agents[agent_id]
            skill_level = agent.get_skill_level(skill_name)
            if skill_level and skill_level.value >= min_level.value:
                matching_agents.append(agent_id)
        
        return matching_agents
    
    def get_agent_pool_stats(self) -> Dict[str, Any]:
        """Get statistics about agent pools"""
        stats = {
            'total_agents': len(self.agents),
            'available_agents': sum(1 for agent in self.agents.values() if agent.availability),
            'agent_types': {},
            'skills_coverage': {},
            'current_assignments': len(self.task_assignments)
        }
        
        # Agent type distribution
        for agent_type, agent_ids in self.agent_pools.items():
            stats['agent_types'][agent_type.value] = len(agent_ids)
        
        # Skills coverage
        for skill_name, agent_ids in self.skill_registry.items():
            stats['skills_coverage'][skill_name] = len(agent_ids)
        
        return stats
    
    def update_agent_performance(self, agent_id: str, capability_name: str, 
                                success: bool, execution_time: Optional[float] = None):
        """Update agent performance metrics"""
        if agent_id not in self.agents:
            logger.warning(f"Agent {agent_id} not found for performance update")
            return
        
        agent = self.agents[agent_id]
        
        # Find and update capability
        for capability in agent.capabilities:
            if capability.name.lower() == capability_name.lower():
                capability.experience_count += 1
                capability.last_used = datetime.now()
                
                # Update success rate with exponential moving average
                alpha = 0.1  # Learning rate
                if success:
                    capability.success_rate = capability.success_rate * (1 - alpha) + alpha
                else:
                    capability.success_rate = capability.success_rate * (1 - alpha)
                
                # Adjust confidence based on recent performance
                capability.confidence = min(0.95, capability.confidence * capability.success_rate)
                
                logger.info(f"Updated performance for agent {agent_id}, capability {capability_name}")
                break


class AgentPoolManager:
    """Manages agent pools and dynamic load balancing"""
    
    def __init__(self, config_manager: AgentConfigManager):
        self.config_manager = config_manager
        self.active_tasks: Dict[str, Dict[str, Any]] = {}  # task_id -> task_info
        
    async def distribute_tasks(self, tasks: List[Dict[str, Any]], 
                             phase: WorkflowPhaseType) -> Dict[str, List[str]]:
        """Distribute tasks across available agents"""
        
        agent_assignments = {}
        
        for task in tasks:
            task_id = task['id']
            required_skills = task.get('required_skills', [])
            complexity = task.get('complexity', 0.5)
            agent_type_pref = task.get('agent_type_preference')
            
            # Find best agent
            best_agent = self.config_manager.find_best_agent(
                required_skills=required_skills,
                phase=phase,
                task_complexity=complexity,
                agent_type_preference=agent_type_pref
            )
            
            if best_agent:
                if best_agent not in agent_assignments:
                    agent_assignments[best_agent] = []
                agent_assignments[best_agent].append(task_id)
                
                # Assign task
                self.config_manager.assign_task(task_id, best_agent)
                
                # Track active task
                self.active_tasks[task_id] = {
                    'agent_id': best_agent,
                    'phase': phase.value,
                    'start_time': datetime.now(),
                    'required_skills': required_skills
                }
            else:
                logger.warning(f"No suitable agent found for task {task_id}")
        
        return agent_assignments
    
    async def complete_task(self, task_id: str, success: bool, 
                          execution_time: Optional[float] = None):
        """Mark task as complete and update agent performance"""
        
        if task_id not in self.active_tasks:
            logger.warning(f"Task {task_id} not found in active tasks")
            return
        
        task_info = self.active_tasks[task_id]
        agent_id = task_info['agent_id']
        
        # Update agent performance for each required skill
        for skill in task_info['required_skills']:
            self.config_manager.update_agent_performance(
                agent_id=agent_id,
                capability_name=skill,
                success=success,
                execution_time=execution_time
            )
        
        # Remove from active tasks
        del self.active_tasks[task_id]
        
        # Remove from task assignments
        if task_id in self.config_manager.task_assignments:
            del self.config_manager.task_assignments[task_id]
        
        logger.info(f"Completed task {task_id} for agent {agent_id}")
    
    def get_load_balance_report(self) -> Dict[str, Any]:
        """Get load balancing report"""
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'active_tasks': len(self.active_tasks),
            'agent_workloads': {},
            'utilization_stats': {}
        }
        
        # Calculate workloads
        for agent_id in self.config_manager.agents:
            workload = self.config_manager.get_agent_workload(agent_id)
            max_capacity = self.config_manager.agents[agent_id].max_concurrent_tasks
            utilization = workload / max_capacity if max_capacity > 0 else 0
            
            report['agent_workloads'][agent_id] = {
                'current_tasks': workload,
                'max_capacity': max_capacity,
                'utilization': utilization,
                'available': self.config_manager.agents[agent_id].availability
            }
        
        # Overall utilization stats
        total_workload = sum(info['current_tasks'] for info in report['agent_workloads'].values())
        total_capacity = sum(info['max_capacity'] for info in report['agent_workloads'].values())
        
        report['utilization_stats'] = {
            'total_active_tasks': total_workload,
            'total_capacity': total_capacity,
            'overall_utilization': total_workload / total_capacity if total_capacity > 0 else 0
        }
        
        return report