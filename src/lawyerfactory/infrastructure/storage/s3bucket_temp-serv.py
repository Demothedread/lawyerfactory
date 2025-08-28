# app.py
# FastAPI file uploader → local tmp + S3 object
# Requires: fastapi, uvicorn[standard], boto3, python-multipart

import hashlib
import io
import logging
import mimetypes
import os
from pathlib import Path
import time
from typing import Dict, Optional
import uuid

import boto3
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)</search>
</search_and_replace>

# Import unified storage API
try:
    from lawyerfactory.storage.unified_storage_api import (
        UnifiedStorageAPI,
        get_unified_storage_api,
    )
    UNIFIED_STORAGE_AVAILABLE = True
except ImportError:
    UNIFIED_STORAGE_AVAILABLE = False
    logger.warning("Unified storage API not available, falling back to standalone mode")

# --- Config from environment (already sourced by your venv/bin/activate) ---
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "us-west-2")
S3_BUCKET = os.getenv("S3_BUCKET")  # e.g., "briefcase-case"

if not all([AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, S3_BUCKET]):
    raise RuntimeError("Missing required AWS_* or S3_BUCKET environment variables.")

# Optional: base S3 prefix for organization
S3_PREFIX = os.getenv("S3_PREFIX", "uploads")

# Local temp directory
TMP_DIR = Path(os.getenv("UPLOAD_TMP_DIR", "./uploads/tmp")).resolve()
TMP_DIR.mkdir(parents=True, exist_ok=True)

# Allowed types (loose: accept many, but you asked to focus on pdf/csv/txt)
ALLOWED_EXTS = {
    ".pdf",
    ".csv",
    ".tsv",
    ".txt",
    ".log",
    ".json",
    ".xml",
    ".md",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".doc",
    ".docx",
    ".ppt",
    ".pptx",
    ".xls",
    ".xlsx",
    ".zip",
    ".gz",
    ".tar",
    ".bz2",
}

app = FastAPI(title="Uploader → S3", version="1.0.0")

# Initialize unified storage API
unified_storage = None
if UNIFIED_STORAGE_AVAILABLE:
    try:
        unified_storage = get_unified_storage_api()
        # Register this S3 service as the S3 client
        unified_storage.register_storage_client("s3", S3StorageClient())
        logger.info("Unified storage API initialized and S3 client registered")
    except Exception as e:
        logger.warning(f"Failed to initialize unified storage API: {e}")
        unified_storage = None


def guess_content_type(
    filename: str, fallback: str = "application/octet-stream"
) -> str:
    ctype, _ = mimetypes.guess_type(filename)
    return ctype or fallback


def safe_name(name: str) -> str:
    # Keep it simple: strip path parts and limit characters
    base = Path(name).name
    return (
        "".join(ch for ch in base if ch.isalnum() or ch in ("-", "_", ".", " ")).strip()
        or "file"
    )


def s3_client():
    return boto3.client(
        "s3",
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )


def build_s3_key(object_id: str, filename: str) -> str:
    today = time.strftime("%Y/%m/%d")
    return f"{S3_PREFIX}/{today}/{object_id}/{filename}"


def public_https_url(bucket: str, region: str, key: str) -> str:
    # Standard virtual-hosted–style URL (non-signed)
    # Note: If the object isn’t public, clients will need signed URLs.
    return f"https://{bucket}.s3.{region}.amazonaws.com/{key}"


class S3StorageClient:
    """S3 client wrapper for unified storage API"""

    def __init__(self):
        self.client = s3_client()
        self.bucket = S3_BUCKET
        self.region = AWS_REGION
        self.prefix = S3_PREFIX

    async def store_file(self, file_content: bytes, filename: str, object_id: str) -> Dict[str, Any]:
        """Store file in S3 and return metadata"""
        try:
            # Generate S3 key
            key = build_s3_key(object_id, filename)

            # Upload to S3
            self.client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=io.BytesIO(file_content),
                ContentType=guess_content_type(filename),
                Metadata={
                    "original-name": filename,
                    "object-id": object_id,
                    "sha256": hashlib.sha256(file_content).hexdigest(),
                },
            )

            # Get object metadata
            head = self.client.head_object(Bucket=self.bucket, Key=key)
            etag = head.get("ETag", "").strip('"')

            return {
                "url": public_https_url(self.bucket, self.region, key),
                "key": key,
                "etag": etag,
                "size": len(file_content)
            }

        except Exception as e:
            logger.error(f"S3 storage failed for {object_id}: {e}")
            raise

    async def get_file(self, s3_url: str) -> Optional[bytes]:
        """Retrieve file from S3"""
        try:
            # Extract key from URL
            key = s3_url.split(f"s3://{self.bucket}/")[-1]

            response = self.client.get_object(Bucket=self.bucket, Key=key)
            return response['Body'].read()

        except Exception as e:
            logger.error(f"S3 retrieval failed for {s3_url}: {e}")
            return None


