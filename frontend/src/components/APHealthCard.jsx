export default function APHealthCard({ ap }) {
  const statusClass =
    ap.status === 'up' ? 'status-up' : ap.status === 'down' ? 'status-down' : 'status-degraded'

  const utilClass =
    ap.channel_utilization > 70 ? 'util-high' : ap.channel_utilization > 40 ? 'util-med' : 'util-low'

  return (
    <div className="card">
      <h3>
        <span className={`status-dot ${statusClass}`} />
        {ap.name}
      </h3>
      <div style={{ fontSize: '0.85rem', color: '#94a3b8' }}>
        {ap.radio_count} radios · {ap.client_count} clients
      </div>
      <div style={{ marginTop: '0.5rem' }}>
        <span className={utilClass}>
          Util: {ap.channel_utilization}%
        </span>
      </div>
    </div>
  )
}
