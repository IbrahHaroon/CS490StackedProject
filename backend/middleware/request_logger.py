import inspect
import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from database.auth import decode_access_token

logger = logging.getLogger("ats")


# Paths used internally by the logging infrastructure itself — skip to avoid noise
_EXCLUDED_PATHS = {"/logs/flush", "/logs/backend"}


def _resolve_handler(request: Request):
    """Extract the handler function name and file from the matched route."""
    route = request.scope.get("route")
    if route and hasattr(route, "endpoint"):
        name = route.endpoint.__name__
        try:
            filepath = inspect.getfile(route.endpoint)
        except (TypeError, OSError):
            filepath = getattr(route.endpoint, "__module__", "unknown")
        return name, filepath
    return "unknown", "unknown"


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs every HTTP request with handler resolution and user identity."""

    async def dispatch(self, request: Request, call_next):
        # Skip logging for the log-infrastructure endpoints
        if request.url.path in _EXCLUDED_PATHS:
            return await call_next(request)

        start_time = time.perf_counter()

        # Extract correlation ID set by the frontend
        request_id = request.headers.get("x-request-id", "none")

        # Best-effort user identity extraction from JWT (no DB hit)
        user_email = None
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            try:
                payload = decode_access_token(token)
                if payload:
                    user_email = payload.get("sub")
            except Exception:
                pass

        # Process the request — route is resolved during call_next
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            # Resolve handler after call_next so the route has been matched
            handler_name, handler_file = _resolve_handler(request)
            logger.error(
                "%s %s -> 500 (%sms) [%s]",
                request.method,
                request.url.path,
                duration_ms,
                handler_name,
                exc_info=True,
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "query_params": str(request.query_params),
                    "handler": handler_name,
                    "handler_file": handler_file,
                    "user_email": user_email,
                    "status_code": 500,
                    "duration_ms": duration_ms,
                },
            )
            raise

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # Resolve handler after call_next so the route has been matched
        handler_name, handler_file = _resolve_handler(request)

        # Echo request ID back for frontend correlation
        response.headers["X-Request-ID"] = request_id

        logger.info(
            "%s %s -> %s (%sms) [%s]",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            handler_name,
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "handler": handler_name,
                "handler_file": handler_file,
                "user_email": user_email,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )

        return response
