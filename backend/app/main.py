"""FastAPI application entrypoint."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.middleware.error_handler import error_handler_middleware
from app.middleware.logging import logging_middleware
from app.routers import access_points, audit_log, clients, events, remediation

# Configure structured logging
logging.basicConfig(
    level=getattr(logging, settings.app.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    logger.info("Aruba Wireless AI Analyzer starting (mock_mode=%s)", settings.mock_mode)
    yield
    logger.info("Aruba Wireless AI Analyzer shutting down")


app = FastAPI(
    title="Aruba Wireless AI Analyzer",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow the React dev server (port 3000) during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom middleware
app.middleware("http")(logging_middleware)
app.middleware("http")(error_handler_middleware)

# --- API Routers (Phase 4) ---
app.include_router(clients.router, prefix="/api/v1")
app.include_router(access_points.router, prefix="/api/v1")
app.include_router(events.router, prefix="/api/v1")
app.include_router(remediation.router, prefix="/api/v1")
app.include_router(audit_log.router, prefix="/api/v1")


@app.get("/health")
def health():
    return {"status": "ok", "mock_mode": settings.mock_mode}
