"""Local object storage service (Phase 2 AI file uploads).

Emulates the object storage described in the design (Supabase/S3) using the
local filesystem so the platform runs with zero external dependencies. Returns
``storage://`` URIs that the OCR engine can resolve back to local paths.
"""
from __future__ import annotations

import os
import uuid
from pathlib import Path

def _root() -> Path:
    root = Path(os.getenv("STORAGE_ROOT", "./storage")).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def save_bytes(data: bytes, filename: str, bucket: str = "ai-submissions") -> str:
    """Persist raw bytes and return a ``storage://bucket/key`` URI."""
    bucket_dir = _root() / bucket
    bucket_dir.mkdir(parents=True, exist_ok=True)
    ext = Path(filename).suffix or ".bin"
    key = f"{uuid.uuid4().hex}{ext}"
    (bucket_dir / key).write_bytes(data)
    return f"storage://{bucket}/{key}"


def resolve_path(uri: str) -> Path | None:
    """Resolve a ``storage://bucket/key`` URI to a local filesystem path."""
    if not uri.startswith("storage://"):
        return None
    rel = uri[len("storage://"):]
    path = (_root() / rel).resolve()
    # Guard against path traversal outside the storage root.
    if _root() not in path.parents and path != _root():
        return None
    return path
