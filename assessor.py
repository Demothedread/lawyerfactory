from datetime import date
from pathlib import Path
from typing import Optional, Protocol
import warnings

import nltk

from repository import add_entry

LEGAL_KEYWORDS = {
    "contract": "legal:contract",
    "litigation": "legal:litigation",
    "evidence": "legal:evidence-primary",
    "news": "legal:news",
    "scholarship": "legal:scholarship",
    "caselaw": "legal:caselaw",
}
BUSINESS_KEYWORDS = {
    "financial": "business:financial-statements",
    "market": "business:market-analysis",
}
RESEARCH_KEYWORDS = {
    "study": "research:study",
    "analysis": "research:analysis",
}

NLTK_RESOURCE_PATHS = (
    "tokenizers/punkt",
    "tokenizers/punkt_tab/english.pickle",
)

# Cache for NLTK resource availability to avoid repeated checks
_nltk_available: Optional[bool] = None


class Summarizer(Protocol):
    """Interface for summary generation."""

    def summarize(self, text: str) -> str:
        """Return a condensed summary for ``text``."""
        ...


class PassthroughSummarizer:
    """Fallback summarizer that returns input text."""

    def summarize(self, text: str) -> str:
        """Return the input ``text`` unchanged."""
        return text


def _ensure_nltk_resources() -> bool:
    """Confirm required NLTK resources exist, returning availability."""
    global _nltk_available
    if _nltk_available is not None:
        return _nltk_available
    missing = []
    for resource in NLTK_RESOURCE_PATHS:
        try:
            nltk.data.find(resource)
        except LookupError:
            missing.append(resource)
    if not missing:
        _nltk_available = True
        return True
    resource_names = ", ".join(path.split("/")[-1] for path in missing)
    warnings.warn(
        "Missing NLTK resources: "
        f"{resource_names}. "
        "Install them with: python -m nltk.downloader punkt punkt_tab. "
        "Falling back to whitespace tokenization.",
        RuntimeWarning,
    )
    _nltk_available = False
    return False


def summarize(
    text: str,
    max_tokens: int = 250,
    summarizer: Optional[Summarizer] = None,
) -> str:
    """Summarize by extracting tokens from the start and end of ``text``.

    Uses NLTK word tokenization when available, otherwise falls back to
    whitespace splitting. When the text has more than ``max_tokens`` tokens,
    returns approximately the first half and last half of tokens, up to
    ``max_tokens`` total tokens.
    """
    tokenizer_ready = _ensure_nltk_resources()
    if tokenizer_ready:
        tokens = nltk.word_tokenize(text)
    else:
        tokens = text.split()
    if len(tokens) <= max_tokens:
        snippet = ' '.join(tokens)
    else:
        head_count = (max_tokens + 1) // 2
        tail_count = max_tokens // 2
        head = tokens[:head_count]
        tail = tokens[-tail_count:]
        snippet = ' '.join(head + tail)
    active_summarizer = summarizer or PassthroughSummarizer()
    return active_summarizer.summarize(snippet)


def categorize(text: str) -> str:
    """Return a hierarchical category label."""
    lowered = text.lower()
    for key, label in LEGAL_KEYWORDS.items():
        if key in lowered:
            return label
    for key, label in BUSINESS_KEYWORDS.items():
        if key in lowered:
            return label
    for key, label in RESEARCH_KEYWORDS.items():
        if key in lowered:
            return label
    return 'general'


def hashtags_from_category(category: str) -> str:
    """Convert ``category`` into a hashtag-friendly form."""
    return "#" + category.replace(":", "_")


def intake_document(
    author: str,
    title: str,
    publication_date: Optional[str],
    text: str,
    summarizer: Optional[Summarizer] = None,
) -> None:
    """Process ``text`` and store metadata in the repository."""
    if publication_date is None:
        publication_date = date.today().isoformat()
    summary = summarize(text, summarizer=summarizer)
    category = categorize(text)
    hashtags = hashtags_from_category(category)
    entry = {
        'author': author,
        'title': title,
        'publication_date': publication_date,
        'summary': summary,
        'category': category,
        'hashtags': hashtags,
    }
    add_entry(entry)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Intake a document into the repository'
    )
    parser.add_argument('file', type=Path, help='Path to a text file')
    parser.add_argument(
        '--author',
        required=True,
        help='Author of the document',
    )
    parser.add_argument('--title', required=True, help='Document title')
    parser.add_argument(
        '--date',
        help='Publication date in YYYY-MM-DD format',
    )
    args = parser.parse_args()

    text = args.file.read_text(encoding='utf-8')
    intake_document(args.author, args.title, args.date, text)
    print('Document ingested.')
