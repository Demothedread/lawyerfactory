import json
from pathlib import Path

GRAPH_PATH = Path('knowledge_graph.json')

def load_graph():
    if GRAPH_PATH.exists():
        with open(GRAPH_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"entities": [], "relationships": [], "observations": []}


def save_graph(graph):
    with open(GRAPH_PATH, 'w', encoding='utf-8') as f:
        json.dump(graph, f, indent=2)


def add_observation(text):
    graph = load_graph()
    graph.setdefault("observations", []).append(text)
    save_graph(graph)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        add_observation(' '.join(sys.argv[1:]))
    else:
        print(json.dumps(load_graph(), indent=2))
