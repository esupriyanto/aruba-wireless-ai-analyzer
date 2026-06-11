import { useState } from 'react'
import { useHermes } from '../hooks/useHermes'

export default function ResolveButton({ issue, action = 'restart_ap' }) {
  const { loading, execute } = useHermes()
  const [showModal, setShowModal] = useState(false)
  const [result, setResult] = useState(null)

  const handleResolve = async () => {
    try {
      const res = await execute(issue.id, action)
      setResult({ success: true, message: res.message })
    } catch (err) {
      setResult({ success: false, message: err.message })
    }
  }

  return (
    <>
      <button
        className="badge"
        style={{ cursor: 'pointer', border: 'none', background: '#166534', color: '#86efac' }}
        onClick={() => setShowModal(true)}
      >
        Resolve with AI
      </button>

      {showModal && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0,0,0,0.7)', display: 'flex',
          alignItems: 'center', justifyContent: 'center', zIndex: 1000,
        }}>
          <div style={{
            background: '#1e293b', border: '1px solid #334155',
            borderRadius: '8px', padding: '1.5rem', maxWidth: '400px', width: '90%',
          }}>
            <h3 style={{ marginBottom: '0.75rem' }}>Confirm Remediation</h3>
            <p style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '1rem' }}>
              Action: <strong>{action}</strong><br />
              Issue: <strong>{issue.title}</strong><br />
              Target: <strong>{issue.affected_aps?.[0] || 'network'}</strong>
            </p>

            {result && (
              <div style={{
                marginBottom: '1rem', padding: '0.5rem', borderRadius: '4px',
                background: result.success ? '#14532d' : '#7f1d1d',
                color: result.success ? '#86efac' : '#fca5a5',
                fontSize: '0.85rem',
              }}>
                {result.success ? '✓ ' : '✗ '}{result.message}
              </div>
            )}

            <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
              <button
                className="badge"
                style={{ cursor: 'pointer', border: 'none', background: '#334155', color: '#e2e8f0' }}
                onClick={() => { setShowModal(false); setResult(null) }}
              >
                Cancel
              </button>
              {!result?.success && (
                <button
                  className="badge"
                  style={{ cursor: 'pointer', border: 'none', background: '#166534', color: '#86efac' }}
                  onClick={handleResolve}
                  disabled={loading}
                >
                  {loading ? 'Executing...' : 'Confirm'}
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  )
}
