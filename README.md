# lawyerfactory

This repository provides a small knowledge graph utility.

## Knowledge Graph Module

The `knowledge_graph.py` module loads and saves `knowledge_graph.json`, which
tracks entities, their features and relationships. You can use the helper
functions to load the graph, add entities or relationships, append
observations, and save the updated graph.

Example usage:

```python
from knowledge_graph import load_graph, save_graph, add_observation

graph = load_graph()
add_observation(graph, "Used the knowledge graph module.")
save_graph(graph)
```
