import { useState } from 'react'
import { useAruba } from '../hooks/useAruba'
import ClientTable from '../components/ClientTable'
import APHealthCard from '../components/APHealthCard'
import AlertPanel from '../components/AlertPanel'
import RSSIChart from '../components/RSSIChart'
import ChannelHeatmap from '../components/ChannelHeatmap'
import AIInsightPanel from '../components/AIInsightPanel'

export default function Dashboard() {
  const { clients, aps, alerts, loading, error, lastUpdated } = useAruba()
  const [selectedIssue, setSelectedIssue] = useState(null)

  return (
    <div>
      <div className="header">
        <h1>Aruba Wireless AI Analyzer</h1>
        <nav>
          <a href="/">Dashboard</a>
          <a href="/audit">Audit Log</a>
        </nav>
      </div>

      <div className="container">
        {loading && <p>Loading...</p>}
        {error && <p style={{ color: '#f87171' }}>Error: {error}</p>}
        {lastUpdated && (
          <p style={{ fontSize: '0.75rem', color: '#64748b', marginBottom: '1rem' }}>
            Last updated: {lastUpdated.toLocaleTimeString()}
          </p>
        )}

        {/* AP Health Grid */}
        <h2 style={{ marginBottom: '0.75rem', color: '#94a3b8', fontSize: '1rem' }}>
          Access Points ({aps.length})
        </h2>
        <div className="grid-4" style={{ marginBottom: '1.5rem' }}>
          {aps.map((ap) => (
            <APHealthCard key={ap.name} ap={ap} />
          ))}
        </div>

        {/* Alerts + AI */}
        <div className="charts-row" style={{ marginBottom: '1.5rem' }}>
          <AlertPanel alerts={alerts} onSelectIssue={setSelectedIssue} selectedIssue={selectedIssue} />
          <AIInsightPanel selectedIssue={selectedIssue} />
        </div>

        {/* Charts */}
        <div className="charts-row" style={{ marginBottom: '1.5rem' }}>
          <RSSIChart clients={clients} />
          <ChannelHeatmap aps={aps} />
        </div>

        {/* Client Table */}
        <ClientTable clients={clients} />
      </div>
    </div>
  )
}
