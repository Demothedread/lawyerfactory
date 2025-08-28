"""
# Script Name: workflow_api.py
# Description: Handles workflow api functionality in the LawyerFactory system.
# Relationships:
#   - Entity Type: API
#   - Directory Group: Backend
#   - Group Tags: orchestration, api
"""

from typing import List

from .knowledge_graph import add_observation
from .models import STAGE_SEQUENCE, Task


def progress_task(task: Task, graph: dict | None = None) -> None:
    """Advance a task to the next stage and optionally log it."""
    task.advance()
    if graph is not None:
        msg = f"Task {task.id} moved to {task.stage.value}"
        add_observation(graph, msg)


def is_complete(task: Task) -> bool:
    """Return True if the task is at the final stage."""
    return task.stage == STAGE_SEQUENCE[-1]


class TaskBoard:
    def __init__(self, tasks: List[Task] | None = None) -> None:
        self.tasks: List[Task] = tasks or []

    def add_task(self, task: Task, graph: dict | None = None) -> None:
        self.tasks.append(task)
        if graph is not None:
            msg = f"Task {task.id} added at {task.stage.value}"
            add_observation(graph, msg)

    def assign_task(self, task_id: int, agent: str, graph: dict | None = None) -> None:
        for task in self.tasks:
            if task.id == task_id:
                task.assign(agent)
                if graph is not None:
                    msg = f"Task {task.id} assigned to {agent}"
                    add_observation(graph, msg)
                break

    def tasks_by_stage(self) -> dict:
        result: dict = {stage: [] for stage in STAGE_SEQUENCE}
        for task in self.tasks:
            result[task.stage].append(task)
        return result
