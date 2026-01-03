"""Lightweight TF-IDF based vector store for retrieval with persistence."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import pickle
from typing import Any, Iterable

# 3P
from sklearn.feature_extraction.text import TfidfVectorizer  # 3P
from sklearn.metrics.pairwise import cosine_similarity  # 3P


@dataclass(frozen=True)
class VectorEntry:
    """Represents a chunked entry stored in the vector index."""

    text: str
    metadata: dict[str, Any]


class VectorStore:
    """Persisted vector store that supports metadata filtering and chunking."""

    def __init__(
        self,
        storage_path: str | Path = "vector_store.pkl",
        chunk_size: int = 200,
        chunk_overlap: int = 40,
    ) -> None:
        self.storage_path = Path(storage_path)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.texts: list[str] = []
        self.metadata: list[dict[str, Any]] = []
        self._vectorizer = TfidfVectorizer()
        self._matrix = None
        self._pending_texts: list[str] = []
        self._entry_counter = 0
        self._load()

    def add(self, text: str, metadata: dict[str, Any] | None = None) -> None:
        """Add ``text`` and ``metadata`` to the store without updating vectors."""
        entry_metadata = dict(metadata or {})
        chunks = self._chunk_text(text)
        if not chunks:
            return
        entry_id = entry_metadata.get("entry_id") or self._next_entry_id()
        entry_metadata["entry_id"] = entry_id
        citation = (
            entry_metadata.get("citation")
            or entry_metadata.get("source")
            or "Unattributed"
        )
        entry_metadata["citation"] = citation
        for chunk_index, chunk_text in enumerate(chunks):
            chunk_metadata = dict(entry_metadata)
            chunk_metadata["chunk_index"] = chunk_index
            chunk_metadata["chunk_total"] = len(chunks)
            chunk_metadata["chunk_id"] = f"{entry_id}:{chunk_index}"
            self.texts.append(chunk_text)
            self.metadata.append(chunk_metadata)
            self._pending_texts.append(chunk_text)
        self._persist_state()

    def add_entries(self, entries: Iterable[tuple[str, dict[str, Any]]]) -> None:
        """Add multiple ``(text, metadata)`` entries."""
        for text, metadata in entries:
            self.add(text, metadata)

    def search(
        self,
        query: str,
        top_k: int = 3,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Return ``top_k`` chunks most similar to ``query`` with metadata."""
        if not self.texts:
            return []
        self.update_vectors()
        query_vec = self._vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self._matrix).flatten()
        indices = scores.argsort()[::-1]
        results: list[dict[str, Any]] = []
        for index in indices:
            metadata = self.metadata[index]
            if not self._passes_filters(metadata, filters):
                continue
            results.append(
                {
                    "text": self.texts[index],
                    "metadata": metadata,
                    "score": float(scores[index]),
                }
            )
            if len(results) >= top_k:
                break
        return results

    def update_vectors(self) -> None:
        """Update the vectorizer and matrix with pending texts."""
        if self.texts and (self._pending_texts or self._matrix is None):
            self._matrix = self._vectorizer.fit_transform(self.texts)
            self._pending_texts = []
            self._persist_state()

    def _chunk_text(self, text: str) -> list[str]:
        words = text.split()
        if not words:
            return []
        chunk_size = max(1, self.chunk_size)
        overlap = min(self.chunk_overlap, chunk_size - 1) if chunk_size > 1 else 0
        step = chunk_size - overlap
        chunks = []
        for start in range(0, len(words), step):
            chunk_words = words[start : start + chunk_size]
            if not chunk_words:
                continue
            chunks.append(" ".join(chunk_words))
            if start + chunk_size >= len(words):
                break
        return chunks

    def _load(self) -> None:
        if not self.storage_path.exists():
            return
        with self.storage_path.open("rb") as handle:
            payload = pickle.load(handle)
        self.texts = payload.get("texts", [])
        self.metadata = payload.get("metadata", [])
        self._vectorizer = payload.get("vectorizer", TfidfVectorizer())
        self._matrix = payload.get("matrix")
        self._entry_counter = payload.get("entry_counter", len(self.metadata))
        self._pending_texts = []

    def _next_entry_id(self) -> str:
        self._entry_counter += 1
        return f"entry-{self._entry_counter}"

    def _passes_filters(
        self,
        metadata: dict[str, Any],
        filters: dict[str, Any] | None,
    ) -> bool:
        if not filters:
            return True
        jurisdiction = filters.get("jurisdiction")
        if jurisdiction and metadata.get("jurisdiction") != jurisdiction:
            return False
        claim_elements = filters.get("claim_elements")
        if claim_elements:
            metadata_elements = set(metadata.get("claim_elements", []))
            if not metadata_elements.intersection(claim_elements):
                return False
        return True

    def _persist_state(self) -> None:
        payload = {
            "texts": self.texts,
            "metadata": self.metadata,
            "vectorizer": self._vectorizer,
            "matrix": self._matrix,
            "entry_counter": self._entry_counter,
        }
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        with self.storage_path.open("wb") as handle:
            pickle.dump(payload, handle)
