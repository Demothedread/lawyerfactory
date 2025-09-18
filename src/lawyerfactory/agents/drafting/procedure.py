"""
# Script Name: procedure.py
# Description: DEPRECATED shim. Use lawyerfactory.compose.bots.procedure instead.
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Orchestration
#   - Group Tags: deprecation-shim
"""

import warnings as _w

_w.warn(
    "Module lawyerfactory.agents.drafting.procedure is deprecated; use lawyerfactory.compose.bots.procedure",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export the canonical LegalProcedureBot for backward compatibility
from lawyerfactory.compose.bots.procedure import LegalProcedureBot as _CanonicalLegalProcedureBot

# Public name preserved
LegalProcedureBot = _CanonicalLegalProcedureBot
