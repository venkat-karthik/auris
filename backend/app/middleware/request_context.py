"""
Auris - Request Context Middleware
Adds request tracking, timing, and structured logging context
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from loguru import logger
import time
import uuid
from datetime import datetime


class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware that:
    1. Generates unique request ID for tracing
    2. Tracks request timing (latency)
    3. Logs request/response details
    4. Attaches context to request.state for downstream use
    """
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # ── Generate request ID ───────────────────────────────────────────────
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        
        # ── Capture start time ────────────────────────────────────────────────
        start_time = time.time()
        request.state.start_time = start_time
        request.state.timestamp = datetime.utcnow().isoformat()
        
        # ── Log request details ───────────────────────────────────────────────
        logger.info(
            f"[{request_id}] → {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query": str(request.query_params),
                "client": request.client.host if request.client else "unknown",
            }
        )
        
        # ── Call next middleware/route ────────────────────────────────────────
        try:
            response = await call_next(request)
        except Exception as e:
            # Log exception with request context
            elapsed = time.time() - start_time
            logger.error(
                f"[{request_id}] ✗ {request.method} {request.url.path} "
                f"(error in {elapsed:.2f}s): {type(e).__name__}",
                extra={
                    "request_id": request_id,
                    "elapsed_ms": elapsed * 1000,
                    "error": str(e),
                }
            )
            raise
        
        # ── Calculate latency ─────────────────────────────────────────────────
        elapsed = time.time() - start_time
        
        # ── Add headers to response ───────────────────────────────────────────
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(elapsed)
        
        # ── Log response details ──────────────────────────────────────────────
        # Determine log level based on status code
        if response.status_code >= 500:
            log_func = logger.error
            symbol = "✗"
        elif response.status_code >= 400:
            log_func = logger.warning
            symbol = "⚠"
        else:
            log_func = logger.info
            symbol = "✓"
        
        log_func(
            f"[{request_id}] {symbol} {request.method} {request.url.path} "
            f"{response.status_code} ({elapsed*1000:.1f}ms)",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "elapsed_ms": elapsed * 1000,
            }
        )
        
        return response
