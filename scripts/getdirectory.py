# Script Name: getdirectory.py
# Description: Async workspace tree lister  Usage: python scripts/list_workspace.py [PATH] [--max-depth N] [--json OUT.json] [--exclude PATTERN] [--show-hidden]  Produces a readable tree to stdout and optionally writes JSON metadata.
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Core
#   - Group Tags: null
Async workspace tree lister

Usage:
  python scripts/list_workspace.py [PATH] [--max-depth N] [--json OUT.json] [--exclude PATTERN] [--show-hidden]

Produces a readable tree to stdout and optionally writes JSON metadata.
"""
from __future__ import annotations

import argparse
import asyncio
import fnmatch
import json
import os
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Dict, List, Optional

# Constants for tree drawing
BRANCH = "├── "
LAST_BRANCH = "└── "
VERTICAL = "│   "
EMPTY_PREFIX = "    "


@dataclass
class EntryNode:
    name: str
    path: str
    is_dir: bool
    size: Optional[int] = None
    mtime: Optional[str] = None
    children: Optional[List["EntryNode"]] = None


async def scan_entry(
    path: str,
    depth: int,
    max_depth: int,
    exclude_patterns: List[str],
    show_hidden: bool
) -> EntryNode:
    """
    Recursively scan 'path' asynchronously (uses thread executor internally).
    Returns an EntryNode representing the entry and optionally its children.
    """
    try:
        stat_result = await asyncio.to_thread(os.stat, path, follow_symlinks=False)
    except Exception as exc:
        raise RuntimeError(f"Failed to stat path '{path}': {exc}") from exc

    name = os.path.basename(path) or path
    is_dir = os.path.isdir(path)
    mtime = datetime.fromtimestamp(stat_result.st_mtime).isoformat()
    size = stat_result.st_size if not is_dir else None

    node = EntryNode(name=name, path=path, is_dir=is_dir, size=size, mtime=mtime)

    if is_dir and (max_depth < 0 or depth < max_depth):
        try:
            entries = await asyncio.to_thread(list, os.scandir(path))
        except PermissionError:
            node.children = []
            return node
        except FileNotFoundError:
            node.children = []
            return node
        except Exception as exc:
            raise RuntimeError(f"Failed to read directory '{path}': {exc}") from exc

        children_nodes: List[EntryNode] = []
        entries_sorted = sorted(entries, key=lambda e: (not e.is_dir(), e.name.lower()))
        for entry in entries_sorted:
            entry_name = entry.name
            # Hidden files start with dot on UNIX; simple check
            if not show_hidden and entry_name.startswith("."):
                continue
            full_path = os.path.join(path, entry_name)
            excluded = any(fnmatch.fnmatch(entry_name, pat) for pat in exclude_patterns)
            if excluded:
                continue
            try:
                child_node = await scan_entry(
                    full_path,
                    depth + 1,
                    max_depth,
                    exclude_patterns,
                    show_hidden,
                )
            except Exception:
                # On error scanning child, represent it but continue
                child_node = EntryNode(
                    name=entry_name,
                    path=full_path,
                    is_dir=entry.is_dir(follow_symlinks=False),
                    size=None,
                    mtime=None,
                    children=[],
                )
            children_nodes.append(child_node)
        node.children = children_nodes
    else:
        node.children = [] if is_dir else None

    return node


def format_tree(node: EntryNode, prefix: str = "") -> str:
    """
    Format EntryNode tree into printable string lines with unicode branches.
    """
    lines: List[str] = []
    header = node.name or node.path
    if node.is_dir:
        header = f"{header}/"
    lines.append(header)

    def _format_children(children: List[EntryNode], current_prefix: str) -> None:
        for idx, child in enumerate(children):
            is_last = idx == (len(children) - 1)
            branch = LAST_BRANCH if is_last else BRANCH
            line = f"{current_prefix}{branch}{child.name}{'/' if child.is_dir else ''}"
            lines.append(line)
            if child.children:
                next_prefix = current_prefix + (EMPTY_PREFIX if is_last else VERTICAL)
                _format_children(child.children, next_prefix)

    if node.children:
        _format_children(node.children, prefix)

    return "\n".join(lines)


async def write_json(output_path: str, root_node: EntryNode) -> None:
    """
    Write JSON representation to file using a thread executor.
    """
    try:
        json_data = asdict(root_node)
        await asyncio.to_thread(
            _write_json_sync, output_path, json_data
        )
    except Exception as exc:
        raise RuntimeError(f"Failed to write JSON to '{output_path}': {exc}") from exc


def _write_json_sync(output_path: str, data: Dict) -> None:
    """
    Synchronous JSON writer used via asyncio.to_thread.
    """
    directory = os.path.dirname(output_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Async workspace tree lister")
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Root path to list (default: current directory)",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=5,
        help="Maximum recursion depth (-1 for unlimited). Default: 5",
    )
    parser.add_argument(
        "--json",
        dest="json_out",
        default=None,
        help="Path to write JSON output (optional)",
    )
    parser.add_argument(
        "--exclude",
        dest="exclude",
        action="append",
        default=[],
        help="Glob pattern to exclude (can be repeated)",
    )
    parser.add_argument(
        "--show-hidden",
        dest="show_hidden",
        action="store_true",
        help="Include hidden files and directories",
    )
    return parser.parse_args(argv)


async def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    root_path = args.path
    max_depth = args.max_depth
    exclude_patterns = args.exclude
    show_hidden = args.show_hidden
    json_out = args.json_out

    if not os.path.exists(root_path):
        print(f"Error: Path does not exist: {root_path}", file=sys.stderr)
        return 2

    try:
        root_node = await scan_entry(
            os.path.abspath(root_path),
            depth=0,
            max_depth=max_depth,
            exclude_patterns=exclude_patterns,
            show_hidden=show_hidden,
        )
    except Exception as exc:
        print(f"Error scanning workspace: {exc}", file=sys.stderr)
        return 3

    tree_text = format_tree(root_node)
    print(tree_text)

    if json_out:
        try:
            await write_json(json_out, root_node)
            print(f"\nJSON written to: {json_out}")
        except Exception as exc:
            print(f"Error writing JSON: {exc}", file=sys.stderr)
            return 4

    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
    except KeyboardInterrupt:
        print("Cancelled by user", file=sys.stderr)
        exit_code = 130
    except Exception as exc:
        print(f"Unhandled error: {exc}", file=sys.stderr)
        exit_code