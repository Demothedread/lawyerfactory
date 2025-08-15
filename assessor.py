from datetime import date
from pathlib import Path
from typing import Optional

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

# Ensure NLTK sentence tokenizer data is available
try:
    nltk.data.find("tokenizers/punkt")
    nltk.data.find("tokenizers/punkt_tab/english.pickle")
except LookupError:
    nltk.download("punkt")
    nltk.download("punkt_tab")


def _llm_summarize(text: str) -> str:
    """Return a condensed summary via LLM (placeholder)."""
    return text


def summarize(text: str, max_words: int = 250) -> str:
    """Summarize using the first and last ``max_words`` tokens."""
    tokens = nltk.word_tokenize(text)
    if len(tokens) <= max_words:
        snippet = ' '.join(tokens)
    else:
        head = tokens[:max_words]
        tail = tokens[-max_words:]
        snippet = ' '.join(head + tail)
    return _llm_summarize(snippet)


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
) -> None:
    """Process ``text`` and store metadata in the repository."""
    if publication_date is None:
        publication_date = date.today().isoformat()
    summary = summarize(text)
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
