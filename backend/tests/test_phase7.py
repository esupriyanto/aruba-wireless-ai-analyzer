"""Tests for Phase 7: mapping, error handling, cache, and audit log."""

import json
from pathlib import Path

import pytest

from app.services.aruba_client import ArubaClient, _TTLCache
from app.services.audit_log import log_action, get_audit_log

FIXTURES = Path(__file__).parent / "fixtures"


class TestMapClient:
    """Test _map_client normalization from real Aruba API responses."""

    def test_full_response(self):
        raw = json.loads((FIXTURES / "aruba_clients.json").read_text())
        client_raw = raw["clients"][0]
        mapped = ArubaClient._map_client(client_raw)
        assert mapped["mac"] == "aa:bb:cc:dd:ee:01"
        assert mapped["ip"] == "10.0.1.101"
        assert mapped["ap_name"] == "AP-001"
        assert mapped["rssi_dbm"] == -62.0
        assert mapped["status"] == "connected"
        assert mapped["auth_type"] == "WPA2-Enterprise"

    def test_minimal_response(self):
        """Handles missing optional fields gracefully."""
        raw = {"mac": "aa:bb:cc:dd:ee:02", "band": "2.4GHz"}
        mapped = ArubaClient._map_client(raw)
        assert mapped["mac"] == "aa:bb:cc:dd:ee:02"
        assert mapped["ip"] == ""
        assert mapped["channel"] == 0
        assert mapped["rssi_dbm"] == 0.0
        assert mapped["status"] == "connected"  # default
        assert mapped["last_activity"] is None

    def test_alternative_field_names(self):
        """Maps alternative field names (rssi, macaddr, ap, …)."""
        raw = {"macaddr": "aa:bb:cc:dd:ee:03", "rssi": -70, "ap": "AP-005"}
        mapped = ArubaClient._map_client(raw)
        assert mapped["mac"] == "aa:bb:cc:dd:ee:03"
        assert mapped["rssi_dbm"] == -70.0
        assert mapped["ap_name"] == "AP-005"

    def test_integration_with_client_info_model(self):
        """Mapped dict can be unpacked into ClientInfo."""
        from app.models.client import ClientInfo
        raw = json.loads((FIXTURES / "aruba_clients.json").read_text())
        client_raw = raw["clients"][0]
        mapped = ArubaClient._map_client(client_raw)
        info = ClientInfo(**mapped)
        assert info.mac == "aa:bb:cc:dd:ee:01"
        assert info.rssi_dbm == -62.0


class TestMapAP:
    """Test _map_ap normalization."""

    def test_full_response(self):
        raw = json.loads((FIXTURES / "aruba_aps.json").read_text())
        ap_raw = raw["access_points"][0]
        mapped = ArubaClient._map_ap(ap_raw)
        assert mapped["name"] == "AP-001"
        assert mapped["model"] == "AP-535"
        assert mapped["status"] == "up"
        assert mapped["client_count"] == 12
        assert mapped["channel_utilization"] == 45.0

    def test_high_utilization(self):
        raw = json.loads((FIXTURES / "aruba_aps.json").read_text())
        ap_raw = raw["access_points"][1]
        mapped = ArubaClient._map_ap(ap_raw)
        assert mapped["channel_utilization"] == 82.0
        assert mapped["status"] == "up"

    def test_alternative_field_names(self):
        raw = {"name": "AP-X", "utilization": 90, "power": 20}
        mapped = ArubaClient._map_ap(raw)
        assert mapped["channel_utilization"] == 90.0
        assert mapped["tx_power"] == 20.0


class TestMapEvent:
    """Test _map_event normalization."""

    def test_full_response(self):
        raw = json.loads((FIXTURES / "aruba_events.json").read_text())
        evt_raw = raw["events"][0]
        mapped = ArubaClient._map_event(evt_raw)
        assert mapped["id"] == "EVT-0001"
        assert mapped["severity"] == "warning"
        assert "weak RSSI" in mapped["message"]

    def test_minimal(self):
        mapped = ArubaClient._map_event({})
        assert mapped["id"] == ""
        assert mapped["severity"] == "info"


class TestTTLCache:
    """Test the TTL cache."""

    def test_set_and_get(self):
        cache = _TTLCache(ttl_seconds=10)
        cache.set("key", "value")
        assert cache.get("key") == "value"

    def test_expiry(self):
        import time
        cache = _TTLCache(ttl_seconds=0)
        cache.set("key", "value")
        time.sleep(0.05)
        assert cache.get("key") is None

    def test_invalidate_single(self):
        cache = _TTLCache(ttl_seconds=60)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.invalidate("a")
        assert cache.get("a") is None
        assert cache.get("b") == 2

    def test_invalidate_all(self):
        cache = _TTLCache(ttl_seconds=60)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.invalidate()
        assert cache.get("a") is None
        assert cache.get("b") is None


class TestAuditLog:
    """Test SQLite audit log."""

    def test_log_and_retrieve(self, tmp_path, monkeypatch):
        # Use a temp database for testing
        from app.services import audit_log as al
        orig = al.DB_PATH
        al.DB_PATH = tmp_path / "test_audit.db"
        try:
            log_action("issue-001", "restart_ap", "accepted", "Test message")
            log_action("issue-002", "kick_client", "accepted", "Another message")
            entries = get_audit_log()
            assert len(entries) == 2
            assert entries[1]["issue_id"] == "issue-001"  # ordered DESC
            assert entries[0]["action"] == "kick_client"
        finally:
            al.DB_PATH = orig
