import pathlib
import sys
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))  # noqa: E402

from lawyerfactory.models import Task, Stage  # noqa: E402
from lawyerfactory.workflow import progress_task, is_complete  # noqa: E402


def test_progress_task_advances_stage_and_logs():
    task = Task(id=1, title="example")
    graph = {"observations": []}
    assert task.stage == Stage.PREPRODUCTION_PLANNING
    progress_task(task, graph)
    assert task.stage == Stage.RESEARCH_AND_DEVELOPMENT
    assert graph["observations"]


def test_is_complete():
    task = Task(id=1, title="example", stage=Stage.FINAL_DRAFT)
    assert is_complete(task)
