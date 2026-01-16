"""
# Script Name: procedure_bot.py
# Description: DEPRECATED shim. Use lawyerfactory.compose.bots.procedure instead.
# Relationships:
#   - Entity Type: Agent
#   - Directory Group: Workflow
#   - Group Tags: deprecation-shim
"""

import warnings as _w

_w.warn(
    "Module lawyerfactory.phases.phaseB02_drafting.generator.procedure_bot is deprecated; use lawyerfactory.compose.bots.procedure",
    DeprecationWarning,
    stacklevel=2,
)

from lawyerfactory.compose.bots.procedure import LegalProcedureBot

ProcedureBot = LegalProcedureBot
