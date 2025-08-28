# Script Name: document_export_system.py
# Description: AUTO-SHIM (top-level): deprecated module
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Document Generation
#   - Group Tags: null
import warnings as _w

_w.warn("Import 'document_export_system.py' is deprecated; use 'lawyerfactory.phases.06_post_production.formatters.document_export_system'.", DeprecationWarning, stacklevel=2)
from lawyerfactory.phases.06_post_production.formatters.document_export_system import *  # noqa: F401,F403
