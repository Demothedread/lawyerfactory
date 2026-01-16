"""
# Script Name: editor.py
# Description: DEPRECATED shim. Use lawyerfactory.compose.bots.editor instead.
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Orchestration
#   - Group Tags: deprecation-shim
"""

import warnings as _w

_w.warn(
    "Module lawyerfactory.agents.drafting.editor is deprecated; use lawyerfactory.compose.bots.editor",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export the canonical LegalEditorBot for backward compatibility
from lawyerfactory.compose.bots.editor import LegalEditorBot as _CanonicalLegalEditorBot

# Public name preserved for downstream imports
LegalEditorBot = _CanonicalLegalEditorBot
