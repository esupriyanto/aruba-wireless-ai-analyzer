"""Audit log API endpoints."""

from fastapi import APIRouter

from app.services.audit_log import get_audit_log

router = APIRouter(prefix="/audit", tags=["Audit Log"])


@router.get("/")
async def list_audit_log(limit: int = 100):
    """Return recent remediation audit log entries."""
    return {"entries": get_audit_log(limit=limit), "total": 0}
