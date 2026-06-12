"""Global error handler middleware for FastAPI."""

import logging
import traceback
import uuid

from fastapi import Request
from fastapi.responses import JSONResponse
from httpx import ConnectError, TimeoutException

logger = logging.getLogger(__name__)


async def error_handler_middleware(request: Request, call_next):
    """Catch unhandled exceptions and return consistent JSON error responses."""
    request_id = str(uuid.uuid4())[:8]
    try:
        response = await call_next(request)
        return response
    except TimeoutException as exc:
        logger.error("[%s] Timeout: %s", request_id, exc)
        return JSONResponse(
            status_code=504,
            content={
                "error": "Gateway Timeout",
                "detail": str(exc),
                "code": 504,
                "request_id": request_id,
            },
        )
    except ConnectError as exc:
        logger.error("[%s] Connection error: %s", request_id, exc)
        return JSONResponse(
            status_code=503,
            content={
                "error": "Service Unavailable",
                "detail": str(exc),
                "code": 503,
                "request_id": request_id,
            },
        )
    except ValueError as exc:
        logger.error("[%s] Validation error: %s", request_id, exc)
        return JSONResponse(
            status_code=502,
            content={
                "error": "Bad Gateway",
                "detail": str(exc),
                "code": 502,
                "request_id": request_id,
            },
        )
    except Exception as exc:
        logger.error("[%s] Unhandled error: %s\n%s", request_id, exc, traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "detail": str(exc) if __debug__ else "An unexpected error occurred",
                "code": 500,
                "request_id": request_id,
            },
        )
