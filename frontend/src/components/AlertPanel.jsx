export default function AlertPanel({ alerts, onSelectIssue, selectedIssue }) {
  if (!alerts.length) {
    return (
      <div className="panel">
        <h2>Alerts</h2>
        <div className="placeholder">No alerts — network healthy ✓</div>
      </div>
    )
  }

  return (
    <div className="panel">
      <h2>Alerts ({alerts.length})</h2>
      {alerts.map((a) => (
        <div
          className="alert-item"
          key={a.id}
          onClick={() => onSelectIssue?.(a)}
          style={{
            cursor: 'pointer',
            background: selectedIssue?.id === a.id ? '#1e293b' : 'transparent',
            borderRadius: '4px',
          }}
        >
          <span className={`badge badge-${a.severity}`}>{a.severity}</span>
          <div className="alert-body">
            <div className="title">{a.title}</div>
            <div className="desc">{a.description}</div>
          </div>
        </div>
      ))}
    </div>
  )
}
