import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'

export default function ChannelHeatmap({ aps }) {
  const data = aps.map((ap) => ({
    name: ap.name,
    utilization: ap.channel_utilization,
  }))

  const getColor = (val) => {
    if (val > 80) return '#ef4444'
    if (val > 60) return '#f59e0b'
    if (val > 40) return '#eab308'
    return '#22c55e'
  }

  return (
    <div className="panel">
      <h2>Channel Utilization</h2>
      <div className="chart-container">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 11 }} />
            <YAxis domain={[0, 100]} tick={{ fill: '#94a3b8', fontSize: 11 }} unit="%" />
            <Tooltip
              contentStyle={{ background: '#1e293b', border: '1px solid #334155' }}
              formatter={(v) => [`${v}%`, 'Utilization']}
            />
            <Bar dataKey="utilization" radius={[4, 4, 0, 0]}>
              {data.map((entry, i) => (
                <Cell key={i} fill={getColor(entry.utilization)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
