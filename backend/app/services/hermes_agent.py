"""Hermes Agent service — AI-powered diagnosis and remediation."""

from __future__ import annotations

import json
from typing import Any

import httpx

from app.config import settings as _settings_obj

_SETTINGS = _settings_obj


class HermesAgent:
    """Talks to the Hermes AI Agent for wireless diagnosis and remediation.

    In *mock* mode (default, when no API key is configured) the agent
    returns canned analysis text so the rest of the stack can be tested
    end-to-end without a live LLM.
    """

    def __init__(self, *, mock_mode: bool | None = None) -> None:
        cfg = _settings_obj
        self._mock_mode = mock_mode if mock_mode is not None else cfg.mock_mode
        self._base_url = cfg.hermes.agent_url
        self._api_key = cfg.hermes.api_key
        self._model = cfg.llm.model

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def diagnose(
        self,
        issue: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Analyse a detected wireless issue and return AI recommendations.

        Parameters
        ----------
        issue:
            A single alert/issue dict  (as produced by the Analyzer).
        context:
            Optional extra context — e.g. adjacent AP stats, recent events.

        Returns
        -------
        dict with keys: analysis, root_cause, impact, recommendation
        """
        if self._mock_mode:
            return self._mock_diagnose(issue, context)

        prompt = self._build_diagnosis_prompt(issue, context)
        return await self._call_llm(prompt)

    async def execute_remediation(
        self,
        actions: list[str],
        target: str | None = None,
    ) -> dict[str, Any]:
        """Request Hermes to execute remediation actions.

        Parameters
        ----------
        actions:
            Ordered list of remediation steps (e.g. ["restart_ap", "adjust_power"]).
        target:
            Optional target identifier (AP name, client MAC, …).

        Returns
        -------
        dict with keys: status, message, actions_executed
        """
        if self._mock_mode:
            return self._mock_execute(actions, target)

        prompt = self._build_remediation_prompt(actions, target)
        return await self._call_llm(prompt)

    # ------------------------------------------------------------------
    # Mock helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _mock_diagnose(
        issue: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        issue_id = issue.get("id", "unknown")
        title = issue.get("title", "Unknown issue")
        severity = issue.get("severity", "medium")
        affected_clients = issue.get("affected_clients", [])
        affected_aps = issue.get("affected_aps", [])

        analysis = (
            f"[{severity.upper()}] {title} (ID: {issue_id}). "
            f"Affected clients: {len(affected_clients)}, "
            f"affected APs: {len(affected_aps)}."
        )

        root_cause_map: dict[str, str] = {
            "low_rssi": "Clients are far from AP or experiencing physical obstruction / interference.",
            "high_channel_utilization": "Too many clients on the same channel, causing airtime congestion.",
            "ap_down": "Access point lost connectivity — possible hardware failure, power loss, or uplink issue.",
            "roaming_loop": "Client oscillating between APs due to poor roaming configuration or overlapping coverage.",
        }

        category = issue.get("category", "")
        root_cause = root_cause_map.get(
            category,
            "Unknown root cause — requires manual investigation.",
        )

        impact = (
            f"User experience degraded for {len(affected_clients)} client(s). "
            "If left unresolved, may lead to full disconnection."
            if severity in ("critical", "high")
            else "Moderate impact — monitor for escalation."
        )

        recommendation_map: dict[str, str] = {
            "low_rssi": "Consider relocating AP, adjusting Tx power, or removing physical obstruction.",
            "high_channel_utilization": "Enable band steering, reduce channel width, or add capacity.",
            "ap_down": "Check PoE switch port, power cycle AP, verify uplink connectivity.",
            "roaming_loop": "Review FT/802.11r settings, adjust RSSI thresholds for roaming.",
        }
        recommendation = recommendation_map.get(
            category,
            "Investigate further with site survey or packet capture.",
        )

        return {
            "analysis": analysis,
            "root_cause": root_cause,
            "impact": impact,
            "recommendation": recommendation,
            "mock": True,
        }

    @staticmethod
    def _mock_execute(
        actions: list[str],
        target: str | None,
    ) -> dict[str, Any]:
        target_str = target or "network"
        return {
            "status": "accepted",
            "message": f"Remediation queued for {target_str}: {', '.join(actions)}",
            "actions_executed": actions,
            "target": target_str,
            "mock": True,
        }

    # ------------------------------------------------------------------
    # LLM helpers (real mode)
    # ------------------------------------------------------------------

    def _build_diagnosis_prompt(
        self,
        issue: dict[str, Any],
        context: dict[str, Any] | None,
    ) -> str:
        parts = [
            "You are a senior Aruba wireless network engineer.\n",
            f"ISSUE:\n{json.dumps(issue, indent=2, default=str)}",
        ]
        if context:
            parts.append(f"\nCONTEXT:\n{json.dumps(context, indent=2, default=str)}")
        parts.append(
            "\nRespond in this format:\n"
            "Diagnosis: <one sentence>\n"
            "Root Cause: <one sentence>\n"
            "Impact: <one sentence>\n"
            "Recommendation: <one sentence>"
        )
        return "\n".join(parts)

    def _build_remediation_prompt(
        self,
        actions: list[str],
        target: str | None,
    ) -> str:
        return (
            f"Execute the following remediation actions on {target or 'the network'}:\n"
            + "\n".join(f"- {a}" for a in actions)
            + "\nRespond with a confirmation summary."
        )

    async def _call_llm(self, prompt: str) -> dict[str, Any]:
        """Send prompt to the configured LLM endpoint and parse the response."""
        if not self._api_key:
            raise RuntimeError("hermes_api_key not configured")

        async with httpx.AsyncClient(timeout=30) as http:
            resp = await http.post(
                f"{self._base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self._model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.2,
                    "max_tokens": 2048,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            content: str = data["choices"][0]["message"]["content"]
            # Try to parse structured output
            result: dict[str, Any] = {"raw": content}
            for line in content.splitlines():
                line = line.strip()
                if line.lower().startswith("diagnosis:"):
                    result["analysis"] = line.split(":", 1)[1].strip()
                elif line.lower().startswith("root cause:"):
                    result["root_cause"] = line.split(":", 1)[1].strip()
                elif line.lower().startswith("impact:"):
                    result["impact"] = line.split(":", 1)[1].strip()
                elif line.lower().startswith("recommendation:"):
                    result["recommendation"] = line.split(":", 1)[1].strip()
            return result
