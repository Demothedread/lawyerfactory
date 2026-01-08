"""Lightweight TF-IDF based vector store for retrieval with persistence."""

from __future__ import annotations

from pathlib import Path
import pickle
from typing import Any, Iterable

# 3P
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


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
        """Chunk text with sentence-aware boundaries.

        Attempts to split on sentence boundaries first, falling back to word
        boundaries if sentences are too long.
        """
        # Split into sentences (simple approach using common terminators)
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text)
        if not sentences:
            return []

        chunks = []
        current_chunk: list[str] = []
        current_word_count = 0

        for sentence in sentences:
            sentence_words = sentence.split()
            sentence_word_count = len(sentence_words)

            # If a single sentence exceeds chunk_size, split it by words
            if sentence_word_count > self.chunk_size:
                # Flush current chunk if it has content
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                    current_chunk = []
                    current_word_count = 0

                # Split long sentence into word-based chunks
                step = self.chunk_size - self.chunk_overlap
                for i in range(0, sentence_word_count, step):
                    chunk_words = sentence_words[i:i + self.chunk_size]
                    if chunk_words:
                        chunks.append(" ".join(chunk_words))
            elif current_word_count + sentence_word_count > self.chunk_size:
                # Current chunk would exceed size, flush it
                if current_chunk:
                    chunks.append(" ".join(current_chunk))

                # Start new chunk with overlap if applicable
                if self.chunk_overlap > 0 and current_chunk:
                    overlap_start = -self.chunk_overlap
                    overlap_words = (
                        " ".join(current_chunk).split()[overlap_start:]
                    )
                    current_chunk = overlap_words + sentence_words
                    current_word_count = len(current_chunk)
                else:
                    current_chunk = sentence_words
                    current_word_count = sentence_word_count
            else:
                # Add sentence to current chunk
                current_chunk.extend(sentence_words)
                current_word_count += sentence_word_count

        # Add final chunk if it has content
        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks if chunks else []

    def _load(self) -> None:
        """Load persisted state from disk.

        Security Warning: pickle.load can execute arbitrary code during
        deserialization. Only load from trusted storage_path locations that
        are not writable by untrusted users.
        """
        if not self.storage_path.exists():
            return
        try:
            with self.storage_path.open("rb") as handle:
                payload = pickle.load(handle)
            self.texts = payload.get("texts", [])
            self.metadata = payload.get("metadata", [])
            self._vectorizer = payload.get("vectorizer", TfidfVectorizer())
            self._matrix = payload.get("matrix")
            self._entry_counter = payload.get("entry_counter", len(self.metadata))
            self._pending_texts = []
        except (pickle.UnpicklingError, EOFError, AttributeError, ImportError) as e:
            # Handle corrupted files, version incompatibilities, or malicious payloads
            # Initialize with empty state and log the error
            print(f"Warning: Failed to load vector store from {self.storage_path}: {e}")
            print("Initializing with empty state.")
            self.texts = []
            self.metadata = []
            self._vectorizer = TfidfVectorizer()
            self._matrix = None
            self._entry_counter = 0
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
        """Persist the current state to disk using pickle.

        Security Warning: Only write to trusted storage_path locations. The
        pickled data can execute arbitrary code when loaded, so ensure the
        storage_path is not writable by untrusted users.
        """
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
