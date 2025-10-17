# Script Name: __init__.py
# Description: Handles   init   functionality in the LawyerFactory system.
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Research
#   - Group Tags: knowledge-graph
"""Package initialization file"""

# Canonical KnowledgeGraph exports
from .graph_api import EnhancedKnowledgeGraph
from .graph_api import KnowledgeGraph

# Make EnhancedKnowledgeGraph the primary export
__all__ = ["EnhancedKnowledgeGraph", "KnowledgeGraph"]
