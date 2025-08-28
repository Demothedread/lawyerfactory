# Shim file to redirect legal_research_integration imports to the correct location
from lawyerfactory.research.retrievers.integration import *

# Re-export the main classes for backward compatibility
from lawyerfactory.research.retrievers.integration import (
    LegalResearchAPIIntegration,
    AuthorityLevel,
    LegalResearchRequest,
    ResearchPriority,
    AuthorityValidation,
    ResearchCacheEntry,
)