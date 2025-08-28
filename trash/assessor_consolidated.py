"""
Consolidated Assessor module

Combines the lightweight assessor and enhanced ingestion helpers into a
single, compact module that provides:
- sentence tokenization (nltk optional)
- summarization
- simple and enhanced categorization (with fallback)
- intake_document helper
- ingest_files: read first and last 300 lines from provided files and produce
  summarized/categorized payloads
- process_evidence_table_with_authority: minimal authority enrichment when
  CourtAuthorityHelper is available

This reduces file clutter while preserving capabilities.
"""

from datetime import date
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Optional nltk support
try:
    import nltk

    NLTK_AVAILABLE = True
except Exception:
    nltk = None
    NLTK_AVAILABLE = False

# Ensure punkt if nltk exists (defensive: avoid attr access on None for type-checkers)
if NLTK_AVAILABLE and nltk is not None:
    try:
        # only call data.find if the attribute exists and is not None
        if hasattr(nltk, "data") and getattr(nltk, "data") is not None:
            nltk.data.find("tokenizers/punkt")
        else:
            raise AttributeError("nltk.data unavailable")
    except Exception:
        try:
            # only call download if available
            if hasattr(nltk, "download") and callable(getattr(nltk, "download")):
                nltk.download("punkt")
            else:
                NLTK_AVAILABLE = False
        except Exception:
            NLTK_AVAILABLE = False

# Repository hook (kept for backward compatibility)
try:
    from repository import add_entry  # type: ignore
except Exception:

    def add_entry(_):
        return None


# Try to import enhanced categorizer
try:
    from .enhanced_document_categorizer import EnhancedDocumentCategorizer  # type: ignore

    ENHANCED_AVAILABLE = True
except Exception:
    EnhancedDocumentCategorizer = None
    ENHANCED_AVAILABLE = False

# Try to import court authority helper (optional)
try:
    from ...agents.research.court_authority_helper import CourtAuthorityHelper  # type: ignore

    AUTHORITY_HELPER_AVAILABLE = True
except Exception:
    CourtAuthorityHelper = None
    AUTHORITY_HELPER_AVAILABLE = False

# try to import new LLM service
try:
    from ...lf_core.llm import LLMService

    LLM_SERVICE_AVAILABLE = True
except Exception:
    LLM_SERVICE_AVAILABLE = False
    logger.warning("LLM service not available - using fallback categorization")
# Import LLM integration functions
try:
    from .llm_integration import (
        llm_classify_evidence,
        llm_extract_metadata,
        llm_summarize_text,
    )

    LLM_INTEGRATION_AVAILABLE = True
except Exception:
    LLM_INTEGRATION_AVAILABLE = False
    logger.warning("LLM integration functions not available")

# --- Text utilities ---


def _sent_tokenize(text: str) -> List[str]:
    if NLTK_AVAILABLE and nltk:
        try:
            return nltk.sent_tokenize(text)
        except Exception:
            pass
    import re

    sentences = re.split(r"(?<=[.!?])\s+", (text or "").strip())
    return [s for s in sentences if s]


def summarize(text: str, max_sentences: int = 2) -> str:
    if not text:
        return ""
    sents = _sent_tokenize(text)
    return " ".join(sents[:max_sentences])


# --- Categorization ---


