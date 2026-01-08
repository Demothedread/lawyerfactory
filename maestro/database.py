from typing import Any


class Database:
    """Simple in-memory store for structured research artifacts."""

    def __init__(self) -> None:
        self._data: list[dict[str, Any]] = []

    def add(self, item: dict[str, Any]) -> None:
        self._data.append(item)

    def all(self) -> list[dict[str, Any]]:
        return list(self._data)
