"""Tests for search endpoint and utilities (Phase 9)."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.search_service import (
    detect_query_type,
    is_valid_ipv4,
    is_valid_mac,
    normalize_mac,
)

FIXTURES = Path(__file__).parent / "fixtures"


class TestNormalizeMac:
    """Test MAC normalization."""

    def test_colon_format(self):
        assert normalize_mac("AA:BB:CC:DD:EE:FF") == "AA:BB:CC:DD:EE:FF"

    def test_dash_format(self):
        assert normalize_mac("AA-BB-CC-DD-EE-FF") == "AA:BB:CC:DD:EE:FF"

    def test_no_separator(self):
        assert normalize_mac("AABBCCDDEEFF") == "AA:BB:CC:DD:EE:FF"

    def test_lowercase(self):
        assert normalize_mac("aa:bb:cc:dd:ee:ff") == "AA:BB:CC:DD:EE:FF"

    def test_mixed_case(self):
        assert normalize_mac("aA:Bb:Cc:Dd:Ee:FF") == "AA:BB:CC:DD:EE:FF"


class TestValidIp:
    """Test IPv4 validation."""

    def test_valid_ipv4(self):
        assert is_valid_ipv4("192.168.1.100") is True
        assert is_valid_ipv4("10.0.0.1") is True

    def test_invalid_ipv4(self):
        assert is_valid_ipv4("invalid") is False
        assert is_valid_ipv4("256.1.1.1") is False
        assert is_valid_ipv4("192.168.1") is False


class TestValidMac:
    """Test MAC validation."""

    def test_valid_mac_colon(self):
        assert is_valid_mac("AA:BB:CC:DD:EE:FF") is True

    def test_valid_mac_dash(self):
        assert is_valid_mac("AA-BB-CC-DD-EE-FF") is True

    def test_valid_mac_no_sep(self):
        assert is_valid_mac("AABBCCDDEEFF") is True

    def test_invalid_mac(self):
        assert is_valid_mac("invalid") is False
        assert is_valid_mac("AA:BB:CC") is False


class TestDetectQueryType:
    """Test query type detection."""

    def test_detect_mac_colon(self):
        assert detect_query_type("AA:BB:CC:DD:EE:FF") == "mac"

    def test_detect_mac_dash(self):
        assert detect_query_type("AA-BB-CC-DD-EE-FF") == "mac"

    def test_detect_mac_no_sep(self):
        assert detect_query_type("AABBCCDDEEFF") == "mac"

    def test_detect_ipv4(self):
        assert detect_query_type("192.168.1.100") == "ip"

    def test_detect_unknown(self):
        assert detect_query_type("random") == "unknown"
        assert detect_query_type("") == "unknown"


class TestSearchEndpoint:
    """Test search endpoint (mock mode)."""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_search_by_mac_found(self, client):
        """Search for a known mock MAC (deterministic, iseed=42 generates '72:47:34:2C:D8:10')."""
        resp = client.get("/api/v1/search?query=72:47:34:2C:D8:10")
        assert resp.status_code == 200
        data = resp.json()
        assert data["found"] is True
        assert data["query_type"] == "mac"
        assert data["device"]["mac_address"] == "72:47:34:2C:D8:10"

    def test_search_by_mac_found_uppercase(self, client):
        """Search with uppercase MAC."""
        resp = client.get("/api/v1/search?query=72:47:34:2C:D8:10")
        assert resp.status_code == 200
        assert resp.json()["found"] is True

    def test_search_by_mac_not_found(self, client):
        resp = client.get("/api/v1/search?query=FF:FF:FF:FF:FF:FF")
        assert resp.status_code == 200
        data = resp.json()
        assert data["found"] is False

    def test_search_by_ip_not_found(self, client):
        resp = client.get("/api/v1/search?query=1.2.3.4")
        assert resp.status_code == 200
        data = resp.json()
        assert data["found"] is False

    def test_search_invalid_query(self, client):
        resp = client.get("/api/v1/search?query=invalid")
        assert resp.status_code == 400

    def test_search_empty_query(self, client):
        resp = client.get("/api/v1/search?query=")
        assert resp.status_code == 400

    def test_search_response_structure(self, client):
        resp = client.get("/api/v1/search?query=72:47:34:2C:D8:10")
        assert resp.status_code == 200
        data = resp.json()
        assert "query" in data
        assert "query_type" in data
        assert "found" in data
        if data["found"]:
            assert "device" in data
            assert "metrics" in data
            assert "ai_diagnosis" in data
            assert "remediation_actions" in data