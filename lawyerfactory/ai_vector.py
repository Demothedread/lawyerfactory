"""Lightweight TF-IDF based vector store for retrieval."""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class VectorStore:
    """Simple in-memory vector store."""

    def __init__(self) -> None:
        self.texts: list[str] = []
        self._vectorizer = TfidfVectorizer()
        self._matrix = None

    def add(self, text: str) -> None:
        """Add ``text`` to the store and update vectors."""
        self.texts.append(text)
        self._matrix = self._vectorizer.fit_transform(self.texts)

    def search(self, query: str, top_k: int = 3) -> list[str]:
        """Return ``top_k`` texts most similar to ``query``."""
        if not self.texts:
            return []
        query_vec = self._vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self._matrix).flatten()
        indices = scores.argsort()[::-1][:top_k]
        return [self.texts[i] for i in indices]
