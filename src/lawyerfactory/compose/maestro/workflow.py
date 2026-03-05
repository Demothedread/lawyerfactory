"""
# Script Name: workflow.py
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
    "Module workflow.py is deprecated; import lawyerfactory.compose.maestro.workflow_enhanced instead.",
    DeprecationWarning,
    stacklevel=2,
)
from lawyerfactory.compose.maestro.workflow_enhanced import *  # noqa: F401,F403
from lawyerfactory.compose.maestro.workflow_models import WorkflowTask  # noqa: F401
