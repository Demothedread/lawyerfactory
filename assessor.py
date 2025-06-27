from datetime import date
from pathlib import Path
from typing import Optional

import nltk

from repository import add_entry

# Ensure NLTK sentence tokenizer data is available
try:
    nltk.data.find("tokenizers/punkt")
    nltk.data.find("tokenizers/punkt_tab/english.pickle")
except LookupError:
    nltk.download("punkt")
    nltk.download("punkt_tab")


def summarize(text: str, max_sentences: int = 2) -> str:
    """Return a naive summary consisting of the first `max_sentences` sentences."""
    sentences = nltk.sent_tokenize(text)
    return ' '.join(sentences[:max_sentences])


def categorize(text: str) -> str:
    """Categorize text using simple keyword rules."""
    lowered = text.lower()
    if 'contract' in lowered:
        return 'contract'
    if 'litigation' in lowered:
        return 'litigation'
    return 'general'


def hashtags_from_category(category: str) -> str:
    return f"#{category}"


def intake_document(
    author: str,
    title: str,
    publication_date: Optional[str],
    text: str,
) -> None:
    """Process and store a new document in the repository."""
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

    parser = argparse.ArgumentParser(description='Intake a document into the repository')
    parser.add_argument('file', type=Path, help='Path to a text file')
    parser.add_argument('--author', required=True, help='Author of the document')
    parser.add_argument('--title', required=True, help='Document title')
    parser.add_argument('--date', help='Publication date in YYYY-MM-DD format')
    args = parser.parse_args()

    text = args.file.read_text(encoding='utf-8')
    intake_document(args.author, args.title, args.date, text)
    print('Document ingested.')
