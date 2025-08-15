
# lawyerfactory

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
=======
LawyerFactory is a lightweight demonstration of a swarm-based workflow for legal document creation. Agents collaborate through a simple planner, research bot, writer, and editor coordinated by the `Maestro` class. A small TF-IDF vector store provides retrieval augmented generation for reference material.

## Synopsis
- **Agents:** Step planner, research bot, writer bot, and legal editor
- **Orchestrator:** `Maestro` coordinates asynchronous calls and stores research
- **Vector Store:** In-memory TF-IDF vectors via `ai_vector.VectorStore`
- **Knowledge Graph:** `knowledge_graph.json` tracks entities and relationships

## Prerequisites
```
pip install -r requirements.txt
```

The requirements include `scikit-learn` for the TF-IDF vector store.

## Running the Demo
Execute the demo chain to see planning, research, and drafting in action:
```
python -m maestro.maestro
```

## Document Intake
`assessor.py` ingests text files and stores metadata in `repository.csv`. The
summary combines the first and last 250 tokens of each document for a concise
LLM-ready context. Categorization distinguishes legal, business, and research
topics with fine-grained labels such as `legal:caselaw` or `business:market-analysis`.
Example usage:
```
python assessor.py sample.txt --author "Author" --title "Doc" --date 2024-01-01
```

## Testing and Linting

* Lint the code with flake8::

    flake8

* Run the tests with pytest::

    python -m pytest
=======

## Use Cases
This prototype illustrates how a network of specialized agents can assemble structured legal content. The approach can be expanded with additional agents or a persistent vector database for larger projects.

## FAQ
**Q:** Is this production ready?
**A:** No. It is a minimal example intended for experimentation.

**Q:** How do I update the knowledge graph?
**A:** Modify `knowledge_graph.json` directly or use `knowledge_graph.py` to add observations.



