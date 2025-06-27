
# lawyerfactory

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
