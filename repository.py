import csv
from pathlib import Path
from typing import List, Dict

REPO_FILE = Path('repository.csv')

FIELDS = [
    'author',
    'title',
    'publication_date',
    'summary',
    'category',
    'hashtags',
]

def init_repo() -> None:
    """Create repository file with headers if it doesn't exist."""
    if not REPO_FILE.exists():
        with REPO_FILE.open('w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()

def add_entry(entry: Dict[str, str]) -> None:
    """Add a dictionary entry to the repository."""
    init_repo()
    with REPO_FILE.open('a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writerow(entry)

def list_entries() -> List[Dict[str, str]]:
    """Return all repository entries."""
    init_repo()
    with REPO_FILE.open('r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)