def simple_categorize(text: str) -> str:
    """
    Enhanced text recognition method using comprehensive keyword arrays
    to categorize legal documents based on content analysis.
    """
    if not text:
        return "general"

    lowered = text.lower()

    # Contract-related keywords
    contract_keywords = [
        "contract",
        "agreement",
        "terms",
        "conditions",
        "clause",
        "provision",
        "party",
        "parties",
        "hereby",
        "whereas",
        "therefore",
        "shall",
        "warrant",
        "guarantee",
        "obligation",
        "breach",
        "termination",
        "amendment",
        "modification",
        "consideration",
        "recitals",
    ]

    # Litigation-related keywords
    litigation_keywords = [
        "litigation",
        "lawsuit",
        "complaint",
        "motion",
        "brief",
        "petition",
        "plaintiff",
        "defendant",
        "court",
        "judge",
        "attorney",
        "counsel",
        "jurisdiction",
        "venue",
        "discovery",
        "deposition",
        "trial",
        "settlement",
        "verdict",
        "judgment",
        "appeal",
        "subpoena",
        "summons",
        "witness",
        "testimony",
        "evidence",
        "affidavit",
        "pleading",
        "caption",
        "docket",
        "case number",
    ]

    # Financial document keywords
    financial_keywords = [
        "invoice",
        "receipt",
        "payment",
        "bill",
        "statement",
        "account",
        "ledger",
        "transaction",
        "deposit",
        "withdrawal",
        "balance",
        "amount",
        "fee",
        "charge",
        "cost",
        "expense",
        "revenue",
        "profit",
        "loss",
        "tax",
        "audit",
        "accounting",
        "bookkeeping",
    ]

    # Correspondence keywords
    correspondence_keywords = [
        "email",
        "letter",
        "correspondence",
        "memo",
        "memorandum",
        "message",
        "communication",
        "notice",
        "notification",
        "announcement",
        "press release",
        "newsletter",
        "report",
    ]

    # Regulatory/Compliance keywords
    regulatory_keywords = [
        "regulation",
        "compliance",
        "policy",
        "procedure",
        "guideline",
        "standard",
        "requirement",
        "mandate",
        "directive",
        "rule",
        "law",
        "statute",
        "code",
        "ordinance",
        "decree",
        "edict",
    ]

    # Employment/HR keywords
    employment_keywords = [
        "employment",
        "employee",
        "employer",
        "hire",
        "termination",
        "resignation",
        "position",
        "job",
        "role",
        "salary",
        "wage",
        "compensation",
        "benefit",
        "policy",
        "handbook",
        "manual",
    ]

    # Real Estate keywords
    real_estate_keywords = [
        "property",
        "real estate",
        "lease",
        "rental",
        "mortgage",
        "deed",
        "title",
        "land",
        "building",
        "premises",
        "tenant",
        "landlord",
        "possession",
        "occupancy",
        "eviction",
    ]

    # Intellectual Property keywords
    ip_keywords = [
        "patent",
        "trademark",
        "copyright",
        "intellectual property",
        "invention",
        "brand",
        "logo",
        "design",
        "confidential",
        "non-disclosure",
        "nda",
        "license",
        "royalty",
        "infringement",
    ]

    # Medical/Legal keywords
    medical_keywords = [
        "medical",
        "health",
        "patient",
        "doctor",
        "physician",
        "treatment",
        "diagnosis",
        "prescription",
        "record",
        "chart",
        "hospital",
        "clinic",
        "insurance",
        "claim",
        "malpractice",
    ]

    # Check for matches in each category
    if any(keyword in lowered for keyword in contract_keywords):
        return "contract"
    elif any(keyword in lowered for keyword in litigation_keywords):
        return "litigation"
    elif any(keyword in lowered for keyword in financial_keywords):
        return "financial"
    elif any(keyword in lowered for keyword in correspondence_keywords):
        return "correspondence"
    elif any(keyword in lowered for keyword in regulatory_keywords):
        return "regulatory"
    elif any(keyword in lowered for keyword in employment_keywords):
        return "employment"
    elif any(keyword in lowered for keyword in real_estate_keywords):
        return "real_estate"
    elif any(keyword in lowered for keyword in ip_keywords):
        return "intellectual_property"
    elif any(keyword in lowered for keyword in medical_keywords):
        return "medical"
    else:
        return "general"


def simple_categorize(text: str) -> str:
    lowered = (text or "").lower()
    if "contract" in lowered:
        return "contract"
    if "litigation" in lowered or "lawsuit" in lowered or "complaint" in lowered:
        return "litigation"
    return "general"


def hashtags_from_category(category: str) -> str:
    return f"#{category}"


def enhanced_categorize_document(
    content: str, filename: Optional[str] = None, defendant_hint: Optional[str] = None
) -> Dict[str, Any]:
    """Try to run the enhanced categorizer; fall back to simple categorization."""
    try:
        if ENHANCED_AVAILABLE and EnhancedDocumentCategorizer is not None:
            categorizer = EnhancedDocumentCategorizer()
            # ensure non-None strings are passed into downstream APIs
            safe_filename = filename or ""
            safe_defendant = defendant_hint or None
            doc = categorizer.categorize_document(
                text=content, filename=safe_filename, defendant_hint=safe_defendant
            )
            return {
                "document_type": getattr(
                    doc.document_type,
                    "value",
                    str(getattr(doc, "document_type", "unknown")),
                ),
                "authority_level": getattr(doc, "authority_level", "unknown"),
                "defendant_name": getattr(doc, "defendant_name", None),
                "confidence_score": getattr(doc, "confidence_score", 0.0),
                "extracted_entities": getattr(doc, "extracted_entities", []),
                "key_legal_issues": getattr(doc, "key_legal_issues", []),
                "cluster_id": getattr(doc, "cluster_id", None),
            }
    except Exception as e:
        logger.warning("Enhanced categorization failed: %s", e)
    # Fallback
    return {"document_type": simple_categorize(content)}


# --- Ingestion helpers ---

# --- LLM-powered functions ---


