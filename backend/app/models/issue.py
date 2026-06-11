from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class IssueSeverity(str, Enum):
    """Severity level for detected issues."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class IssueCategory(str, Enum):
    """Category of a wireless issue."""
    LOW_RSSI = "low_rssi"
    HIGH_CHANNEL_UTILIZATION = "high_channel_utilization"
    CLIENT_DISCONNECT = "client_disconnect"
    ROAMING_ISSUE = "roaming_issue"
    AUTH_FAILURE = "auth_failure"
    CAPACITY = "capacity"
    INTERFERENCE = "interference"
    GENERAL = "general"


class Issue(BaseModel):
    """A detected wireless issue or alert."""
    id: str
    severity: IssueSeverity
    category: IssueCategory
    title: str
    description: str
    affected_clients: list[str] = []  # MAC addresses
    affected_aps: list[str] = []  # AP names
    timestamp: datetime
    resolved: bool = False
    ai_analysis: str | None = None
    recommended_actions: list[str] = []
    controller_name: str | None = None


class AlertListResponse(BaseModel):
    """Paginated list of issues/alerts."""
    total: int
    alerts: list[Issue]
    page: int = 1
    page_size: int = 50
