"""Vercel Blob REST API wrapper.

Set BLOB_READ_WRITE_TOKEN to enable cloud storage. When unset the caller falls
back to local-disk storage so local development works without any extra setup.
"""

from __future__ import annotations

import os
import re

import httpx

BLOB_READ_WRITE_TOKEN: str = os.environ.get("BLOB_READ_WRITE_TOKEN", "")
_BLOB_API = "https://blob.vercel-storage.com"


def enabled() -> bool:
    return bool(BLOB_READ_WRITE_TOKEN)


def is_blob_url(path: str | None) -> bool:
    return bool(path and path.startswith("https://"))


def build_pathname(first_name: str, last_name: str, user_id: int, filename: str) -> str:
    """Return a structured blob storage path for a user document."""
    last_initial = (last_name or "X")[0].upper()
    first_initial = (first_name or "X")[0].upper()
    full_name = (
        re.sub(r"[^\w ]", "", f"{first_name} {last_name}".strip()) or f"user_{user_id}"
    )
    safe_file = re.sub(r"[^\w.\-]", "_", filename)
    return f"uploads/{last_initial}/{first_initial}/{full_name}/{user_id}/{safe_file}"


def upload(
    pathname: str, data: bytes, content_type: str = "application/octet-stream"
) -> str:
    """Upload bytes to Vercel Blob. Returns the public URL."""
    resp = httpx.put(
        f"{_BLOB_API}/{pathname}",
        content=data,
        headers={
            "Authorization": f"Bearer {BLOB_READ_WRITE_TOKEN}",
            "Content-Type": content_type,
            "x-api-version": "7",
        },
        timeout=60.0,
    )
    resp.raise_for_status()
    return resp.json()["url"]


def fetch(url: str) -> bytes:
    """Download raw bytes from a Vercel Blob public URL."""
    resp = httpx.get(url, timeout=60.0)
    resp.raise_for_status()
    return resp.content


def delete(url: str) -> None:
    """Delete a blob by URL. Errors are swallowed — this is best-effort."""
    if not enabled():
        return
    try:
        httpx.delete(
            _BLOB_API,
            headers={
                "Authorization": f"Bearer {BLOB_READ_WRITE_TOKEN}",
                "Content-Type": "application/json",
                "x-api-version": "7",
            },
            json={"urls": [url]},
            timeout=30.0,
        )
    except Exception:
        pass
