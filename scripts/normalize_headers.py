#!/usr/bin/env python3
"""
normalize_headers.py — Apply standard header schema to Python files in the codebase.

Usage:
  python normalize_headers.py --dry-run  # Preview changes
  python normalize_headers.py --apply     # Apply changes in-place
  python normalize_headers.py --apply --files src/lawyerfactory/compose/maestro/enhanced_maestro.py  # Specific files

Description:
  This script applies the standard header schema to Python files, preserving license headers
  and ensuring consistent documentation across the codebase.
"""

import argparse
import os
from pathlib import Path
import re
from typing import Dict, List, Optional, Tuple

# Standard header template
HEADER_TEMPLATE = """# Script Name: {filename}
# Description: {description}
# Relationships:
#   - Entity Type: {entity_type}
#   - Directory Group: {directory_group}
#   - Group Tags: {group_tags}
"""

# Script Name: normalize_headers.py
# Description: !/usr/bin/env python3
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Core
#   - Group Tags: null
def infer_file_metadata(filepath: Path) -> Dict[str, str]:
    """Infer metadata about a file from its path and content"""
    # Ensure we are working with an absolute/resolved path to avoid relative/absolute mix-ups
    project_root = Path.cwd().resolve()
    if not isinstance(filepath, Path):
        filepath = Path(filepath)
    try:
        filepath_resolved = filepath.resolve(strict=False)
    except Exception:
        filepath_resolved = (project_root / filepath).resolve(strict=False)

    filename = filepath_resolved.name
    # Try to compute a path relative to the project root; fall back to a safe string if not possible
    try:
        relative_path = str(filepath_resolved.relative_to(project_root))
    except Exception:
        # Fallback: strip the project_root prefix if present, else use absolute path
        rp = str(filepath_resolved)
        pr = str(project_root)
        relative_path = rp.split(pr, 1)[-1].lstrip(os.sep) if pr in rp else rp

    # Infer entity type from file structure and name
    if "test" in filename.lower() or "test" in relative_path:
        entity_type = "Test"
    elif "api" in relative_path or "routes" in relative_path:
        entity_type = "API"
    elif "ui" in relative_path or "templates" in relative_path:
        entity_type = "UI Component"
    elif "model" in filename.lower() or "schema" in filename.lower():
        entity_type = "Data Model"
    elif "config" in filename.lower() or "settings" in filename.lower():
        entity_type = "Configuration"
    elif "util" in filename.lower() or "helper" in filename.lower():
        entity_type = "Utility"
    elif "bot" in filename.lower() or "agent" in filename.lower():
        entity_type = "Agent"
    elif "engine" in filename.lower() or "processor" in filename.lower():
        entity_type = "Engine"
    else:
        entity_type = "Module"

    # Infer directory group
    if (
        "ui" in relative_path
        or "templates" in relative_path
        or "static" in relative_path
    ):
        directory_group = "Frontend"
    elif "api" in relative_path or "routes" in relative_path:
        directory_group = "Backend"
    elif "storage" in relative_path or "data" in relative_path:
        directory_group = "Storage"
    elif "ingest" in relative_path or "ingestion" in relative_path:
        directory_group = "Ingestion"
    elif "research" in relative_path or "kg" in relative_path:
        directory_group = "Research"
    elif "document" in relative_path or "export" in relative_path:
        directory_group = "Document Generation"
    elif "phases" in relative_path:
        directory_group = "Workflow"
    elif "compose" in relative_path or "maestro" in relative_path:
        directory_group = "Orchestration"
    else:
        directory_group = "Core"

    # Infer group tags
    tags = []
    if "maestro" in relative_path:
        tags.append("orchestration")
    if "knowledge" in relative_path or "kg" in relative_path:
        tags.append("knowledge-graph")
    if "claims" in relative_path:
        tags.append("claims-analysis")
    if "evidence" in relative_path:
        tags.append("evidence-processing")
    if "research" in relative_path:
        tags.append("legal-research")
    if "ui" in relative_path:
        tags.append("user-interface")
    if "api" in relative_path:
        tags.append("api")
    if "test" in filename.lower():
        tags.append("testing")

    group_tags = ", ".join(tags) if tags else "null"

    return {
        "filename": filename,
        "entity_type": entity_type,
        "directory_group": directory_group,
        "group_tags": group_tags,
    }


