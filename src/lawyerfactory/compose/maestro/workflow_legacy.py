"""
# Script Name: workflow_legacy.py
# Description: Compatibility wrapper - imports from new location This file maintains backward compatibility during refactoring
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Orchestration
#   - Group Tags: orchestration
Compatibility wrapper - imports from new location
This file maintains backward compatibility during refactoring
"""
import warnings as _w

_w.warn(
    "Module workflow_legacy.py is deprecated; import lawyerfactory.compose.maestro.workflow_api instead.",
    DeprecationWarning,
    stacklevel=2,
)
from lawyerfactory.compose.maestro.workflow_api import *  # noqa: F401,F403
