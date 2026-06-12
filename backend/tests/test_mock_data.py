"""Tests for mock data generators."""

import re

from app.models.client import ClientInfo
from app.models.ap import AccessPoint
from app.models.issue import Issue, IssueSeverity, IssueCategory
from app.models.common import TimeSeriesPoint
from app.services.mock_data import (
    generate_clients,
    generate_access_points,
    generate_issues,
    generate_rssi_timeseries,
)


MAC_REGEX = re.compile(r"^([0-9A-F]{2}:){5}[0-9A-F]{2}$")


class TestGenerateClients:
    def test_default_count(self):
        clients = generate_clients()
        assert len(clients) == 50

    def test_custom_count(self):
        clients = generate_clients(10)
        assert len(clients) == 10

    def test_all_are_client_info(self):
        clients = generate_clients(5)
        for c in clients:
            assert isinstance(c, ClientInfo)

    def test_mac_format_valid(self):
        clients = generate_clients(20)
        for c in clients:
            assert MAC_REGEX.match(c.mac), f"Invalid MAC format: {c.mac}"

    def test_weak_signal_clients_present(self):
        """Ensure edge case: clients with RSSI below -75 dBm threshold."""
        clients = generate_clients()
        weak = [c for c in clients if c.rssi_dbm < -75]
        assert len(weak) >= 5, f"Expected at least 5 weak clients, got {len(weak)}"

    def test_all_bands_valid(self):
        clients = generate_clients()
        for c in clients:
            assert c.band in ("2.4GHz", "5GHz"), f"Invalid band: {c.band}"

    def test_unique_macs(self):
        clients = generate_clients(50)
        macs = [c.mac for c in clients]
        assert len(set(macs)) == 50, "Client MACs should be unique"


class TestGenerateAccessPoints:
    def test_default_count(self):
        aps = generate_access_points()
        assert len(aps) == 10

    def test_custom_count(self):
        aps = generate_access_points(5)
        assert len(aps) == 5

    def test_all_are_ap(self):
        aps = generate_access_points(3)
        for ap in aps:
            assert isinstance(ap, AccessPoint)

    def test_high_utilization_aps_present(self):
        """Ensure edge case: APs with channel utilization above 80%."""
        aps = generate_access_points()
        overloaded = [a for a in aps if a.channel_utilization > 80]
        assert len(overloaded) >= 2, (
            f"Expected at least 2 high-utilization APs, got {len(overloaded)}"
        )

    def test_utilization_range(self):
        aps = generate_access_points()
        for ap in aps:
            assert 0 <= ap.channel_utilization <= 100, (
                f"Utilization out of range: {ap.channel_utilization}"
            )

    def test_ap_names_unique(self):
        aps = generate_access_points(10)
        names = [ap.name for ap in aps]
        assert len(set(names)) == 10


class TestGenerateIssues:
    def test_issues_generated(self):
        clients = generate_clients()
        aps = generate_access_points()
        issues = generate_issues(clients, aps)
        assert len(issues) >= 3

    def test_issues_are_issue_model(self):
        clients = generate_clients()
        aps = generate_access_points()
        issues = generate_issues(clients, aps)
        for issue in issues:
            assert isinstance(issue, Issue)

    def test_weak_signal_issue_exists(self):
        """Should have a LOW_RSSI issue because mock data includes weak clients."""
        clients = generate_clients()
        aps = generate_access_points()
        issues = generate_issues(clients, aps)
        rssi_issues = [i for i in issues if i.category == IssueCategory.LOW_RSSI]
        assert len(rssi_issues) >= 1, "Expected at least one LOW_RSSI issue"

    def test_high_utilization_issue_exists(self):
        """Should have a HIGH_CHANNEL_UTILIZATION issue because mock data has overloaded APs."""
        clients = generate_clients()
        aps = generate_access_points()
        issues = generate_issues(clients, aps)
        util_issues = [
            i for i in issues if i.category == IssueCategory.HIGH_CHANNEL_UTILIZATION
        ]
        assert len(util_issues) >= 1, (
            "Expected at least one HIGH_CHANNEL_UTILIZATION issue"
        )

    def test_affected_clients_are_macs(self):
        clients = generate_clients()
        aps = generate_access_points()
        issues = generate_issues(clients, aps)
        for issue in issues:
            for mac in issue.affected_clients:
                assert MAC_REGEX.match(mac), f"Invalid MAC in issue: {mac}"

    def test_severity_is_valid(self):
        clients = generate_clients()
        aps = generate_access_points()
        issues = generate_issues(clients, aps)
        for issue in issues:
            assert isinstance(issue.severity, IssueSeverity)


class TestGenerateRssiTimeseries:
    def test_returns_points(self):
        points = generate_rssi_timeseries("AA:BB:CC:DD:EE:FF")
        assert len(points) > 0

    def test_all_are_time_series_points(self):
        points = generate_rssi_timeseries("AA:BB:CC:DD:EE:FF", hours=0.5)
        for p in points:
            assert isinstance(p, TimeSeriesPoint)

    def test_custom_duration(self):
        points = generate_rssi_timeseries("AA:BB:CC:DD:EE:FF", hours=2)
        # 2 hours * 60 min * 2 points/min = 240
        assert len(points) == 240

    def test_rssi_in_valid_range(self):
        points = generate_rssi_timeseries("AA:BB:CC:DD:EE:FF")
        for p in points:
            assert -90 <= p.value <= -20, f"RSSI out of range: {p.value}"

    def test_deterministic_with_same_mac(self):
        """Same MAC should produce same RSSI values (fixed seed via hash)."""
        mac = "AA:BB:CC:DD:EE:FF"
        pts1 = generate_rssi_timeseries(mac, hours=0.5)
        pts2 = generate_rssi_timeseries(mac, hours=0.5)
        assert len(pts1) == len(pts2)
        for a, b in zip(pts1, pts2):
            assert a.value == b.value
            # Timestamps are relative to datetime.now(), so only values are deterministic

    def test_different_macs_differ(self):
        pts1 = generate_rssi_timeseries("AA:BB:CC:DD:EE:01", hours=0.5)
        pts2 = generate_rssi_timeseries("AA:BB:CC:DD:EE:02", hours=0.5)
        values1 = [p.value for p in pts1]
        values2 = [p.value for p in pts2]
        assert values1 != values2, "Different MACs should produce different series"


class TestDeterministicSeed:
    def test_clients_deterministic(self):
        c1 = generate_clients(10)
        c2 = generate_clients(10)
        for a, b in zip(c1, c2):
            assert a.mac == b.mac
            assert a.rssi_dbm == b.rssi_dbm

    def test_aps_deterministic(self):
        a1 = generate_access_points(5)
        a2 = generate_access_points(5)
        for a, b in zip(a1, a2):
            assert a.name == b.name
            assert a.channel_utilization == b.channel_utilization