def llm_categorize_document(
    content: str, filename: Optional[str] = None, defendant_hint: Optional[str] = None
) -> Dict[str, Any]:
    """Use LLM service to categorize evidence with enhanced classification."""
    if not LLM_INTEGRATION_AVAILABLE:
        logger.warning(
            "LLM integration not available, falling back to enhanced categorization"
        )
        return enhanced_categorize_document(
            content, filename=filename, defendant_hint=defendant_hint
        )

    try:
        # Use LLM-powered classification
        # Normalize optional parameters to plain strings expected by LLM integration
        safe_filename = filename or ""
        safe_defendant = defendant_hint or ""
        result = llm_classify_evidence(content, safe_filename, safe_defendant)

        # Transform to match existing format
        return {
            "document_type": result.get("specific_category", "general"),
            "authority_level": result.get("authority_level", "secondary"),
            "defendant_name": result.get("defendant_name"),
            "confidence_score": result.get("confidence_score", 0.0),
            "extracted_entities": result.get("extracted_entities", []),
            "key_legal_issues": result.get("key_legal_issues", []),
            "cluster_id": result.get("cluster_id"),
            "evidence_type": result.get("evidence_type", "SECONDARY"),
            "classification_method": result.get("classification_method", "llm"),
        }

    except Exception as e:
        logger.error("LLM categorization error: %s", e)
        return enhanced_categorize_document(
            content, filename=filename, defendant_hint=defendant_hint
        )


def llm_extract_document_metadata(
    content: str, filename: Optional[str] = None
) -> Dict[str, Any]:
    """Use LLM service to extract comprehensive metadata from document content."""
    if not LLM_INTEGRATION_AVAILABLE:
        logger.warning("LLM integration not available for metadata extraction")
        return {"title": (filename or "Unknown"), "summary": summarize(content)}

    try:
        # Use LLM-powered metadata extraction
        metadata = llm_extract_metadata(content, filename or "")

        # Add basic summary if not provided
        if not metadata.get("summary"):
            metadata["summary"] = summarize(content)

        return metadata

    except Exception as e:
        logger.error("LLM metadata extraction error: %s", e)
        return {"title": (filename or "Unknown"), "summary": summarize(content)}


def llm_generate_summary(content: str, max_length: int = 200) -> str:
    """Use LLM service to generate intelligent document summaries."""
    if not LLM_INTEGRATION_AVAILABLE:
        logger.warning("LLM integration not available for summarization")
        return summarize(content, max_sentences=3)

    try:
        # Use LLM-powered summarization
        return llm_summarize_text(content, max_length)

    except Exception as e:
        logger.error("LLM summarization error: %s", e)
        return summarize(content, max_sentences=3)


def llm_enhanced_ingest_files(paths: List[str]) -> List[Dict[str, Any]]:
    """Enhanced version of ingest_files using LLM-powered processing."""
    results = []

    for path_str in paths:
        try:
            path = Path(path_str)
            if not path.exists():
                logger.warning("File not found: %s", path_str)
                continue

            # Read file content
            content = path.read_text(encoding="utf-8", errors="replace")

            # Use LLM-powered categorization and metadata extraction
            categorization = llm_categorize_document(content, path.name)
            metadata = llm_extract_document_metadata(content, path.name)
            summary = llm_generate_summary(content)

            # Build result payload
            result = {
                "filename": path.name,
                "path": str(path),
                "content_preview": (
                    content[:500] + "..." if len(content) > 500 else content
                ),
                "summary": summary,
                "categorization": categorization,
                "metadata": metadata,
                "hashtags": hashtags_from_category(
                    categorization.get("document_type", "general")
                ),
                "processing_method": "llm_enhanced",
            }

            results.append(result)

        except Exception as e:
            logger.error("Error processing file %s: %s", path_str, e)
            # Fallback to basic processing
            try:
                path = Path(path_str)
                content = path.read_text(encoding="utf-8", errors="replace")
                result = {
                    "filename": path.name,
                    "path": str(path),
                    "content_preview": (
                        content[:500] + "..." if len(content) > 500 else content
                    ),
                    "summary": summarize(content),
                    "categorization": {"document_type": simple_categorize(content)},
                    "metadata": {"title": path.name},
                    "hashtags": hashtags_from_category(simple_categorize(content)),
                    "processing_method": "fallback",
                }
                results.append(result)
            except Exception as fallback_error:
                logger.error(
                    "Fallback processing failed for %s: %s", path_str, fallback_error
                )

    return results


