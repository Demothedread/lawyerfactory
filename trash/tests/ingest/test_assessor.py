# Script Name: test_assessor.py
# Description: Handles test assessor functionality in the LawyerFactory system.
# Relationships:
#   - Entity Type: Test
#   - Directory Group: Ingestion
#   - Group Tags: testing
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))
from assessor import intake_document
import repository


def test_intake_document(tmp_path):
    repo_file = tmp_path / 'repository.csv'
    repository.REPO_FILE = repo_file
    repository.init_repo()

    text = 'This is a contract between parties. It outlines terms.'
    intake_document('Alice', 'Contract A', '2023-01-01', text)

    entries = repository.list_entries()
    assert len(entries) == 1
    entry = entries[0]
    assert entry['author'] == 'Alice'
    assert entry['title'] == 'Contract A'
    assert entry['category'] == 'contract'
    assert entry['hashtags'] == '#contract'

    # Log output to /logs
    log_dir = Path(__file__).parent.parent / 'logs'
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / 'test_assessor.log'
    with open(log_file, 'w') as f:
        f.write('Assessor test completed.\n')

