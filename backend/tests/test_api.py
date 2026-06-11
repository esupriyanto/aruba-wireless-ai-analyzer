"""Integration tests for all API endpoints using FastAPI TestClient."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# ------------------------------------------------------------------
# Health
# ------------------------------------------------------------------

class TestHealth:
    def test_health_returns_ok(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "mock_mode" in data


# ------------------------------------------------------------------
# Clients
# ------------------------------------------------------------------

class TestListClients:
    def test_returns_200_with_default_pagination(self):
        resp = client.get("/api/v1/clients/")
        assert resp.status_code == 200

    def test_returns_client_list_response(self):
        resp = client.get("/api/v1/clients/")
        data = resp.json()
        assert "total" in data
        assert "clients" in data
        assert "page" in data
        assert "page_size" in data

    def test_returns_approximately_50_clients(self):
        resp = client.get("/api/v1/clients/")
        data = resp.json()
        assert len(data["clients"]) == 50

    def test_custom_page_size(self):
        resp = client.get("/api/v1/clients/", params={"page_size": 10})
        data = resp.json()
        assert len(data["clients"]) == 10
        assert data["page_size"] == 10

    def test_client_has_expected_fields(self):
        resp = client.get("/api/v1/clients/")
        first = resp.json()["clients"][0]
        assert "mac" in first
        assert "ip" in first
        assert "ssid" in first
        assert "ap_name" in first
        assert "rssi_dbm" in first
        assert "status" in first


class TestGetClient:
    def test_returns_client_by_mac(self):
        # First get the list to find a valid MAC
        list_resp = client.get("/api/v1/clients/")
        mac = list_resp.json()["clients"][0]["mac"]

        resp = client.get(f"/api/v1/clients/{mac}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["mac"].upper() == mac.upper()

    def test_returns_404_for_unknown_mac(self):
        resp = client.get("/api/v1/clients/AA:BB:CC:DD:EE:FF")
        assert resp.status_code == 404


class TestClientRSSI:
    def test_returns_rssi_timeseries(self):
        list_resp = client.get("/api/v1/clients/")
        mac = list_resp.json()["clients"][0]["mac"]

        resp = client.get(f"/api/v1/clients/{mac}/rssi")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0
        # Each point should have timestamp and value
        assert "timestamp" in data[0]
        assert "value" in data[0]

    def test_returns_404_for_unknown_mac(self):
        resp = client.get("/api/v1/clients/AA:BB:CC:DD:EE:FF/rssi")
        assert resp.status_code == 404

    def test_custom_hours_parameter(self):
        list_resp = client.get("/api/v1/clients/")
        mac = list_resp.json()["clients"][0]["mac"]

        resp = client.get(f"/api/v1/clients/{mac}/rssi", params={"hours": 2})
        assert resp.status_code == 200
        assert len(resp.json()) > 0


# ------------------------------------------------------------------
# Access Points
# ------------------------------------------------------------------

class TestListAccessPoints:
    def test_returns_200(self):
        resp = client.get("/api/v1/access-points/")
        assert resp.status_code == 200

    def test_returns_ap_list_response(self):
        resp = client.get("/api/v1/access-points/")
        data = resp.json()
        assert "total" in data
        assert "access_points" in data
        assert "page" in data
        assert "page_size" in data

    def test_returns_approximately_10_aps(self):
        resp = client.get("/api/v1/access-points/")
        data = resp.json()
        assert len(data["access_points"]) == 10

    def test_ap_has_expected_fields(self):
        resp = client.get("/api/v1/access-points/")
        first = resp.json()["access_points"][0]
        assert "name" in first
        assert "model" in first
        assert "status" in first
        assert "channel_utilization" in first
        assert "band" in first


# ------------------------------------------------------------------
# Events
# ------------------------------------------------------------------

class TestListEvents:
    def test_returns_200(self):
        resp = client.get("/api/v1/events/")
        assert resp.status_code == 200

    def test_returns_event_list(self):
        resp = client.get("/api/v1/events/")
        data = resp.json()
        assert isinstance(data, list)

    def test_custom_limit(self):
        resp = client.get("/api/v1/events/", params={"limit": 5})
        data = resp.json()
        assert len(data) <= 5


class TestListAlerts:
    def test_returns_200(self):
        resp = client.get("/api/v1/events/alerts")
        assert resp.status_code == 200

    def test_returns_alert_list_response(self):
        resp = client.get("/api/v1/events/alerts")
        data = resp.json()
        assert "total" in data
        assert "alerts" in data

    def test_detects_issues_from_mock_data(self):
        resp = client.get("/api/v1/events/alerts")
        data = resp.json()
        # Mock data has weak-signal clients and overloaded APs,
        # so the analyzer should find at least one issue
        assert data["total"] > 0

    def test_alert_has_expected_fields(self):
        resp = client.get("/api/v1/events/alerts")
        alerts = resp.json()["alerts"]
        assert len(alerts) > 0
        first = alerts[0]
        assert "id" in first
        assert "severity" in first
        assert "category" in first
        assert "title" in first
        assert "description" in first


# ------------------------------------------------------------------
# Remediation
# ------------------------------------------------------------------

class TestRemediationAnalyze:
    def test_returns_200_with_default_body(self):
        resp = client.post("/api/v1/remediation/analyze")
        assert resp.status_code == 200

    def test_returns_analyze_response_structure(self):
        resp = client.post("/api/v1/remediation/analyze")
        data = resp.json()
        assert "issues" in data
        assert "summary" in data
        assert "recommended_next_steps" in data

    def test_summary_mentions_issues(self):
        resp = client.post("/api/v1/remediation/analyze")
        data = resp.json()
        # Mock data should trigger alerts
        assert data["issues"]["total"] > 0
        assert "Detected" in data["summary"]

    def test_with_category_filter(self):
        resp = client.post(
            "/api/v1/remediation/analyze",
            json={"category": "low_rssi"},
        )
        assert resp.status_code == 200


class TestRemediationExecute:
    def test_returns_200_for_valid_action(self):
        resp = client.post(
            "/api/v1/remediation/execute",
            json={"issue_id": "ANA-0001", "action": "restart_ap"},
        )
        assert resp.status_code == 200

    def test_returns_execute_response_structure(self):
        resp = client.post(
            "/api/v1/remediation/execute",
            json={"issue_id": "ANA-0001", "action": "adjust_power"},
        )
        data = resp.json()
        assert data["status"] == "accepted"
        assert data["issue_id"] == "ANA-0001"
        assert data["action"] == "adjust_power"
        assert "message" in data

    def test_returns_400_for_invalid_action(self):
        resp = client.post(
            "/api/v1/remediation/execute",
            json={"issue_id": "ANA-0001", "action": "invalid_action"},
        )
        assert resp.status_code == 400

    def test_kick_client_action(self):
        resp = client.post(
            "/api/v1/remediation/execute",
            json={"issue_id": "ANA-0002", "action": "kick_client"},
        )
        assert resp.status_code == 200
        assert resp.json()["action"] == "kick_client"


# ------------------------------------------------------------------
# Router registration / Swagger
# ------------------------------------------------------------------

class TestRouterRegistration:
    def test_all_api_routes_exist(self):
        """Verify all expected API routes are registered."""
        routes = [r.path for r in app.routes if hasattr(r, "path")]
        expected = [
            "/health",
            "/api/v1/clients/",
            "/api/v1/clients/{mac}",
            "/api/v1/clients/{mac}/rssi",
            "/api/v1/access-points/",
            "/api/v1/events/",
            "/api/v1/events/alerts",
            "/api/v1/remediation/analyze",
            "/api/v1/remediation/execute",
        ]
        for route in expected:
            assert route in routes, f"Route {route} not found in registered routes"

    def test_openapi_schema_available(self):
        """Swagger UI endpoint should be accessible."""
        resp = client.get("/openapi.json")
        assert resp.status_code == 200
        schema = resp.json()
        assert "paths" in schema
        assert "/api/v1/clients/" in schema["paths"]
        assert "/api/v1/access-points/" in schema["paths"]
