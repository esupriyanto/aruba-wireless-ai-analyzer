import { useState, useCallback } from 'react'
import axios from 'axios'

const API = '/api/v1'

export function useHermes() {
  const [response, setResponse] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const analyze = useCallback(async (issue) => {
    setLoading(true)
    setError(null)
    try {
      // Call the remediation analyze endpoint which runs the analyzer
      const alertsRes = await axios.get(`${API}/events/alerts`)
      const alerts = alertsRes.data.alerts || []
      const matched = issue
        ? alerts.filter((a) => a.id === issue.id)
        : alerts

      if (matched.length === 0) {
        setResponse({
          analysis: 'No matching issues found.',
          root_cause: 'N/A',
          impact: 'N/A',
          recommendation: 'Run analysis first.',
        })
        return
      }

      // Mock AI diagnosis (Phase 6 — real Hermes integration)
      const issueData = matched[0]
      const result = await mockDiagnose(issueData)
      setResponse(result)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  const execute = useCallback(async (issueId, action = 'restart_ap') => {
    setLoading(true)
    setError(null)
    try {
      const res = await axios.post(`${API}/remediation/execute`, {
        issue_id: issueId,
        action,
      })
      setResponse(res.data)
      return res.data
    } catch (err) {
      setError(err.message)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  return { response, loading, error, analyze, execute }
}

// Mock diagnosis — simulates Hermes Agent response
async function mockDiagnose(issue) {
  // Simulate network delay
  await new Promise((r) => setTimeout(r, 800))

  const rootCauseMap = {
    low_rssi: 'Clients are far from AP or experiencing physical obstruction / interference.',
    high_channel_utilization: 'Too many clients on the same channel, causing airtime congestion.',
    ap_down: 'Access point lost connectivity — possible hardware failure or power loss.',
    roaming_loop: 'Client oscillating between APs due to poor roaming configuration.',
  }

  const recommendationMap = {
    low_rssi: 'Consider relocating AP, adjusting Tx power, or removing obstruction.',
    high_channel_utilization: 'Enable band steering, reduce channel width, or add capacity.',
    ap_down: 'Check PoE switch port, power cycle AP, verify uplink connectivity.',
    roaming_loop: 'Review FT/802.11r settings, adjust RSSI thresholds.',
  }

  return {
    analysis: `[${issue.severity.toUpperCase()}] ${issue.title} — ${issue.description}`,
    root_cause: rootCauseMap[issue.category] || 'Unknown root cause — requires investigation.',
    impact: `Affects ${issue.affected_clients?.length || 0} client(s) and ${issue.affected_aps?.length || 0} AP(s).`,
    recommendation: recommendationMap[issue.category] || 'Investigate further with site survey.',
  }
}
