import json
import logging
import os
import shutil
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from typing import List

from fastapi import APIRouter, Query
from pydantic import BaseModel

router = APIRouter()

# Set up a dedicated file logger for frontend logs
_logs_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs"
)
os.makedirs(_logs_dir, exist_ok=True)

_frontend_logger = logging.getLogger("ats.frontend")
_frontend_logger.setLevel(logging.INFO)
_frontend_logger.propagate = False

_file_handler = RotatingFileHandler(
    os.path.join(_logs_dir, "frontend.log"),
    maxBytes=5 * 1024 * 1024,  # 5 MB per file
    backupCount=5,
)
# Raw formatter — the log message is already JSON, just emit it as-is
_file_handler.setFormatter(logging.Formatter("%(message)s"))
_frontend_logger.addHandler(_file_handler)


class FrontendLogEntry(BaseModel):
    requestId: str | None = None
    method: str | None = None
    url: str | None = None
    path: str | None = None
    caller: str | None = None
    action: str | None = None
    timestamp: str | None = None
    status: int | None = None
    durationMs: int | None = None
    error: str | None = None
    stack: str | None = None
    # Action log fields
    type: str | None = None
    component: str | None = None
    element: str | None = None
    page: str | None = None


class FrontendLogBatch(BaseModel):
    logs: List[FrontendLogEntry]


@router.post("/flush", status_code=204)
def flush_frontend_logs(batch: FrontendLogBatch):
    """Receive a batch of frontend logs and persist them to logs/frontend.log."""
    received_at = datetime.now(timezone.utc).isoformat()
    for entry in batch.logs:
        record = entry.model_dump(exclude_none=True)
        record["received_at"] = received_at
        _frontend_logger.info(json.dumps(record))


@router.get("/backend")
def get_backend_logs(tail: int = 100, after: str = Query(default=None)):
    """Return the most recent backend log entries as a JSON array.

    If ``after`` is provided (ISO timestamp), only entries with a timestamp
    strictly greater than that value are returned.  This lets the frontend
    "clear" the view without touching the log file.
    """
    log_path = os.path.join(_logs_dir, "backend.log")
    if not os.path.exists(log_path):
        return []

    lines = []
    try:
        with open(log_path, "rb") as f:
            f.seek(0, 2)
            file_size = f.tell()
            if file_size == 0:
                return []
            # Read up to 512KB from the end (enough for ~100 JSON lines)
            read_size = min(file_size, 512 * 1024)
            f.seek(file_size - read_size)
            content = f.read().decode("utf-8", errors="replace")
            raw_lines = content.strip().split("\n")
            raw_lines = raw_lines[-tail:]
            for line in raw_lines:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                # Filter by timestamp when `after` is supplied
                if after and entry.get("timestamp", "") <= after:
                    continue
                lines.append(entry)
    except OSError:
        return []

    return lines


@router.post("/backend/clear", status_code=200)
def clear_backend_logs():
    """Archive the current backend.log and start fresh.

    The existing file is moved to ``logs/backend.log.archived.<timestamp>``.
    A new empty ``backend.log`` is created so the file handler keeps working.
    Returns the current UTC timestamp so the frontend can filter any stragglers.
    """
    log_path = os.path.join(_logs_dir, "backend.log")
    now = datetime.now(timezone.utc)
    cleared_at = now.isoformat()

    if os.path.exists(log_path) and os.path.getsize(log_path) > 0:
        archive_name = f"backend.log.archived.{now.strftime('%Y%m%dT%H%M%SZ')}"
        archive_path = os.path.join(_logs_dir, archive_name)
        try:
            shutil.copy2(log_path, archive_path)
            # Truncate the live log file instead of removing it —
            # the RotatingFileHandler still holds the open fd.
            with open(log_path, "w") as f:
                f.truncate(0)
        except OSError:
            pass

    return {"cleared_at": cleared_at}
