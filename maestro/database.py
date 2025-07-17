class Database:
    """Simple in-memory store for research results."""

    def __init__(self) -> None:
        self._data = []

    def add(self, item: str) -> None:
        self._data.append(item)

    def all(self) -> list[str]:
        return list(self._data)
