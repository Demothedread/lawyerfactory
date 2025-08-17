"""
Compatibility wrapper - imports from new location
This file maintains backward compatibility during refactoring
"""
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# Ensure src/ is on sys.path so imports like `from storage.api.file_storage import *` work
try:
    project_root = Path(__file__).resolve().parent.parent
    src_path = project_root / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
except Exception:
    # best-effort; fall back to current sys.path
    src_path = None

# Try importing the new module location, fall back gracefully and raise a clear error
try:
    from storage.api.file_storage import *  # type: ignore
    logger.info("Imported storage.api.file_storage from src successfully")
except Exception as _err:
    try:
        # Last resort: try the src package import style
        from src.storage.api.file_storage import *  # type: ignore
        logger.info("Imported src.storage.api.file_storage successfully")
    except Exception as err:
        logger.exception("Failed to import file_storage compatibility wrapper: %s", err)
        raise