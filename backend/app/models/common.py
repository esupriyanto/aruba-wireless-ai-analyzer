from datetime import datetime
from pydantic import BaseModel


class TimeSeriesPoint(BaseModel):
    """A single data point in a time series (e.g., RSSI over time)."""
    timestamp: datetime
    value: float
    label: str | None = None
