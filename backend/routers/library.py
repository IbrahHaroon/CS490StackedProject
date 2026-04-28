"""Document library upload workflow.

Provides a validated file-upload endpoint that enforces:
- Extension allow-list: .pdf, .docx, .txt, .md
- 10 MB per-file size cap (enforced before writing to disk)
- Filename sanitisation (path-traversal prevention, null-byte stripping)
- Structured JSON logging via the shared "ats" logger

Storage and DB patterns are identical to the existing /documents/upload endpoint:
files land in backend/uploads/<LastInitial>/<FirstInitial>/<Full Name>/<user_id>/
and a Documents row is created via create_document().
"""

import logging
import os
import re

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from utils import blob_storage

from database import get_db
from database.auth import get_current_user
from database.models.document import create_document, get_document, update_document
from database.models.document_tag import add_tag
from database.models.document_version import create_document_version
from database.models.profile import get_profile_by_user_id
from database.models.user import User
from schemas import DocumentResponse

router = APIRouter()
logger = logging.getLogger("ats")

# ── Constants ─────────────────────────────────────────────────────────────────

_MAX_FILE_BYTES: int = 10 * 1024 * 1024  # 10 MB

_ALLOWED_EXTENSIONS: frozenset[str] = frozenset({".pdf", ".docx", ".txt", ".md"})

# ── Storage path helpers ──────────────────────────────────────────────────────

_ROUTERS_DIR = os.path.dirname(os.path.abspath(__file__))
_BACKEND_DIR = os.path.dirname(_ROUTERS_DIR)
_UPLOAD_BASE = os.path.join(_BACKEND_DIR, "uploads")


def _sanitize_filename(raw: str) -> str:
    """Return a filesystem-safe filename derived from the client-supplied name.

    Strips directory components, ASCII control characters (including null bytes),
    redundant dots, and leading dots so the result cannot escape the upload
    directory or create hidden files on Unix.
    """
    # Drop any path prefix the client may have injected (e.g. "../../etc/passwd")
    name = os.path.basename(raw)
    # Strip null bytes and ASCII control characters (0x00-0x1F)
    name = re.sub(r"[\x00-\x1f]", "", name)
    # Collapse sequences of two or more dots (path-traversal remnants)
    name = re.sub(r"\.{2,}", ".", name)
    # Remove leading dots to prevent hidden-file creation on Unix
    name = name.lstrip(".")
    return name or "upload"


def _build_upload_path(
    first_name: str, last_name: str, user_id: int, filename: str
) -> str:
    """Return the absolute path where the file should be stored.

    Layout mirrors /documents/upload:
        uploads/<LastInitial>/<FirstInitial>/<First Last>/<user_id>/<filename>
    """
    return os.path.join(
        _UPLOAD_BASE,
        last_name[0].upper(),
        first_name[0].upper(),
        f"{first_name} {last_name}",
        str(user_id),
        filename,
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.get(
    "/supported-types",
    summary="List supported document file types",
)
def get_supported_types() -> dict:
    """Return the file extensions and size limit accepted by POST /library/upload."""
    return {
        "extensions": sorted(_ALLOWED_EXTENSIONS),
        "max_size_mb": _MAX_FILE_BYTES // (1024 * 1024),
    }


@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a validated document to the library",
)
async def upload_library_document(
    file: UploadFile = File(...),
    document_type: str = Form(...),
    tags: str | None = Form(default=None),
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentResponse:
    """Accept, validate, persist, and record a document file upload.

    Validation order (fails fast):
    1. Filename present
    2. Extension in allow-list
    3. File non-empty and within the 10 MB cap
    4. User profile exists (required to build the storage path)
    """
    # ── 1. Require a non-empty filename ───────────────────────────────────────
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must have a filename.",
        )

    safe_name = _sanitize_filename(file.filename)
    ext = os.path.splitext(safe_name)[1].lower()

    # ── 2. Extension allow-list ───────────────────────────────────────────────
    if ext not in _ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                f"File type '{ext or '(none)'}' is not supported. "
                f"Allowed types: {', '.join(sorted(_ALLOWED_EXTENSIONS))}"
            ),
        )

    # ── 3. Read into memory and enforce size / empty constraints ──────────────
    contents = await file.read()

    if len(contents) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    if len(contents) > _MAX_FILE_BYTES:
        size_mb = len(contents) / (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                f"File size {size_mb:.1f} MB exceeds the 10 MB limit. "
                "Please upload a smaller file."
            ),
        )

    # ── 4. Require a user profile to build the storage path ───────────────────
    profile = get_profile_by_user_id(session, current_user.user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User profile not found — create a profile before uploading documents.",
        )

    # ── 5. Persist to Vercel Blob (cloud) or local disk ──────────────────────
    _MIME = {
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".txt": "text/plain",
        ".md": "text/markdown",
    }
    if blob_storage.enabled():
        pathname = blob_storage.build_pathname(
            profile.first_name, profile.last_name, current_user.user_id, safe_name
        )
        try:
            dest_path = blob_storage.upload(
                pathname, contents, _MIME.get(ext, "application/octet-stream")
            )
        except Exception as exc:
            logger.error(
                "Library upload: failed to upload to blob storage",
                extra={"user_id": current_user.user_id, "upload_filename": safe_name},
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Could not save the uploaded file: {exc}",
            )
    else:
        dest_path = _build_upload_path(
            profile.first_name, profile.last_name, current_user.user_id, safe_name
        )
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        try:
            with open(dest_path, "wb") as fh:
                fh.write(contents)
        except OSError:
            logger.error(
                "Library upload: failed to write file to disk",
                extra={"user_id": current_user.user_id, "upload_filename": safe_name},
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not save the uploaded file. Please try again.",
            )

    # ── 6. Create the v2 document + initial version + tags ───────────────────
    document = create_document(
        session,
        current_user.user_id,
        title=safe_name,
        document_type=document_type,
    )
    version = create_document_version(
        session,
        document.document_id,
        storage_location=dest_path,
        source="upload",
    )
    update_document(
        session, document.document_id, current_version_id=version.version_id
    )
    if tags:
        for raw in tags.split(","):
            label = raw.strip()
            if label:
                add_tag(session, document.document_id, label)
    document = get_document(session, document.document_id)

    logger.info(
        "Library upload: document stored",
        extra={
            "user_id": current_user.user_id,
            "document_id": document.document_id,
            "upload_filename": safe_name,
            "size_bytes": len(contents),
            "document_type": document_type,
        },
    )

    return document
