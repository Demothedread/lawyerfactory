# Script Name: lf.py
# Description: Handles lf functionality in the LawyerFactory system.
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Core
#   - Group Tags: null

from __future__ import annotations

import argparse
import asyncio

from .one_click_case_builder import build_case_package, collect_intake_answers


def display_board(board) -> str:
    """Render a simple stage board if legacy board objects are provided."""
    if not hasattr(board, "tasks_by_stage"):
        return "No board renderer available for this object."

    lines: list[str] = []
    tasks_by_stage = board.tasks_by_stage()
    for stage, tasks in tasks_by_stage.items():
        task_list = ", ".join(
            f"{getattr(task, 'id', '?')}:{getattr(task, 'title', 'Untitled')}"
            + (f" ({getattr(task, 'assignee', None)})" if getattr(task, "assignee", None) else "")
            for task in tasks
        ) or "-"
        lines.append(f"{stage}: {task_list}")
    return "\n".join(lines)


async def _run_one_click(output_dir: str) -> int:
    answers = collect_intake_answers()
    result = await build_case_package(answers, output_dir=output_dir)
    print("\n✅ One-click package complete")
    print(f"Case ID: {result.case_id}")
    print(f"Evidence files indexed: {result.evidence_count}")
    print(f"Output PDF: {result.output_path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="LawyerFactory CLI")
    subparsers = parser.add_subparsers(dest="command")

    one_click = subparsers.add_parser(
        "one-click-done",
        help="Collect intake answers and generate a ready-to-file PDF package",
    )
    one_click.add_argument(
        "--output-dir",
        default="output/cli",
        help="Directory for generated package output",
    )

    args = parser.parse_args()
    if args.command == "one-click-done":
        return asyncio.run(_run_one_click(output_dir=args.output_dir))

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
