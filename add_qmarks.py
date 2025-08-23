import os
import sys
import argparse
from typing import List

def fix_headers_in_file(path: str, backup: bool = True, apply_changes: bool = True) -> bool:
    """Ensure triple quote at start if file contains a docstring later.

    Returns True if the file would be changed (or was changed).
    If apply_changes is False, do not modify files; only analyze.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except (OSError, UnicodeDecodeError) as exc:
        print(f"Skipping unreadable file: {path} ({exc})")
        return False

    if not lines:
        return False

    # Look for triple-quote anywhere (docstring later) but check whether file
    # already starts with a triple-quote after optional shebang/encoding lines.
    has_docstring = any('"""' in line for line in lines)
    # Skip over common first-line markers (shebang, encoding comment, blank lines)
    idx = 0
    while idx < len(lines) and lines[idx].strip() in ("",) or lines[idx].lstrip().startswith(("#!", "# -*-")):
        idx += 1
    starts_with_docstring = idx < len(lines) and lines[idx].lstrip().startswith('"""')

    if has_docstring and not starts_with_docstring:
        if apply_changes:
            try:
                print(f"Fixing: {path}")
                if backup:
                    os.rename(path, path + ".bak")
                new_lines = ['"""\n'] + lines
                with open(path, "w", encoding="utf-8") as f:
                    f.writelines(new_lines)
            except OSError as exc:
                print(f"Error updating {path}: {exc}")
                return False
        return True
    return False

def scan_directory(root_dir: str, extensions=(".py",), depth: int = None, apply_changes: bool = True) -> List[str]:
    """Walk directory and either fix files or return the list of files that would be changed.

    depth: optional max depth (None means unlimited). Returns list of affected files.
    apply_changes: when False, only analyze and collect filenames.
    """
    affected: List[str] = []
    root_depth = len(os.path.abspath(root_dir).split(os.sep))
    for dirpath, _, filenames in os.walk(root_dir):
        if depth is not None:
            cur_depth = len(os.path.abspath(dirpath).split(os.sep)) - root_depth
            if cur_depth > depth:
                continue
        for fname in filenames:
            if fname.endswith(extensions):
                path = os.path.join(dirpath, fname)
                try:
                    changed = fix_headers_in_file(path, apply_changes=apply_changes)
                except Exception as exc:
                    print(f"Error processing {path}: {exc}")
                    changed = False
                if changed:
                    affected.append(path)
    return affected

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ensure files with docstrings start with a triple-quote header.")
    parser.add_argument("target", help="Path to file or directory")
    parser.add_argument("--analyze", action="store_true", help="List files that would be changed and print a count (no write).")
    parser.add_argument("--extensions", default=".py", help="Comma-separated file extensions to include (default: .py)")
    parser.add_argument("--depth", type=int, default=None, help="Max directory depth to scan (0 = root only)")
    parser.add_argument("--no-backup", action="store_true", help="Do not create .bak backups when modifying files")
    args = parser.parse_args()

    exts = tuple(s if s.startswith(".") else f".{s}" for s in args.extensions.split(","))
    apply_changes_flag = not args.analyze

    target = args.target
    affected_files = []
    if os.path.isfile(target):
        changed = fix_headers_in_file(target, backup=not args.no_backup, apply_changes=apply_changes_flag)
        if changed:
            affected_files.append(target)
    else:
        affected_files = scan_directory(target, extensions=exts, depth=args.depth, apply_changes=apply_changes_flag)

    if args.analyze:
        if affected_files:
            print("\nFiles that would be changed:")
            for p in affected_files:
                print(p)
        else:
            print("No files would be changed.")
        print(f"\nTotal files affected: {len(affected_files)}")
    else:
        print(f"Completed. Files changed: {len(affected_files)}")