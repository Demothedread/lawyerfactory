# Script Name: table.py
# Description: DEPRECATED shim. Use lawyerfactory.storage.evidence.table instead.
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Workflow
#   - Group Tags: evidence-processing
import warnings as _w

_w.warn(
    "Module lawyerfactory.phases.phaseA01_intake.evidence.table is deprecated; use lawyerfactory.storage.evidence.table instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Explicit re-exports for backward compatibility
from lawyerfactory.storage.evidence.table import (
    ClaimEntry,
    EnhancedEvidenceTable,
    EvidenceEntry,
    EvidenceType,
    FactAssertion,
    LegalElement,
    PrivilegeMarker,
    RelevanceLevel,
)
