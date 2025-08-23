# Script Name: knowledge_graph.py
# Description: AUTO-SHIM (package): deprecated path lawyerfactory.knowledge_graph
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Core
#   - Group Tags: knowledge-graph
import warnings as _w
_w.warn("Use 'lawyerfactory.kg.graph' instead of 'lawyerfactory.knowledge_graph'.", DeprecationWarning, stacklevel=2)
from lawyerfactory.kg.graph import *  # noqa: F401,F403
