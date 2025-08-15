import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import repository  # noqa: E402
from assessor import intake_document  # noqa: E402


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
    assert entry['category'] == 'legal:contract'
    assert entry['hashtags'] == '#legal_contract'
