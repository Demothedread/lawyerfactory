from .knowledge_graph import KnowledgeGraph


class Agent:
    """Simple agent that owns a knowledge graph."""

    def __init__(self, name):
        self.name = name
        self.graph = KnowledgeGraph()

    def learn(self, entity, data=None):
        self.graph.add_entity(entity, data)
