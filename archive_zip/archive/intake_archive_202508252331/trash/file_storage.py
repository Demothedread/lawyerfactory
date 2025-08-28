# Script Name: file_storage.py
# Description: AUTO-SHIM (package): deprecated path lawyerfactory.file_storage
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Storage
#   - Group Tags: null
import warnings as _w

_w.warn("Use 'lawyerfactory.infra.file_storage' instead of 'lawyerfactory.file_storage'.", DeprecationWarning, stacklevel=2)
from lawyerfactory.infra.file_storage import *  # noqa: F401,F403
