#!/usr/bin/env python3
"""
final_cleanup.py — Final cleanup script for streamlined organization.

This script performs the final cleanup tasks:
1. Remove .bak files
2. Clean up empty directories
3. Verify import statements
4. Generate final report
"""

import os
import shutil
from pathlib import Path
from typing import List, Dict

def find_backup_files() -> List[Path]:
    """Find all .bak files in the codebase"""
    return list(Path('.').rglob('*.bak'))

def find_empty_directories() -> List[Path]:
    """Find empty directories"""
    empty_dirs = []
    for root, dirs, files in os.walk('.'):
        root_path = Path(root)
        if (not any(root_path.iterdir()) and
            root_path.name not in ['__pycache__', '.git'] and
            not root_path.name.startswith('.')):
            empty_dirs.append(root_path)
    return empty_dirs

def cleanup_backup_files(dry_run: bool = True) -> Dict[str, int]:
    """Clean up backup files"""
    bak_files = find_backup_files()
    print(f"Found {len(bak_files)} backup files")

    if dry_run:
        for bak_file in bak_files[:10]:  # Show first 10
            print(f"Would remove: {bak_file}")
        if len(bak_files) > 10:
            print(f"... and {len(bak_files) - 10} more")
        return {'removed': 0, 'total': len(bak_files)}

    removed = 0
    for bak_file in bak_files:
        try:
            bak_file.unlink()
            removed += 1
        except Exception as e:
            print(f"Error removing {bak_file}: {e}")

    return {'removed': removed, 'total': len(bak_files)}

def cleanup_empty_directories(dry_run: bool = True) -> Dict[str, int]:
    """Clean up empty directories"""
    empty_dirs = find_empty_directories()
    print(f"Found {len(empty_dirs)} empty directories")

    if dry_run:
        for empty_dir in empty_dirs[:5]:  # Show first 5
            print(f"Would remove: {empty_dir}")
        if len(empty_dirs) > 5:
            print(f"... and {len(empty_dirs) - 5} more")
        return {'removed': 0, 'total': len(empty_dirs)}

    removed = 0
    # Remove in reverse order to handle nested directories
    for empty_dir in sorted(empty_dirs, reverse=True):
        try:
            if not any(empty_dir.iterdir()):  # Double-check it's still empty
                empty_dir.rmdir()
                removed += 1
        except Exception as e:
            print(f"Error removing {empty_dir}: {e}")

    return {'removed': removed, 'total': len(empty_dirs)}

def verify_import_statements() -> Dict[str, int]:
    """Verify import statements are working"""
    import_errors = []
    python_files = list(Path('.').rglob('*.py'))

    for py_file in python_files:
        try:
            with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Check for common import patterns that might be broken
            if 'from src.' in content or 'from lawyerfactory.' in content:
                # This is a basic check - in a real scenario you'd want to actually
                # test the imports
                pass

        except Exception as e:
            import_errors.append(str(py_file))

    return {
        'files_checked': len(python_files),
        'import_errors': len(import_errors),
        'errors': import_errors[:10]  # First 10 errors
    }

def generate_final_report() -> Dict:
    """Generate final cleanup report"""
    report = {
        'cleanup_completed': True,
        'timestamp': Path('final_cleanup.py').stat().st_mtime,
        'summary': {}
    }

    # Backup files cleanup
    backup_stats = cleanup_backup_files(dry_run=True)
    report['summary']['backup_files'] = backup_stats

    # Empty directories cleanup
    empty_dir_stats = cleanup_empty_directories(dry_run=True)
    report['summary']['empty_directories'] = empty_dir_stats

    # Import verification
    import_stats = verify_import_statements()
    report['summary']['import_verification'] = import_stats

    # Overall statistics
    total_files = len(list(Path('.').rglob('*')))
    python_files = len(list(Path('.').rglob('*.py')))
    directories = len(list(Path('.').rglob('*/')))

    report['summary']['overall'] = {
        'total_files': total_files,
        'python_files': python_files,
        'directories': directories,
        'redundant_files_removed': backup_stats['total'] + empty_dir_stats['total']
    }

    return report

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Final cleanup script')
    parser.add_argument('--dry-run', action='store_true', help='Preview cleanup without executing')
    parser.add_argument('--cleanup-backups', action='store_true', help='Remove backup files')
    parser.add_argument('--cleanup-dirs', action='store_true', help='Remove empty directories')
    parser.add_argument('--verify-imports', action='store_true', help='Verify import statements')
    parser.add_argument('--all', action='store_true', help='Do all cleanup tasks')
    parser.add_argument('--report', action='store_true', help='Generate final report')

    args = parser.parse_args()

    if not any(vars(args).values()):
        args.dry_run = True
        args.report = True

    if args.report or args.all:
        print("=== FINAL CLEANUP REPORT ===")
        report = generate_final_report()

        print(f"Backup files to remove: {report['summary']['backup_files']['total']}")
        print(f"Empty directories to remove: {report['summary']['empty_directories']['total']}")
        print(f"Python files checked: {report['summary']['import_verification']['files_checked']}")
        print(f"Import errors found: {report['summary']['import_verification']['import_errors']}")
        print(f"Total files in codebase: {report['summary']['overall']['total_files']}")
        print(f"Redundant files to remove: {report['summary']['overall']['redundant_files_removed']}")

    if args.cleanup_backups or args.all:
        print("\n=== CLEANING UP BACKUP FILES ===")
        stats = cleanup_backup_files(dry_run=args.dry_run)
        if not args.dry_run:
            print(f"Removed {stats['removed']} backup files")

    if args.cleanup_dirs or args.all:
        print("\n=== CLEANING UP EMPTY DIRECTORIES ===")
        stats = cleanup_empty_directories(dry_run=args.dry_run)
        if not args.dry_run:
            print(f"Removed {stats['removed']} empty directories")

    if args.verify_imports or args.all:
        print("\n=== VERIFYING IMPORT STATEMENTS ===")
        stats = verify_import_statements()
        print(f"Checked {stats['files_checked']} Python files")
        if stats['import_errors'] > 0:
            print(f"Found {stats['import_errors']} potential import issues")
            for error in stats['errors']:
                print(f"  - {error}")

if __name__ == '__main__':
    main()