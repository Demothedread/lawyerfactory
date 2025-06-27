# LawyerFactory

This project provides a simple workflow manager for building legal documents. It
features sequential stages with human feedback loops and a basic Kanban board
interface.
Tasks can be assigned to agents and progressed through defined stages.
Each action is logged to `knowledge_graph.json` for traceability.

## Running

```
python app.py
```

## Tests and Linting

Install dependencies and run:

```
pip install -r requirements.txt
flake8
pytest
```
