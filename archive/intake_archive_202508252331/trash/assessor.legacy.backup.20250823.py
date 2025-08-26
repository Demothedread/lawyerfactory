"""
Lightweight assessor compatibility wrapper.

This file now delegates to `assessor_consolidated` to provide a single
consolidated implementation while preserving the original public API
(`categorize`, `summarize`, `hashtags_from_category`, `intake_document`, etc.)
so existing imports across the codebase continue to work without changes.
"""

from .assessor_consolidated import (
    add_entry,
    enhanced_categorize_document,
    hashtags_from_category,
    ingest_files,
    intake_document,
    process_evidence_table_with_authority,
)
from .assessor_consolidated import simple_categorize as categorize
from .assessor_consolidated import (
    summarize,
)

__all__ = [
    'summarize', 'categorize', 'enhanced_categorize_document',
    'hashtags_from_category', 'intake_document', 'ingest_files',
    'process_evidence_table_with_authority', 'add_entry'
]
    'process_evidence_table_with_authority', 'add_entry'
]
    'process_evidence_table_with_authority', 'add_entry'
]
