
# lawyerfactory

## Setup

Install dependencies::

    pip install -r requirements.txt

## Running checks

* Lint the code with flake8::

    flake8

* Run the tests with pytest::

    python -m pytest
=======
This repository contains an experimental agent-based workflow for generating long-form legal content. The approach relies on a team of specialized GPT-4.1-mini agents managed in an assembly-line fashion.

See [docs/team_chart.md](docs/team_chart.md) for an overview of the agents and phases.

The knowledge graph describing entities and relationships is stored in `knowledge_graph.json` and can be updated via `knowledge_graph.py`.


This project contains a simple agentic chain with several bots orchestrated by the `Maestro` class. The maestro directs output from one bot to another and stores research results in a small in-memory database.

Run the demo to see a basic flow:

```bash
python -m maestro.maestro

This repository contains a simple document intake system.

## Assessor

The `assessor.py` script ingests text documents and stores metadata
in `repository.csv`. It automatically generates a short summary,
assigns a category based on keywords, and adds a hashtag.

Run the script from the command line:

```bash
python assessor.py path/to/document.txt --author "Author Name" --title "Doc Title" --date YYYY-MM-DD
```

## Tests

Install dependencies and run tests with `pytest`:

```bash
pip install -r requirements.txt  # or `pip install flake8 pytest nltk`
flake8 .
pytest -q
=======
# LawyerFactory

This project provides a simple workflow manager for building legal documents. It
features sequential stages with human feedback loops and a basic Kanban board
interface.
Tasks can be assigned to agents and progressed through defined stages.
Each action is logged to `knowledge_graph.json` for traceability.

## Running

]
```

