"""Structured logging middleware for FastAPI."""

import logging
import time
import uuid

from fastapi import Request

logger = logging.getLogger("aruba.request")


async def logging_middleware(request: Request, call_next):
    """Log all requests with structured format including request ID."""
    request_id = str(uuid.uuid4())[:8]
    start = time.monotonic()

    logger.info(
        "[%s] %s %s — started",
        request_id,
        request.method,
        request.url.path,
    )

    response = await call_next(request)

    duration = time.monotonic() - start
    logger.info(
        "[%s] %s %s — %d (%.3fs)",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        duration,
    )

    response.headers["X-Request-ID"] = request_id
    return response
