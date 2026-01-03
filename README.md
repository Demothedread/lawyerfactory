# lawyerfactory

LawyerFactory is a lightweight demonstration of a swarm-based workflow for legal document creation. Agents collaborate through a simple planner, research bot, writer, and editor coordinated by the `Maestro` class. A small TF-IDF vector store provides retrieval augmented generation for reference material.

## Synopsis
- **Agents:** Step planner, research bot, writer bot, and legal editor
- **Orchestrator:** `Maestro` coordinates asynchronous calls and stores research
- **Vector Store:** In-memory TF-IDF vectors via `ai_vector.VectorStore`
- **Knowledge Graph:** `knowledge_graph.json` tracks entities and relationships

## Knowledge Graph Module
The `knowledge_graph.py` module loads and saves `knowledge_graph.json`, which tracks entities, their features, relationships, and observations. You can use the helper functions to load the graph, add entities or relationships, append observations, and save the updated graph.

Example usage:

```python
from knowledge_graph import load_graph, save_graph, add_observation

graph = load_graph()
add_observation(graph, "Used the knowledge graph module.")
save_graph(graph)
```

## Workflow DAG
A stage-by-stage DAG describing how OCR intake, shotlisting, research, and drafting interact is documented in [`docs/workflow_dag.md`](docs/workflow_dag.md). It highlights the StageTimeline and ResearchChecklist surfaces used to track progress.

## Document Intake
`assessor.py` ingests text files and stores metadata in `repository.csv`. The summary combines the first and last 250 tokens of each document for a concise LLM-ready context. Categorization distinguishes legal, business, and research topics with fine-grained labels such as `legal:caselaw` or `business:market-analysis`.

Example usage:
```bash
python assessor.py sample.txt --author "Author" --title "Doc" --date 2024-01-01
```

## Draft a Lawsuit
Use the workflow to move from intake to research, drafting, and export. This section outlines the minimum inputs, the pipeline sequence, and how to produce a structured export bundle.

### Input requirements
Provide enough detail for the agents to identify claims and draft sections:
- **Matter details:** claim type, jurisdiction, court, filing deadline, and opposing parties.
- **Parties:** names, roles (plaintiff/defendant), and contact details.
- **Facts & timeline:** key events, dates, and any causation details.
- **Relief sought:** damages, injunctions, declaratory relief, and fees.
- **Supporting documents:** intake files (PDF/text) and citations or exhibits.

### Pipeline steps
1. **Intake (assessor):** Store uploads in `repository.csv` and normalize summaries.
2. **Research (Maestro + bots):** Generate a step plan, gather research, and store it in the vector store.
3. **Draft (writer + editor):** Use research outputs to draft core sections and refine language.
4. **Export (bundle):** Package sections, research notes, and metadata into a JSON export or file output.

### API usage
The workflow is exposed as Python modules and simple scripts. Intake can also be done via CLI.

```bash
python assessor.py intake.txt --author "R. Quinn" --title "Intake Notes" --date 2024-06-12
```

Minimal Python example (intake → research → draft → export):

```python
import asyncio
import json
from pathlib import Path

from assessor import intake_document
from maestro.maestro import Maestro

intake_payload = {
    "matter": {
        "claim": "Breach of contract",
        "jurisdiction": "California",
        "court": "Superior Court",
    },
    "parties": {
        "plaintiff": "Apex Logistics, Inc.",
        "defendant": "Metro Freight LLC",
    },
    "facts": [
        {"date": "2023-11-01", "event": "Executed shipping agreement."},
        {"date": "2024-01-15", "event": "Defendant failed to deliver goods."},
    ],
    "relief": ["$250,000 in damages", "Costs and attorneys' fees"],
}

intake_document(
    "R. Quinn",
    "Contract breach intake",
    "2024-06-12",
    "Plaintiff signed agreement. Defendant missed delivery deadlines.",
)

async def run_pipeline() -> None:
    maestro = Maestro()
    research_notes = await maestro.research_and_write(
        f"{intake_payload['matter']['claim']} in {intake_payload['matter']['jurisdiction']}"
    )
    draft_sections = {
        "caption": "Apex Logistics, Inc. v. Metro Freight LLC",
        "statement_of_facts": "Plaintiff and Defendant entered a shipping agreement...",
        "causes_of_action": ["Breach of Contract"],
        "prayer_for_relief": intake_payload["relief"],
    }
    export_bundle = {
        "matter": intake_payload["matter"],
        "parties": intake_payload["parties"],
        "facts": intake_payload["facts"],
        "research": research_notes,
        "draft": draft_sections,
    }
    Path("draft_export.json").write_text(json.dumps(export_bundle, indent=2))

asyncio.run(run_pipeline())
```

### Output format
Export bundles are JSON-friendly and should be easy to hand off to a renderer or filing workflow.

Expected output structure:
```json
{
  "matter": {
    "claim": "Breach of contract",
    "jurisdiction": "California",
    "court": "Superior Court"
  },
  "parties": {
    "plaintiff": "Apex Logistics, Inc.",
    "defendant": "Metro Freight LLC"
  },
  "facts": [
    {"date": "2023-11-01", "event": "Executed shipping agreement."}
  ],
  "research": "Research results and notes gathered by the research bot.",
  "draft": {
    "caption": "Apex Logistics, Inc. v. Metro Freight LLC",
    "statement_of_facts": "Narrative fact section text...",
    "causes_of_action": ["Breach of Contract"],
    "prayer_for_relief": ["$250,000 in damages", "Costs and attorneys' fees"]
  }
}
```

## Testing and Linting
- Lint the code with flake8:
  ```bash
  flake8
  ```
- Run the tests with pytest:
  ```bash
  python -m pytest
  ```

## Use Cases
This prototype illustrates how a network of specialized agents can assemble structured legal content. The approach can be expanded with additional agents or a persistent vector database for larger projects.

## FAQ
**Q:** Is this production ready?

**A:** No. It is a minimal example intended for experimentation.

**Q:** How do I update the knowledge graph?

**A:** Modify `knowledge_graph.json` directly or use `knowledge_graph.py` to add observations.
