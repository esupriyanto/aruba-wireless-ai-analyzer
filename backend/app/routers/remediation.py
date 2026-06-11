"""Remediation API endpoints (analysis + execution stubs)."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.dependencies import get_analyzer, get_aruba_client, get_hermes_agent
from app.models.issue import AlertListResponse
from app.services.analyzer import Analyzer
from app.services.aruba_client import ArubaClient
from app.services.hermes_agent import HermesAgent

router = APIRouter(prefix="/remediation", tags=["Remediation"])


# ------------------------------------------------------------------
# Request / response schemas
# ------------------------------------------------------------------

class AnalyzeRequest(BaseModel):
    """Body for the analyze endpoint."""
    mac: str | None = None  # Optional: focus on a specific client
    category: str | None = None  # Optional: filter by issue category


class AnalyzeResponse(BaseModel):
    """Response from the analyze endpoint."""
    issues: AlertListResponse
    summary: str
    recommended_next_steps: list[str]


class ExecuteRequest(BaseModel):
    """Body for the execute endpoint."""
    issue_id: str
    action: str  # e.g. "restart_ap", "adjust_power", "kick_client"


class ExecuteResponse(BaseModel):
    """Response from the execute endpoint."""
    status: str
    message: str
    issue_id: str
    action: str


# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------

@router.post("/analyze")
async def analyze(
    body: AnalyzeRequest = AnalyzeRequest(),
    client: ArubaClient = Depends(get_aruba_client),
    analyzer: Analyzer = Depends(get_analyzer),
) -> AnalyzeResponse:
    """Analyze current network state and return issues with recommendations."""
    clients_resp = await client.get_clients()
    aps_resp = await client.get_access_points()

    alerts = analyzer.analyze(
        clients=clients_resp.clients,
        aps=aps_resp.access_points,
    )

    # Build a human-readable summary
    if alerts.total == 0:
        summary = "No issues detected. Network appears healthy."
        next_steps = ["Continue monitoring at regular intervals."]
    else:
        severity_counts: dict[str, int] = {}
        for a in alerts.alerts:
            severity_counts[a.severity.value] = severity_counts.get(a.severity.value, 0) + 1
        parts = [f"{count} {sev}" for sev, count in severity_counts.items()]
        summary = f"Detected {alerts.total} issue(s): {', '.join(parts)}."
        next_steps = [
            "Review critical issues first",
            "Use /api/v1/remediation/execute to apply automated fixes",
            "Monitor affected clients/APs for improvement",
        ]

    return AnalyzeResponse(
        issues=alerts.model_dump(),
        summary=summary,
        recommended_next_steps=next_steps,
    )


@router.post("/execute", response_model=ExecuteResponse)
async def execute(
    body: ExecuteRequest,
    hermes: HermesAgent = Depends(get_hermes_agent),
) -> ExecuteResponse:
    """Execute a remediation action via Hermes AI Agent."""
    allowed_actions = {"restart_ap", "adjust_power", "kick_client", "clear_rogue"}
    if body.action not in allowed_actions:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unknown action '{body.action}'. "
                f"Allowed: {', '.join(sorted(allowed_actions))}"
            ),
        )

    result = await hermes.execute_remediation(
        actions=[body.action],
        target=body.issue_id,
    )

    return ExecuteResponse(
        status=result.get("status", "accepted"),
        message=result.get("message", "Remediation queued."),
        issue_id=body.issue_id,
        action=body.action,
    )
