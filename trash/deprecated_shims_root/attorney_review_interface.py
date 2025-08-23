# Script Name: attorney_review_interface.py
# Description: AUTO-SHIM
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Core
#   - Group Tags: null
import warnings as _w
_w.warn("Import 'attorney_review_interface' moved; define UI API under lawyerfactory.ui or import directly from apps.ui.templates if intentional.", DeprecationWarning, stacklevel=2)
from src.lawyerfactory.phases.04_human_review.attorney_review_interface import *  # noqa: F401,F403
