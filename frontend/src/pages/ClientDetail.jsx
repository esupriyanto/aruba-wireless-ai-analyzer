import { useParams, Link } from 'react-router-dom'
import { useAruba } from '../hooks/useAruba'

export default function ClientDetail() {
  const { mac } = useParams()
  const { clients, loading } = useAruba()

  const client = clients.find((c) => c.mac === mac)

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
          <div className="panel">
            <h2>{client.mac}</h2>
            <table>
              <tbody>
                <tr><td>AP</td><td>{client.ap_name}</td></tr>
                <tr><td>Band</td><td>{client.band}</td></tr>
                <tr><td>RSSI</td><td>{client.rssi} dBm</td></tr>
                <tr><td>Auth</td><td>{client.auth_type}</td></tr>
                <tr><td>Channel</td><td>{client.channel}</td></tr>
              </tbody>
            </table>
          </div>
        ) : (
          !loading && <div className="placeholder">Client {mac} not found</div>
        )}
      </div>
    </div>
  )
}
