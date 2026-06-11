"""
Mock data generators for development and testing.

Uses fixed seed (42) for deterministic output.
Includes edge cases: clients with RSSI < -75 dBm, APs with utilization > 80%.
"""

import random
from datetime import datetime, timedelta

from backend.app.models.client import ClientInfo, ClientStatus
from backend.app.models.ap import AccessPoint, APStatus
from backend.app.models.issue import Issue, IssueSeverity, IssueCategory
from backend.app.models.common import TimeSeriesPoint


def _random_mac(rng: random.Random) -> str:
    """Generate a random MAC address in colon-separated format."""
    parts = [f"{rng.randint(0, 255):02X}" for _ in range(6)]
    return ":".join(parts)


def generate_clients(count: int = 50) -> list[ClientInfo]:
    """
    Generate a list of mock wireless clients.

    Ensures some clients have RSSI below the alert threshold (-75 dBm).
    """
    rng = random.Random(42)

    ssids = ["CorpWiFi", "GuestNet", "IoT-Devices", "Lab-SSID"]
    bands = ["2.4GHz", "5GHz"]
    auth_types = ["WPA2-Enterprise", "WPA2-PSK", "Open", "WPA3-SAE"]
    statuses = list(ClientStatus)

    clients = []
    for i in range(count):
        band = rng.choice(bands)
        # Normal RSSI range with some weak clients (edge case: below -75 dBm)
        if i < 8:
            # First 8 clients are weak signal (edge case)
            rssi = rng.uniform(-90, -76)
        elif i < 15:
            # Next 7 clients are borderline
            rssi = rng.uniform(-76, -72)
        else:
            # Rest are normal signal
            rssi = rng.uniform(-65, -35)

        snr = max(0, rssi + rng.uniform(20, 40))

        client = ClientInfo(
            mac=_random_mac(rng),
            ip=f"10.0.{rng.randint(1, 10)}.{rng.randint(1, 254)}",
            ssid=rng.choice(ssids),
            ap_name=f"AP-{rng.randint(1, 10):03d}",
            band=band,
            channel=rng.randint(1, 11) if band == "2.4GHz" else rng.randint(36, 165),
            rssi_dbm=round(rssi, 1),
            snr=round(snr, 1),
            tx_rate=rng.choice([6.0, 12.0, 24.0, 54.0, 72.2, 150.0, 300.0]),
            rx_rate=rng.choice([6.0, 12.0, 24.0, 54.0, 72.2, 150.0, 300.0]),
            vlan=rng.choice([100, 200, 300, None]),
            role=rng.choice(["employee", "contractor", "guest", None]),
            username=f"user{i:03d}@corp.local" if rng.random() > 0.3 else None,
            status=rng.choice(statuses),
            auth_type=rng.choice(auth_types),
            last_activity=datetime.now() - timedelta(minutes=rng.randint(0, 120)),
            uptime_seconds=rng.randint(0, 86400),
        )
        clients.append(client)

    return clients


def generate_access_points(count: int = 10) -> list[AccessPoint]:
    """
    Generate a list of mock access points.

    Ensures some APs have channel utilization above 80% (edge case).
    """
    rng = random.Random(42)

    models = ["AP-505", "AP-515", "AP-535", "AP-555", "AP-303", "AP-365"]
    statuses = list(APStatus)

    aps = []
    for i in range(count):
        band = "dual-band" if i < 6 else rng.choice(["2.4GHz", "5GHz"])

        # Normal utilization with some high-utilization APs (edge case)
        if i < 3:
            # First 3 APs are overloaded (edge case)
            channel_util = rng.uniform(81, 98)
        elif i < 5:
            # Next 2 are borderline
            channel_util = rng.uniform(75, 82)
        else:
            # Rest are normal
            channel_util = rng.uniform(15, 65)

        ap = AccessPoint(
            name=f"AP-{i + 1:03d}",
            model=rng.choice(models),
            serial=f"AP{rng.randint(100000, 999999)}",
            ip_address=f"10.0.0.{rng.randint(10, 250)}",
            status=rng.choice(statuses),
            group=rng.choice(["Building-A", "Building-B", "Building-C"]),
            site=rng.choice(["HQ", "Branch-1", "Branch-2"]),
            client_count=rng.randint(0, 45),
            channel_utilization=round(channel_util, 1),
            tx_power=round(rng.uniform(8.0, 23.0), 1),
            band=band,
            channel=rng.randint(1, 11) if "2.4" in band else rng.randint(36, 165),
            frequency_mhz=rng.choice([2412, 2437, 2462, 5180, 5240, 5745]),
            uptime_seconds=rng.randint(3600, 2592000),
            firmware_version=rng.choice(["8.10.0.10", "8.11.0.0", "10.5.1.0"]),
            last_reboot=datetime.now() - timedelta(hours=rng.randint(1, 720)),
        )
        aps.append(ap)

    return aps


