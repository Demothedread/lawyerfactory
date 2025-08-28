# Script Name: repository.py
# Description: AUTO-SHIM
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Core
#   - Group Tags: null
import warnings as _w

_w.warn("Import 'repository' is deprecated; use 'lawyerfactory.infra.repository'.", DeprecationWarning, stacklevel=2)
from lawyerfactory.infra.repository import *  # noqa: F401,F403
