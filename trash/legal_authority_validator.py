# Shim file to redirect legal_authority_validator imports to the correct location
from lawyerfactory.research.validate import *

# Re-export the main classes for backward compatibility
from lawyerfactory.research.validate import (
    LegalAuthorityValidator,
    CitationCompliance,
    AuthorityConflict,
    FederalPreemptionAnalysis,
    BluebookValidation,
)