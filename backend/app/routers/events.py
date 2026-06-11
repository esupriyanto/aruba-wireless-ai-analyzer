"""Events and alert API endpoints."""

from fastapi import APIRouter, Depends, Query

from app.dependencies import get_analyzer, get_aruba_client
from app.models.issue import AlertListResponse
from app.services.analyzer import Analyzer
from app.services.aruba_client import ArubaClient

router = APIRouter(prefix="/events", tags=["Events"])


@router.get("/")
async def list_events(
    limit: int = Query(100, ge=1, le=1000, description="Max events to return"),
    client: ArubaClient = Depends(get_aruba_client),
) -> list[dict]:
    """Return recent controller events."""
    return await client.get_events(limit=limit)


@router.get("/alerts", response_model=AlertListResponse)
async def list_alerts(
    client: ArubaClient = Depends(get_aruba_client),
    analyzer: Analyzer = Depends(get_analyzer),
) -> AlertListResponse:
    """Run the analyzer against current clients/APs and return detected issues."""
    clients_resp = await client.get_clients()
    aps_resp = await client.get_access_points()

    return analyzer.analyze(
        clients=clients_resp.clients,
        aps=aps_resp.access_points,
    )
