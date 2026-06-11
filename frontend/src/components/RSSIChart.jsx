import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, ResponsiveContainer } from 'recharts'

export default function RSSIChart({ clients }) {
  // Build chart data: one point per client, sorted by RSSI
  const data = [...clients]
    .sort((a, b) => a.rssi - b.rssi)
    .map((c) => ({
      mac: c.mac,
      rssi: c.rssi,
      ap: c.ap_name,
    }))

  return (
    <div className="panel">
      <h2>RSSI Distribution</h2>
      <div className="chart-container">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="mac" tick={false} label="Clients" />
            <YAxis domain={['dataMin - 5', 'dataMax + 5']} tick={{ fill: '#94a3b8', fontSize: 11 }} />
            <Tooltip
              contentStyle={{ background: '#1e293b', border: '1px solid #334155' }}
              labelFormatter={(i) => `${data[i]?.mac} (${data[i]?.ap})`}
              formatter={(v) => [`${v} dBm`, 'RSSI']}
            />
            <ReferenceLine y={-75} stroke="#f87171" strokeDasharray="5 5" label="Weak Threshold" />
            <Line type="monotone" dataKey="rssi" stroke="#60a5fa" dot={false} strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