@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    label: Optional[str] = Form(None),
):
    # Validate extension
    ext = Path(file.filename or "").suffix.lower()
    if ext and ext not in ALLOWED_EXTS:
        raise HTTPException(status_code=400, detail=f"File type not allowed: {ext}")

    # Read file content
    try:
        blob = await file.read()
    except Exception:
        raise HTTPException(status_code=400, detail="Failed to read uploaded file.")

    if not blob:
        raise HTTPException(status_code=400, detail="Empty upload.")

    filename = safe_name(file.filename or "upload.bin")

    # Use unified storage API if available
    if unified_storage and UNIFIED_STORAGE_AVAILABLE:
        try:
            # Prepare metadata
            metadata = {
                "label": label,
                "content_type": file.content_type or guess_content_type(filename),
                "sha256": hashlib.sha256(blob).hexdigest(),
                "source": "s3_service_api"
            }

            # Store through unified API
            result = await unified_storage.store_evidence(
                file_content=blob,
                filename=filename,
                metadata=metadata,
                source_phase="intake"
            )

            if result.success:
                # Save tmp file for backward compatibility
                tmp_path = TMP_DIR / f"{result.object_id}-{filename}"
                try:
                    with open(tmp_path, "wb") as f:
                        f.write(blob)
                except Exception:
                    logger.warning(f"Failed to save temp file: {tmp_path}")

                # Return unified response
                return JSONResponse({
                    "status": "ok",
                    "object_id": result.object_id,
                    "bucket": S3_BUCKET,
                    "key": result.s3_url.split(f"s3://{S3_BUCKET}/")[-1] if result.s3_url else None,
                    "size_bytes": len(blob),
                    "sha256": metadata["sha256"],
                    "content_type": metadata["content_type"],
                    "s3_uri": result.s3_url,
                    "https_url": result.s3_url,  # Unified API returns full URL
                    "label": label,
                    "tmp_path": str(tmp_path) if 'tmp_path' in locals() else None,
                    "evidence_id": result.evidence_id,
                    "vector_ids": result.vector_ids,
                    "processing_time": result.processing_time,
                    "unified_storage": True
                })
            else:
                raise HTTPException(status_code=500, detail=f"Unified storage failed: {result.error}")

        except Exception as e:
            logger.error(f"Unified storage failed, falling back to direct S3: {e}")
            # Fall through to direct S3 implementation

    # Fallback to direct S3 implementation (original logic)
    content_type = file.content_type or guess_content_type(filename)
    object_id = uuid.uuid4().hex
    sha256 = hashlib.sha256(blob).hexdigest()
    size_bytes = len(blob)

    # Save tmp file
    tmp_path = TMP_DIR / f"{object_id}-{filename}"
    try:
        with open(tmp_path, "wb") as f:
            f.write(blob)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to write temp file.")

    # Upload to S3 directly
    key = build_s3_key(object_id, filename)
    client = s3_client()
    try:
        client.put_object(
            Bucket=S3_BUCKET,
            Key=key,
            Body=io.BytesIO(blob),
            ContentType=content_type,
            Metadata={
                "original-name": filename,
                "object-id": object_id,
                "sha256": sha256,
                **({"label": label} if label else {}),
            },
        )
        head = client.head_object(Bucket=S3_BUCKET, Key=key)
        etag = head.get("ETag", "").strip('"')
    except Exception as e:
        # Cleanup tmp file on failure
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass
        raise HTTPException(status_code=502, detail=f"S3 upload failed: {e}")

    # Success response (legacy format)
    return JSONResponse({
        "status": "ok",
        "object_id": object_id,
        "bucket": S3_BUCKET,
        "key": key,
        "size_bytes": size_bytes,
        "sha256": sha256,
        "content_type": content_type,
        "etag": etag,
        "s3_uri": f"s3://{S3_BUCKET}/{key}",
        "https_url": public_https_url(S3_BUCKET, AWS_REGION, key),
        "label": label,
        "tmp_path": str(tmp_path),
        "unified_storage": False
    })</search>
</search_and_replace>


# Optional: health
@app.get("/healthz")
def healthz():
    return {"ok": True}
