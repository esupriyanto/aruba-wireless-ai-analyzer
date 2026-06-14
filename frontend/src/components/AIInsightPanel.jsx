import { useState } from 'react'
import { useHermes } from '../hooks/useHermes'

const API = '/api/v1'

const RISK_STYLES = {
  low:    { bg: '#1e293b', color: '#94a3b8', border: '#334155' },
  medium: { bg: '#451a03', color: '#fbbf24', border: '#78350f' },
  high:   { bg: '#450a0a', color: '#f87171', border: '#7f1d1d' },
}

function ActionButton({ action, label, risk, icon, onExecute }) {
  const [loading, setLoading] = useState(false)
  const [feedback, setFeedback] = useState(null) // 'success' | 'error' | null
  const style = RISK_STYLES[risk] || RISK_STYLES.low

  const handleClick = async () => {
    if (risk === 'high') {
      const confirmed = window.confirm(
        `⚠️ High-risk action: ${label}\n\nAre you sure you want to proceed? This may impact active clients.`
      )
      if (!confirmed) return
    }

    setLoading(true)
    setFeedback(null)
    try {
      await onExecute(action)
      setFeedback('success')
      setTimeout(() => setFeedback(null), 3000)
    } catch (err) {
      setFeedback('error')
      setTimeout(() => setFeedback(null), 3000)
    } finally {
      setLoading(false)
    }
  }

  const feedbackBg = feedback === 'success' ? '#052e16' : feedback === 'error' ? '#450a0a' : style.bg
  const feedbackColor = feedback === 'success' ? '#4ade80' : feedback === 'error' ? '#f87171' : style.color
  const feedbackBorder = feedback === 'success' ? '#166534' : feedback === 'error' ? '#7f1d1d' : style.border

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
      <button
        onClick={handleClick}
        disabled={loading}
        style={{
          padding: '0.5rem 0.85rem',
          borderRadius: '6px',
          border: `1px solid ${feedbackBorder}`,
          background: feedbackBg,
          color: feedbackColor,
          cursor: loading ? 'wait' : 'pointer',
          fontSize: '0.8rem',
          fontWeight: '600',
          display: 'flex',
          alignItems: 'center',
          gap: '0.4rem',
          opacity: loading ? 0.7 : 1,
          transition: 'all 0.2s',
        }}
      >
        {loading ? '⏳' : icon} {label}
        {risk === 'high' && <span style={{ fontSize: '0.65rem', marginLeft: '2px' }}>⚠️</span>}
        {risk === 'medium' && <span style={{ fontSize: '0.65rem', marginLeft: '2px' }}>⚡</span>}
      </button>
      {feedback === 'success' && (
        <span style={{ fontSize: '0.7rem', color: '#4ade80', paddingLeft: '0.25rem' }}>✅ Action completed</span>
      )}
      {feedback === 'error' && (
        <span style={{ fontSize: '0.7rem', color: '#f87171', paddingLeft: '0.25rem' }}>❌ Action failed — check logs</span>
      )}
    </div>
  )
}

