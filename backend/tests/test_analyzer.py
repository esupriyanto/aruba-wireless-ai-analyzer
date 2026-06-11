"""Tests for Analyzer — crafted inputs that trigger every rule."""

import pytest

from backend.app.services.analyzer import Analyzer
from backend.app.models.client import ClientInfo, ClientStatus
from backend.app.models.ap import AccessPoint, APStatus
from backend.app.models.issue import (
    AlertListResponse,
    IssueCategory,
    IssueSeverity,
)


# ------------------------------------------------------------------
# Helpers — hand-crafted objects that exceed thresholds
# ------------------------------------------------------------------


def _weak_client(mac: str = "AA:00:00:00:00:01", **overrides) -> ClientInfo:
    """Client with RSSI well below -75 dBm."""
    defaults = dict(
        mac=mac,
        ip="10.0.1.50",
        ssid="CorpWiFi",
        ap_name="AP-001",
        band="5GHz",
        channel=36,
        rssi_dbm=-85.0,
        snr=15.0,
        tx_rate=54.0,
        rx_rate=54.0,
    )
    defaults.update(overrides)
    return ClientInfo(**defaults)


def _normal_client(mac: str = "AA:00:00:00:00:10", **overrides) -> ClientInfo:
    """Client with healthy RSSI."""
    defaults = dict(
        mac=mac,
        ip="10.0.1.60",
        ssid="CorpWiFi",
        ap_name="AP-002",
        band="5GHz",
        channel=36,
        rssi_dbm=-42.0,
        snr=35.0,
        tx_rate=300.0,
        rx_rate=300.0,
    )
    defaults.update(overrides)
    return ClientInfo(**defaults)


def _roaming_client(mac: str = "AA:00:00:00:00:20", **overrides) -> ClientInfo:
    """Client in ROAMING status."""
    defaults = dict(
        mac=mac,
        ip="10.0.1.70",
        ssid="CorpWiFi",
        ap_name="AP-003",
        band="2.4GHz",
        channel=6,
        rssi_dbm=-55.0,
        snr=25.0,
        tx_rate=54.0,
        rx_rate=54.0,
        status=ClientStatus.ROAMING,
    )
    defaults.update(overrides)
    return ClientInfo(**defaults)


def _overloaded_ap(name: str = "AP-100", **overrides) -> AccessPoint:
    """AP with channel utilization above 80%."""
    defaults = dict(
        name=name,
        model="AP-515",
        serial="AP999001",
        ip_address="10.0.0.100",
        channel_utilization=92.0,
        tx_power=17.0,
        band="dual-band",
    )
    defaults.update(overrides)
    return AccessPoint(**defaults)


def _normal_ap(name: str = "AP-200", **overrides) -> AccessPoint:
    """AP with normal utilization."""
    defaults = dict(
        name=name,
        model="AP-515",
        serial="AP999002",
        ip_address="10.0.0.200",
        channel_utilization=35.0,
        tx_power=14.0,
        band="5GHz",
    )
    defaults.update(overrides)
    return AccessPoint(**defaults)


def _down_ap(name: str = "AP-300", **overrides) -> AccessPoint:
    """AP in DOWN status."""
    defaults = dict(
        name=name,
        model="AP-515",
        serial="AP999003",
        ip_address="10.0.0.201",
        status=APStatus.DOWN,
        channel_utilization=0.0,
        tx_power=0.0,
        band="5GHz",
    )
    defaults.update(overrides)
    return AccessPoint(**defaults)


# ------------------------------------------------------------------
# Tests
# ------------------------------------------------------------------


class TestAnalyzerLowRSSI:
    def test_weak_clients_detected(self):
        analyzer = Analyzer(rssi_threshold=-75)
        clients = [_weak_client(), _weak_client(mac="AA:00:00:00:00:02")]
        result = analyzer.analyze(clients, aps=[])
        assert isinstance(result, AlertListResponse)
        low_rssi = [
            a for a in result.alerts if a.category == IssueCategory.LOW_RSSI
        ]
        assert len(low_rssi) == 1
        assert low_rssi[0].severity == IssueSeverity.HIGH
        assert len(low_rssi[0].affected_clients) == 2

    def test_critical_when_many_weak(self):
        analyzer = Analyzer(rssi_threshold=-75)
        clients = [_weak_client(mac=f"AA:00:00:00:{i:02X}:01") for i in range(12)]
        result = analyzer.analyze(clients, aps=[])
        low_rssi = [
            a for a in result.alerts if a.category == IssueCategory.LOW_RSSI
        ]
        assert low_rssi[0].severity == IssueSeverity.CRITICAL

    def test_no_weak_clients_no_alert(self):
        analyzer = Analyzer(rssi_threshold=-75)
        clients = [_normal_client(), _normal_client(mac="AA:00:00:00:00:11")]
        result = analyzer.analyze(clients, aps=[])
        low_rssi = [
            a for a in result.alerts if a.category == IssueCategory.LOW_RSSI
        ]
        assert len(low_rssi) == 0

    def test_borderline_rssi_not_flagged(self):
        analyzer = Analyzer(rssi_threshold=-75)
        clients = [_normal_client(rssi_dbm=-75.0)]
        result = analyzer.analyze(clients, aps=[])
        low_rssi = [
            a for a in result.alerts if a.category == IssueCategory.LOW_RSSI
        ]
        assert len(low_rssi) == 0


