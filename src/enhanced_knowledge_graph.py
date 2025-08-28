# Shim file to redirect enhanced_knowledge_graph imports to the correct location
from lawyerfactory.kg.enhanced_graph import *

# Re-export the main classes for backward compatibility
from lawyerfactory.kg.enhanced_graph import (
    EnhancedKnowledgeGraph,
    LegalEntity,
    LegalRelationship,
    LegalEntityType,
    LegalRelationshipType,
    ConfidenceFactors,
    CauseOfAction,
    LegalElement,
    ElementQuestion,
    JurisdictionAuthority,
    FactElementAttachment,
)

# Also redirect knowledge_graph imports
from lawyerfactory.kg.graph_api import KnowledgeGraph