class KnowledgeGraph:
    """Simple in-memory knowledge graph."""

    def __init__(self):
        self.entities = {}
        self.relationships = []

    def add_entity(self, name, data=None):
        self.entities[name] = data or {}

    def get_entity(self, name):
        return self.entities.get(name)

    def add_relationship(self, source, target, relation):
        self.relationships.append({
            'source': source,
            'target': target,
            'relation': relation,
        })

    def get_relationships(self):
        return list(self.relationships)
