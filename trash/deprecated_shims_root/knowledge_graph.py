# Script Name: knowledge_graph.py
# Description: AUTO-SHIM
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Core
#   - Group Tags: knowledge-graph
import warnings as _w
_w.warn("Import 'knowledge_graph' is deprecated; use 'lawyerfactory.kg.graph_root'.", DeprecationWarning, stacklevel=2)
from lawyerfactory.kg.graph_root import *  # noqa: F401,F403
