from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class APStatus(str, Enum):
    """Operational status of an access point."""
    UP = "up"
    DOWN = "down"
    DEGRADED = "degraded"


class AccessPoint(BaseModel):
    """Represents an Aruba access point."""
    name: str
    model: str
    serial: str
    ip_address: str
    status: APStatus = APStatus.UP
    group: str | None = None
    site: str | None = None
    client_count: int = 0
    channel_utilization: float  # percentage 0-100
    tx_power: float  # dBm
    band: str  # "2.4GHz", "5GHz", or "dual-band"
    channel: int | None = None
    frequency_mhz: int | None = None
    uptime_seconds: int | None = None
    firmware_version: str | None = None
    last_reboot: datetime | None = None


class APListResponse(BaseModel):
    """Paginated list of access points."""
    total: int
    access_points: list[AccessPoint]
    page: int = 1
    page_size: int = 50
