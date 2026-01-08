class Agent:
    """Simple agent with a name and processing method."""

    def __init__(self, name: str):
        self.name = name

    def process(self, text: str) -> str:
        """Process the given text and return a response."""
        return f"{self.name} processed: {text}"


if __name__ == "__main__":
    agent = Agent("LexOmnia")
    print(agent.process("Hello world"))
