# Script Name: kanban_cli.py
# Description: Handles kanban cli functionality in the LawyerFactory system.
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Core
#   - Group Tags: null
from .models import STAGE_SEQUENCE
from .workflow import TaskBoard


def display_board(board: TaskBoard) -> str:
    lines = []
    for stage in STAGE_SEQUENCE:
        tasks = board.tasks_by_stage().get(stage, [])
        task_list = ', '.join(
            f"{t.id}:{t.title}" + (f" ({t.assignee})" if t.assignee else "")
            for t in tasks
        ) or '-'
        lines.append(f"{stage.value}: {task_list}")
    return '\n'.join(lines)
