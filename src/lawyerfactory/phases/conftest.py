"""Pytest configuration to ensure src/ is on sys.path for package imports."""

import sys
from pathlib import Path

SRC_PATH = Path(__file__).resolve().parents[2]
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))
