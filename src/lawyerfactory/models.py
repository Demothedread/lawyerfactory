# Script Name: models.py
# Description: AUTO-SHIM (package): deprecated path lawyerfactory.models
# Relationships:
#   - Entity Type: Data Model
#   - Directory Group: Core
#   - Group Tags: null
import warnings as _w

_w.warn(
    "Use 'lawyerfactory.lf_core.models' instead of 'lawyerfactory.models'.",
    DeprecationWarning,
    stacklevel=2,
)
from lawyerfactory.lf_core.models import *  # noqa: F401,F403
