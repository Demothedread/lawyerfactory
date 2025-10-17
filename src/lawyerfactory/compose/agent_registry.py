"""
# Script Name: agent_registry.py
# Description: Agent configuration and registry for LawyerFactory orchestration system
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Orchestration
#   - Group Tags: null
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class AgentConfig:
    """Configuration class for AI agents in the orchestration system"""

    agent_type: str
    config: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.config is None:
            self.config = {}


class AgentInterface:
    """Base interface for all AI agents in the system"""

    def __init__(self, config: AgentConfig):
        self.config = config
        self.agent_type = config.agent_type

    async def execute_task(self, task, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a workflow task"""
        raise NotImplementedError("Subclasses must implement execute_task")

    async def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate input data"""
        return {"valid": True, "errors": []}

    def get_capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities"""
        return {
            "agent_type": self.agent_type,
            "supported_tasks": [],
            "configuration": self.config.config if self.config.config else {}
        }