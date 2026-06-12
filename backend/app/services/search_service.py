"""Search utility functions for MAC/IP normalization and validation."""

import re
from typing import Literal


MAC_PATTERNS = [
    # AA:BB:CC:DD:EE:FF
    re.compile(r"^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$"),
    # AA-BB-CC-DD-EE-FF
    re.compile(r"^([0-9A-Fa-f]{2}-){5}[0-9A-Fa-f]{2}$"),
    # AABBCCDDEEFF
    re.compile(r"^[0-9A-Fa-f]{12}$"),
]

IP_PATTERN = re.compile(
    r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}"
    r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
)


def normalize_mac(mac: str) -> str | None:
    """
    Normalize MAC address to AA:BB:CC:DD:EE:FF format.
    
    Supports:
    - AA:BB:CC:DD:EE:FF (already normalized)
    - AA-BB-CC-DD-EE-FF (dash separated)
    - AABBCCDDEEFF (no separator)
    
    Returns None if input is not a valid MAC address.
    """
    mac = mac.strip().upper()
    
    # Check if already normalized
    if MAC_PATTERNS[0].match(mac):
        return mac
    
    # Try dash-separated
    if MAC_PATTERNS[1].match(mac):
        return mac.replace("-", ":")
    
    # Try no separator
    if MAC_PATTERNS[2].match(mac):
        return ":".join(mac[i:i+2] for i in range(0, 12, 2))
    
    return None


def is_valid_ipv4(ip: str) -> bool:
    """Check if string is a valid IPv4 address."""
    return bool(IP_PATTERN.match(ip.strip()))


def is_valid_mac(mac: str) -> bool:
    """Check if string is a valid MAC address (any format)."""
    return any(pattern.match(mac.strip()) for pattern in MAC_PATTERNS)


def detect_query_type(query: str) -> Literal["mac", "ip", "unknown"]:
    """
    Detect whether the query string is a MAC address, IP address, or unknown.
    
    Priority: MAC address takes precedence over IP address.
    """
    query = query.strip()
    
    # Check MAC first
    if is_valid_mac(query):
        return "mac"
    
    # Check IP
    if is_valid_ipv4(query):
        return "ip"
    
    return "unknown"


def normalize_client_response(client: dict) -> dict:
    """
    Normalize raw client data from Aruba API to consistent format.
    
    Handles field name variations: macaddr/mac, ip_address/ip, ap_name/ap, etc.
    """
    return {
        "mac_address": client.get("mac") or client.get("macaddr", ""),
        "ip_address": client.get("ip") or client.get("ip_address", ""),
        "hostname": client.get("hostname") or client.get("username") or "",
        "ap_name": client.get("ap_name") or client.get("ap", ""),
        "ssid": client.get("ssid") or client.get("essid", ""),
        "vlan": client.get("vlan") or 0,
        "data_rate_mbps": client.get("tx_rate") or client.get("txrate") or 0,
        "channel": client.get("channel") or 0,
        "rssi_dbm": client.get("rssi") or client.get("rssi_dbm") or 0,
        "status": client.get("status", "connected").lower(),
        "auth_type": client.get("authentication") or client.get("auth_type", ""),
        "band": client.get("band", ""),
        "last_seen": client.get("last_seen") or client.get("last_activity"),
        "uptime": client.get("uptime", 0),
    }