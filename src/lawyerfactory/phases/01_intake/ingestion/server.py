"""
# Script Name: server.py
# Description: Sample MCP Server for ChatGPT Integration  This server implements the Model Context Protocol (MCP) with search and fetch capabilities designed to work with ChatGPT's chat and deep research features.
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Ingestion
#   - Group Tags: null
Sample MCP Server for ChatGPT Integration

This server implements the Model Context Protocol (MCP) with search and fetch
capabilities designed to work with ChatGPT's chat and deep research features.
"""

import asyncio
import hashlib
import json
import logging
import os
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List

from qdrant_client import QdrantClient

qdrant_client = QdrantClient(
    url="https://4ce95fca-f9f6-4152-ad39-b059a7f4dfdd.us-west-1-0.aws.cloud.qdrant.io:6333",
    api_key=os.environ.get("QDRANT_API_KEY"),
)

# Test Qdrant connection (optional - only if debugging)
if os.environ.get("DEBUG_QDRANT") == "true":
    try:
        collections = qdrant_client.get_collections()
        logger.info(f"Qdrant collections: {collections}")
    except Exception as e:
        logger.warning(f"Qdrant connection test failed: {e}")
# Try to import optional SDKs; fall back gracefully
try:
    from fastmcp import FastMCP  # optional; not required for fallback
    FASTMCP_AVAILABLE = True
except Exception:
    FastMCP = None
    FASTMCP_AVAILABLE = False

try:
    from openai import \
        OpenAI  # optional; used only if available and API key present
    OPENAI_SDK_AVAILABLE = True
except Exception:
    OpenAI = None
    OPENAI_SDK_AVAILABLE = False

# aiohttp server fallback
try:
    from aiohttp import web
    AIOHTTP_AVAILABLE = True
except Exception:
    web = None
    AIOHTTP_AVAILABLE = False

# assessor import (used to feed downstream ingest)
try:
    from assessor import (categorize, hashtags_from_category, intake_document,
                          summarize)
    ASSESSOR_AVAILABLE = True
except Exception:
    ASSESSOR_AVAILABLE = False

# facts matrix adapter import
try:
    from lawyerfactory.ingest.adapters.facts_matrix_adapter import FactsMatrixAdapter
    FACTS_MATRIX_ADAPTER_AVAILABLE = True
except Exception:
    try:
        # Fallback to relative import
        from .adapters.facts_matrix_adapter import FactsMatrixAdapter
        FACTS_MATRIX_ADAPTER_AVAILABLE = True
    except Exception:
        FACTS_MATRIX_ADAPTER_AVAILABLE = False

# Enhanced Evidence API import
try:
    from maestro.evidence_api import EvidenceAPI, setup_evidence_routes
    EVIDENCE_API_AVAILABLE = True
except Exception:
    EVIDENCE_API_AVAILABLE = False
    # provide minimal fallbacks so names are always defined (static checks / best-effort runtime)
    def summarize(text: str, max_sentences: int = 2) -> str:
        if not text:
            return ""
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
        return " ".join(sentences[:max_sentences]) if sentences else text[:200]

    def categorize(text: str) -> str:
        txt = (text or "").lower()
        if any(k in txt for k in ("contract", "agreement", "terms")):
            return "contract"
        if any(k in txt for k in ("litigation", "lawsuit", "complaint", "motion")):
            return "litigation"
        if any(k in txt for k in ("invoice", "receipt", "payment", "bill")):
            return "financial"
        if any(k in txt for k in ("email", "correspondence", "message")):
            return "correspondence"
        return "general"

    def hashtags_from_category(category: str) -> List[str]:
        cat = (category or "general").strip().lower()
        return [f"#{cat.replace(' ', '_')}"]

    def intake_document(*args, **kwargs):
        logger.info("intake_document called but assessor not available; no-op")
        return None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test Qdrant connection (optional - only if debugging)
if os.environ.get("DEBUG_QDRANT") == "true":
    try:
        collections = qdrant_client.get_collections()
        logger.info(f"Qdrant collections: {collections}")
    except Exception as e:
        logger.warning(f"Qdrant connection test failed: {e}")

# Log adapter availability after logger is configured
if not FACTS_MATRIX_ADAPTER_AVAILABLE:
    logger.warning("FactsMatrixAdapter not available")

# OpenAI configuration (optional)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
VECTOR_STORE_ID = os.environ.get("VECTOR_STORE_ID", "")
# Add configurable target embedding dimension (defaults to 1536)
TARGET_DIM = int(os.environ.get("EMBED_DIM", "1536"))

# Optional OpenAI client initialization
openai_client = None
if OPENAI_SDK_AVAILABLE and OPENAI_API_KEY and OpenAI is not None:
    try:
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        logger.info("OpenAI SDK initialized")
    except Exception as e:
        logger.warning("OpenAI SDK could not be initialized: %s", e)
        openai_client = None

# Local storage paths
BASE_DIR = Path.cwd()
UPLOAD_DIR = BASE_DIR / "uploads"
FACT_DRAFTS_DIR = BASE_DIR / "uploads" / "fact_drafts"
CASE_DRAFTS_DIR = BASE_DIR / "uploads" / "case_drafts"
INDEX_PATH = BASE_DIR / "vector_backup.json"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
FACT_DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
CASE_DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
EVIDENCE_TABLE_PATH = BASE_DIR / "evidence_table.json"
LOCAL_VECTOR_PATH = BASE_DIR / "local_vectors.jsonl"
if not EVIDENCE_TABLE_PATH.exists():
    EVIDENCE_TABLE_PATH.write_text(json.dumps({"rows": []}, ensure_ascii=False, indent=2), encoding="utf-8")
if not LOCAL_VECTOR_PATH.exists():
    LOCAL_VECTOR_PATH.write_text("", encoding="utf-8")


