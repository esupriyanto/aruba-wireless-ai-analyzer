import { useParams, Link } from 'react-router-dom'
import { useState } from 'react'
import { useAruba } from '../hooks/useAruba'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, ResponsiveContainer } from 'recharts'

export default function ClientDetail() {
  const { mac } = useParams()
  const { clients, loading } = useAruba()
  const [rssiData, setRssiData] = useState([])
  const [loadingRssi, setLoadingRssi] = useState(false)

  const client = clients.find((c) => c.mac === mac)

  // Fetch RSSI history on mount
  useState(() => {
    if (client) {
      setLoadingRssi(true)
      fetch(`/api/v1/clients/${mac}/rssi?hours=24`)
        .then((r) => r.json())
        .then((data) => setRssiData(data || []))
        .catch(() => setRssiData([]))
        .finally(() => setLoadingRssi(false))
    }
  })

  return (
    <div>
      <div className="header">
        <h1>Aruba Wireless AI Analyzer</h1>
        <nav>
          <Link to="/">Dashboard</Link>
          <Link to="/audit" style={{ marginLeft: '1.5rem' }}>Audit Log</Link>
        </nav>
      </div>

      <div className="container">
        <Link to="/" className="back-link">← Back to Dashboard</Link>

        {loading && <p>Loading...</p>}

        {client ? (
          <>
            <div className="panel" style={{ marginBottom: '1rem' }}>
              <h2>{client.mac}</h2>
              <table>
                <tbody>
                  <tr><td>IP</td><td>{client.ip}</td></tr>
                  <tr><td>AP</td><td>{client.ap_name}</td></tr>
                  <tr><td>Band</td><td>{client.band}</td></tr>
                  <tr><td>RSSI</td><td>{client.rssi_dbm ?? client.rssi} dBm</td></tr>
                  <tr><td>SNR</td><td>{client.snr}</td></tr>
                  <tr><td>Auth</td><td>{client.auth_type}</td></tr>
                  <tr><td>Channel</td><td>{client.channel}</td></tr>
                  <tr><td>Status</td><td>{client.status}</td></tr>
                  <tr><td>TX Rate</td><td>{client.tx_rate} Mbps</td></tr>
                  <tr><td>RX Rate</td><td>{client.rx_rate} Mbps</td></tr>
                </tbody>
              </table>
            </div>

            <div className="panel">
              <h2>RSSI History (24h)</h2>
              {loadingRssi ? (
                <div className="placeholder">Loading...</div>
              ) : rssiData.length > 0 ? (
                <div className="chart-container" style={{ height: 300 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={rssiData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                      <XAxis dataKey="timestamp" tick={{ fill: '#94a3b8', fontSize: 10 }} />
                      <YAxis domain={['dataMin - 5', 'dataMax + 5']} tick={{ fill: '#94a3b8', fontSize: 11 }} />
                      <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155' }} />
                      <ReferenceLine y={-75} stroke="#f87171" strokeDasharray="5 5" label="Weak" />
                      <Line type="monotone" dataKey="value" stroke="#60a5fa" dot={false} strokeWidth={2} name="RSSI dBm" />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="placeholder">No RSSI history available (mock data only supports real-time)</div>
              )}
            </div>
          </>
        ) : (
          !loading && <div className="placeholder">Client {mac} not found</div>
        )}
      </div>
    </div>
  )
}
