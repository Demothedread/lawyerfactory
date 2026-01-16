"""
# Script Name: writer.py
# Description: DEPRECATED shim. Use lawyerfactory.compose.bots.writer instead.
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Orchestration
#   - Group Tags: deprecation-shim
"""

import warnings as _w

_w.warn(
    "Module lawyerfactory.agents.drafting.writer is deprecated; use lawyerfactory.compose.bots.writer",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export the canonical WriterBot for backward compatibility
from lawyerfactory.compose.bots.writer import WriterBot as _CanonicalWriterBot

# Public name preserved
WriterBot = _CanonicalWriterBot
