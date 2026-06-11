"""FastAPI dependency injection helpers.

Provides get_settings(), get_aruba_client(), and get_analyzer() for use
with FastAPI's ``Depends()`` mechanism.
"""

from typing import AsyncGenerator

from app.config import settings, Settings
from app.services.analyzer import Analyzer
from app.services.aruba_client import ArubaClient
from app.services.hermes_agent import HermesAgent


def get_settings() -> Settings:
    """Return the global application settings singleton."""
    return settings


async def get_aruba_client() -> AsyncGenerator[ArubaClient, None]:
    """Create and yield an ArubaClient, ensuring proper lifecycle cleanup."""
    client = ArubaClient()
    await client.connect()
    try:
        yield client
    finally:
        await client.close()


def get_analyzer() -> Analyzer:
    """Return a fresh Analyzer instance (stateless, safe to create per-request)."""
    return Analyzer()


def get_hermes_agent() -> HermesAgent:
    """Return a fresh HermesAgent instance."""
    return HermesAgent()
