"""
Aruba Wireless Controller client.

Supports mock mode (returns deterministic fake data) and real mode
(session-managed REST API calls via httpx).
"""

import logging
from datetime import datetime

import httpx

from backend.app.config import settings
from backend.app.models.ap import APListResponse, AccessPoint
from backend.app.models.client import ClientInfo, ClientListResponse
from backend.app.models.common import TimeSeriesPoint
from backend.app.services import mock_data

logger = logging.getLogger(__name__)

# Real API paths
_LOGIN_PATH = "/v1/api/login"
_CLIENTS_PATH = "/v1/monitoring/clients"
_APS_PATH = "/v1/monitoring/aps"
_EVENTS_PATH = "/v1/monitoring/events"


class ArubaClient:
    """Async client for an Aruba Wireless Controller.

    Parameters
    ----------
    mock_mode : bool | None
        Override the global ``settings.mock_mode``.  ``None`` (default) uses
        the global setting.
    """

    def __init__(self, mock_mode: bool | None = None) -> None:
        self._mock_mode = (
            mock_mode if mock_mode is not None else settings.mock_mode
        )
        self._base_url = (
            f"https://{settings.aruba.controller_host}:{settings.aruba.controller_port}"
        )
        self._http: httpx.AsyncClient | None = None
        self._session_id: str | None = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def connect(self) -> None:
        """Initialise the underlying HTTP client.

        In real mode this also authenticates against the controller.
        No-op in mock mode.
        """
        if self._mock_mode:
            logger.info("ArubaClient: mock mode — connect() is a no-op")
            return

        self._http = httpx.AsyncClient(
            base_url=self._base_url,
            verify=settings.aruba.ssl_verify,
            timeout=30.0,
        )
        await self._login()
        logger.info("ArubaClient: connected to %s", self._base_url)

    async def close(self) -> None:
        """Tear down the HTTP client."""
        if self._http:
            await self._http.aclose()
            self._http = None

    # ------------------------------------------------------------------
    # Authentication helpers
    # ------------------------------------------------------------------

    async def _login(self) -> None:
        """POST credentials and store the session cookie."""
        payload = {
            "user": settings.aruba.username,
            "password": settings.aruba.password,
        }
        resp = await self._http.post(_LOGIN_PATH, json=payload)
        resp.raise_for_status()
        data = resp.json()
        # Aruba returns {"_global_result": {"status": "0", ...}, ...}
        self._session_id = data.get("_global_result", {}).get("session_id")
        if self._session_id:
            self._http.cookies.set("session", self._session_id)
            logger.debug("ArubaClient: login session %s", self._session_id)

    async def _ensure_session(self) -> httpx.AsyncClient:
        """Return an authenticated client, re-logging-in on 401."""
        if not self._http:
            raise RuntimeError("Client not connected — call connect() first")
        return self._http

    async def _request(
        self, method: str, path: str, **kwargs
    ) -> httpx.Response:
        """Issue a request; auto-re-authenticate on 401."""
        client = await self._ensure_session()
        resp = await client.request(method, path, **kwargs)
        if resp.status_code == 401:
            logger.warning("ArubaClient: 401 — re-authenticating")
            await self._login()
            resp = await client.request(method, path, **kwargs)
        resp.raise_for_status()
        return resp

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def get_clients(
        self, page: int = 1, page_size: int = 50
    ) -> ClientListResponse:
        """Return the list of wireless clients."""
        if self._mock_mode:
            all_clients = mock_data.generate_clients()
            total = len(all_clients)
            start = (page - 1) * page_size
            end = start + page_size
            return ClientListResponse(
                total=total,
                clients=all_clients[start:end],
                page=page,
                page_size=page_size,
            )

        resp = await self._request("GET", _CLIENTS_PATH)
        raw = resp.json()
        clients = [ClientInfo(**c) for c in raw.get("clients", [])]
        return ClientListResponse(
            total=raw.get("total", len(clients)),
            clients=clients,
            page=page,
            page_size=page_size,
        )

    async def get_access_points(
        self, page: int = 1, page_size: int = 50
    ) -> APListResponse:
        """Return the list of access points."""
        if self._mock_mode:
            return APListResponse(
                total=0,
                access_points=mock_data.generate_access_points(),
                page=page,
                page_size=page_size,
            )

        resp = await self._request("GET", _APS_PATH)
        raw = resp.json()
        aps = [AccessPoint(**a) for a in raw.get("access_points", [])]
        return APListResponse(
            total=raw.get("total", len(aps)),
            access_points=aps,
            page=page,
            page_size=page_size,
        )

    async def get_events(self, limit: int = 100) -> list[dict]:
        """Return recent controller events."""
        if self._mock_mode:
            return [
                {
                    "id": f"EVT-{i:04d}",
                    "severity": "info",
                    "message": f"Mock event #{i}",
                    "timestamp": datetime.now().isoformat(),
                }
                for i in range(min(limit, 10))
            ]

        resp = await self._request(
            "GET", _EVENTS_PATH, params={"length": limit}
        )
        return resp.json().get("events", [])

    async def get_client_detail(self, mac: str) -> ClientInfo | None:
        """Return detailed info for a single client by MAC address."""
        if self._mock_mode:
            for c in mock_data.generate_clients():
                if c.mac.upper() == mac.upper():
                    return c
            return None

        resp = await self._request(
            "GET", f"{_CLIENTS_PATH}/{mac}"
        )
        raw = resp.json()
        if not raw:
            return None
        return ClientInfo(**raw)

    async def get_rssi_timeseries(
        self, mac: str, hours: float = 1
    ) -> list[TimeSeriesPoint]:
        """Return RSSI time-series for a client over the given window."""
        if self._mock_mode:
            return mock_data.generate_rssi_timeseries(mac, hours=hours)

        resp = await self._request(
            "GET",
            f"{_CLIENTS_PATH}/{mac}/rssi",
            params={"hours": hours},
        )
        return [
            TimeSeriesPoint(**pt) for pt in resp.json().get("timeseries", [])
        ]
