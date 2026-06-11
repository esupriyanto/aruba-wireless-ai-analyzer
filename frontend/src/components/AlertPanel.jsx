export default function AlertPanel({ alerts }) {
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
        <div className="alert-item" key={a.id}>
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