# Simple local "vector backup" store
class VectorBackup:
    def __init__(self, path: Path):
        self.path = path
        self._lock = asyncio.Lock()
        if not self.path.exists():
            self._write_index({"files": {}})
        self._index = self._read_index()

    def _read_index(self):
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return {"files": {}}

    def _write_index(self, data):
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    async def add_file(self, file_id: str, metadata: Dict[str, Any]):
        async with self._lock:
            self._index = self._read_index()
            self._index["files"][file_id] = metadata
            self._write_index(self._index)

    async def get_file(self, file_id: str) -> Dict[str, Any] | None:
        async with self._lock:
            self._index = self._read_index()
            return self._index["files"].get(file_id)

    async def search(self, query: str) -> List[Dict[str, Any]]:
        async with self._lock:
            self._index = self._read_index()
            results = []
            q = query.lower()
            for fid, md in self._index["files"].items():
                text = (md.get("content") or "").lower()
                if not text:
                    continue
                score = text.count(q)
                if score > 0 or q in (md.get("title","").lower()):
                    snippet = (md.get("content","")[:300] + "...") if len(md.get("content","")) > 300 else md.get("content","")
                    results.append({
                        "id": fid,
                        "title": md.get("title"),
                        "text": snippet,
                        "score": score,
                        "url": md.get("url")
                    })
            # sort by score desc
            results.sort(key=lambda r: r["score"], reverse=True)
            return results

vector_backup = VectorBackup(INDEX_PATH)

# Helper to extract text for indexing (lightweight)
async def extract_text_for_index(file_path: Path) -> str:
    suffix = file_path.suffix.lower()
    if suffix in (".txt", ".md"):
        try:
            return file_path.read_text(encoding="utf-8")
        except Exception:
            return ""
    # For other types we store a small placeholder or attempt lightweight extraction
    if suffix == ".pdf":
        try:
            import PyPDF2
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                return "\n".join((p.extract_text() or "") for p in reader.pages)
        except Exception:
            return f"[PDF file indexed: {file_path.name}]"
    if suffix == ".docx":
        try:
            import docx
            doc = docx.Document(str(file_path))
            return "\n".join(p.text for p in doc.paragraphs)
        except Exception:
            return f"[DOCX file indexed: {file_path.name}]"
    # Binary fallback
    return f"[Binary file indexed: {file_path.name}]"

# New utilities: tokenization, embedding, local persistence, chunking, analysis, and evidence appends.
async def _simple_tokenize(text: str) -> Dict[str, Any]:
    """
    Lightweight tokenizer that returns token list and token count.
    Not a substitute for model tokenizers; used as fallback and for chunking heuristics.
    """
    try:
        if not text:
            return {"tokens": [], "count": 0}
        # split on whitespace and punctuation (simple)
        tokens = re.findall(r"\w+|[^\s\w]", text, flags=re.UNICODE)
        return {"tokens": tokens, "count": len(tokens)}
    except Exception as exc:
        logger.exception("Tokenization failed: %s", exc)
        return {"tokens": [], "count": 0}

async def _embed_text(text: str, model: str = "text-embedding-3-small") -> List[float]:
    """
    Return an embedding vector for text. Uses OpenAI client if available, otherwise
    returns a deterministic pseudo-vector based on SHA256 digest (float list).
    """
    if not text:
        return []
    # Try OpenAI embeddings if configured
    if openai_client and OPENAI_SDK_AVAILABLE and OPENAI_API_KEY:
        try:
            def _call_embeddings():
                # Modern OpenAI client: client.embeddings.create
                embeddings_api = getattr(openai_client, "embeddings", None)
                if embeddings_api is None:
                    raise RuntimeError("openai client has no 'embeddings' attribute")
                resp = embeddings_api.create(model=model, input=text)
                # safe parse
                data = getattr(resp, "data", None) or (resp.get("data") if isinstance(resp, dict) else None)
                if not data:
                    raise RuntimeError("no embedding data returned")
                first = data[0]
                vector = getattr(first, "embedding", None) or first.get("embedding")
                return vector
            vector = await asyncio.to_thread(_call_embeddings)
            return list(vector) if vector else []
        except Exception as exc:
            logger.warning("OpenAI embedding failed, falling back to local: %s", exc)

    # Fallback: deterministic pseudo-embedding (sha256 -> floats)
    try:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        # convert bytes to normalized floats in range [-1,1]
        vector = [((b / 255.0) * 2.0) - 1.0 for b in digest]
        return vector
    except Exception as exc:
        logger.exception("Fallback embedding failed: %s", exc)
        return []

