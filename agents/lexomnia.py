class Agent:
    """Simple agent with a name and processing method."""

    def __init__(self, name: str):
        self.name = name

    def process(self, text: str) -> str:
        """Process the given text and return a response."""
        return f"{self.name} processed: {text}"


class Runner:
    """Runner that executes an agent's processing routine."""

    def __init__(self, agent: Agent):
        self.agent = agent

    def run(self, text: str) -> str:
        """Run the agent on the provided text."""
        return self.agent.process(text)


if __name__ == "__main__":
    agent = Agent("LexOmnia")
    runner = Runner(agent)
    output = runner.run("Hello world")
    print(output)
