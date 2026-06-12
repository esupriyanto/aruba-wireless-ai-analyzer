"""Search endpoint for MAC/IP device lookup with AI-powered troubleshooting."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.dependencies import get_aruba_client, get_hermes_agent
from app.services.aruba_client import ArubaClient
from app.services.hermes_agent import HermesAgent
from app.services.search_service import (
    detect_query_type,
    is_valid_ipv4,
    is_valid_mac,
    normalize_client_response,
    normalize_mac,
)

router = APIRouter(prefix="/search", tags=["Search"])


class SearchQuery(BaseModel):
    """Search query parameter model."""
    query: str


class DeviceInfo(BaseModel):
    """Normalized device information."""
    mac_address: str = ""
    ip_address: str = ""
    hostname: str = ""
    ap_name: str = ""
    ssid: str = ""
    vlan: int = 0
    data_rate_mbps: int = 0
    channel: int = 0
    status: str = "unknown"
    auth_type: str = ""
    band: str = ""
    connection_duration: str | None = None


class MetricsData(BaseModel):
    """Device metrics."""
    rssi: dict[str, Any] = {"current": 0, "trend": [], "unit": "dBm"}
    channel_utilization: int = 0
    noise_floor: int = -95


class AIDiagnosis(BaseModel):
    """AI-powered diagnostic result."""
    health_score: int = 0
    severity: str = "info"
    summary: str = ""
    root_causes: list[str] = []
    recommendations: list[str] = []


class RemediationAction(BaseModel):
    """Available remediation action."""
    action: str
    label: str
    risk: str = "low"


class SearchResponse(BaseModel):
    """Full search response."""
    query: str
    query_type: str
    found: bool = True
    device: DeviceInfo | None = None
    metrics: MetricsData | None = None
    ai_diagnosis: AIDiagnosis | None = None
    remediation_actions: list[RemediationAction] = []


def _compute_connection_duration(uptime: int) -> str | None:
    """Convert uptime seconds to human-readable duration string."""
    if not uptime or uptime <= 0:
        return None
    hours = uptime // 3600
    minutes = (uptime % 3600) // 60
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


def _build_ai_diagnosis(client: dict) -> AIDiagnosis:
    """Build mock AI diagnosis from client data."""
    rssi = float(client.get("rssi_dbm", client.get("rssi", 0)))
    channel_util = int(client.get("channel_utilization", 0))

    # Determine severity based on RSSI and utilization
    if rssi < -80 or channel_util > 80:
        severity = "critical"
        health_score = 35
    elif rssi < -70 or channel_util > 60:
        severity = "warning"
        health_score = 60
    elif rssi < -60 or channel_util > 40:
        severity = "warning"
        health_score = 72
    else:
        severity = "healthy"
        health_score = 92

    root_causes: list[str] = []
    if rssi < -75:
        root_causes.append(
            f"Low RSSI ({rssi} dBm) — device is far from AP or signal obstructed"
        )
    if channel_util > 60:
        ap_name = client.get("ap_name", client.get("ap", "unknown"))
        root_causes.append(
            f"AP {ap_name} channel utilization at {channel_util}% — near congestion"
        )
    if not root_causes:
        root_causes.append("No significant issues detected")

    recommendations: list[str] = []
    if rssi < -75:
        recommendations.append("Move device closer to AP or check for interference sources")
    if channel_util > 60:
        recommendations.append("Enable band steering to distribute clients to less congested channels")
    if not recommendations:
        recommendations.append("No remediation needed — device is healthy")

    severity_label = severity  # healthy, warning, critical
    summary = f"Device health score: {health_score} — {severity_label.upper()}"
    if root_causes:
        summary += f". Issues: {'; '.join(root_causes)}"

    return AIDiagnosis(
        health_score=health_score,
        severity=severity_label,
        summary=summary,
        root_causes=root_causes,
        recommendations=recommendations,
    )


def _build_remediation_actions(client: dict) -> list[RemediationAction]:
    """Build available remediation actions based on device state."""
    actions: list[RemediationAction] = []
    rssi = float(client.get("rssi_dbm", client.get("rssi", 0)))
    channel_util = int(client.get("channel_utilization", 0))

    if rssi < -70:
        actions.append(
            RemediationAction(action="client_roam", label="Force Client Roam", risk="medium")
        )
    if channel_util > 60:
        actions.append(
            RemediationAction(action="band_steering", label="Enable Band Steering", risk="low")
        )
    actions.append(
        RemediationAction(action="diagnose", label="Run Full Diagnosis", risk="low")
    )
    return actions


@router.get("", response_model=SearchResponse)
async def search_device(
    query: str,
    aruba: ArubaClient = Depends(get_aruba_client),
    hermes: HermesAgent = Depends(get_hermes_agent),
) -> SearchResponse:
    """Search for a device by MAC address or IP address and return diagnostic info."""
    query = query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query parameter is required")

    query_type = detect_query_type(query)
    if query_type == "unknown":
        raise HTTPException(
            status_code=400,
            detail="Invalid query format. Please provide a valid MAC address (AA:BB:CC:DD:EE:FF) or IP address (192.168.1.1).",
        )

    # Normalize MAC if needed
    search_key = normalize_mac(query) if query_type == "mac" else query

    # Search in clients list
    resp = await aruba.get_clients(page_size=200)
    client_list = resp.clients if hasattr(resp, "clients") else list(resp)
    found_client = None
    for client in client_list:
        c = client.model_dump() if hasattr(client, "model_dump") else client
        client_mac = c.get("mac", "").lower()
        client_ip = c.get("ip", c.get("ip_address", ""))
        if query_type == "mac" and search_key.lower() == client_mac:
            found_client = c
            break
        elif query_type == "ip" and query.strip() == client_ip:
            found_client = c
            break

    if not found_client:
        # Return empty response with found=False
        return SearchResponse(
            query=query,
            query_type=query_type,
            found=False,
            device=None,
        )

    # Normalize client data
    device_data = normalize_client_response(found_client)

    # Build connection duration
    conn_duration = _compute_connection_duration(device_data.get("uptime", 0))

    # Build device info
    device_info = DeviceInfo(
        mac_address=device_data.get("mac_address", ""),
        ip_address=device_data.get("ip_address", ""),
        hostname=device_data.get("hostname", ""),
        ap_name=device_data.get("ap_name", ""),
        ssid=device_data.get("ssid", ""),
        vlan=device_data.get("vlan", 0),
        data_rate_mbps=int(device_data.get("data_rate_mbps", 0)),
        channel=device_data.get("channel", 0),
        status=device_data.get("status", "connected"),
        auth_type=device_data.get("auth_type", ""),
        band=device_data.get("band", ""),
        connection_duration=conn_duration,
    )

    # Build metrics
    metrics = MetricsData(
        rssi={
            "current": device_data.get("rssi_dbm", 0),
            "trend": [str(device_data.get("rssi_dbm", 0))],
            "unit": "dBm",
        },
        channel_utilization=found_client.get("channel_utilization", 0),
        noise_floor=found_client.get("noise_floor", -95),
    )

    # Build AI diagnosis (mock for now)
    diagnosis = _build_ai_diagnosis(found_client)

    # Build remediation actions
    remediation_actions = _build_remediation_actions(found_client)

    return SearchResponse(
        query=query,
        query_type=query_type,
        found=True,
        device=device_info,
        metrics=metrics,
        ai_diagnosis=diagnosis,
        remediation_actions=remediation_actions,
    )