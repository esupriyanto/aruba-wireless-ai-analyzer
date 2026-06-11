import { useState } from 'react'
import { useHermes } from '../hooks/useHermes'

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
              <div>
                <strong style={{ color: '#4ade80' }}>Recommendation:</strong>
                <p style={{ fontSize: '0.85rem', marginTop: '0.2rem' }}>{response.recommendation}</p>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
