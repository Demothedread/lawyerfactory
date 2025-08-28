# Script Name: assessor.py
# Description: AUTO-SHIM (top-level): deprecated module
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Core
#   - Group Tags: null
import warnings as _w

_w.warn("Import 'assessor.py' is deprecated; use 'lawyerfactory.phases.phaseA01_intake.ingestion.assessor'.", DeprecationWarning, stacklevel=2)
from lawyerfactory.phases.phaseA01_intake.ingestion.assessor import *  # noqa: F401,F403
