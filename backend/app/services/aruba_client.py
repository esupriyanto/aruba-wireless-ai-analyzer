"""
Aruba Wireless Controller client.

Supports mock mode (returns deterministic fake data) and real mode
(session-managed REST API calls via httpx).
"""

import asyncio
import logging
import time
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

# Session refresh interval (25 min — Aruba default is 30 min)
_SESSION_REFRESH_INTERVAL = 1500


class _TTLCache:
    """Simple in-memory TTL cache to prevent over-polling the controller."""

    def __init__(self, ttl_seconds: int = 30):
        self._ttl = ttl_seconds
        self._data: dict[str, tuple[float, object]] = {}

    def get(self, key: str):
        entry = self._data.get(key)
        if entry is None:
            return None
        ts, val = entry
        if time.monotonic() - ts > self._ttl:
            del self._data[key]
            return None
        return val

    def set(self, key: str, value):
        self._data[key] = (time.monotonic(), value)

    def invalidate(self, key: str | None = None):
        if key is None:
            self._data.clear()
        else:
            self._data.pop(key, None)


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
        self._session_created: float | None = None
        self._cache = _TTLCache(ttl_seconds=settings.app.poll_interval_seconds)

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
            self._session_created = time.monotonic()
            logger.debug("ArubaClient: login session %s", self._session_id)

    async def _ensure_session(self) -> httpx.AsyncClient:
        """Return an authenticated client, re-logging-in on 401 or expiry."""
        if not self._http:
            raise RuntimeError("Client not connected — call connect() first")

        # Proactive refresh before 30-min timeout
        if (
            self._session_created
            and time.monotonic() - self._session_created > _SESSION_REFRESH_INTERVAL
        ):
            logger.info("ArubaClient: proactive session refresh")
            await self._login()

        return self._http

    async def _request(
        self, method: str, path: str, **kwargs
    ) -> httpx.Response:
        """Issue a request; auto-re-authenticate on 401 with retry backoff."""
        client = await self._ensure_session()

        for attempt in range(3):
            try:
                resp = await client.request(method, path, **kwargs)
                if resp.status_code == 401:
                    logger.warning("ArubaClient: 401 — re-authenticating (attempt %d)", attempt + 1)
                    await self._login()
                    resp = await client.request(method, path, **kwargs)
                resp.raise_for_status()
                return resp
            except (httpx.ConnectError, httpx.TimeoutException) as exc:
                wait = 2 ** attempt
                logger.warning("ArubaClient: %s — retrying in %ds", type(exc).__name__, wait)
                if attempt < 2:
                    await asyncio.sleep(wait)
                else:
                    raise

    # ------------------------------------------------------------------
    # Response mapping (real API → Pydantic models)
    # ------------------------------------------------------------------

    @staticmethod
    def _map_client(raw: dict) -> dict:
        """Normalize a raw Aruba client dict into ClientInfo-compatible fields.

        Handles field name differences between ArubaOS 8.x and AOS 10.x:
        - mac → mac (or macaddr)
        - ip → ip (or ip_address)
        - ap_name → ap_name (or ap, apname)
        - rssi_dbm → rssi_dbm (or rssi)
        - last_activity → last_activity (or last_seen, ISO string)
        """
        def _parse_dt(val):
            if not val:
                return None
            if isinstance(val, datetime):
                return val
            for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
                try:
                    return datetime.strptime(val.split(".")[0], fmt)
                except ValueError:
                    continue
            return None

        return {
            "mac": raw.get("mac") or raw.get("macaddr") or raw.get("client_mac", ""),
            "ip": raw.get("ip") or raw.get("ip_address", ""),
            "ssid": raw.get("ssid") or raw.get("essid", ""),
            "ap_name": raw.get("ap_name") or raw.get("ap") or raw.get("apname", ""),
            "band": raw.get("band") or raw.get("radio_band", ""),
            "channel": int(raw.get("channel", 0) or 0),
            "rssi_dbm": float(raw.get("rssi_dbm") or raw.get("rssi", 0) or 0),
            "snr": float(raw.get("snr", 0) or 0),
            "tx_rate": float(raw.get("tx_rate") or raw.get("txrate", 0) or 0),
            "rx_rate": float(raw.get("rx_rate") or raw.get("rxrate", 0) or 0),
            "vlan": int(raw.get("vlan", 0)) if raw.get("vlan") else None,
            "role": raw.get("role"),
            "username": raw.get("username") or raw.get("user"),
            "status": raw.get("status", "connected"),
            "auth_type": raw.get("auth_type") or raw.get("authentication"),
            "last_activity": _parse_dt(raw.get("last_activity") or raw.get("last_seen")),
            "uptime_seconds": int(raw.get("uptime", 0) or 0) or None,
        }

    @staticmethod
    def _map_ap(raw: dict) -> dict:
        """Normalize a raw Aruba AP dict into AccessPoint-compatible fields."""
        def _parse_dt(val):
            if not val:
                return None
            if isinstance(val, datetime):
                return val
            for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
                try:
                    return datetime.strptime(val.split(".")[0], fmt)
                except ValueError:
                    continue
            return None

        status_raw = raw.get("status", "up").lower()
        status_map = {"up": "up", "down": "down", "degraded": "degraded"}
        status = status_map.get(status_raw, "up")

        return {
            "name": raw.get("name") or raw.get("ap_name", ""),
            "model": raw.get("model") or raw.get("ap_model", ""),
            "serial": raw.get("serial") or raw.get("serial_number", ""),
            "ip_address": raw.get("ip_address") or raw.get("ip", ""),
            "status": status,
            "group": raw.get("group") or raw.get("ap_group"),
            "site": raw.get("site"),
            "client_count": int(raw.get("client_count") or raw.get("num_clients", 0) or 0),
            "channel_utilization": float(
                raw.get("channel_utilization") or raw.get("utilization", 0) or 0
            ),
            "tx_power": float(raw.get("tx_power") or raw.get("power", 0) or 0),
            "band": raw.get("band") or raw.get("radio_band", "dual-band"),
            "channel": int(raw.get("channel", 0)) if raw.get("channel") else None,
            "frequency_mhz": int(raw.get("frequency", 0)) if raw.get("frequency") else None,
            "uptime_seconds": int(raw.get("uptime", 0) or 0) or None,
            "firmware_version": raw.get("firmware") or raw.get("version"),
            "last_reboot": _parse_dt(raw.get("last_reboot")),
        }

    @staticmethod
    def _map_event(raw: dict) -> dict:
        """Normalize a raw Aruba event dict."""
        return {
            "id": str(raw.get("id") or raw.get("event_id", "")),
            "severity": raw.get("severity", "info"),
            "message": raw.get("message") or raw.get("description", ""),
            "timestamp": raw.get("timestamp") or raw.get("time", datetime.now().isoformat()),
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def get_clients(
        self, page: int = 1, page_size: int = 50
    ) -> ClientListResponse:
        """Return the list of wireless clients."""
        cache_key = f"clients_{page}_{page_size}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        if self._mock_mode:
            all_clients = mock_data.generate_clients()
            total = len(all_clients)
            start = (page - 1) * page_size
            end = start + page_size
            result = ClientListResponse(
                total=total,
                clients=all_clients[start:end],
                page=page,
                page_size=page_size,
            )
            self._cache.set(cache_key, result)
            return result

        resp = await self._request("GET", _CLIENTS_PATH)
        raw = resp.json()
        raw_clients = raw.get("clients", [])
        mapped = [ClientInfo(**self._map_client(c)) for c in raw_clients]
        result = ClientListResponse(
            total=raw.get("total", len(mapped)),
            clients=mapped,
            page=page,
            page_size=page_size,
        )
        self._cache.set(cache_key, result)
        return result

    async def get_access_points(
        self, page: int = 1, page_size: int = 50
    ) -> APListResponse:
        """Return the list of access points."""
        cache_key = f"aps_{page}_{page_size}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        if self._mock_mode:
            aps = mock_data.generate_access_points()
            result = APListResponse(
                total=len(aps),
                access_points=aps,
                page=page,
                page_size=page_size,
            )
            self._cache.set(cache_key, result)
            return result

        resp = await self._request("GET", _APS_PATH)
        raw = resp.json()
        raw_aps = raw.get("access_points", [])
        mapped = [AccessPoint(**self._map_ap(a)) for a in raw_aps]
        result = APListResponse(
            total=raw.get("total", len(mapped)),
            access_points=mapped,
            page=page,
            page_size=page_size,
        )
        self._cache.set(cache_key, result)
        return result

    async def get_events(self, limit: int = 100) -> list[dict]:
        """Return recent controller events."""
        cache_key = f"events_{limit}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        if self._mock_mode:
            result = [
                {
                    "id": f"EVT-{i:04d}",
                    "severity": "info",
                    "message": f"Mock event #{i}",
                    "timestamp": datetime.now().isoformat(),
                }
                for i in range(min(limit, 10))
            ]
            self._cache.set(cache_key, result)
            return result

        resp = await self._request(
            "GET", _EVENTS_PATH, params={"length": limit}
        )
        raw_events = resp.json().get("events", [])
        result = [self._map_event(e) for e in raw_events]
        self._cache.set(cache_key, result)
        return result

    async def get_client_detail(self, mac: str) -> ClientInfo | None:
        """Return detailed info for a single client by MAC address."""
        cache_key = f"client_{mac}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        if self._mock_mode:
            for c in mock_data.generate_clients():
                if c.mac.upper() == mac.upper():
                    self._cache.set(cache_key, c)
                    return c
            return None

        resp = await self._request(
            "GET", f"{_CLIENTS_PATH}/{mac}"
        )
        raw = resp.json()
        if not raw:
            return None
        result = ClientInfo(**self._map_client(raw))
        self._cache.set(cache_key, result)
        return result

    async def get_rssi_timeseries(
        self, mac: str, hours: float = 1
    ) -> list[TimeSeriesPoint]:
        """Return RSSI time-series for a client over the given window."""
        cache_key = f"rssi_{mac}_{hours}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        if self._mock_mode:
            result = mock_data.generate_rssi_timeseries(mac, hours=hours)
            self._cache.set(cache_key, result)
            return result

        resp = await self._request(
            "GET",
            f"{_CLIENTS_PATH}/{mac}/rssi",
            params={"hours": hours},
        )
        result = [
            TimeSeriesPoint(**pt) for pt in resp.json().get("timeseries", [])
        ]
        self._cache.set(cache_key, result)
        return result

    def invalidate_cache(self, key: str | None = None):
        """Invalidate cache entries. Pass None to clear all."""
        self._cache.invalidate(key)
