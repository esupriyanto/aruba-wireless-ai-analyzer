"""FastAPI application entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import access_points, clients, events, remediation


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    # --- startup ---
    yield
    # --- shutdown ---


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

# --- API Routers (Phase 4) ---
app.include_router(clients.router, prefix="/api/v1")
app.include_router(access_points.router, prefix="/api/v1")
app.include_router(events.router, prefix="/api/v1")
app.include_router(remediation.router, prefix="/api/v1")


@app.get("/health")
def health():
    return {"status": "ok", "mock_mode": settings.mock_mode}
