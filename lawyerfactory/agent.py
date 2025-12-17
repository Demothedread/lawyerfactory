from .knowledge_graph import EMPTY_GRAPH, KnowledgeGraph


class Agent:
    """Simple agent that owns a knowledge graph."""

    def __init__(self, name):
        self.name = name
        self.graph = KnowledgeGraph(seed=EMPTY_GRAPH)

    def learn(self, entity, data=None):
        self.graph.add_entity(entity, data)
