"""
# Script Name: databases.py
# Description: Handles databases functionality in the LawyerFactory system.
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Storage
#   - Group Tags: null
class Database:
    """Simple in-memory store for research results."""

    def __init__(self) -> None:
        self._data = []

    def add(self, item: str) -> None:
        self._data.append(item)

    def all(self) -> list[str]:
        return list(self._data)
