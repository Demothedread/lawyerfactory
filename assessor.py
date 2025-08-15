from datetime import date
from pathlib import Path
from typing import Optional

# Try to import nltk, otherwise provide fallbacks
try:
    import nltk
    NLTK_AVAILABLE = True
except Exception:
    nltk = None
    NLTK_AVAILABLE = False

from repository import add_entry

# Ensure NLTK tokenizer data is available if nltk is present
if NLTK_AVAILABLE:
    try:
        nltk.data.find("tokenizers/punkt")
    except Exception:
        try:
            nltk.download("punkt")
        except Exception:
            # if download fails, mark as unavailable for sentence tokenization
            NLTK_AVAILABLE = False

def _sent_tokenize(text: str):
    """Wrapper to provide sentence tokenization using nltk when available,
    otherwise split on sentence-ending punctuation as a fallback."""
    if NLTK_AVAILABLE and nltk:
        try:
            return nltk.sent_tokenize(text)
        except Exception:
            pass
    # Simple fallback splitter (naive)
    import re
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    sentences = [s for s in sentences if s]
    return sentences

def summarize(text: str, max_sentences: int = 2) -> str:
    """Return a naive summary consisting of the first `max_sentences` sentences."""
    if not text:
        return ""
    sentences = _sent_tokenize(text)
    return " ".join(sentences[:max_sentences])


def categorize(text: str) -> str:
    """Categorize text using simple keyword rules."""
    lowered = (text or "").lower()
    if 'contract' in lowered:
        return 'contract'
    if 'litigation' in lowered or 'lawsuit' in lowered or 'complaint' in lowered:
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
    try:
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
    except Exception as e:
        # Don't raise in intake - log and continue (repository may be optional)
        import logging
        logging.getLogger(__name__).exception("Failed to intake document: %s", e)


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
