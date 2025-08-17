#storage
# .py
# A function-first mini file service:
# - ingest_file(file_input, filename, ...)  -> uploads to S3 + indexes in Qdrant
# - optional FastAPI routes call the same function under the hood
#
# Dependencies:
#   pip install boto3 qdrant-client sentence-transformers python-dotenv pypdf fastapi uvicorn
#
# Env (.env):
#   AWS_ACCESS_KEY_ID=...
#   AWS_SECRET_ACCESS_KEY=...
#   AWS_REGION=us-east-1
#   S3_BUCKET=your-bucket
#   QDRANT_HOST=localhost
#   QDRANT_PORT=6333
#   QDRANT_COLLECTION=files

import os
import io
import re
import mimetypes
from uuid import uuid4
from pathlib import Path
from typing import Any, Dict, Optional, Union, List

import boto3
from dotenv import load_dotenv

from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance, Filter, FieldCondition, MatchValue

from sentence_transformers import SentenceTransformer

try:
    # optional, used to extract text from PDFs for better embeddings
    from pypdf import PdfReader
except Exception:
    PdfReader = None  # graceful fallback

# ---------- Load environment ----------
load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
S3_BUCKET = os.getenv("S3_BUCKET")

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "files")

# ---------- Initialize clients ----------
s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION,
)

qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

_embedder_singleton: Optional[SentenceTransformer] = None
def _embedder() -> SentenceTransformer:
    global _embedder_singleton
    if _embedder_singleton is None:
        _embedder_singleton = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedder_singleton

def _ensure_collection(vector_size: int) -> None:
    # Create if missing; do NOT wipe on restart.
    try:
        qdrant.get_collection(QDRANT_COLLECTION)  # will raise if not exists
    except Exception:
        qdrant.create_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )

# ---------- Utilities ----------
def _safe_filename(name: str) -> str:
    # keep base name, strip path, normalize problematic chars
    base = Path(name).name
    base = re.sub(r"[^\w.\- ]+", "_", base)
    return base or f"file-{uuid4()}"

def _to_bytesio(file_input: Union[str, bytes, bytearray, io.BytesIO, Any]) -> io.BytesIO:
    if isinstance(file_input, (bytes, bytearray)):
        return io.BytesIO(file_input)
    if isinstance(file_input, str):
        with open(file_input, "rb") as f:
            return io.BytesIO(f.read())
    if hasattr(file_input, "read"):  # file-like
        data = file_input.read()
        return io.BytesIO(data)
    raise TypeError("file_input must be path str, bytes, bytearray, or file-like object")

def _guess_content_type(filename: str) -> str:
    ctype, _ = mimetypes.guess_type(filename)
    return ctype or "application/octet-stream"

def _extract_text_for_embedding(buf: bytes, filename: str, max_chars: int = 12000) -> str:
    ext = Path(filename).suffix.lower()
    if ext in {".txt", ".md", ".csv", ".log", ".json"}:
        try:
            text = buf.decode("utf-8", errors="ignore")
            return text[:max_chars]
        except Exception:
            return Path(filename).stem
    if ext == ".pdf" and PdfReader:
        try:
            reader = PdfReader(io.BytesIO(buf))
            parts = []
            for page in reader.pages[:50]:  # cap pages for speed
                try:
                    parts.append(page.extract_text() or "")
                except Exception:
                    continue
            text = "\n".join(parts)
            return (text[:max_chars] if text else Path(filename).stem)
        except Exception:
            return Path(filename).stem
    # Fallback: just use filename if we can't parse content
    return Path(filename).stem

# ---------- Core function ----------
def ingest_file(
    file_input: Union[str, bytes, bytearray, io.BytesIO, Any],
    filename: str,
    *,
    s3_bucket: Optional[str] = None,
    s3_prefix: str = "",
    private: bool = True,
    user_payload: Optional[Dict[str, Any]] = None,
    presign_expires_in: int = 900,
) -> Dict[str, Any]:
    """
    Upload a file to S3 and index metadata + embedding in Qdrant.
    Returns dict with S3 key, presigned GET URL, and Qdrant point id.

    Args:
      file_input: path/bytes/file-like
      filename: original filename for key/display
      s3_bucket: override bucket (default env S3_BUCKET)
      s3_prefix: optional "folder/" prefix for S3 keys
      private: if True, object ACL=private; presigned URL returned for fetch
      user_payload: dict merged into Qdrant payload (e.g., owner_id, tags)
      presign_expires_in: seconds for the GET presigned URL
    """
    bucket = s3_bucket or S3_BUCKET
    if not bucket:
        raise RuntimeError("S3 bucket not configured. Set S3_BUCKET or pass s3_bucket.")

    b = _to_bytesio(file_input)
    data = b.getvalue()  # keep for both upload & embedding

    safe_name = _safe_filename(filename)
    key = f"{s3_prefix}{uuid4()}-{safe_name}" if s3_prefix else f"{uuid4()}-{safe_name}"
    content_type = _guess_content_type(safe_name)

    # Upload to S3
    b.seek(0)
    extra_args = {"ContentType": content_type}
    if private:
        extra_args["ACL"] = "private"
    else:
        extra_args["ACL"] = "public-read"

    s3_client.upload_fileobj(b, bucket, key, ExtraArgs=extra_args)

    # Prepare embedding
    text = _extract_text_for_embedding(data, safe_name)
    model = _embedder()
    vector = model.encode(text).tolist()
    _ensure_collection(model.get_sentence_embedding_dimension())

    # Upsert in Qdrant
    point_id = str(uuid4())
    payload = {
        "file_key": key,
        "filename": safe_name,
        "content_type": content_type,
        "size_bytes": len(data),
        "public": (not private),
    }
    if user_payload:
        payload.update(user_payload)

    qdrant.upsert(
        collection_name=QDRANT_COLLECTION,
        points=[PointStruct(id=point_id, vector=vector, payload=payload)],
    )

    # Fetch URL
    if private:
        url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=presign_expires_in,
        )
    else:
        url = f"https://{bucket}.s3.{AWS_REGION}.amazonaws.com/{key}"

    return {
        "message": "Ingested to S3 and Qdrant",
        "s3_bucket": bucket,
        "s3_key": key,
        "download_url": url,
        "qdrant_point_id": point_id,
        "payload": payload,
    }

