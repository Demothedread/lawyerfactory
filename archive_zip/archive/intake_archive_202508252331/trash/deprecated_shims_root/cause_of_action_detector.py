# Script Name: cause_of_action_detector.py
# Description: AUTO-SHIM
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Core
#   - Group Tags: null
import warnings as _w

_w.warn("Import 'cause_of_action_detector' is deprecated; use 'lawyerfactory.claims.detect'.", DeprecationWarning, stacklevel=2)
from lawyerfactory.claims.detect import *  # noqa: F401,F403