def _read_first_last_lines(path: Path, lines: int = 300) -> Dict[str, str]:
    """Read first and last `lines` lines from a text file. Returns dict with 'first' and 'last'."""
    first_part = ""
    last_part = ""
    try:
        with path.open("r", encoding="utf-8", errors="replace") as f:
            all_lines = f.readlines()
            if not all_lines:
                return {"first": "", "last": ""}
            first_part = "".join(all_lines[:lines])
            if len(all_lines) <= lines * 2:
                # file small enough: last part may overlap; keep the tail
                last_part = "".join(all_lines[lines:])
            else:
                last_part = "".join(all_lines[-lines:])
    except Exception as e:
        logger.exception("Failed to read file %s: %s", path, e)
    return {"first": first_part, "last": last_part}


def ingest_files(paths: List[str]) -> List[Dict[str, Any]]:
    """Ingest the provided file paths. For each file, ingest first and last 300 lines,
    summarize and categorize. Returns list of metadata dicts."""
    results = []
    for p in paths:
        path = Path(p)
        if not path.exists():
            logger.warning("Path does not exist: %s", p)
            continue
        parts = _read_first_last_lines(path, lines=300)
        combined = (parts.get("first", "") or "") + "\n" + (parts.get("last", "") or "")
        summary = summarize(combined, max_sentences=2)
        category_info = enhanced_categorize_document(combined, filename=path.name)
        category = category_info.get("document_type")
        hashtags = hashtags_from_category(category) if category else None
        entry = {
            "path": str(path),
            "first_part": parts.get("first", ""),
            "last_part": parts.get("last", ""),
            "summary": summary,
            "category_info": category_info,
            "hashtags": hashtags,
        }
        results.append(entry)
    return results


# --- Evidence authority enrichment (minimal) ---


def process_evidence_table_with_authority(
    evidence_table_path: str, intake_context: Optional[Any] = None
) -> Dict[str, Any]:
    """Load an evidence table (JSON), categorize entries and, if available,
    try to enrich with court authority helper. Returns processing summary."""
    path = Path(evidence_table_path)
    if not path.exists():
        return {"success": False, "error": "evidence table not found"}

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        logger.exception("Failed to read evidence table %s: %s", evidence_table_path, e)
        return {"success": False, "error": "read_error"}

    entries = data.get("evidence_entries") or data.get("entries") or []
    processed = []
    authority_helper = None
    if AUTHORITY_HELPER_AVAILABLE and CourtAuthorityHelper is not None:
        try:
            authority_helper = CourtAuthorityHelper()
        except Exception as e:
            logger.warning("CourtAuthorityHelper init failed: %s", e)
            authority_helper = None

    binding_count = 0
    persuasive_count = 0
    no_authority = 0

    for e in entries:
        text = e.get("content") or e.get("text") or ""
        bluebook = e.get("bluebook_citation")
        cat = enhanced_categorize_document(text, filename=e.get("source_document"))
        authority = None
        stars = None
        if authority_helper and bluebook:
            try:
                # best-effort call; helper API may differ across versions — use getattr to appease static checkers
                if hasattr(authority_helper, "assess_citation"):
                    authority = getattr(authority_helper, "assess_citation")(bluebook)
                elif hasattr(authority_helper, "assess"):
                    authority = getattr(authority_helper, "assess")(bluebook)
            except Exception as ex:
                logger.debug("Authority helper call failed for %s: %s", bluebook, ex)
        if authority:
            # normalize minimal expected fields
            stars = authority.get("stars") if isinstance(authority, dict) else None
            if stars is None:
                stars = authority.get("rating") if isinstance(authority, dict) else None
            if stars and stars >= 4:
                binding_count += 1
            elif stars:
                persuasive_count += 1
        else:
            no_authority += 1

        processed.append(
            {
                "evidence_id": e.get("evidence_id") or e.get("id"),
                "category": cat,
                "authority": authority,
                "stars": stars,
                "summary": summarize(text, max_sentences=2),
            }
        )

    return {
        "success": True,
        "entries_processed": len(processed),
        "binding_count": binding_count,
        "persuasive_count": persuasive_count,
        "no_authority_count": no_authority,
        "processed_entries": processed,
    }


# --- Backwards-compatible exported API ---
__all__ = [
    "summarize",
    "simple_categorize",
    "enhanced_categorize_document",
    "hashtags_from_category",
    "ingest_files",
    "process_evidence_table_with_authority",
    "add_entry",
]
__all__ = [
    "summarize",
    "simple_categorize",
    "enhanced_categorize_document",
    "hashtags_from_category",
    "ingest_files",
    "process_evidence_table_with_authority",
    "add_entry",
]
__all__ = [
    "summarize",
    "simple_categorize",
    "enhanced_categorize_document",
    "hashtags_from_category",
    "ingest_files",
    "process_evidence_table_with_authority",
    "add_entry",
]