# ---------- Helper: semantic search ----------
def semantic_search(query: str, limit: int = 5, filter_payload: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    model = _embedder()
    vector = model.encode(query).tolist()
    _ensure_collection(model.get_sentence_embedding_dimension())

    q_filter = None
    if filter_payload:
        # simple AND filter over exact matches
        conditions = []
        for k, v in filter_payload.items():
            conditions.append(FieldCondition(key=k, match=MatchValue(value=v)))
        q_filter = Filter(must=conditions)

    hits = qdrant.search(
        collection_name=QDRANT_COLLECTION,
        query_vector=vector,
        limit=limit,
        query_filter=q_filter,
    )
    return [
        {
            "score": h.score,
            "file_key": h.payload.get("file_key"),
            "filename": h.payload.get("filename"),
            "content_type": h.payload.get("content_type"),
            "size_bytes": h.payload.get("size_bytes"),
            "public": h.payload.get("public"),
            "payload": h.payload,
        }
        for h in hits
    ]

# ---------- OPTIONAL: FastAPI wrapper (uses the same function) ----------
if os.getenv("ENABLE_API", "1") == "1":
    from fastapi import FastAPI, File, UploadFile, HTTPException, Query
    from fastapi.responses import JSONResponse

    app = FastAPI(title="Mini File Service + Qdrant", version="1.0")

    @app.post("/upload/")
    async def upload_route(file: UploadFile = File(...), private: bool = True):
        try:
            return ingest_file(
                file_input=await file.read(),
                filename=file.filename,
                private=private,
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/download/")
    def download_route(file_key: str = Query(...), expires_in: int = 600):
        try:
            url = s3_client.generate_presigned_url(
                "get_object", Params={"Bucket": S3_BUCKET, "Key": file_key}, ExpiresIn=expires_in
            )
            return {"file_key": file_key, "download_url": url}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/list/")
    def list_route(limit: int = 20):
        try:
            resp = s3_client.list_objects_v2(Bucket=S3_BUCKET, MaxKeys=limit)
            items = []
            for obj in resp.get("Contents", []):
                items.append({
                    "key": obj["Key"],
                    "size": obj["Size"],
                    "last_modified": obj["LastModified"].isoformat(),
                })
            return {"files": items}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.delete("/delete/")
    def delete_route(file_key: str = Query(...)):
        try:
            s3_client.delete_object(Bucket=S3_BUCKET, Key=file_key)
            # also remove from Qdrant if present
            try:
                qdrant.delete(
                    collection_name=QDRANT_COLLECTION,
                    points_selector=Filter(must=[FieldCondition(key="file_key", match=MatchValue(value=file_key))])
                )
            except Exception:
                pass
            return {"message": f"Deleted {file_key}"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/search/")
    def search_route(query: str, limit: int = 5):
        try:
            return {"query": query, "results": semantic_search(query, limit=limit)}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

# ---------- OPTIONAL: CLI usage ----------
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Ingest a file into S3 + Qdrant")
    parser.add_argument("path", help="Path to file")
    parser.add_argument("--private", action="store_true", default=True, help="Keep S3 object private (default)")
    parser.add_argument("--public", dest="private", action="store_false", help="Make S3 object public-read")
    parser.add_argument("--prefix", default="", help='S3 key prefix, e.g., "uploads/2025/"')
    parser.add_argument("--owner", default=None, help="Optional owner id to store in payload")
    args = parser.parse_args()

    payload = {"owner": args.owner} if args.owner else None
    res = ingest_file(args.path, Path(args.path).name, s3_prefix=args.prefix, private=args.private, user_payload=payload)
    print(res)
