"""Tests for all Pydantic data models."""

from datetime import datetime

from app.models.common import TimeSeriesPoint
from app.models.client import ClientInfo, ClientStats, ClientListResponse, ClientStatus
from app.models.ap import AccessPoint, APListResponse, APStatus
from app.models.issue import Issue, IssueSeverity, IssueCategory, AlertListResponse


class TestTimeSeriesPoint:
    def test_construct_from_dict(self):
        data = {
            "timestamp": "2026-01-15T10:30:00",
            "value": -52.3,
            "label": "rssi_dbm",
        }
        point = TimeSeriesPoint(**data)
        assert point.value == -52.3
        assert point.label == "rssi_dbm"
        assert isinstance(point.timestamp, datetime)

    def test_optional_label(self):
        data = {"timestamp": "2026-01-15T10:30:00", "value": 10.5}
        point = TimeSeriesPoint(**data)
        assert point.label is None


class TestClientInfo:
    def test_construct_from_dict(self):
        data = {
            "mac": "AA:BB:CC:DD:EE:FF",
            "ip": "10.0.1.100",
            "ssid": "CorpWiFi",
            "ap_name": "AP-001",
            "band": "5GHz",
            "channel": 36,
            "rssi_dbm": -45.0,
            "snr": 35.0,
            "tx_rate": 300.0,
            "rx_rate": 150.0,
        }
        client = ClientInfo(**data)
        assert client.mac == "AA:BB:CC:DD:EE:FF"
        assert client.status == ClientStatus.CONNECTED
        assert client.vlan is None

    def test_all_fields(self):
        data = {
            "mac": "00:11:22:33:44:55",
            "ip": "10.0.2.50",
            "ssid": "GuestNet",
            "ap_name": "AP-005",
            "band": "2.4GHz",
            "channel": 6,
            "rssi_dbm": -72.0,
            "snr": 20.0,
            "tx_rate": 54.0,
            "rx_rate": 24.0,
            "vlan": 200,
            "role": "guest",
            "username": "guest123",
            "status": "idle",
            "auth_type": "Open",
            "last_activity": "2026-01-15T09:00:00",
            "uptime_seconds": 3600,
        }
        client = ClientInfo(**data)
        assert client.status == ClientStatus.IDLE
        assert client.vlan == 200
        assert client.role == "guest"


class TestClientStats:
    def test_construct_from_dict(self):
        data = {
            "mac": "AA:BB:CC:DD:EE:FF",
            "avg_rssi_dbm": -55.0,
            "min_rssi_dbm": -78.0,
            "max_rssi_dbm": -30.0,
            "avg_snr": 30.0,
        }
        stats = ClientStats(**data)
        assert stats.total_tx_bytes == 0
        assert stats.disconnect_count == 0


class TestClientListResponse:
    def test_construct_from_dict(self):
        data = {
            "total": 1,
            "clients": [
                {
                    "mac": "AA:BB:CC:DD:EE:FF",
                    "ip": "10.0.1.1",
                    "ssid": "Test",
                    "ap_name": "AP-001",
                    "band": "5GHz",
                    "channel": 36,
                    "rssi_dbm": -50.0,
                    "snr": 30.0,
                    "tx_rate": 100.0,
                    "rx_rate": 100.0,
                }
            ],
        }
        resp = ClientListResponse(**data)
        assert resp.total == 1
        assert resp.page == 1
        assert len(resp.clients) == 1


class TestAccessPoint:
    def test_construct_from_dict(self):
        data = {
            "name": "AP-001",
            "model": "AP-515",
            "serial": "AP123456",
            "ip_address": "10.0.0.10",
            "channel_utilization": 45.0,
            "tx_power": 17.0,
            "band": "dual-band",
        }
        ap = AccessPoint(**data)
        assert ap.status == APStatus.UP
        assert ap.client_count == 0

    def test_degraded_ap(self):
        data = {
            "name": "AP-002",
            "model": "AP-535",
            "serial": "AP654321",
            "ip_address": "10.0.0.11",
            "status": "degraded",
            "channel_utilization": 92.0,
            "tx_power": 23.0,
            "band": "2.4GHz",
        }
        ap = AccessPoint(**data)
        assert ap.status == APStatus.DEGRADED
        assert ap.channel_utilization > 80


class TestAPListResponse:
    def test_construct_from_dict(self):
        data = {
            "total": 1,
            "access_points": [
                {
                    "name": "AP-001",
                    "model": "AP-505",
                    "serial": "AP111111",
                    "ip_address": "10.0.0.1",
                    "channel_utilization": 30.0,
                    "tx_power": 14.0,
                    "band": "5GHz",
                }
            ],
        }
        resp = APListResponse(**data)
        assert resp.total == 1


class TestIssue:
    def test_construct_from_dict(self):
        data = {
            "id": "ISS-0001",
            "severity": "high",
            "category": "low_rssi",
            "title": "Weak signal",
            "description": "Some clients have weak signal.",
            "timestamp": "2026-01-15T10:00:00",
        }
        issue = Issue(**data)
        assert issue.severity == IssueSeverity.HIGH
        assert issue.category == IssueCategory.LOW_RSSI
        assert issue.resolved is False
        assert issue.affected_clients == []

    def test_issue_with_analysis(self):
        data = {
            "id": "ISS-0002",
            "severity": "critical",
            "category": "high_channel_utilization",
            "title": "Channel overloaded",
            "description": "Channel utilization above 80%.",
            "timestamp": "2026-01-15T10:00:00",
            "resolved": True,
            "ai_analysis": "Recommend load balancing.",
            "recommended_actions": ["Move clients to 5GHz"],
            "affected_aps": ["AP-001", "AP-002"],
        }
        issue = Issue(**data)
        assert issue.resolved is True
        assert len(issue.recommended_actions) == 1


class TestAlertListResponse:
    def test_construct_from_dict(self):
        data = {
            "total": 0,
            "alerts": [],
        }
        resp = AlertListResponse(**data)
        assert resp.total == 0
        assert resp.page == 1
