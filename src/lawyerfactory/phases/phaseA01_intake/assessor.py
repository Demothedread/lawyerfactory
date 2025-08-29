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

import asyncio  # new: used for async ingestion helpers
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
# Try to import enhanced evidence assessor
try:
    from .enhanced_evidence_assessor import EnhancedEvidenceAssessor  # type: ignore

    EVIDENCE_ASSESSOR_AVAILABLE = True
except Exception:
    EnhancedEvidenceAssessor = None
    EVIDENCE_ASSESSOR_AVAILABLE = False


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

# Import LLM integration functions (ensure names used below exist or are None)
try:
    from .llm_integration import llm_classify_evidence, llm_extract_metadata, llm_summarize_text

    LLM_INTEGRATION_AVAILABLE = True
except Exception:
    # fallback to None so callers can check LLM_INTEGRATION_AVAILABLE
    llm_classify_evidence = None
    llm_extract_metadata = None
    llm_summarize_text = None
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
async def intake_document(path: str, use_llm: bool = False) -> Dict[str, Any]:
    """Async ingestion helper: read file content, summarize, categorize and return metadata.

    - path: filesystem path to document
    - use_llm: prefer LLM-powered processing when available
    """
    result: Dict[str, Any] = {
        "path": path,
        "filename": Path(path).name if path else None,
        "summary": "",
        "categorization": {},
        "metadata": {},
        "content_preview": "",
        "hashtags": None,
        "processing_method": "none",
        "success": False,
        "error": None,
    }

    p = Path(path)
    if not p.exists() or not p.is_file():
        result.update({"error": "file_not_found"})
        logger.warning("intake_document: file not found: %s", path)
        return result

    loop = asyncio.get_event_loop()
    try:
        # Read file in threadpool (I/O bound)
        content = await loop.run_in_executor(
            None, lambda: p.read_text(encoding="utf-8", errors="replace")
        )
        result["content_preview"] = content[:500] + ("..." if len(content) > 500 else "")

        # Choose processing path
        if use_llm and LLM_INTEGRATION_AVAILABLE:
            # prefer LLM-powered processing when requested and available
            categorization = llm_classify_evidence(content, filename=p.name)
            metadata = llm_extract_metadata(content, filename=p.name)
            summary = llm_summarize_text(content)
            method = "llm"
        else:
            # fallback to enhanced/local processing
            categorization = enhanced_categorize_document(content, filename=p.name)
            metadata = {"title": p.name, "summary": summarize(content)}
            summary = summarize(content, max_sentences=3)
            method = "enhanced"

        result.update(
            {
                "summary": summary,
                "categorization": categorization,
                "metadata": metadata,
                "hashtags": (
                    hashtags_from_category(categorization.get("document_type", "general"))
                    if isinstance(categorization, dict)
                    else hashtags_from_category(categorization or "general")
                ),
                "processing_method": method,
                "success": True,
            }
        )
    except Exception as exc:
        logger.exception("intake_document failed for %s: %s", path, exc)
        result.update({"error": str(exc), "success": False})
    return result


async def async_ingest_files(paths: List[str], use_llm: bool = False) -> List[Dict[str, Any]]:
    """Concurrent ingestion of multiple files using intake_document."""
    if not paths:
        return []

    # If a specialized LLM-enhanced bulk helper exists and LLM integration is available,
    # run it in executor to avoid blocking the event loop (it is synchronous).
    if use_llm and LLM_INTEGRATION_AVAILABLE and "llm_enhanced_ingest_files" in globals():
        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(None, llm_enhanced_ingest_files, paths)
        except Exception as exc:
            logger.warning(
                "llm_enhanced_ingest_files failed, falling back to per-file ingest: %s", exc
            )

    # Otherwise run intake_document concurrently per file
    tasks = [intake_document(p, use_llm=use_llm) for p in paths]
    results = await asyncio.gather(*tasks, return_exceptions=False)
    return results


def intake_document_sync(path: str, use_llm: bool = False) -> Dict[str, Any]:
    """Synchronous wrapper for intake_document. Use cautiously inside existing event loops."""
    try:
        return asyncio.run(intake_document(path, use_llm=use_llm))
    except RuntimeError:
        # If there's already a running loop (e.g., in async environment), fallback to new loop execution
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Schedule and wait using a future if running loop exists
            coro = intake_document(path, use_llm=use_llm)
            fut = asyncio.run_coroutine_threadsafe(coro, loop)
            return fut.result()
        raise


def ingest_files(paths: List[str], use_llm: bool = False) -> List[Dict[str, Any]]:
    """Synchronous wrapper for async_ingest_files for backwards-compatibility."""
    try:
        return asyncio.run(async_ingest_files(paths, use_llm=use_llm))
    except RuntimeError:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            fut = asyncio.run_coroutine_threadsafe(async_ingest_files(paths, use_llm=use_llm), loop)
            return fut.result()
        raise


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


# --- Evidence assessment ---
def assess_evidence_content(content: str, filename: Optional[str] = None) -> Dict[str, Any]:
    """Try to run the enhanced evidence assessor; fallback to minimal processing."""
    try:
        if EVIDENCE_ASSESSOR_AVAILABLE and EnhancedEvidenceAssessor is not None:
            assessor = EnhancedEvidenceAssessor()
            return assessor.assess(content=content, filename=filename or "")
    except Exception as e:
        logger.warning("Enhanced evidence assessment failed: %s", e)
    return {"evidence_assessment": None}


# --- Backwards-compatible exported API ---
__all__ = [
    "summarize",
    "simple_categorize",
    "enhanced_categorize_document",
    "hashtags_from_category",
    "ingest_files",
    "process_evidence_table_with_authority",
    "add_entry",
    "intake_document",
    "async_ingest_files",
    "intake_document_sync",
    "assess_evidence_content",
]
