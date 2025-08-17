import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# Ensure the project root and src/ are on sys.path to make imports between
# the top-level modules, maestro package, and src package consistent regardless
# of how modules are imported or which working directory is used.
try:
    package_file = Path(__file__).resolve()
    project_root = package_file.parent.parent
    src_path = project_root / "src"
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    if src_path.exists() and str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    logger.debug("Added project root and src to sys.path: %s, %s", project_root, src_path)
except Exception:
    # Best-effort; do not fail import if path manipulation fails
    logger.exception("Failed to adjust sys.path in maestro package init")