def generate_issues(
    clients: list[ClientInfo], aps: list[AccessPoint]
) -> list[Issue]:
    """
    Generate issues based on the provided clients and APs.

    Creates issues for weak-signal clients and overloaded APs.
    """
    rng = random.Random(42)

    issues: list[Issue] = []
    issue_id = 1

    # Find clients with low RSSI
    weak_clients = [c for c in clients if c.rssi_dbm < -75]
    if weak_clients:
        issues.append(
            Issue(
                id=f"ISS-{issue_id:04d}",
                severity=IssueSeverity.HIGH,
                category=IssueCategory.LOW_RSSI,
                title=f"{len(weak_clients)} clients with weak signal",
                description=(
                    f"{len(weak_clients)} clients have RSSI below -75 dBm threshold. "
                    "Consider moving APs closer or increasing transmit power."
                ),
                affected_clients=[c.mac for c in weak_clients[:10]],
                affected_aps=list({c.ap_name for c in weak_clients}),
                timestamp=datetime.now() - timedelta(minutes=5),
                resolved=False,
                ai_analysis="Weak signal coverage detected in overlapping zones.",
                recommended_actions=[
                    "Increase AP transmit power in affected areas",
                    "Add additional APs for coverage gap",
                ],
            )
        )
        issue_id += 1

    # Find APs with high channel utilization
    overloaded_aps = [a for a in aps if a.channel_utilization > 80]
    if overloaded_aps:
        issues.append(
            Issue(
                id=f"ISS-{issue_id:04d}",
                severity=IssueSeverity.CRITICAL,
                category=IssueCategory.HIGH_CHANNEL_UTILIZATION,
                title=f"{len(overloaded_aps)} APs with high channel utilization",
                description=(
                    f"{len(overloaded_aps)} access points have channel utilization "
                    "above 80%. This may cause degraded performance."
                ),
                affected_aps=[a.name for a in overloaded_aps],
                timestamp=datetime.now() - timedelta(minutes=2),
                resolved=False,
                ai_analysis="Channel congestion detected in high-density areas.",
                recommended_actions=[
                    "Load-balance clients across 5GHz band",
                    "Reduce channel width on congested channels",
                    "Consider adding additional APs for capacity",
                ],
            )
        )
        issue_id += 1

    # Add a few generic issues
    issues.append(
        Issue(
            id=f"ISS-{issue_id:04d}",
            severity=IssueSeverity.MEDIUM,
            category=IssueCategory.CLIENT_DISCONNECT,
            title="Intermittent client disconnections",
            description="Several clients experiencing periodic disconnections.",
            affected_clients=[clients[0].mac] if clients else [],
            timestamp=datetime.now() - timedelta(minutes=15),
            resolved=False,
            recommended_actions=["Check AP firmware version", "Review DHCP lease times"],
        )
    )
    issue_id += 1

    issues.append(
        Issue(
            id=f"ISS-{issue_id:04d}",
            severity=IssueSeverity.LOW,
            category=IssueCategory.ROAMING_ISSUE,
            title="Sticky client detected",
            description="Client not roaming to closest AP.",
            affected_clients=[clients[1].mac] if clients else [],
            affected_aps=[aps[0].name] if aps else [],
            timestamp=datetime.now() - timedelta(minutes=30),
            resolved=True,
        )
    )

    return issues


def generate_rssi_timeseries(
    mac: str, hours: float = 1, points_per_minute: int = 2
) -> list[TimeSeriesPoint]:
    """
    Generate RSSI time series data for a given client MAC.

    Args:
        mac: Client MAC address.
        hours: Duration in hours.
        points_per_minute: How many data points per minute.

    Returns:
        List of TimeSeriesPoint with RSSI values.
    """
    rng = random.Random(hash(mac) + 42)

    total_points = int(hours * 60 * points_per_minute)
    interval = timedelta(seconds=60 / points_per_minute)
    start = datetime.now() - timedelta(hours=hours)

    # Base RSSI with slight random walk
    base_rssi = rng.uniform(-60, -45)
    points: list[TimeSeriesPoint] = []

    for i in range(total_points):
        # Random walk with mean reversion
        base_rssi += rng.gauss(0, 2)
        base_rssi = max(-90, min(-20, base_rssi))
        # Mean reversion toward -50
        base_rssi += (-50 - base_rssi) * 0.02

        points.append(
            TimeSeriesPoint(
                timestamp=start + interval * i,
                value=round(base_rssi, 1),
                label="rssi_dbm",
            )
        )

    return points