async def _persist_local_vector(vector: List[float], metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Append a JSONL record to LOCAL_VECTOR_PATH with vector and metadata.
    Returns the record written (with assigned id and timestamp).
    """
    
    try:
        record_id = metadata.get("id") or hashlib.sha1(json.dumps(metadata, sort_keys=True).encode("utf-8")).hexdigest()
        timestamp = datetime.utcnow().isoformat() + "Z"
        record = {
            "id": record_id,
            "vector": vector,
            "metadata": metadata,
            "timestamp": timestamp
        }

        def _write():
            with open(LOCAL_VECTOR_PATH, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(record, ensure_ascii=False) + "\n")
            return record

        written = await asyncio.to_thread(_write)
        return written
    except Exception as exc:
        logger.exception("Persisting local vector failed: %s", exc)
        raise

async def _chunk_and_vectorize(text: str, metadata: Dict[str, Any], chunk_size_tokens: int = 400, overlap_tokens: int = 50) -> List[Dict[str, Any]]:
    """
    Chunk the input text into smaller pieces and vectorize each chunk. Returns
    a list of persisted records (ids, offsets, text snippet, metadata).
    Chunking uses token approximation via _simple_tokenize.
    """
    try:
        tk = await _simple_tokenize(text)
        tokens = tk["tokens"]
        if not tokens:
            return []
        results = []
        start = 0
        n = len(tokens)
        while start < n:
            end = min(start + chunk_size_tokens, n)
            chunk_tokens = tokens[start:end]
            chunk_text = " ".join(chunk_tokens)
            # embed
            vector = await _embed_text(chunk_text)

            # normalize vector length to TARGET_DIM
            if not vector:
                # fallback: zero vector if nothing returned
                vector = [0.0] * TARGET_DIM
            elif len(vector) != TARGET_DIM:
                reps = (TARGET_DIM + len(vector) - 1) // len(vector)
                vector = (vector * reps)[:TARGET_DIM]

            # prepare chunk metadata and deterministic chunk id
            chunk_meta = dict(metadata)
            chunk_meta.update({"chunk_start": start, "chunk_end": end, "snippet": chunk_text[:500]})
            chunk_meta.update({"chunk_index": len(results)})  # index before appending
            record_id = f"{metadata.get('id','doc')}::chunk{chunk_meta['chunk_index']}"
            chunk_meta["id"] = record_id

            # persist
            persisted = await _persist_local_vector(vector, chunk_meta)
            results.append({
                "id": persisted["id"],
                "start": start,
                "end": end,
                "snippet": chunk_text,
                "persisted": persisted
            })
            # advance with overlap
            start = end - overlap_tokens if (end - overlap_tokens) > start else end
        return results
    except Exception as exc:
        logger.exception("Chunking/vectorizing failed: %s", exc)
        return []

async def _analyze_with_openai(chunk_text: str, metadata: Dict[str, Any] | None = None, system_prompt: str | None = None, model: str = "gpt-4o-mini") -> Dict[str, Any]:
    """
    Ask the assistant to analyze a chunk (summary, categories, hashtags).
    Robust: accepts metadata, avoids undefined 'ai', and returns a normalized structure.
    """
    if metadata is None:
        metadata = {}

    try:
        default_system = (
            "You are an assistant that analyzes a text chunk and returns a short JSON with keys: "
            "summary (one paragraph), categories (array of short category strings), hashtags (array). "
            "Respond only with JSON when possible."
        )
        system_message = system_prompt or default_system

        async def _determine_type_and_group(evidence_hint: str | None, categories: List[str] | None, title_text: str | None):
            # Normalize hints
            hint = (evidence_hint or "").lower() if evidence_hint else ""
            title_low = (title_text or "").lower()
            cats_low = " ".join(categories or []).lower() if categories else ""

            # Decide primary vs secondary
            if hint and ("primary" in hint or hint.strip() == "p"):
                type_val = "primary"
            elif hint and ("secondary" in hint or hint.strip() == "s"):
                type_val = "secondary"
            else:
                # heuristics by text
                primary_indicators = ("email", "receipt", "invoice", "contract", "agreement", "sms", "message", "dataset", "spreadsheet", "photo", "image")
                secondary_indicators = ("news", "report", "journal", "case", "caselaw", "docket", "statute", "opinion", "article", "tweet", "social", "press")
                if any(k in title_low or k in cats_low for k in primary_indicators):
                    type_val = "primary"
                elif any(k in title_low or k in cats_low for k in secondary_indicators):
                    type_val = "secondary"
                else:
                    type_val = "secondary"

            # group mapping (same heuristics as before)
            if type_val == "primary":
                primary_groups = ["communications", "receipts", "contracts", "data", "photos", "other"]
                for g in primary_groups:
                    if g in cats_low or g in title_low:
                        return type_val, g
                if any(k in title_low for k in ("email", "message", "sms")):
                    return type_val, "communications"
                if any(k in title_low for k in ("invoice", "receipt")):
                    return type_val, "receipts"
                if any(k in title_low for k in ("contract", "agreement")):
                    return type_val, "contracts"
                if any(k in title_low for k in ("dataset", "data", "spreadsheet", "csv")):
                    return type_val, "data"
                return type_val, "other"
            else:
                secondary_groups = ["news article", "journal article", "caselaw", "report", "statute", "docket item", "background", "social media posts", "other"]
                for g in secondary_groups:
                    if g in cats_low or g in title_low:
                        return type_val, g
                if "case" in title_low or "opinion" in title_low or "caselaw" in cats_low:
                    return type_val, "caselaw"
                if "docket" in title_low:
                    return type_val, "docket item"
                if "news" in title_low or "press" in title_low:
                    return type_val, "news article"
                return type_val, "other"

        def _extract_tags(categories: List[str], parsed_tags: List[str], title_text: str, assistant_text: str) -> List[str]:
            # A small consistent set of tags related to claims/sections; at most 3 returned.
            mapping = {
                "contract": "#contract",
                "breach": "#breach",
                "fraud": "#fraud",
                "negligence": "#negligence",
                "damages": "#damages",
                "liability": "#liability",
                "statute": "#statute",
                "privacy": "#privacy",
                "employment": "#employment",
                "patent": "#patent"
            }
            candidates = []
            # prefer explicit parsed hashtags first
            for t in (parsed_tags or []):
                tag = t if t.startswith("#") else f"#{t}"
                if tag not in candidates:
                    candidates.append(tag)
            text_blob = " ".join([ " ".join(categories or []), title_text or "", assistant_text or "" ]).lower()
            for k, v in mapping.items():
                if k in text_blob and v not in candidates:
                    candidates.append(v)
            return candidates[:3]

        if openai_client and OPENAI_SDK_AVAILABLE and OPENAI_API_KEY:
            def _call_chat():
                chat_api = getattr(openai_client, "chat", None)
                if chat_api is None:
                    comp_api = getattr(openai_client, "chat_completions", None)
                    if comp_api is None:
                        # best-effort older client
                        raise RuntimeError("openai client has no chat/chat_completions API")
                    resp = comp_api.create(model=model, messages=[{"role": "system", "content": system_message},
                                                                 {"role": "user", "content": chunk_text}], max_tokens=400)
                else:
                    resp = chat_api.completions.create(model=model, messages=[{"role": "system", "content": system_message},
                                                                               {"role": "user", "content": chunk_text}], max_tokens=400)
                # extract assistant text robustly
                content = ""
                if hasattr(resp, "choices") and resp.choices:
                    first = resp.choices[0]
                    msg = getattr(first, "message", None)
                    if msg:
                        content = getattr(msg, "content", "") or ""
                    else:
                        content = getattr(first, "text", "") or ""
                elif isinstance(resp, dict):
                    choices = resp.get("choices") or []
                    if choices:
                        content = choices[0].get("message", {}).get("content") or choices[0].get("text") or ""
                return content or ""

            assistant_text = await asyncio.to_thread(_call_chat)

            # try to parse assistant output as JSON; if not, fallback to heuristics
            parsed = None
            try:
                parsed = json.loads(assistant_text)
            except Exception:
                parsed = None

            upload_id = metadata.get("id") or hashlib.sha1(json.dumps(metadata or {}, sort_keys=True).encode("utf-8")).hexdigest()
            title = metadata.get("title") or metadata.get("original_filename") or upload_id
            author = metadata.get("author") or (parsed.get("author") if parsed else None) or "Unknown"
            publication_date = metadata.get("publication_date") or (parsed.get("publication_date") if parsed else None) or date.today().isoformat()
            summary = (parsed.get("summary") if parsed else None) or (assistant_text.strip().split("\n")[0][:500] if assistant_text else None)
            analysis_text = (parsed.get("analysis") if parsed else None) or assistant_text

            parsed_categories = parsed.get("categories") if parsed else []
            parsed_hashtags = parsed.get("hashtags") if parsed else []

            evidence_hint = parsed.get("type") if parsed else None
            type_val, group_val = await _determine_type_and_group(evidence_hint, parsed_categories, title)

            tags = _extract_tags(parsed_categories, parsed_hashtags, title, assistant_text)

            # star rating heuristics (1-5)
            importance = 3
            if type_val == "primary":
                importance += 1
            if any(k in (title or "").lower() for k in ("contract", "agreement", "invoice", "receipt", "email", "sms", "message")):
                importance = max(importance, 5)
            if len(chunk_text or "") > 2000:
                importance = min(5, importance + 1)
            stars = max(1, min(5, importance))

            return {
                "uploadID": upload_id,
                "source_file": title,
                "title": title,
                "author": author,
                "publication_date": publication_date,
                "summary": summary,
                "analysis": analysis_text,
                "type": type_val,
                "tags": tags,
                "group": group_val,
                "stars": stars,
                "raw": assistant_text
            }

        else:
            # Local fallback analysis
            summary = (chunk_text or "").strip().replace("\n", " ")[:400]
            words = re.findall(r"\w+", chunk_text.lower() if chunk_text else "")
            freq = {}
            for w in words:
                if len(w) < 4:
                    continue
                freq[w] = freq.get(w, 0) + 1
            top = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:5]
            hashtags = [f"#{w[0]}" for w in top]
            categories = [top[0][0]] if top else []
            # decide type/group via heuristics above
            type_val, group_val = await _determine_type_and_group(None, categories, metadata.get("title") or "")
            # stars simple heuristic
            stars = 4 if type_val == "primary" else 2
            upload_id = metadata.get("id") or hashlib.sha1(json.dumps(metadata or {}, sort_keys=True).encode("utf-8")).hexdigest()

            return {
                "uploadID": upload_id,
                "source_file": metadata.get("original_filename") or metadata.get("title"),
                "title": metadata.get("title"),
                "author": metadata.get("author") or "Unknown",
                "publication_date": metadata.get("publication_date") or date.today().isoformat(),
                "summary": summary,
                "analysis": None,
                "type": type_val,
                "tags": hashtags[:3],
                "group": group_val,
                "stars": stars,
                "raw": None
            }
    except Exception as exc:
        logger.exception("Analysis call failed: %s", exc)
        return {"summary": None, "categories": [], "hashtags": [], "raw": None, "type": "secondary", "tags": [], "group": "other", "stars": 1}

async def _append_evidence_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Append an evidence row to EVIDENCE_TABLE_PATH JSON. Returns the appended row (with timestamp).
    """
    try:
        def _read_write():
            if not EVIDENCE_TABLE_PATH.exists():
                base = {"rows": []}
            else:
                with open(EVIDENCE_TABLE_PATH, "r", encoding="utf-8") as fh:
                    base = json.load(fh)
            row_copy = dict(row)
            row_copy.setdefault("id", hashlib.sha1(json.dumps(row_copy, sort_keys=True).encode("utf-8")).hexdigest())
            row_copy.setdefault("timestamp", datetime.utcnow().isoformat() + "Z")
            base.setdefault("rows", []).append(row_copy)
            with open(EVIDENCE_TABLE_PATH, "w", encoding="utf-8") as fh:
                json.dump(base, fh, ensure_ascii=False, indent=2)
            return row_copy

        appended = await asyncio.to_thread(_read_write)
        return appended
    except Exception as exc:
        logger.exception("Appending evidence row failed: %s", exc)
        raise

# Draft document processing functions
async def _process_draft_document(content: str, metadata: Dict[str, Any], draft_type: str) -> Dict[str, Any]:
    """Enhanced processing for draft documents with foundational categorization"""
    try:
        # Mark as foundational/pre-existing in metadata
        metadata.update({
            'draft_type': draft_type,
            'document_category': 'foundational',
            'priority_level': 'high',
            'processing_phase': 'pre_intake'
        })
        
        # Enhanced analysis for draft documents
        analysis_result = await _analyze_with_openai(
            content,
            metadata,
            system_prompt=(
                f"You are analyzing a {draft_type} draft document that contains foundational legal information. "
                "Extract key legal entities, facts, parties, dates, claims, and legal issues. "
                "This is foundational content that should be treated with high confidence. "
                "Return JSON with: summary, legal_entities, key_facts, legal_issues, parties, dates, claims."
            )
        )
        
        # Enhance the analysis with draft-specific categorization
        analysis_result.update({
            'draft_type': draft_type,
            'confidence_boost': 0.2,  # Higher confidence for draft documents
            'foundational': True,
            'processing_priority': 'immediate'
        })
        
        return analysis_result
        
    except Exception as exc:
        logger.exception("Draft document processing failed: %s", exc)
        return {"error": str(exc), "draft_type": draft_type}

async def _aggregate_draft_documents(draft_list: List[Dict[str, Any]], draft_type: str) -> Dict[str, Any]:
    """Aggregate multiple draft documents into unified fact base"""
    try:
        if not draft_list:
            return {"aggregated_content": "", "entity_count": 0}
        
        # Combine all content
        combined_content = "\n\n--- DOCUMENT SEPARATOR ---\n\n".join([
            draft.get('content', '') for draft in draft_list
        ])
        
        # Extract and merge entities from all drafts
        all_entities = []
        all_facts = []
        all_legal_issues = []
        
        for draft in draft_list:
            if 'analysis' in draft:
                analysis = draft['analysis']
                if isinstance(analysis, dict):
                    all_entities.extend(analysis.get('legal_entities', []))
                    all_facts.extend(analysis.get('key_facts', []))
                    all_legal_issues.extend(analysis.get('legal_issues', []))
        
        # Deduplicate and prioritize
        unique_entities = list(set(all_entities))
        unique_facts = list(set(all_facts))
        unique_issues = list(set(all_legal_issues))
        
        aggregated_data = {
            'aggregated_content': combined_content,
            'entity_count': len(unique_entities),
            'entities': unique_entities,
            'facts': unique_facts,
            'legal_issues': unique_issues,
            'draft_type': draft_type,
            'source_count': len(draft_list),
            'priority': 'foundational'
        }
        
        return aggregated_data
        
    except Exception as exc:
        logger.exception("Draft aggregation failed: %s", exc)
        return {"error": str(exc), "draft_type": draft_type}

async def _process_with_facts_matrix_adapter(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process raw ingestion data using the FactsMatrixAdapter to ensure
    canonical facts_matrix format for downstream consumers.
    """
    if not FACTS_MATRIX_ADAPTER_AVAILABLE:
        logger.warning("FactsMatrixAdapter not available, returning raw data")
        return raw_data
    
    try:
        logger.info("Processing raw data with FactsMatrixAdapter")
        # Use the new canonical API method
        facts_matrix = FactsMatrixAdapter.process(raw_data)
        
        # Validate the output
        if FactsMatrixAdapter.validate_facts_matrix(facts_matrix):
            logger.info("Facts matrix validation passed")
            logger.info(f"Generated facts matrix with {len(facts_matrix.get('undisputed_facts', []))} undisputed facts, "
                       f"{len(facts_matrix.get('disputed_facts', []))} disputed facts, "
                       f"{len(facts_matrix.get('procedural_facts', []))} procedural facts")
            return {
                "facts_matrix": facts_matrix,
                "adapter_version": "2.0",  # Updated version with canonical contract
                "processing_timestamp": datetime.now().isoformat(),
                "original_data": raw_data  # Keep original for debugging
            }
        else:
            logger.error("Facts matrix validation failed, returning original data")
            return raw_data
            
    except Exception as e:
        logger.error(f"Error processing with FactsMatrixAdapter: {e}")
        return raw_data

async def _ingest_to_knowledge_graph(entities: List[Dict[str, Any]], metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Ingest draft document entities into knowledge graph with high confidence"""
    try:
        # Attempt to use actual knowledge graph if available
        try:
            from knowledge_graph_extensions import extend_knowledge_graph

            from knowledge_graph import KnowledgeGraph

            # Initialize knowledge graph connection
            kg = KnowledgeGraph('knowledge_graphs/main.db')
            extend_knowledge_graph(kg)
            
            # Process entities for knowledge graph ingestion
            entities_stored = 0
            relationships_discovered = 0
            
            for entity in entities:
                if isinstance(entity, dict):
                    # Create entity record for KG
                    entity_data = {
                        'type': entity.get('type', 'UNKNOWN'),
                        'name': entity.get('name', str(entity)),
                        'description': entity.get('description', ''),
                        'confidence': 0.9,  # High confidence for draft documents
                        'extraction_method': f"draft_{metadata.get('draft_type', 'unknown')}",
                        'source_text': metadata.get('content', '')[:500],  # First 500 chars
                        'legal_attributes': json.dumps({
                            'draft_type': metadata.get('draft_type'),
                            'foundational': True,
                            'priority': 'high'
                        })
                    }
                    
                    # Add entity to knowledge graph
                    entity_id = kg.add_entity_dict(entity_data)
                    if entity_id:
                        entities_stored += 1
                        
                        # Estimate relationships (simplified for now)
                        relationships_discovered += 1
            
            kg_result = {
                'entities_stored': entities_stored,
                'confidence_scores': [0.9] * entities_stored,
                'relationships_discovered': relationships_discovered,
                'foundational_categorization': True,
                'metadata': metadata,
                'kg_integration': 'successful'
            }
            
            logger.info(f"KG ingestion successful: {entities_stored} entities from {metadata.get('draft_type', 'unknown')} draft")
            return kg_result
            
        except ImportError:
            logger.warning("Knowledge graph modules not available, using fallback")
            # Fallback to simulated ingestion
            kg_result = {
                'entities_stored': len(entities),
                'confidence_scores': [0.9] * len(entities),  # High confidence for drafts
                'relationships_discovered': len(entities) * 2,  # Estimate relationships
                'foundational_categorization': True,
                'metadata': metadata,
                'kg_integration': 'simulated'
            }
            
            logger.info(f"Simulated KG ingestion: {len(entities)} entities from {metadata.get('draft_type', 'unknown')} draft")
            return kg_result
        
    except Exception as exc:
        logger.exception("Knowledge graph ingestion failed: %s", exc)
        return {"error": str(exc), "kg_integration": "failed"}

# aiohttp handlers (fallback MCP-like HTTP interface)
async def handle_upload(request):
    """
    POST /api/upload
    multipart form with 'file'
    returns JSON { success: True, upload_id, original_filename, filename, ... }
    """
    reader = await request.multipart()
    field = await reader.next()
    if field is None or field.name != "file":
        return web.json_response({"success": False, "error": "No file field provided"}, status=400)

    original_filename = field.filename or "unnamed"
    save_name = f"{int(asyncio.get_event_loop().time()*1000)}_{original_filename}"
    save_path = UPLOAD_DIR / save_name

    # write file to disk
    with open(save_path, "wb") as f:
        while True:
            chunk = await field.read_chunk()
            if not chunk:
                break
            f.write(chunk)

    # extract content for index (async)
    content = await extract_text_for_index(save_path)
    file_id = save_name  # unique id for local store
    metadata = {
        "id": file_id,
        "title": original_filename,
        "original_filename": original_filename,
        "filename": str(save_path),
        "url": f"/uploads/{save_name}",
        "content": content
    }
    await vector_backup.add_file(file_id, metadata)

    # chunk_and_vectorize expects (text, metadata)
    chunk_count = await _chunk_and_vectorize(content, metadata)
    # analyze the content with metadata context
    evidence_row = await _analyze_with_openai(content, metadata)

    evidence_row.update({
        "upload_id": file_id,
        "url": f"/uploads/{save_name}",
        "token_chunks": chunk_count,
        "bytes": os.path.getsize(save_path)
    })
    await _append_evidence_row(evidence_row)
    # Try to feed assessor intake automatically (best-effort)

    if ASSESSOR_AVAILABLE:
        try:
            # best-effort: call intake_document to populate repository
            intake_document(
                author="Uploader",
                title=original_filename,
                publication_date=None,
                text=content or f"[No extractable content for {original_filename}]"
            )
            stored = True
        except Exception as e:
            logger.exception("Assessor intake failed: %s", e)
            stored = False
    else:
        stored = False

    return web.json_response({
        "success": True,
        "upload_id": file_id,
        "original_filename": original_filename,
        "filename": str(save_path),
        "upload_session_id": file_id,
        "stored_in_repository": stored,
        "evidence_row": evidence_row,"token_chunks": chunk_count
    })

async def handle_upload_fact_draft(request):
    """
    POST /api/upload-fact-draft
    Handle fact statement draft uploads with enhanced processing
    """
    try:
        reader = await request.multipart()
        field = await reader.next()
        if field is None or field.name != "file":
            return web.json_response({"success": False, "error": "No file field provided"}, status=400)

        original_filename = field.filename or "unnamed_fact_draft"
        save_name = f"fact_draft_{int(asyncio.get_event_loop().time()*1000)}_{original_filename}"
        save_path = FACT_DRAFTS_DIR / save_name

        # Write file to fact drafts directory
        with open(save_path, "wb") as f:
            while True:
                chunk = await field.read_chunk()
                if not chunk:
                    break
                f.write(chunk)

        # Extract content and process as draft document
        content = await extract_text_for_index(save_path)
        file_id = save_name
        
        metadata = {
            "id": file_id,
            "title": original_filename,
            "original_filename": original_filename,
            "filename": str(save_path),
            "url": f"/uploads/fact_drafts/{save_name}",
            "content": content,
            "draft_type": "fact_statement"
        }
        
        # Process as draft document with enhanced analysis
        draft_analysis = await _process_draft_document(content, metadata, "fact_statement")
        
        # Add to vector backup with draft categorization
        await vector_backup.add_file(file_id, metadata)
        
        # Enhanced chunking and vectorization for draft content
        chunk_count = await _chunk_and_vectorize(content, metadata)
        
        # Create evidence row with draft-specific data
        evidence_row = dict(draft_analysis)
        evidence_row.update({
            "upload_id": file_id,
            "url": f"/uploads/fact_drafts/{save_name}",
            "token_chunks": chunk_count,
            "bytes": os.path.getsize(save_path),
            "document_type": "fact_statement_draft",
            "priority": "foundational"
        })
        
        await _append_evidence_row(evidence_row)
        
        # Ingest into knowledge graph with high priority
        if 'legal_entities' in draft_analysis:
            kg_result = await _ingest_to_knowledge_graph(
                draft_analysis.get('legal_entities', []),
                metadata
            )
            evidence_row['knowledge_graph_result'] = kg_result

        return web.json_response({
            "success": True,
            "upload_id": file_id,
            "original_filename": original_filename,
            "filename": str(save_path),
            "document_type": "fact_statement_draft",
            "draft_analysis": draft_analysis,
            "evidence_row": evidence_row,
            "processing_priority": "foundational"
        })

    except Exception as e:
        logger.exception("Fact draft upload failed: %s", e)
        return web.json_response({"success": False, "error": str(e)}, status=500)

async def handle_upload_case_draft(request):
    """
    POST /api/upload-case-draft
    Handle case/complaint draft uploads with enhanced processing
    """
    try:
        reader = await request.multipart()
        field = await reader.next()
        if field is None or field.name != "file":
            return web.json_response({"success": False, "error": "No file field provided"}, status=400)

        original_filename = field.filename or "unnamed_case_draft"
        save_name = f"case_draft_{int(asyncio.get_event_loop().time()*1000)}_{original_filename}"
        save_path = CASE_DRAFTS_DIR / save_name

        # Write file to case drafts directory
        with open(save_path, "wb") as f:
            while True:
                chunk = await field.read_chunk()
                if not chunk:
                    break
                f.write(chunk)

        # Extract content and process as draft document
        content = await extract_text_for_index(save_path)
        file_id = save_name
        
        metadata = {
            "id": file_id,
            "title": original_filename,
            "original_filename": original_filename,
            "filename": str(save_path),
            "url": f"/uploads/case_drafts/{save_name}",
            "content": content,
            "draft_type": "case_complaint"
        }
        
        # Process as draft document with enhanced analysis
        draft_analysis = await _process_draft_document(content, metadata, "case_complaint")
        
        # Add to vector backup with draft categorization
        await vector_backup.add_file(file_id, metadata)
        
        # Enhanced chunking and vectorization for draft content
        chunk_count = await _chunk_and_vectorize(content, metadata)
        
        # Create evidence row with draft-specific data
        evidence_row = dict(draft_analysis)
        evidence_row.update({
            "upload_id": file_id,
            "url": f"/uploads/case_drafts/{save_name}",
            "token_chunks": chunk_count,
            "bytes": os.path.getsize(save_path),
            "document_type": "case_complaint_draft",
            "priority": "foundational"
        })
        
        await _append_evidence_row(evidence_row)
        
        # Ingest into knowledge graph with high priority
        if 'legal_entities' in draft_analysis:
            kg_result = await _ingest_to_knowledge_graph(
                draft_analysis.get('legal_entities', []),
                metadata
            )
            evidence_row['knowledge_graph_result'] = kg_result

        return web.json_response({
            "success": True,
            "upload_id": file_id,
            "original_filename": original_filename,
            "filename": str(save_path),
            "document_type": "case_complaint_draft",
            "draft_analysis": draft_analysis,
            "evidence_row": evidence_row,
            "processing_priority": "foundational"
        })

    except Exception as e:
        logger.exception("Case draft upload failed: %s", e)
        return web.json_response({"success": False, "error": str(e)}, status=500)


async def handle_search(request):
    """
    POST /mcp/search  payload: { "query": "..." }
    Searches local vector backup (fallback) or OpenAI vector store if available.
    """
    try:
        payload = await request.json()
        query = payload.get("query", "")
    except Exception:
        return web.json_response({"results": []})

    if not query.strip():
        return web.json_response({"results": []})

    # If OpenAI vector store available, attempt to use it (best-effort)
    if openai_client and OPENAI_SDK_AVAILABLE and OPENAI_API_KEY:
        try:
            # Use the OpenAI client vector store if configured
            resp = openai_client.vector_stores.search(vector_store_id=VECTOR_STORE_ID, query=query)
            results = []
            if hasattr(resp, "data") and resp.data:
                for i, item in enumerate(resp.data):
                    item_id = getattr(item, "file_id", f"vs_{i}")
                    item_filename = getattr(item, "filename", f"Document {i+1}")
                    content_list = getattr(item, "content", [])
                    text_content = ""
                    if content_list and len(content_list) > 0:
                        first_content = content_list[0]
                        if hasattr(first_content, "text"):
                            text_content = first_content.text
                        elif isinstance(first_content, dict):
                            text_content = first_content.get("text", "")
                    text_snippet = text_content[:200] + "..." if len(text_content) > 200 else text_content
                    results.append({
                        "id": item_id,
                        "title": item_filename,
                        "text": text_snippet,
                        "url": f"https://platform.openai.com/storage/files/{item_id}"
                    })
            return web.json_response({"results": results})
        except Exception as e:
            logger.warning("OpenAI vector search failed, falling back to local index: %s", e)

    # Fallback local search
    results = await vector_backup.search(query)
    return web.json_response({"results": results})


async def handle_fetch(request):
    """
    GET /mcp/fetch?id=...
    Returns file metadata and full text from local backup or OpenAI vector store.
    """
    file_id = request.rel_url.query.get("id", "")
    if not file_id:
        return web.json_response({"error": "file id is required"}, status=400)

    # Try OpenAI retrieval first if available
    if openai_client and OPENAI_SDK_AVAILABLE and OPENAI_API_KEY:
        try:
            content_response = openai_client.vector_stores.files.content(vector_store_id=VECTOR_STORE_ID, file_id=file_id)
            file_info = openai_client.vector_stores.files.retrieve(vector_store_id=VECTOR_STORE_ID, file_id=file_id)
            file_content = ""
            if hasattr(content_response, "data") and content_response.data:
                parts = []
                for item in content_response.data:
                    if hasattr(item, "text"):
                        parts.append(item.text)
                file_content = "\n".join(parts)
            else:
                file_content = "No content available"
            filename = getattr(file_info, "filename", f"Document {file_id}")
            return web.json_response({
                "id": file_id,
                "title": filename,
                "text": file_content,
                "url": f"https://platform.openai.com/storage/files/{file_id}",
                "metadata": getattr(file_info, "attributes", None)
            })
        except Exception as e:
            logger.warning("OpenAI fetch failed, falling back to local index: %s", e)

    # Fallback to local index
    metadata = await vector_backup.get_file(file_id)
    if not metadata:
        return web.json_response({"error": "file not found"}, status=404)
    return web.json_response({
        "id": metadata["id"],
        "title": metadata.get("title"),
        "text": metadata.get("content", "No content available"),
        "url": metadata.get("url"),
        "metadata": None
    })


# Minimal workflow start endpoint (frontend expects /api/workflow POST)
async def handle_start_workflow(request):
    """
    POST /api/workflow
    Accepts JSON: { case_name, case_description, uploaded_files, ... }
    Returns a lightweight session id and echoes payload. This server acts as an in-between:
    it stores files and triggers assessor intake (already done on upload) and returns a session id
    that the frontend can use to join sockets (if an external orchestrator exists).
    """
    try:
        payload = await request.json()
    except Exception:
        return web.json_response({"success": False, "error": "invalid json"}, status=400)

    session_id = f"session_{int(asyncio.get_event_loop().time()*1000)}"
    # lightweight response expected by the frontend
    response = {
        "success": True,
        "session_id": session_id,
        "case_name": payload.get("case_name"),
        "case_description": payload.get("case_description"),
        "uploaded_files": payload.get("uploaded_files", []),
        "message": "Workflow started (ingest handled). This server is a pass-through to assessor/reader_bot."
    }
    return web.json_response(response)


# Static file route for uploads (optional serving)
async def handle_uploaded_file(request):
    name = request.match_info.get("name")
    
    # Check if this is a request for a draft document
    if 'fact_drafts' in str(request.url):
        path = FACT_DRAFTS_DIR / name
    elif 'case_drafts' in str(request.url):
        path = CASE_DRAFTS_DIR / name
    else:
        path = UPLOAD_DIR / name
        
    if not path.exists():
        raise web.HTTPNotFound()
    return web.FileResponse(path)

async def handle_evidence_table(request):
    try:
        data = json.loads(EVIDENCE_TABLE_PATH.read_text(encoding="utf-8"))
    except Exception:
        data = {"rows": []}
    return web.json_response(data)
# Intake processor import
try:
    from ...intake_processor import IntakeProcessor
    INTAKE_PROCESSOR_AVAILABLE = True
except Exception:
    INTAKE_PROCESSOR_AVAILABLE = False

async def handle_intake_form(request):
    """Handle intake form submission"""
    try:
        data = await request.json()
        logger.info(f"Received intake form data for session")

        if not INTAKE_PROCESSOR_AVAILABLE:
            return web.json_response({
                "error": "Intake processor not available"
            }, status=503)

        # Process intake form data
        intake_processor = IntakeProcessor()
        intake_data = intake_processor.process_intake_form(data)

        # Convert to facts matrix for downstream processing
        facts_matrix = intake_processor.get_facts_matrix_from_intake(intake_data)

        return web.json_response({
            "session_id": intake_data.session_id,
            "case_name": intake_data.case_name,
            "case_description": intake_data.case_description,
            "jurisdiction": intake_data.jurisdiction,
            "venue": intake_data.venue,
            "court_type": intake_data.court_type,
            "facts_matrix": facts_matrix
        })

    except Exception as e:
        logger.error(f"Error processing intake form: {e}")
        return web.json_response({
            "error": str(e)
        }, status=500)

def create_app():
    if not AIOHTTP_AVAILABLE:
        raise RuntimeError("aiohttp is required for the fallback server but is not installed.")
    app = web.Application()
    
    # Standard upload endpoints
    app.router.add_post("/api/upload", handle_upload)
    app.router.add_post("/api/workflow", handle_start_workflow)
    app.router.add_post("/mcp/search", handle_search)
    app.router.add_get("/mcp/fetch", handle_fetch)
    app.router.add_get("/uploads/{name}", handle_uploaded_file)
    
    # NEW: Draft document upload endpoints
    app.router.add_post("/api/upload-fact-draft", handle_upload_fact_draft)
    app.router.add_post("/api/upload-case-draft", handle_upload_case_draft)
    
    # Static file routes for draft documents
    app.router.add_get("/uploads/fact_drafts/{name}", handle_uploaded_file)
    app.router.add_get("/uploads/case_drafts/{name}", handle_uploaded_file)
    # Intake form endpoint
    app.router.add_post("/api/intake", handle_intake_form)
    
    # Enhanced Evidence API integration
    if EVIDENCE_API_AVAILABLE:
        try:
            # Set up the enhanced evidence API routes
            evidence_api = EvidenceAPI()
            setup_evidence_routes(app, evidence_api)
            logger.info("Enhanced Evidence API routes registered successfully")
        except Exception as e:
            logger.error(f"Failed to setup Enhanced Evidence API: {e}")
            # Fallback to legacy evidence route
            app.router.add_get("/api/evidence", handle_evidence_table)
    else:
        # Fallback to legacy evidence route if new API is not available
        app.router.add_get("/api/evidence", handle_evidence_table)
        logger.warning("Enhanced Evidence API not available, using legacy handler")
    
    logger.info("Draft document processing endpoints registered: /api/upload-fact-draft, /api/upload-case-draft")
    return app


def main():
    # prefer FastMCP if available and you want MCP/TCP features; otherwise run aiohttp
    if FASTMCP_AVAILABLE:
        logger.info("FastMCP available - consider wiring FastMCP tools to the handlers if desired")
        # For now, still run aiohttp for compatibility with frontend
    if not AIOHTTP_AVAILABLE:
        logger.error("aiohttp not available; cannot start HTTP server")
        raise RuntimeError("aiohttp is required to run the fallback server")

    app = create_app()
    runner = web.AppRunner(app)

    async def _run():
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", 8000)
        logger.info("Starting fallback MCP HTTP server on 0.0.0.0:8000")
        await site.start()
        # run forever
        while True:
            await asyncio.sleep(3600)

    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.exception("Server error: %s", e)
        raise

if __name__ == "__main__":
    main()

# Provide a minimal web fallback so static analysis doesn't treat web as None
if not AIOHTTP_AVAILABLE:
    class _WebFallback:
        @staticmethod
        def json_response(*args, **kwargs):
            raise RuntimeError("aiohttp not installed; web.json_response unavailable")
        class FileResponse:
            def __init__(self, *a, **k):
                raise RuntimeError("aiohttp not installed; FileResponse unavailable")
        class HTTPNotFound(Exception):
            pass
        class Application:
            def __init__(self, *a, **k):
                # allow creation but most operations will fail early
                pass
        class AppRunner:
            def __init__(self, *a, **k):
                raise RuntimeError("aiohttp not installed; AppRunner unavailable")
        class TCPSite:
            def __init__(self, *a, **k):
                raise RuntimeError("aiohttp not installed; TCPSite unavailable")
    web = _WebFallback()