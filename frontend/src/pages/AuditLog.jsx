import { useState, useEffect } from 'react'

export default function AuditLog() {
  const [entries, setEntries] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/api/v1/audit/')
      .then((r) => r.json())
      .then((d) => setEntries(d.entries || []))
      .catch(() => setEntries([]))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div>
      <div className="header">
        <h1>Aruba Wireless AI Analyzer</h1>
        <nav>
          <a href="/">Dashboard</a>
          <a href="/audit" style={{ marginLeft: '1.5rem' }}>Audit Log</a>
        </nav>
      </div>

      <div className="container">
        <a href="/" className="back-link">← Back to Dashboard</a>
        <div className="panel">
          <h2>Audit Log ({entries.length})</h2>
          {loading ? (
            <div className="placeholder">Loading...</div>
          ) : entries.length === 0 ? (
            <div className="placeholder">No remediation actions recorded yet</div>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Issue</th>
                  <th>Action</th>
                  <th>Status</th>
                  <th>Message</th>
                </tr>
              </thead>
              <tbody>
                {entries.map((e) => (
                  <tr key={e.id}>
                    <td style={{ fontSize: '0.8rem' }}>{e.timestamp}</td>
                    <td>{e.issue_id}</td>
                    <td>{e.action}</td>
                    <td>
                      <span className={`badge badge-${e.status === 'accepted' ? 'low' : 'info'}`}>
                        {e.status}
                      </span>
                    </td>
                    <td style={{ fontSize: '0.8rem', color: '#94a3b8' }}>{e.message}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  )
}
