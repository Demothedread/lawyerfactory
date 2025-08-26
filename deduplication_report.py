# Script Name: deduplication_report.py
# Description: !/usr/bin/env python3
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Core
#   - Group Tags: null
"""
deduplication_report.py — Identify and report duplicate/redundant files for staging.

Usage:
  python deduplication_report.py --analyze  # Analyze and report duplicates
  python deduplication_report.py --stage    # Stage duplicates to trash

Description:
  This script identifies duplicate and redundant files according to the workflow heuristics:
  - Files ≥90% code-identical
  - Deprecated shims and pass-through imports
  - Case-specific files that don't belong in main codebase
"""

import json
import os
import re
import shutil  # added for robust moves
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple


def identify_deprecated_shims() -> List[Dict]:
    """Identify deprecated shim files that redirect to new locations"""
    shims = []

    # Check maestro directory for deprecated shims
    maestro_dir = Path("maestro")
    if maestro_dir.exists():
        for py_file in maestro_dir.rglob("*.py"):
            try:
                with open(py_file, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                if (
                    "AUTO-GENERATED SHIM" in content
                    and "will be removed in next release" in content
                ):
                    # Extract redirect target
                    redirect_match = re.search(r"import.*from ([^#\n]+)", content)
                    redirect_target = (
                        redirect_match.group(1).strip() if redirect_match else "unknown"
                    )

                    shims.append(
                        {
                            "file": str(py_file),
                            "type": "deprecated_shim",
                            "reason": "Auto-generated shim marked for removal",
                            "redirects_to": redirect_target,
                            "size_lines": len(content.splitlines()),
                            "action": "stage_to_trash",
                        }
                    )
            except Exception as e:
                print(f"Error reading {py_file}: {e}")

    return shims


def identify_duplicate_implementations() -> List[Dict]:
    """Identify duplicate implementations of the same functionality"""
    duplicates = []

    # Known duplicate patterns
    duplicate_patterns = [
        {
            "pattern": "maestro",
            "files": [
                "maestro/enhanced_maestro.py",
                "src/lawyerfactory/compose/maestro/enhanced_maestro.py",
                "src/lawyerfactory/phases/phaseC02_orchestration/maestro/enhanced_maestro.py",
            ],
            "reason": "Multiple maestro implementations - keep the main one in compose/maestro",
        },
        {
            "pattern": "file_storage",
            "files": [
                "lawyerfactory/file-storage.py",
                "src/lawyerfactory/file_storage.py",
                "src/lawyerfactory/infra/file_storage.py",
                "src/lawyerfactory/infra/file_storage_api.py",
            ],
            "reason": "Multiple file storage implementations - consolidate to infra/file_storage.py",
        },
    ]

    for pattern in duplicate_patterns:
        existing_files = []
        for file_path in pattern["files"]:
            if Path(file_path).exists():
                existing_files.append(file_path)

        if len(existing_files) > 1:
            # Mark all but the first as duplicates
            for i, file_path in enumerate(existing_files[1:], 1):
                file_info = Path(file_path)
                try:
                    with open(file_info, "r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()

                    duplicates.append(
                        {
                            "file": file_path,
                            "type": "duplicate_implementation",
                            "reason": pattern["reason"],
                            "keep_instead": existing_files[0],
                            "size_lines": len(lines),
                            "action": "stage_to_trash",
                        }
                    )
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")

    return duplicates


def identify_case_specific_files() -> List[Dict]:
    """Identify case-specific files that don't belong in main codebase"""
    case_files = []

    # Tesla directory - appears to be case-specific data
    tesla_dir = Path("Tesla")
    if tesla_dir.exists():
        for file_path in tesla_dir.rglob("*"):
            if file_path.is_file():
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        lines = content.splitlines()

                    case_files.append(
                        {
                            "file": str(file_path),
                            "type": "case_specific",
                            "reason": "Tesla case-specific data file",
                            "size_lines": len(lines),
                            "action": "stage_to_trash",
                        }
                    )
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")

    return case_files


def identify_empty_or_minimal_files() -> List[Dict]:
    """Identify empty files or files with minimal content"""
    minimal_files = []

    for py_file in Path(".").rglob("*.py"):
        try:
            with open(py_file, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
                non_empty_lines = [line for line in lines if line.strip()]

            # Files with 0-1 lines of actual content
            if len(non_empty_lines) <= 1:
                minimal_files.append(
                    {
                        "file": str(py_file),
                        "type": "minimal_content",
                        "reason": f"Only {len(non_empty_lines)} lines of actual content",
                        "size_lines": len(lines),
                        "action": "stage_to_trash",
                    }
                )
        except Exception as e:
            print(f"Error reading {py_file}: {e}")

    return minimal_files


def generate_deduplication_report() -> Dict:
    """Generate comprehensive deduplication report"""
    report = {
        "generated_at": datetime.now().isoformat(),
        "total_files_analyzed": 0,
        "redundant_files": [],
    }

    # Collect all redundant files
    redundant_files = []

    print("Analyzing deprecated shims...")
    shims = identify_deprecated_shims()
    redundant_files.extend(shims)
    print(f"Found {len(shims)} deprecated shims")

    print("Analyzing duplicate implementations...")
    duplicates = identify_duplicate_implementations()
    redundant_files.extend(duplicates)
    print(f"Found {len(duplicates)} duplicate implementations")

    print("Analyzing case-specific files...")
    case_files = identify_case_specific_files()
    redundant_files.extend(case_files)
    print(f"Found {len(case_files)} case-specific files")

    print("Analyzing minimal files...")
    minimal_files = identify_empty_or_minimal_files()
    redundant_files.extend(minimal_files)
    print(f"Found {len(minimal_files)} minimal files")

    report["redundant_files"] = redundant_files
    report["total_redundant"] = len(redundant_files)

    return report


def stage_files_to_trash(redundant_files: List[Dict]):
    """Stage redundant files to trash directory (robust handling for existing special files).

    Behavior changes:
    - Prefer an existing 'trash' directory if present and a directory; otherwise use '_trash_staging'.
    - If any parent path component exists as a file (e.g. 'trash/#file:staged_for_evaluation'), route the file
      into trash/conflicts/ to avoid attempting to mkdir over a file.
    - If the target file already exists, append a timestamp suffix to avoid overwriting.
    - Use shutil.move for reliability across filesystems.
    """
    # Prefer existing 'trash' directory in repo root when available (per provided context)
    candidate_trash = Path("trash")
    if candidate_trash.exists() and candidate_trash.is_dir():
        trash_dir = candidate_trash
    else:
        trash_dir = Path("_trash_staging")

    # Ensure trash_dir is a usable directory; if a file exists at that path, fallback
    if trash_dir.exists() and not trash_dir.is_dir():
        print(
            f"Warning: {trash_dir} exists and is not a directory. Falling back to '_trash_staging'."
        )
        trash_dir = Path("_trash_staging")

    trash_dir.mkdir(parents=True, exist_ok=True)

    manifest = {"staged_at": datetime.now().isoformat(), "staged_files": []}

    def ensure_parent_dir(target_path: Path) -> Path:
        """Ensure parent dir exists; if any parent is a file, return a safe conflicts path."""
        parent = target_path.parent
        try:
            # Walk up and detect any file-on-the-way
            cur = parent
            while cur != cur.parent and cur != trash_dir.parent:
                if cur.exists() and cur.is_file():
                    # Conflict: a file exists where we need a directory
                    conflict_dir = trash_dir / "conflicts"
                    conflict_dir.mkdir(parents=True, exist_ok=True)
                    return conflict_dir
                cur = cur.parent
            parent.mkdir(parents=True, exist_ok=True)
            return parent
        except Exception as e:
            # On any unexpected error, route to conflicts
            conflict_dir = trash_dir / "conflicts"
            conflict_dir.mkdir(parents=True, exist_ok=True)
            print(
                f"Warning: cannot create parent dir for {target_path}: {e}. Routing to {conflict_dir}"
            )
            return conflict_dir

    for file_info in redundant_files:
        source_path = Path(file_info["file"])
        if not source_path.exists():
            print(f"Skipping missing file: {source_path}")
            continue

        # Compute a safe relative path; fall back to basename if not under cwd
        try:
            relative_path = source_path.relative_to(Path.cwd())
        except ValueError:
            relative_path = Path(source_path.name)

        trash_path = trash_dir / relative_path

        # Ensure parent directory and handle parent-as-file conflicts
        safe_parent = ensure_parent_dir(trash_path)
        trash_path = safe_parent / trash_path.name

        # If target exists, append timestamp suffix to avoid overwriting
        if trash_path.exists():
            ts = datetime.now().strftime("%Y%m%d%H%M%S")
            trash_path = trash_path.with_name(f"{trash_path.name}.dup.{ts}")

        try:
            # Use shutil.move for better cross-filesystem behavior
            shutil.move(str(source_path), str(trash_path))

            manifest["staged_files"].append(
                {
                    "original_path": str(source_path),
                    "trash_path": str(trash_path),
                    "type": file_info.get("type"),
                    "reason": file_info.get("reason"),
                    "size_lines": file_info.get("size_lines"),
                }
            )

            print(f"✓ Staged {source_path} -> {trash_path}")

        except Exception as e:
            print(f"✗ Error staging {source_path} -> {trash_path}: {e}")

    # Write manifest with encoding and error handling
    manifest_path = trash_dir / "staging_manifest.json"
    try:
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        print(f"\nStaging complete. Manifest saved to {manifest_path}")
    except Exception as e:
        print(f"Error writing manifest to {manifest_path}: {e}")

    return manifest


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Deduplication analysis and staging")
    parser.add_argument(
        "--analyze", action="store_true", help="Analyze and report duplicates"
    )
    parser.add_argument(
        "--stage", action="store_true", help="Stage duplicates to trash"
    )
    parser.add_argument(
        "--report-file", default="redundancy_report.json", help="Report output file"
    )

    args = parser.parse_args()

    if not args.analyze and not args.stage:
        args.analyze = True  # Default to analyze

    if args.analyze:
        print("Generating deduplication report...")
        report = generate_deduplication_report()

        with open(args.report_file, "w") as f:
            json.dump(report, f, indent=2)

        print(f"\nReport saved to {args.report_file}")
        print(f"Total redundant files identified: {report['total_redundant']}")

        # Print summary
        type_counts = {}
        for file_info in report["redundant_files"]:
            file_type = file_info["type"]
            type_counts[file_type] = type_counts.get(file_type, 0) + 1

        print("\nBreakdown by type:")
        for file_type, count in type_counts.items():
            print(f"  {file_type}: {count}")

    if args.stage:
        # Load report if not already generated
        if not args.analyze:
            try:
                with open(args.report_file, "r") as f:
                    report = json.load(f)
            except FileNotFoundError:
                print(f"Report file {args.report_file} not found. Run --analyze first.")
                return

        print(f"\nStaging {len(report['redundant_files'])} files to trash...")
        manifest = stage_files_to_trash(report["redundant_files"])


if __name__ == "__main__":
    main()
