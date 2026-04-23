"""
Centralized FastAPI exception handlers.

Extends the existing RequestLoggingMiddleware by capturing errors that
FastAPI handles before they reach the middleware's try/except block —
specifically HTTPException and RequestValidationError, which were previously
processed silently by FastAPI's built-in ExceptionMiddleware with no
structured log output.

All three handlers:
  1. Log through the existing 'ats' structured JSON logger.
  2. Return a normalized response that keeps the `detail` field intact
     (backward-compatible with all frontend consumers reading `errBody.detail`)
     and adds `error_code`, `request_id`, and `timestamp` as extra fields.

Register by calling register_exception_handlers(app) in index.py.
"""

import logging
from datetime import datetime, timezone

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger("ats")

# HTTP status code → machine-readable error classification string
_STATUS_TO_CODE = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    410: "GONE",
    422: "UNPROCESSABLE",
    429: "RATE_LIMITED",
    500: "INTERNAL_ERROR",
    502: "BAD_GATEWAY",
    503: "SERVICE_UNAVAILABLE",
}


def _get_request_id(request: Request) -> str:
    return request.headers.get("x-request-id", "none")


def _log_extra(request: Request, status_code: int) -> dict:
    """Build the extra dict that JSONFormatter / RequestLoggingMiddleware expect."""
    return {
        "request_id": _get_request_id(request),
        "method": request.method,
        "path": request.url.path,
        "query_params": str(request.query_params),
        "status_code": status_code,
    }


def _humanize_validation_errors(errors: list) -> str:
    """Convert Pydantic error dicts into a single readable summary string.

    Example input:  [{"loc": ("body", "title"), "msg": "Field required", ...}]
    Example output: "title: Field required"
    """
    parts = []
    for e in errors:
        loc = e.get("loc", ())
        # Drop transport-layer prefixes ("body", "query", "path", "header")
        field_parts = [
            str(p) for p in loc if p not in ("body", "query", "path", "header")
        ]
        field = ".".join(field_parts) if field_parts else "input"
        msg = e.get("msg", "invalid value")
        parts.append(f"{field}: {msg}")
    return "; ".join(parts) if parts else "Request validation failed"


def _error_body(detail, error_code: str, request_id: str) -> dict:
    """
    Backward-compatible error response body.

    Keeps `detail` at the top level so existing frontend code continues to work,
    and adds `error_code`, `request_id`, and `timestamp` as new fields.
    """
    return {
        "detail": detail,
        "error_code": error_code,
        "request_id": request_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic / FastAPI request body and query-param validation failures."""
    request_id = _get_request_id(request)
    error_count = len(exc.errors())
    logger.warning(
        "Validation error on %s %s — %d field(s) invalid [%s]",
        request.method,
        request.url.path,
        error_count,
        request_id,
        extra=_log_extra(request, 422),
    )
    return JSONResponse(
        status_code=422,
        content={
            **_error_body(exc.errors(), "VALIDATION_ERROR", request_id),
            "message": _humanize_validation_errors(exc.errors()),
        },
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle explicit HTTPException raises from route handlers."""
    request_id = _get_request_id(request)
    error_code = _STATUS_TO_CODE.get(exc.status_code, "HTTP_ERROR")
    # Client errors (4xx) are expected operational events → WARNING.
    # Server errors (5xx) indicate a problem → ERROR.
    log_fn = logger.error if exc.status_code >= 500 else logger.warning
    log_fn(
        "HTTP %s on %s %s — %s [%s]",
        exc.status_code,
        request.method,
        request.url.path,
        exc.detail,
        request_id,
        extra=_log_extra(request, exc.status_code),
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_body(exc.detail, error_code, request_id),
        headers=getattr(exc, "headers", None),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all for any exception not handled by a more specific handler.

    Returns a safe 500 response without exposing internal error details,
    and logs the full traceback for debugging.
    """
    request_id = _get_request_id(request)
    logger.error(
        "Unhandled exception on %s %s [%s]",
        request.method,
        request.url.path,
        request_id,
        exc_info=True,
        extra=_log_extra(request, 500),
    )
    return JSONResponse(
        status_code=500,
        content=_error_body(
            "An unexpected error occurred. Please try again later.",
            "INTERNAL_ERROR",
            request_id,
        ),
    )


def register_exception_handlers(app) -> None:
    """Register all centralized exception handlers onto the FastAPI app instance.

    Call this after the app is created but before adding middleware, so that
    FastAPI's ExceptionMiddleware sees the handlers in the right order.
    """
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
