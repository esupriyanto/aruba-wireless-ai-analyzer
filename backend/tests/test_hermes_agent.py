"""Tests for the Hermes Agent service."""

import pytest

from app.services.hermes_agent import HermesAgent


@pytest.fixture
def sample_issue() -> dict:
    return {
        "id": "issue-001",
        "severity": "critical",
        "category": "low_rssi",
        "title": "Weak signal on AP-001",
        "description": "Client RSSI below -75 dBm",
        "affected_clients": ["aa:bb:cc:dd:ee:01", "aa:bb:cc:dd:ee:02"],
        "affected_aps": ["AP-001"],
    }


class TestHermesAgentMockDiagnose:
    """Tests for HermesAgent.diagnose() in mock mode."""

    def test_returns_dict_with_required_keys(self, sample_issue):
        agent = HermesAgent(mock_mode=True)
        import asyncio

        result = asyncio.get_event_loop().run_until_complete(
            agent.diagnose(sample_issue)
        )
        assert "analysis" in result
        assert "root_cause" in result
        assert "impact" in result
        assert "recommendation" in result

    def test_mock_flag_set(self, sample_issue):
        agent = HermesAgent(mock_mode=True)
        import asyncio

        result = asyncio.get_event_loop().run_until_complete(
            agent.diagnose(sample_issue)
        )
        assert result.get("mock") is True

    def test_analysis_contains_title(self, sample_issue):
        agent = HermesAgent(mock_mode=True)
        import asyncio

        result = asyncio.get_event_loop().run_until_complete(
            agent.diagnose(sample_issue)
        )
        assert sample_issue["title"] in result["analysis"]

    def test_critical_severity_mention(self, sample_issue):
        agent = HermesAgent(mock_mode=True)
        import asyncio

        result = asyncio.get_event_loop().run_until_complete(
            agent.diagnose(sample_issue)
        )
        assert "CRITICAL" in result["analysis"] or "critical" in result["analysis"].lower()

    def test_low_rssi_root_cause(self, sample_issue):
        agent = HermesAgent(mock_mode=True)
        import asyncio

        result = asyncio.get_event_loop().run_until_complete(
            agent.diagnose(sample_issue)
        )
        assert "far from AP" in result["root_cause"] or "obstruction" in result["root_cause"]

    def test_with_context(self, sample_issue):
        agent = HermesAgent(mock_mode=True)
        import asyncio

        ctx = {"adjacent_aps": ["AP-002", "AP-003"]}
        result = asyncio.get_event_loop().run_until_complete(
            agent.diagnose(sample_issue, ctx)
        )
        assert "analysis" in result


class TestHermesAgentMockExecute:
    """Tests for HermesAgent.execute_remediation() in mock mode."""

    def test_returns_accepted_status(self):
        agent = HermesAgent(mock_mode=True)
        import asyncio

        result = asyncio.get_event_loop().run_until_complete(
            agent.execute_remediation(["restart_ap"], "AP-001")
        )
        assert result["status"] == "accepted"

    def test_actions_preserved(self):
        agent = HermesAgent(mock_mode=True)
        import asyncio

        actions = ["restart_ap", "adjust_power"]
        result = asyncio.get_event_loop().run_until_complete(
            agent.execute_remediation(actions, "AP-001")
        )
        assert result["actions_executed"] == actions

    def test_target_in_message(self):
        agent = HermesAgent(mock_mode=True)
        import asyncio

        result = asyncio.get_event_loop().run_until_complete(
            agent.execute_remediation(["restart_ap"], "AP-001")
        )
        assert "AP-001" in result["message"]

    def test_mock_flag_set(self):
        agent = HermesAgent(mock_mode=True)
        import asyncio

        result = asyncio.get_event_loop().run_until_complete(
            agent.execute_remediation(["restart_ap"], "AP-001")
        )
        assert result.get("mock") is True

    def test_no_target(self):
        agent = HermesAgent(mock_mode=True)
        import asyncio

        result = asyncio.get_event_loop().run_until_complete(
            agent.execute_remediation(["kick_client"], None)
        )
        assert result["status"] == "accepted"
