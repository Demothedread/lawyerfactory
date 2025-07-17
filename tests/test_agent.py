from lawyerfactory.agent import Agent


def test_agent_initialization():
    agent = Agent("Test")
    assert agent.name == "Test"
    assert agent.graph.entities == {}


def test_knowledge_graph_operations():
    agent = Agent("Test")
    agent.learn("entity1", {"data": 123})
    assert agent.graph.get_entity("entity1") == {"data": 123}

    agent.graph.add_relationship("entity1", "entity2", "related")
    rels = agent.graph.get_relationships()
    assert rels == [{"source": "entity1", "target": "entity2", "relation": "related"}]