class TestAnalyzerHighChannelUtilization:
    def test_overloaded_ap_detected(self):
        analyzer = Analyzer(channel_util_threshold=80)
        aps = [_overloaded_ap()]
        result = analyzer.analyze(clients=[], aps=aps)
        high_util = [
            a
            for a in result.alerts
            if a.category == IssueCategory.HIGH_CHANNEL_UTILIZATION
        ]
        assert len(high_util) == 1
        assert "AP-100" in high_util[0].affected_aps

    def test_critical_when_extreme_utilization(self):
        analyzer = Analyzer(channel_util_threshold=80)
        aps = [_overloaded_ap(channel_utilization=98.0)]
        result = analyzer.analyze(clients=[], aps=aps)
        high_util = [
            a
            for a in result.alerts
            if a.category == IssueCategory.HIGH_CHANNEL_UTILIZATION
        ]
        assert high_util[0].severity == IssueSeverity.CRITICAL

    def test_normal_utilization_no_alert(self):
        analyzer = Analyzer(channel_util_threshold=80)
        aps = [_normal_ap()]
        result = analyzer.analyze(clients=[], aps=aps)
        high_util = [
            a
            for a in result.alerts
            if a.category == IssueCategory.HIGH_CHANNEL_UTILIZATION
        ]
        assert len(high_util) == 0

    def test_exact_threshold_not_flagged(self):
        analyzer = Analyzer(channel_util_threshold=80)
        aps = [_normal_ap(channel_utilization=80.0)]
        result = analyzer.analyze(clients=[], aps=aps)
        high_util = [
            a
            for a in result.alerts
            if a.category == IssueCategory.HIGH_CHANNEL_UTILIZATION
        ]
        assert len(high_util) == 0


class TestAnalyzerAPDown:
    def test_down_ap_detected(self):
        analyzer = Analyzer()
        aps = [_down_ap()]
        result = analyzer.analyze(clients=[], aps=aps)
        ap_down = [
            a for a in result.alerts if a.category == IssueCategory.GENERAL
        ]
        assert len(ap_down) == 1
        assert ap_down[0].severity == IssueSeverity.CRITICAL
        assert "AP-300" in ap_down[0].affected_aps

    def test_degraded_ap_detected(self):
        analyzer = Analyzer()
        aps = [_normal_ap(status=APStatus.DEGRADED)]
        result = analyzer.analyze(clients=[], aps=aps)
        ap_down = [
            a for a in result.alerts if a.category == IssueCategory.GENERAL
        ]
        assert len(ap_down) == 1

    def test_all_up_no_alert(self):
        analyzer = Analyzer()
        aps = [_normal_ap(), _normal_ap(name="AP-201")]
        result = analyzer.analyze(clients=[], aps=aps)
        ap_down = [
            a for a in result.alerts if a.category == IssueCategory.GENERAL
        ]
        assert len(ap_down) == 0


class TestAnalyzerRoamingLoops:
    def test_roaming_client_detected(self):
        analyzer = Analyzer()
        clients = [_roaming_client()]
        result = analyzer.analyze(clients, aps=[])
        roaming = [
            a
            for a in result.alerts
            if a.category == IssueCategory.ROAMING_ISSUE
        ]
        assert len(roaming) == 1
        assert roaming[0].severity == IssueSeverity.MEDIUM

    def test_no_roaming_no_alert(self):
        analyzer = Analyzer()
        clients = [_normal_client()]
        result = analyzer.analyze(clients, aps=[])
        roaming = [
            a
            for a in result.alerts
            if a.category == IssueCategory.ROAMING_ISSUE
        ]
        assert len(roaming) == 0


class TestAnalyzerCombined:
    def test_multiple_issues_detected(self):
        """All four rules fire on mixed input."""
        analyzer = Analyzer(rssi_threshold=-75, channel_util_threshold=80)
        clients = [
            _weak_client(),
            _weak_client(mac="AA:00:00:00:00:02"),
            _roaming_client(),
            _normal_client(),
        ]
        aps = [_overloaded_ap(), _down_ap(), _normal_ap()]
        result = analyzer.analyze(clients, aps)

        categories = {a.category for a in result.alerts}
        assert IssueCategory.LOW_RSSI in categories
        assert IssueCategory.HIGH_CHANNEL_UTILIZATION in categories
        assert IssueCategory.GENERAL in categories
        assert IssueCategory.ROAMING_ISSUE in categories
        assert result.total == 4

    def test_issue_ids_sequential(self):
        analyzer = Analyzer(rssi_threshold=-75, channel_util_threshold=80)
        clients = [_weak_client()]
        aps = [_overloaded_ap()]
        result = analyzer.analyze(clients, aps)
        ids = [a.id for a in result.alerts]
        assert ids == ["ANA-0001", "ANA-0002"]


class TestAnalyzerCustomThresholds:
    def test_custom_rssi_threshold(self):
        """Analyzer respects a non-default threshold."""
        analyzer = Analyzer(rssi_threshold=-60)
        # Client at -65 is above -75 default but below custom -60
        clients = [_normal_client(rssi_dbm=-65.0)]
        result = analyzer.analyze(clients, aps=[])
        low_rssi = [
            a for a in result.alerts if a.category == IssueCategory.LOW_RSSI
        ]
        assert len(low_rssi) == 1

    def test_custom_channel_util_threshold(self):
        analyzer = Analyzer(channel_util_threshold=50)
        aps = [_normal_ap(channel_utilization=60.0)]
        result = analyzer.analyze(clients=[], aps=aps)
        high_util = [
            a
            for a in result.alerts
            if a.category == IssueCategory.HIGH_CHANNEL_UTILIZATION
        ]
        assert len(high_util) == 1
