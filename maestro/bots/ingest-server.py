"""
Sample MCP Server for ChatGPT Integration

This server implements the Model Context Protocol (MCP) with search and fetch
capabilities designed to work with ChatGPT's chat and deep research features.
"""

import logging
import os
import json
import asyncio
from typing import Dict, List, Any
from pathlib import Path

# Try to import optional SDKs; fall back gracefully
try:
    from fastmcp import FastMCP  # optional; not required for fallback
    FASTMCP_AVAILABLE = True
except Exception:
    FastMCP = None
    FASTMCP_AVAILABLE = False

try:
    from openai import OpenAI  # optional; used only if available and API key present
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
    from assessor import intake_document, summarize, categorize, hashtags_from_category
    ASSESSOR_AVAILABLE = True
except Exception:
    ASSESSOR_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OpenAI configuration (optional)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
VECTOR_STORE_ID = os.environ.get("VECTOR_STORE_ID", "")

# Optional OpenAI client initialization
openai_client = None
if OPENAI_SDK_AVAILABLE and OPENAI_API_KEY:
    try:
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        logger.info("OpenAI SDK initialized")
    except Exception as e:
        logger.warning("OpenAI SDK could not be initialized: %s", e)
        openai_client = None

# Local storage paths
BASE_DIR = Path.cwd()
UPLOAD_DIR = BASE_DIR / "uploads"
INDEX_PATH = BASE_DIR / "vector_backup.json"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

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

    async def get_file(self, file_id: str) -> Dict[str, Any]:
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
        "stored_in_repository": stored
    })


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
    path = UPLOAD_DIR / name
    if not path.exists():
        raise web.HTTPNotFound()
    return web.FileResponse(path)


def create_app():
    if not AIOHTTP_AVAILABLE:
        raise RuntimeError("aiohttp is required for the fallback server but is not installed.")
    app = web.Application()
    app.router.add_post("/api/upload", handle_upload)
    app.router.add_post("/api/workflow", handle_start_workflow)
    app.router.add_post("/mcp/search", handle_search)
    app.router.add_get("/mcp/fetch", handle_fetch)
    app.router.add_get("/uploads/{name}", handle_uploaded_file)
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