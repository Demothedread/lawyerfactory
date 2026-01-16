"""
# Script Name: writer_bot.py
# Description: DEPRECATED shim. Use lawyerfactory.compose.bots.writer instead.
# Relationships:
#   - Entity Type: Agent
#   - Directory Group: Workflow
#   - Group Tags: deprecation-shim
"""

import warnings as _w

_w.warn(
    "Module lawyerfactory.phases.phaseB02_drafting.writer_bot is deprecated; use lawyerfactory.compose.bots.writer",
    DeprecationWarning,
    stacklevel=2,
)

from lawyerfactory.compose.bots.writer import WriterBot as _CanonicalWriterBot

WriterBot = _CanonicalWriterBot