function ActionButtons({ response, selectedIssue, onDiagnose }) {
  const [logView, setLogView] = useState(null)

  const allText = `${response.analysis} ${response.root_cause} ${response.impact} ${response.recommendation}`.toLowerCase()

  const actions = []

  // Contextual buttons based on AI diagnosis
  if (allText.includes('rssi') || allText.includes('weak signal') || allText.includes('sticky') || allText.includes('roam')) {
    actions.push({
      action: 'client_roam',
      label: 'Force Client Roam',
      risk: 'low',
      icon: '🔄',
    })
  }

  if (allText.includes('congestion') || allText.includes('load') || allText.includes('band') || allText.includes('utilization')) {
    actions.push({
      action: 'band_steering',
      label: 'Enable Band Steering',
      risk: 'low',
      icon: '📡',
    })
  }

  if (allText.includes('ap issue') || allText.includes('radio') || allText.includes('interference')) {
    actions.push({
      action: 'disable_radio',
      label: 'Disable Radio',
      risk: 'high',
      icon: '🔴',
    })
  }

  // Always-available buttons
  actions.push({
    action: 'full_diagnosis',
    label: 'Run Full Diagnosis',
    risk: 'low',
    icon: '🤖',
    onClick: onDiagnose,
  })

  actions.push({
    action: 'view_logs',
    label: 'View Logs',
    risk: 'low',
    icon: '📋',
  })

  const executeAction = async (action) => {
    if (action === 'view_logs') {
      // Fetch logs — show in a simple alert for now
      try {
        const res = await fetch(`${API}/events?limit=20`)
        const data = await res.json()
        const events = data.events || data || []
        const logText = events.slice(0, 10).map((e) =>
          `[${e.timestamp || e.time || 'n/a'}] ${e.description || e.message || JSON.stringify(e)}`
        ).join('\n')
        setLogView(logText || 'No recent events found.')
        setTimeout(() => setLogView(null), 15000)
      } catch {
        setLogView('Failed to fetch logs from controller.')
        setTimeout(() => setLogView(null), 5000)
      }
      return
    }

    const res = await fetch(`${API}/remediation/execute`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        issue_id: selectedIssue?.id || selectedIssue?.title || 'manual',
        action,
        analysis_results: {
          analysis: response.analysis,
          root_cause: response.root_cause,
          impact: response.impact,
          recommendation: response.recommendation,
        },
      }),
    })
    if (!res.ok) throw new Error(`Remediation failed: ${res.status}`)
  }

  return (
    <div style={{ marginTop: '1rem' }}>
      <div style={{
        fontSize: '0.75rem',
        fontWeight: 600,
        color: '#94a3b8',
        marginBottom: '0.5rem',
        textTransform: 'uppercase',
        letterSpacing: '0.05em',
      }}>
        AI-Driven Actions
      </div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
        {actions.map((a, i) => (
          <ActionButton
            key={i}
            action={a.action}
            label={a.label}
            risk={a.risk}
            icon={a.icon}
            onExecute={a.onClick ? a.onClick : executeAction}
          />
        ))}
      </div>

      {/* Log Viewer Modal */}
      {logView && (
        <div style={{
          marginTop: '0.75rem',
          background: '#0f172a',
          border: '1px solid #334155',
          borderRadius: '6px',
          padding: '0.75rem',
          maxHeight: '300px',
          overflowY: 'auto',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: '#94a3b8' }}>📋 Recent Controller Events</span>
            <button
              onClick={() => setLogView(null)}
              style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer', fontSize: '0.8rem' }}
            >✕</button>
          </div>
          <pre style={{
            fontSize: '0.72rem',
            color: '#cbd5e1',
            whiteSpace: 'pre-wrap',
            fontFamily: 'monospace',
            margin: 0,
            lineHeight: '1.5',
          }}>{logView}</pre>
        </div>
      )}
    </div>
  )
}

export default function AIInsightPanel({ selectedIssue }) {
  const { response, loading, error, analyze } = useHermes()
  const [showDiagnosis, setShowDiagnosis] = useState(false)

  const handleDiagnose = () => {
    if (selectedIssue) {
      analyze(selectedIssue)
      setShowDiagnosis(true)
    }
  }

  return (
    <div className="panel">
      <h2>AI Insights</h2>

      {!selectedIssue && (
        <div className="placeholder">Select an alert to diagnose</div>
      )}

      {selectedIssue && (
        <>
          <div style={{ marginBottom: '0.75rem' }}>
            <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>
              {selectedIssue.title}
            </div>
            <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
              {selectedIssue.id} · {selectedIssue.severity}
            </div>
          </div>

          {!showDiagnosis && (
            <button
              className="badge"
              style={{ cursor: 'pointer', border: 'none', background: '#1e40af', color: '#93c5fd' }}
              onClick={handleDiagnose}
            >
              🤖 Diagnose with AI
            </button>
          )}

          {loading && (
            <div style={{ marginTop: '0.75rem', color: '#94a3b8' }}>
              ⏳ Analyzing...
            </div>
          )}

          {error && (
            <div style={{ marginTop: '0.75rem', color: '#f87171' }}>
              Error: {error}
            </div>
          )}

          {showDiagnosis && response && !loading && (
            <div style={{ marginTop: '0.75rem' }}>
              <div style={{ marginBottom: '0.5rem' }}>
                <strong style={{ color: '#93c5fd' }}>Diagnosis:</strong>
                <p style={{ fontSize: '0.85rem', marginTop: '0.2rem' }}>{response.analysis}</p>
              </div>
              <div style={{ marginBottom: '0.5rem' }}>
                <strong style={{ color: '#fbbf24' }}>Root Cause:</strong>
                <p style={{ fontSize: '0.85rem', marginTop: '0.2rem' }}>{response.root_cause}</p>
              </div>
              <div style={{ marginBottom: '0.5rem' }}>
                <strong style={{ color: '#f87171' }}>Impact:</strong>
                <p style={{ fontSize: '0.85rem', marginTop: '0.2rem' }}>{response.impact}</p>
              </div>
              <div style={{ marginBottom: '0.75rem' }}>
                <strong style={{ color: '#4ade80' }}>Recommendation:</strong>
                <p style={{ fontSize: '0.85rem', marginTop: '0.2rem' }}>{response.recommendation}</p>
              </div>

              {/* AI-Driven Action Buttons */}
              <ActionButtons
                response={response}
                selectedIssue={selectedIssue}
                onDiagnose={handleDiagnose}
              />
            </div>
          )}
        </>
      )}
    </div>
  )
}
