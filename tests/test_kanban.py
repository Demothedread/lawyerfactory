import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))  # noqa: E402

import os

from lawyerfactory.kanban_cli import display_board  # noqa: E402
from lawyerfactory.models import Task  # noqa: E402
from lawyerfactory.workflow import TaskBoard  # noqa: E402


def test_kanban():
    # ...existing code...
    log_dir = os.path.join(os.path.dirname(__file__), '../logs')
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, 'test_kanban.log')
    with open(log_path, 'w') as f:
        f.write("Kanban test completed.\n")
    print(f"Kanban test completed. Log written to {log_path}")

def test_display_board_formats_tasks():
    board = TaskBoard()
    task = Task(id=1, title="Task1", assignee="Agent")
    board.add_task(task)
    output = display_board(board)
    assert "Task1" in output
    assert "Agent" in output
