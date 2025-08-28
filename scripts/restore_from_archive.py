#!/usr/bin/env python3
import os
from pathlib import Path
import subprocess
import sys
from typing import Iterable

ARCHIVE_ROOTS = [
    Path("archive"),
    Path("archive_zip"),
]

# Any path segments that indicate the “project root” anchor.
# Everything *after* the first occurrence of one of these anchors is treated as the intended target location.
ANCHORS = ["src", "tests", "docs", "examples", "scripts"]


def iter_archive_files() -> Iterable[Path]:
    for root in ARCHIVE_ROOTS:
        if root.exists():
            for p in root.rglob("*"):
                if p.is_file():
                    yield p


def split_at_anchor(p: Path):
    """
    Given an archive path, find the first occurrence of an anchor (e.g., 'src')
    and return (anchor, tail_path_from_anchor). If no anchor found, return (None, None).
    """
    parts = p.parts
    for i, part in enumerate(parts):
        if part in ANCHORS:
            anchor = part
            tail = Path(*parts[i + 1 :])
            return anchor, tail
    return None, None


def is_tracked(path: Path) -> bool:
    try:
        subprocess.run(
            ["git", "ls-files", "--error-unmatch", str(path)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def git_mv(src: Path, dst: Path) -> bool:
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(["git", "mv", str(src), str(dst)], check=True)
        return True
    except subprocess.CalledProcessError:
        return False


def shell_mv(src: Path, dst: Path) -> bool:
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        src.rename(dst)
        return True
    except Exception:
        # Fallback to system mv (handles cross-device moves)
        import shutil

        try:
            shutil.move(str(src), str(dst))
            return True
        except Exception as e:
            print(f"ERROR: could not move {src} -> {dst}: {e}")
            return False


def main():
    repo_root = Path(".").resolve()
    print(f"Repo root: {repo_root}")

    candidates = []
    for f in iter_archive_files():
        anchor, tail = split_at_anchor(f)
        if anchor and tail and tail.name not in {".DS_Store"}:
            target = repo_root / anchor / tail
            candidates.append((f, target))

    if not candidates:
        print("No restorable files found under archive paths with anchors", ANCHORS)
        sys.exit(0)

    print("\nFound potential restores:")
    for i, (src, dst) in enumerate(candidates, 1):
        print(f"[{i}] {src} -> {dst}")

    print("\nProceed interactively. Answer y/N per file.\n")

    for src, dst in candidates:
        rel_src = src.relative_to(repo_root)
        rel_dst = dst.relative_to(repo_root)
        # Skip if destination already exists (avoid clobber)
        if dst.exists():
            print(f"SKIP (exists): {rel_dst}")
            continue

        ans = input(f"Restore {rel_src} -> {rel_dst}? [y/N] ").strip().lower()
        if ans != "y":
            print("  skipped.")
            continue

        if is_tracked(src):
            ok = git_mv(src, dst)
            method = "git mv"
        else:
            ok = shell_mv(src, dst)
            method = "mv"

        if ok:
            print(f"  restored via {method}.")
        else:
            print("  FAILED to restore.")

    print("\nDone. Review with: git status")


if __name__ == "__main__":
    main()
