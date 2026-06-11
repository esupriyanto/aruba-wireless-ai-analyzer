"""
Rule-based wireless analyzer.

Evaluates clients and access points against configurable thresholds and
returns a list of detected issues.
"""

import logging
from datetime import datetime, timedelta

from backend.app.config import settings
from backend.app.models.ap import APStatus, AccessPoint
from backend.app.models.client import ClientInfo, ClientStatus
from backend.app.models.issue import (
    AlertListResponse,
    Issue,
    IssueCategory,
    IssueSeverity,
)

logger = logging.getLogger(__name__)

# Roaming loop detection: number of ROAMING status transitions within the
# window to consider a loop.
_ROAM_LOOP_THRESHOLD = 5
_ROAM_LOOP_WINDOW_MINUTES = 10


class Analyzer:
    """Stateless analyzer that checks clients and APs against thresholds.

    Parameters
    ----------
    rssi_threshold : int | None
        RSSI level (dBm) below which a client is considered "weak".
        Defaults to ``settings.app.alert_rssi_threshold``.
    channel_util_threshold : int | None
        Channel utilization percentage above which an AP is considered
        overloaded.  Defaults to ``settings.app.alert_channel_util_threshold``.
    """

    def __init__(
        self,
        rssi_threshold: int | None = None,
        channel_util_threshold: int | None = None,
    ) -> None:
        self.rssi_threshold = (
            rssi_threshold
            if rssi_threshold is not None
            else settings.app.alert_rssi_threshold
        )
        self.channel_util_threshold = (
            channel_util_threshold
            if channel_util_threshold is not None
            else settings.app.alert_channel_util_threshold
        )

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def analyze(
        self,
        clients: list[ClientInfo],
        aps: list[AccessPoint],
    ) -> AlertListResponse:
        """Run all rules and return detected issues as an AlertListResponse."""
        issues: list[Issue] = []
        issue_counter = 0

        # 1. Low RSSI detection
        low_rssi_issues = self._check_low_rssi(clients)
        for issue in low_rssi_issues:
            issue_counter += 1
            issue.id = f"ANA-{issue_counter:04d}"
            issues.append(issue)

        # 2. High channel utilization detection
        high_util_issues = self._check_high_channel_utilization(aps)
        for issue in high_util_issues:
            issue_counter += 1
            issue.id = f"ANA-{issue_counter:04d}"
            issues.append(issue)

        # 3. AP down detection
        ap_down_issues = self._check_ap_down(aps)
        for issue in ap_down_issues:
            issue_counter += 1
            issue.id = f"ANA-{issue_counter:04d}"
            issues.append(issue)

        # 4. Roaming loop detection
        roam_issues = self._check_roaming_loops(clients)
        for issue in roam_issues:
            issue_counter += 1
            issue.id = f"ANA-{issue_counter:04d}"
            issues.append(issue)

        logger.info("Analyzer: detected %d issue(s)", len(issues))
        return AlertListResponse(total=len(issues), alerts=issues)

    # ------------------------------------------------------------------
    # Individual rules
    # ------------------------------------------------------------------

    def _check_low_rssi(
        self, clients: list[ClientInfo]
    ) -> list[Issue]:
        """Flag clients whose RSSI is below the configured threshold."""
        weak = [c for c in clients if c.rssi_dbm < self.rssi_threshold]
        if not weak:
            return []

        severity = (
            IssueSeverity.CRITICAL
            if len(weak) > 10
            else IssueSeverity.HIGH
        )

        return [
            Issue(
                id="",  # filled by caller
                severity=severity,
                category=IssueCategory.LOW_RSSI,
                title=f"{len(weak)} client(s) with weak signal (RSSI < {self.rssi_threshold} dBm)",
                description=(
                    f"{len(weak)} clients have RSSI below the "
                    f"{self.rssi_threshold} dBm threshold. "
                    "This may cause poor connectivity and high retry rates."
                ),
                affected_clients=[c.mac for c in weak],
                affected_aps=sorted({c.ap_name for c in weak}),
                timestamp=datetime.now(),
                recommended_actions=[
                    "Increase AP transmit power in affected areas",
                    "Add APs to fill coverage gaps",
                    "Review client device roaming settings",
                ],
            )
        ]

    def _check_high_channel_utilization(
        self, aps: list[AccessPoint]
    ) -> list[Issue]:
        """Flag APs whose channel utilization exceeds the threshold."""
        overloaded = [
            a
            for a in aps
            if a.channel_utilization > self.channel_util_threshold
        ]
        if not overloaded:
            return []

        max_util = max(a.channel_utilization for a in overloaded)
        severity = (
            IssueSeverity.CRITICAL
            if max_util > 95
            else IssueSeverity.HIGH
        )

        return [
            Issue(
                id="",
                severity=severity,
                category=IssueCategory.HIGH_CHANNEL_UTILIZATION,
                title=(
                    f"{len(overloaded)} AP(s) with channel utilization "
                    f"> {self.channel_util_threshold}%"
                ),
                description=(
                    f"{len(overloaded)} access points have channel utilization "
                    f"above {self.channel_util_threshold}%. "
                    "This causes degraded performance for connected clients."
                ),
                affected_aps=[a.name for a in overloaded],
                timestamp=datetime.now(),
                recommended_actions=[
                    "Load-balance clients across bands",
                    "Reduce channel width",
                    "Add capacity in high-density areas",
                ],
            )
        ]

    def _check_ap_down(
        self, aps: list[AccessPoint]
    ) -> list[Issue]:
        """Flag APs that are not in UP status."""
        down = [a for a in aps if a.status != APStatus.UP]
        if not down:
            return []

        severity = IssueSeverity.CRITICAL

        return [
            Issue(
                id="",
                severity=severity,
                category=IssueCategory.GENERAL,
                title=f"{len(down)} AP(s) not in UP state",
                description=(
                    f"{len(down)} access points are reporting "
                    f"non-UP status: "
                    f"{', '.join(f'{a.name} ({a.status.value})' for a in down)}."
                ),
                affected_aps=[a.name for a in down],
                timestamp=datetime.now(),
                recommended_actions=[
                    "Verify AP power and network connectivity",
                    "Check controller for AP heartbeat failures",
                    "Reboot unresponsive APs if needed",
                ],
            )
        ]

    def _check_roaming_loops(
        self, clients: list[ClientInfo]
    ) -> list[Issue]:
        """Detect clients stuck in a roaming loop.

        A client is flagged when its current status is ROAMING (indicating
        ongoing roaming activity).  In a production system this would
        analyze historical transitions; with only a snapshot we treat the
        ROAMING status as a signal.
        """
        roaming = [
            c for c in clients if c.status == ClientStatus.ROAMING
        ]
        if not roaming:
            return []

        return [
            Issue(
                id="",
                severity=IssueSeverity.MEDIUM,
                category=IssueCategory.ROAMING_ISSUE,
                title=f"{len(roaming)} client(s) currently roaming",
                description=(
                    f"{len(roaming)} clients are in ROAMING state, "
                    "which may indicate a roaming loop or coverage overlap issue."
                ),
                affected_clients=[c.mac for c in roaming],
                affected_aps=sorted({c.ap_name for c in roaming}),
                timestamp=datetime.now(),
                recommended_actions=[
                    "Check for excessive AP overlap in roaming zones",
                    "Review client 802.11k/v/r settings",
                    "Adjust AP power to reduce roaming domain size",
                ],
            )
        ]
