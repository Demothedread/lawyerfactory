import pathlib
import sys
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))  # noqa: E402

from lawyerfactory.models import Task  # noqa: E402
from lawyerfactory.workflow import TaskBoard  # noqa: E402
from lawyerfactory.kanban_cli import display_board  # noqa: E402


def test_display_board_formats_tasks():
    board = TaskBoard()
    task = Task(id=1, title="Task1", assignee="Agent")
    board.add_task(task)
    output = display_board(board)
    assert "Task1" in output
    assert "Agent" in output
