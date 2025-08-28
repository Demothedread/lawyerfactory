# Script Name: enhanced_knowledge_graph.py
# Description: AUTO-SHIM (top-level): deprecated module
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Core
#   - Group Tags: knowledge-graph
import warnings as _w

_w.warn("Import 'enhanced_knowledge_graph.py' is deprecated; use 'lawyerfactory.kg.enhanced_graph'.", DeprecationWarning, stacklevel=2)
from lawyerfactory.kg.enhanced_graph import *  # noqa: F401,F403
