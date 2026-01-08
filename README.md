# lawyerfactory

LawyerFactory is a lightweight demonstration of a swarm-based workflow for legal document creation. Agents collaborate through a simple planner, research bot, writer, and editor coordinated by the `Maestro` class. A small TF-IDF vector store provides retrieval augmented generation for reference material.

## Synopsis
- **Agents:** Step planner, research bot, writer bot, and legal editor
- **Orchestrator:** `Maestro` coordinates asynchronous calls and stores research
- **Vector Store:** In-memory TF-IDF vectors via `ai_vector.VectorStore`
- **Knowledge Graph:** `knowledge_graph.json` tracks entities and relationships
- **Pipeline Service:** FastAPI backend service that provides job status, stage updates, and drafted sections to the UI

## Pipeline Service

The `pipeline_service.py` module provides a FastAPI backend service that powers the factory UI. It tracks job state, stage progression, and document sections in real-time.

### Running the Service

Start the pipeline service with uvicorn:

```bash
uvicorn pipeline_service:app --host 0.0.0.0 --port 8000
```

The service will be available at `http://localhost:8000`.

### API Endpoints

- `POST /jobs` - Create a new document generation job
- `GET /jobs/{job_id}` - Get job status and task progress
- `GET /jobs/{job_id}/sections` - Get drafted document sections

### Configuration

- **CORS Origins**: Set the `ALLOWED_ORIGINS` environment variable to a comma-separated list of allowed origins (default: `*` for development)
  ```bash
  export ALLOWED_ORIGINS="http://localhost:3000,https://app.example.com"
  uvicorn pipeline_service:app --host 0.0.0.0 --port 8000
  ```

### Important Limitations

⚠️ **Memory Persistence**: The pipeline service stores all job data in memory using a simple dictionary (`JOBS`). This means:
- All job data will be **lost when the service restarts**
- Memory usage will **grow unbounded** as more jobs are created
- No job expiration or cleanup mechanism is implemented
- Not suitable for production use without adding proper data persistence

**Recommendations for Production**:
- Implement a proper data store (Redis, PostgreSQL, MongoDB, etc.)
- Add job expiration/TTL mechanisms
- Implement job cleanup for completed jobs
- Add authentication and rate limiting (currently unprotected)

### Testing

Run the pipeline service tests:

```bash
python -m pytest tests/test_pipeline_service.py -v
```

## Knowledge Graph Module
The `lawyerfactory.knowledge_graph` module loads and saves `knowledge_graph.json`, which tracks entities, their features, relationships, and observations. You can use the helper functions to load the graph, add entities or relationships, append observations, and save the updated graph.

Example usage:

```python
from lawyerfactory.knowledge_graph import load_graph, save_graph, add_observation

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

## Prerequisites
- Python 3.11+
- Dependencies installed via `pip install -r requirements.txt`

## Getting Started
- Run the maestro API server:
  ```bash
  uvicorn server:app --reload
  ```
- Create a job intake:
  ```bash
  curl -X POST http://localhost:8000/api/jobs/intake \
    -H "Content-Type: application/json" \
    -d '{"documents":[{"name":"intake.txt","content":"Client intake text"}],"topic":"contract dispute"}'
  ```

## Deployment
Use a production ASGI server such as `uvicorn` with a process manager (e.g., `gunicorn`) and configure the SQLite path to a persistent volume for job storage.

## Testing and Linting
- Lint the code with flake8:
  ```bash
  flake8
  ```
- Run the tests with pytest:
  ```bash
  python -m pytest
  ```

## E2E Tests
- Launch the API server and exercise the intake, research, draft, and export endpoints in order to validate the full pipeline.

## Use Cases
This prototype illustrates how a network of specialized agents can assemble structured legal content. The approach can be expanded with additional agents or a persistent vector database for larger projects.

## FAQ
**Q:** Is this production ready?

**A:** No. It is a minimal example intended for experimentation.

**Q:** How do I update the knowledge graph?

**A:** Modify `knowledge_graph.json` directly or use `lawyerfactory.knowledge_graph` to add observations.
