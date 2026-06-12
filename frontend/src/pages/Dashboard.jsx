import { useState } from 'react'
import { useAruba } from '../hooks/useAruba'
import ClientTable from '../components/ClientTable'
import APHealthCard from '../components/APHealthCard'
import AlertPanel from '../components/AlertPanel'
import RSSIChart from '../components/RSSIChart'
import ChannelHeatmap from '../components/ChannelHeatmap'
import AIInsightPanel from '../components/AIInsightPanel'
import SearchBar from '../components/SearchBar'
import DeviceDiagnosticPanel from '../components/DeviceDiagnosticPanel'

const API = '/api/v1'

export default function Dashboard() {
  const { clients, aps, alerts, loading, error, lastUpdated } = useAruba()
  const [selectedIssue, setSelectedIssue] = useState(null)
  const [ SearchResult, setSearchResult] = useState(null)
  const [searchLoading, setSearchLoading] = useState(false)

  const handleSearch = async (query) => {
    setSearchLoading(true)
    setSearchResult(null)
    try {
      const url = `${API}/search?query=${encodeURIComponent(query)}`
      const res = await fetch(url)
      if (!res.ok) throw new Error('Search failed')
      const data = await res.json()
      setSearchResult(data)
    } catch (err) {
      console.error('Search error:', err)
      setSearchResult(null)
    } finally {
      setSearchLoading(false)
    }
  }

  const handleRemediate = async (action) => {
    if (!selectedIssue) return
    const payload = {
      issue_id: selectedIssue,
      action: action.action,
      analysis_results: {
        action: action.action,
        label: action.label,
      },
    }
    const res = await fetch(`${API}/remediation/execute`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    if (!res.ok) throw new Error('Remediation failed')
    return res.json()
  }

  return (
    <div>
      <div className="header" style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
        <h1 style={{ flex: '1 1 auto', minWidth: '200px' }}>Aruba Wireless AI Analyzer</h1>
        <nav>
          <a href="/">Dashboard</a>
          <a href="/audit" style={{ marginLeft: '1.5rem' }}>Audit Log</a>
        </nav>
      </div>

      {/* Search Bar */}
      <div style={{
        background: '#1e293b', borderRadius: '8px', padding: '0.75rem',
        marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '1rem',
      }}>
        <SearchBar onSearch={handleSearch} />
        {searchLoading && <span style={{ color: '#64748b', fontSize: '0.85rem' }}>⏳ Searching...</span>}
      </div>

      {/* Search Result */}
      {!searchLoading && SearchResult && (
        <DeviceDiagnosticPanel result={SearchResult} onRemediate={handleRemediate} />
      )}

      <div className="container" style={SearchResult ? { opacity: 0.9 } : {}}>
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