def extract_existing_description(filepath: Path) -> str:
    """Extract existing description from file docstring or comments"""
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        # Look for docstring
        if len(lines) > 0 and lines[0].strip().startswith('"""'):
            # Multi-line docstring
            description_lines = []
            for line in lines[1:]:
                if line.strip().endswith('"""'):
                    break
                description_lines.append(line.strip())
            if description_lines:
                return " ".join(description_lines).strip()

        # Look for existing description comment
        for line in lines[:10]:
            if "# description:" in line.lower() or "# desc:" in line.lower():
                return line.split(":", 1)[1].strip()

        # Look for any meaningful comment in first 10 lines
        for line in lines[:10]:
            if line.strip().startswith("#") and len(line.strip()) > 10:
                comment = line.strip()[1:].strip()
                if not any(
                    skip in comment.lower()
                    for skip in ["copyright", "license", "author", "todo", "fixme"]
                ):
                    return comment

        # Infer from filename and path
        filename = filepath.stem.replace("_", " ").replace("-", " ")
        return f"Handles {filename} functionality in the LawyerFactory system."

    except Exception:
        return f"Handles {filepath.stem} functionality in the LawyerFactory system."


def find_license_header(lines: List[str]) -> int:
    """Find where license header ends (if any)"""
    for i, line in enumerate(lines[:20]):
        if any(
            license_term in line.lower()
            for license_term in ["copyright", "license", "mit", "apache", "gpl"]
        ):
            # Look for end of license block
            for j in range(i + 1, min(i + 20, len(lines))):
                if lines[j].strip() == "" and (
                    j + 1 >= len(lines) or lines[j + 1].strip() == ""
                ):
                    return j + 1
            return i + 1
    return 0


def normalize_file_header(filepath: Path, dry_run: bool = True) -> Tuple[bool, str]:
    """Normalize header for a single file"""
    try:
        # Normalize path to absolute (non-strict) to avoid relative/absolute mismatches
        if not isinstance(filepath, Path):
            filepath = Path(filepath)
        filepath = filepath.resolve(strict=False)

        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            original_lines = f.readlines()

        if not original_lines:
            return False, "Empty file"

        # Find where to insert new header
        license_end = find_license_header(original_lines)

        # Extract existing description
        description = extract_existing_description(filepath)

        # Get metadata
        metadata = infer_file_metadata(filepath)

        # Create new header
        new_header = HEADER_TEMPLATE.format(description=description, **metadata)

        # Find where current header ends (look for first non-comment, non-empty line)
        header_end = license_end
        for i in range(license_end, min(license_end + 25, len(original_lines))):
            line = original_lines[i]
            if (
                not line.strip().startswith("#")
                and not line.strip().startswith('"""')
                and line.strip() != ""
            ):
                header_end = i
                break

        # Create new content
        new_lines = (
            original_lines[:license_end]  # License header
            + [new_header]  # New standard header
            + original_lines[header_end:]  # Rest of file
        )

        # Check if changes are needed
        new_content = "".join(new_lines)
        original_content = "".join(original_lines)

        if new_content == original_content:
            return False, "No changes needed"

        if dry_run:
            return True, f"Would update header in {filepath}"

        # Write changes
        with open(filepath, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

        return True, f"Updated header in {filepath}"

    except Exception as e:
        return False, f"Error processing {filepath}: {e}"


def main():
    parser = argparse.ArgumentParser(description="Normalize file headers")
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes without applying"
    )
    parser.add_argument("--apply", action="store_true", help="Apply changes in-place")
    parser.add_argument("--files", nargs="*", help="Specific files to process")

    args = parser.parse_args()

    if not args.dry_run and not args.apply:
        args.dry_run = True  # Default to dry run

    # Find files to process
    project_root = Path.cwd().resolve()
    if args.files:
        files = [Path(f).resolve(strict=False) for f in args.files if f.endswith(".py")]
    else:
        files = [p.resolve(strict=False) for p in Path(".").rglob("*.py")]
    # Filter out unwanted directories
    exclude_dirs = {
        ".git",
        ".pytest_cache",
        ".ruff_cache",
        "node_modules",
        "__pycache__",
        ".vscode",
        "law_venv",
    }
    # Ensure consistent filtering and remove entries in excluded dirs (works for both absolute and relative paths)
    files = [f for f in files if not any(excl in f.parts for excl in exclude_dirs)]

    print(f"Processing {len(files)} Python files...")

    updated = 0
    for filepath in files:
        changed, message = normalize_file_header(filepath, dry_run=args.dry_run)
        if changed:
            print(f"✓ {message}")
            updated += 1
        elif "Error" in message:
            print(f"✗ {message}")

    print(f"\nCompleted: {updated} files {'would be' if args.dry_run else ''} updated")


if __name__ == "__main__":
    main()
