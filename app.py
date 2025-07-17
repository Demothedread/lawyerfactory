from lawyerfactory.knowledge_graph import (
    load_graph,
    save_graph,
    add_observation,
)
from lawyerfactory.models import Task
from lawyerfactory.workflow import TaskBoard, progress_task
from lawyerfactory.kanban_cli import display_board


def main() -> None:
    graph = load_graph()
    add_observation(graph, "Application run")

    board = TaskBoard()
    board.add_task(Task(id=1, title="Prepare complaint"), graph)
    board.add_task(Task(id=2, title="Draft summons"), graph)

    board.assign_task(1, "ResearchAgent", graph)
    board.assign_task(2, "DraftingAgent", graph)

    print(display_board(board))

    # Example progress through stages
    progress_task(board.tasks[0], graph)
    print("\nAfter progressing task 1:\n")
    print(display_board(board))

    save_graph(graph)


if __name__ == "__main__":
    main()
