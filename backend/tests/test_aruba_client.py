"""Tests for ArubaClient — mock mode and real mode (respx)."""

import pytest
import pytest_asyncio
import httpx
import respx

from app.services.aruba_client import ArubaClient
from app.models.client import ClientInfo, ClientListResponse
from app.models.ap import APListResponse
from app.models.common import TimeSeriesPoint


# ------------------------------------------------------------------
# Mock mode
# ------------------------------------------------------------------


class TestArubaClientMockMode:
    """Validate behaviour when mock_mode=True (no HTTP calls)."""

    @pytest_asyncio.fixture
    async def client(self):
        c = ArubaClient(mock_mode=True)
        await c.connect()
        yield c
        await c.close()

    @pytest.mark.asyncio
    async def test_connect_noop(self, client):
        """connect() should succeed without starting an HTTP session."""
        assert client._http is None  # no httpx client created

    @pytest.mark.asyncio
    async def test_get_clients_returns_valid_model(self, client):
        result = await client.get_clients()
        assert isinstance(result, ClientListResponse)
        assert len(result.clients) > 0
        assert all(isinstance(c, ClientInfo) for c in result.clients)

    @pytest.mark.asyncio
    async def test_get_clients_deterministic(self, client):
        """Two successive calls return the same data (deterministic seed)."""
        r1 = await client.get_clients()
        r2 = await client.get_clients()
        assert [c.mac for c in r1.clients] == [c.mac for c in r2.clients]

    @pytest.mark.asyncio
    async def test_get_access_points_returns_valid_model(self, client):
        result = await client.get_access_points()
        assert isinstance(result, APListResponse)
        assert len(result.access_points) > 0

    @pytest.mark.asyncio
    async def test_get_events_returns_list(self, client):
        events = await client.get_events(limit=5)
        assert isinstance(events, list)
        assert len(events) == 5

    @pytest.mark.asyncio
    async def test_get_events_default_limit(self, client):
        events = await client.get_events()
        assert len(events) == 10  # default cap in mock

    @pytest.mark.asyncio
    async def test_get_client_detail_found(self, client):
        clients_resp = await client.get_clients()
        mac = clients_resp.clients[0].mac
        detail = await client.get_client_detail(mac)
        assert detail is not None
        assert detail.mac == mac

    @pytest.mark.asyncio
    async def test_get_client_detail_not_found(self, client):
        detail = await client.get_client_detail("FF:FF:FF:FF:FF:FF")
        assert detail is None

    @pytest.mark.asyncio
    async def test_get_rssi_timeseries(self, client):
        ts = await client.get_rssi_timeseries("AA:BB:CC:DD:EE:FF", hours=2)
        assert isinstance(ts, list)
        assert len(ts) > 0
        assert all(isinstance(p, TimeSeriesPoint) for p in ts)


# ------------------------------------------------------------------
# Real mode (HTTP mocked with respx)
# ------------------------------------------------------------------


_FAKE_SESSION_PAYLOAD = {
    "_global_result": {"status": "0", "session_id": "fake-session-123"}
}

_FAKE_CLIENTS_PAYLOAD = {
    "total": 1,
    "clients": [
        {
            "mac": "AA:BB:CC:DD:EE:01",
            "ip": "10.0.1.100",
            "ssid": "CorpWiFi",
            "ap_name": "AP-001",
            "band": "5GHz",
            "channel": 36,
            "rssi_dbm": -52.0,
            "snr": 30.0,
            "tx_rate": 300.0,
            "rx_rate": 300.0,
        }
    ],
}

_FAKE_APS_PAYLOAD = {
    "total": 1,
    "access_points": [
        {
            "name": "AP-001",
            "model": "AP-515",
            "serial": "AP123456",
            "ip_address": "10.0.0.10",
            "channel_utilization": 45.0,
            "tx_power": 17.0,
            "band": "dual-band",
        }
    ],
}

_FAKE_EVENTS_PAYLOAD = {
    "events": [
        {
            "id": "EVT-0001",
            "severity": "info",
            "message": "Test event",
        }
    ]
}


class TestArubaClientRealMode:
    """Validate real-mode HTTP flows using respx to mock httpx."""

    @pytest_asyncio.fixture
    async def client(self):
        with respx.mock:
            respx.post("https://192.168.1.1:4343/v1/api/login").mock(
                return_value=httpx.Response(200, json=_FAKE_SESSION_PAYLOAD)
            )
            c = ArubaClient(mock_mode=False)
            await c.connect()
            yield c
            await c.close()

    @respx.mock
    @pytest.mark.asyncio
    async def test_connect_performs_login(self):
        """connect() should POST login and store session cookie."""
        respx.post("https://192.168.1.1:4343/v1/api/login").mock(
            return_value=httpx.Response(200, json=_FAKE_SESSION_PAYLOAD)
        )
        c = ArubaClient(mock_mode=False)
        await c.connect()
        assert c._session_id == "fake-session-123"
        await c.close()

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_clients_real(self, client):
        respx.get("https://192.168.1.1:4343/v1/monitoring/clients").mock(
            return_value=httpx.Response(200, json=_FAKE_CLIENTS_PAYLOAD)
        )
        result = await client.get_clients()
        assert isinstance(result, ClientListResponse)
        assert len(result.clients) == 1
        assert result.clients[0].mac == "AA:BB:CC:DD:EE:01"

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_access_points_real(self, client):
        respx.get("https://192.168.1.1:4343/v1/monitoring/aps").mock(
            return_value=httpx.Response(200, json=_FAKE_APS_PAYLOAD)
        )
        result = await client.get_access_points()
        assert isinstance(result, APListResponse)
        assert result.access_points[0].name == "AP-001"

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_events_real(self, client):
        respx.get("https://192.168.1.1:4343/v1/monitoring/events").mock(
            return_value=httpx.Response(200, json=_FAKE_EVENTS_PAYLOAD)
        )
        events = await client.get_events(limit=1)
        assert len(events) == 1

    @respx.mock
    @pytest.mark.asyncio
    async def test_reauth_on_401(self, client):
        """On 401 the client re-authenticates and retries."""
        login_route = respx.post(
            "https://192.168.1.1:4343/v1/api/login"
        ).mock(return_value=httpx.Response(200, json=_FAKE_SESSION_PAYLOAD))

        # First call returns 401, second returns 200
        respx.get("https://192.168.1.1:4343/v1/monitoring/clients").mock(
            side_effect=[
                httpx.Response(401),
                httpx.Response(200, json=_FAKE_CLIENTS_PAYLOAD),
            ]
        )
        result = await client.get_clients()
        assert len(result.clients) == 1
        # Login called twice: once at connect() + once on 401 retry
        assert login_route.call_count == 2
