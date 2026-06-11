from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class ClientStatus(str, Enum):
    """Current connection status of a wireless client."""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ROAMING = "roaming"
    IDLE = "idle"


class ClientInfo(BaseModel):
    """Represents a wireless client connected to an Aruba controller."""
    mac: str
    ip: str
    ssid: str
    ap_name: str
    band: str  # "2.4GHz" or "5GHz"
    channel: int
    rssi_dbm: float
    snr: float
    tx_rate: float  # Mbps
    rx_rate: float  # Mbps
    vlan: int | None = None
    role: str | None = None
    username: str | None = None
    status: ClientStatus = ClientStatus.CONNECTED
    auth_type: str | None = None  # WPA2-Enterprise, Open, etc.
    last_activity: datetime | None = None
    uptime_seconds: int | None = None


class ClientStats(BaseModel):
    """Aggregated statistics for a specific client."""
    mac: str
    avg_rssi_dbm: float
    min_rssi_dbm: float
    max_rssi_dbm: float
    avg_snr: float
    total_tx_bytes: int = 0
    total_rx_bytes: int = 0
    disconnect_count: int = 0
    roaming_count: int = 0
    session_duration_minutes: float = 0.0


class ClientListResponse(BaseModel):
    """Paginated list of wireless clients."""
    total: int
    clients: list[ClientInfo]
    page: int = 1
    page_size: int = 50
