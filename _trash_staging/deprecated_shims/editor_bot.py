"""
# Script Name: editor_bot.py
# Description: DEPRECATED shim. Use lawyerfactory.compose.bots.editor instead.
# Relationships:
#   - Entity Type: Agent
#   - Directory Group: Workflow
#   - Group Tags: deprecation-shim
"""

import warnings as _w

_w.warn(
    "Module lawyerfactory.phases.phaseB02_drafting.editor_bot is deprecated; use lawyerfactory.compose.bots.editor",
    DeprecationWarning,
    stacklevel=2,
)

from lawyerfactory.compose.bots.editor import LegalEditorBot as _CanonicalLegalEditorBot

LegalEditorBot = _CanonicalLegalEditorBot
