from abc import ABC, abstractmethod


class Bot(ABC):
    """Base class for bots in the agentic chain."""

    @abstractmethod
    async def process(self, message: str) -> str:
        """Process an incoming message and return a response."""
        raise NotImplementedError
