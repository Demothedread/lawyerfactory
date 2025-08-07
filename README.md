# LawyerFactory

LawyerFactory is a collection of simple agent modules used for automation and experimentation. Each agent implements a basic interface and can be executed with a small runner script.

## Usage

Run the example `lexomnia` agent:

```bash
python -m agents.lexomnia
```

This will execute the agent's runner and print the processed output.

## Project goals

* Provide a minimal framework for experimenting with agent-based workflows.
* Encourage modular design so new agents can be added easily under the `agents/` package.
