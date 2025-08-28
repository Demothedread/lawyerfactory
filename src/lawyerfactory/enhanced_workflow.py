# Script Name: enhanced_workflow.py
# Description: AUTO-SHIM (package): deprecated path lawyerfactory.enhanced_workflow
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Core
#   - Group Tags: null
import warnings as _w

_w.warn(
    "Use 'lawyerfactory.compose.maestro.workflow' instead of 'lawyerfactory.enhanced_workflow'.",
    DeprecationWarning,
    stacklevel=2,
)
from lawyerfactory.compose.maestro.workflow import *  # noqa: F401,F403
