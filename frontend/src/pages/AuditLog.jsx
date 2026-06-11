export default function AuditLog() {
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
          <h2>Audit Log</h2>
          <div className="placeholder">Audit log coming soon</div>
        </div>
      </div>
    </div>
  )
}
