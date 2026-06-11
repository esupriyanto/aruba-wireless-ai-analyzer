import { useState } from 'react'

export default function ClientTable({ clients }) {
  const [sortKey, setSortKey] = useState('mac')
  const [sortDir, setSortDir] = useState('asc')

  const handleSort = (key) => {
    if (sortKey === key) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc')
    } else {
      setSortKey(key)
      setSortDir('asc')
    }
  }

  const sorted = [...clients].sort((a, b) => {
    const aVal = a[sortKey] ?? ''
    const bVal = b[sortKey] ?? ''
    const cmp = typeof aVal === 'number' ? aVal - bVal : String(aVal).localeCompare(String(bVal))
    return sortDir === 'asc' ? cmp : -cmp
  })

  const SortIndicator = ({ col }) => {
    if (sortKey !== col) return null
    return sortDir === 'asc' ? ' ▲' : ' ▼'
  }

  return (
    <div className="panel">
      <h2>Clients ({clients.length})</h2>
      <table>
        <thead>
          <tr>
            <th onClick={() => handleSort('mac')}>MAC<SortIndicator col="mac" /></th>
            <th onClick={() => handleSort('ap_name')}>AP<SortIndicator col="ap_name" /></th>
            <th onClick={() => handleSort('band')}>Band<SortIndicator col="band" /></th>
            <th onClick={() => handleSort('rssi')}>RSSI<SortIndicator col="rssi" /></th>
            <th onClick={() => handleSort('auth_type')}>Auth<SortIndicator col="auth_type" /></th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((c) => (
            <tr key={c.mac}>
              <td><a href={`/clients/${c.mac}`}>{c.mac}</a></td>
              <td>{c.ap_name}</td>
              <td>{c.band}</td>
              <td className={c.rssi < -75 ? 'rssi-weak' : ''}>{c.rssi} dBm</td>
              <td>{c.auth_type}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
