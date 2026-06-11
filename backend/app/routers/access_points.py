"""Access-point API endpoints."""

from fastapi import APIRouter, Depends, Query

from app.dependencies import get_aruba_client
from app.models.ap import APListResponse
from app.services.aruba_client import ArubaClient

router = APIRouter(prefix="/access-points", tags=["Access Points"])


@router.get("/", response_model=APListResponse)
async def list_access_points(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    client: ArubaClient = Depends(get_aruba_client),
) -> APListResponse:
    """Return a paginated list of access points."""
    return await client.get_access_points(page=page, page_size=page_size)
