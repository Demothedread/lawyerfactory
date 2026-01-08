"""Legacy proxy to the canonical knowledge graph module."""

from lawyerfactory.knowledge_graph import (  # noqa: F401
    DEFAULT_GRAPH,
    EMPTY_GRAPH,
    KNOWLEDGE_GRAPH_PATH as KGRAPH_FILE,
    KnowledgeGraph,
    add_entity,
    add_observation,
    add_relationship,
    load_graph,
    save_graph,
)

if __name__ == "__main__":
    import sys

    graph_state = load_graph()
    if len(sys.argv) > 1:
        add_observation(graph_state, " ".join(sys.argv[1:]))
        save_graph(graph_state)
    else:
        import json

        print(json.dumps(graph_state, indent=2))
