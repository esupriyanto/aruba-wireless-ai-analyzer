"""Client-related API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies import get_aruba_client
from app.models.client import ClientInfo, ClientListResponse
from app.models.common import TimeSeriesPoint
from app.services.aruba_client import ArubaClient

router = APIRouter(prefix="/clients", tags=["Clients"])


@router.get("/", response_model=ClientListResponse)
async def list_clients(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    client: ArubaClient = Depends(get_aruba_client),
) -> ClientListResponse:
    """Return a paginated list of wireless clients."""
    return await client.get_clients(page=page, page_size=page_size)


@router.get("/{mac}", response_model=ClientInfo)
async def get_client(
    mac: str,
    client: ArubaClient = Depends(get_aruba_client),
) -> ClientInfo:
    """Return detailed info for a single client by MAC address."""
    info = await client.get_client_detail(mac)
    if info is None:
        raise HTTPException(
            status_code=404,
            detail=f"Client with MAC '{mac}' not found",
        )
    return info


@router.get("/{mac}/rssi", response_model=list[TimeSeriesPoint])
async def get_client_rssi(
    mac: str,
    hours: float = Query(1.0, gt=0, le=24, description="Time window in hours"),
    client: ArubaClient = Depends(get_aruba_client),
) -> list[TimeSeriesPoint]:
    """Return RSSI time-series data for a specific client."""
    # Verify client exists first
    info = await client.get_client_detail(mac)
    if info is None:
        raise HTTPException(
            status_code=404,
            detail=f"Client with MAC '{mac}' not found",
        )
    return await client.get_rssi_timeseries(mac, hours=hours)
