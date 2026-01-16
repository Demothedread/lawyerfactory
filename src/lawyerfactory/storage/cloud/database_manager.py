"""
Database functionality for LawyerFactory system.

This module handles database operations for storing research results.

Relationships:
- Entity Type: Module
- Directory Group: Storage
- Group Tags: null
"""


class Database:
    """Simple in-memory store for research results."""

    def __init__(self) -> None:
        self._data: list[str] = []

    def add(self, item: str) -> None:
        self._data.append(item)

    def all(self) -> list[str]:
        return list(self._data)
