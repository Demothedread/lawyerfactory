# Script Name: test_shotlist.py
# Description: Handles test shotlist functionality in the LawyerFactory system.
# Relationships:
#   - Entity Type: Test
#   - Directory Group: Core
#   - Group Tags: evidence-processing, testing
import csv
from pathlib import Path
import tempfile

from lawyerfactory.evidence.shotlist import build_shot_list


def test_build_shot_list_roundtrip():
    rows = [
        {"source_id":"doc1","timestamp":"2024-01-01","summary":"A thing happened","entities":["A","B"],"citations":["CL:123"]},
        {"source_id":"doc2","timestamp":"2024-01-02","summary":"Another thing","entities":["C"],"citations":[]},
    ]
    with tempfile.TemporaryDirectory() as td:
        out = Path(td)/"shot_list.csv"
        path = build_shot_list(rows, out)
        assert path.exists()
        with path.open() as f:
            r = list(csv.DictReader(f))
        assert len(r) == 2
        assert r[0]["summary"] == "A thing happened"
