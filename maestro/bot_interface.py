from abc import ABC, abstractmethod
from typing import Any


class Bot(ABC):
    """Base class for bots in the agentic chain."""

    @abstractmethod
    async def process(self, message: Any) -> Any:
        """Process an incoming message and return a response."""
        raise NotImplementedError
