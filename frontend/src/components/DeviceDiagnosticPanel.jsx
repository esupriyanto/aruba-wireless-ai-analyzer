import { useState } from 'react'

const SEVERITY_CONFIG = {
  critical: { icon: '🔴', label: 'Critical', color: '#ef4444', bg: '#450a0a' },
  warning:  { icon: '🟡', label: 'Warning',  color: '#eab308', bg: '#422006' },
  healthy:  { icon: '🟢', label: 'Healthy',  color: '#22c55e', bg: '#052e16' },
  info:     { icon: '🔵', label: 'Info',     color: '#3b82f6', bg: '#172554' },
}

function HealthGauge({ score }) {
  const pct = Math.max(0, Math.min(100, score))
  const color = pct >= 76 ? '#22c55e' : pct >= 41 ? '#eab308' : '#ef4444'
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
      <div style={{
        width: '64px', height: '64px', borderRadius: '50%',
        background: `conic-gradient(${color} ${pct * 3.6}deg, #1e293b 0deg)`,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}>
        <div style={{
          width: '48px', height: '48px', borderRadius: '50%',
          background: '#0f172a', display: 'flex', alignItems: 'center',
          justifyContent: 'center', fontSize: '0.85rem', fontWeight: '700', color,
        }}>{score}</div>
      </div>
      <div>
        <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Health Score</div>
        <div style={{ fontSize: '1.1rem', fontWeight: '600', color }}>{score}/100</div>
      </div>
    </div>
  )
}

function InfoCard({ device }) {
  if (!device) return null
  const rows = [
    ['MAC', device.mac_address],
    ['IP', device.ip_address],
    ['Hostname', device.hostname || '—'],
    ['AP', device.ap_name],
    ['SSID', device.ssid],
    ['VLAN', device.vlan],
    ['Band', device.band],
    ['Auth', device.auth_type],
    ['Status', device.status],
  ]
  return (
    <div style={{
      background: '#1e293b', borderRadius: '8px', padding: '1rem',
      border: '1px solid #334155',
    }}>
      <h3 style={{ margin: '0 0 0.75rem', fontSize: '0.95rem', color: '#e2e8f0' }}>
        📡 Device Info
      </h3>
      <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '4px 12px', fontSize: '0.825rem' }}>
        {rows.map(([label, val]) => (
          <>
            <span style={{ color: '#94a3b8', fontWeight: '600' }}>{label}</span>
            <span style={{ color: '#e2e8f0', fontFamily: 'monospace' }}>{val || '—'}</span>
          </>
        ))}
      </div>
    </div>
  )
}

function SignalMetrics({ metrics, device }) {
  if (!metrics) return null
  const rssi = metrics.rssi?.current ?? 0
  const trend = metrics.rssi?.trend ?? []
  const channelUtil = metrics.channel_utilization ?? 0
  const noiseFloor = metrics.noiseFloor ?? -95
  const dataRate = device?.data_rate_mbps ?? 0
  const channel = device?.channel ?? 0

  const rssiColor = rssi >= -60 ? '#22c55e' : rssi >= -75 ? '#eab308' : '#ef4444'
  const utilColor = channelUtil < 40 ? '#22c55e' : channelUtil < 60 ? '#eab308' : '#ef4444'

  return (
    <div style={{
      background: '#1e293b', borderRadius: '8px', padding: '1rem',
      border: '1px solid #334155',
    }}>
      <h3 style={{ margin: '0 0 0.75rem', fontSize: '0.95rem', color: '#e2e8f0' }}>
        📊 Signal Metrics
      </h3>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem' }}>
        {/* RSSI */}
        <div style={{ flex: '1 1 140px' }}>
          <div style={{ fontSize: '0.7rem', color: '#94a3b8', marginBottom: '2px' }}>RSSI</div>
          <div style={{ fontSize: '1.25rem', fontWeight: '700', color: rssiColor }}>
            {rssi} <span style={{ fontSize: '0.75rem' }}>dBm</span>
          </div>
          {trend.length > 1 && (
            <div style={{ fontSize: '0.7rem', color: '#64748b' }}>
              Trend: {trend.join(' → ')}
            </div>
          )}
        </div>

        {/* Channel Utilization */}
        <div style={{ flex: '1 1 140px' }}>
          <div style={{ fontSize: '0.7rem', color: '#94a3b8', marginBottom: '2px' }}>Channel Util</div>
          <div style={{ fontSize: '1.25rem', fontWeight: '700', color: utilColor }}>
            {channelUtil}%
          </div>
          <div style={{
            height: '4px', borderRadius: '2px', background: '#334155', marginTop: '4px',
          }}>
            <div style={{
              height: '100%', borderRadius: '2px', background: utilColor,
              width: `${Math.min(100, channelUtil)}%`,
            }} />
          </div>
        </div>

        {/* Noise Floor */}
        <div style={{ flex: '1 1 100px' }}>
          <div style={{ fontSize: '0.7rem', color: '#94a3b8', marginBottom: '2px' }}>Noise Floor</div>
          <div style={{ fontSize: '1.25rem', fontWeight: '700', color: '#e2e8f0' }}>
            {noiseFloor} <span style={{ fontSize: '0.75rem' }}>dBm</span>
          </div>
        </div>

        {/* Data Rate */}
        <div style={{ flex: '1 1 100px' }}>
          <div style={{ fontSize: '0.7rem', color: '#94a3b8', marginBottom: '2px' }}>Data Rate</div>
          <div style={{ fontSize: '1.25rem', fontWeight: '700', color: '#e2e8f0' }}>
            {dataRate} <span style={{ fontSize: '0.75rem' }}>Mbps</span>
          </div>
        </div>

        {/* Channel */}
        <div style={{ flex: '1 1 80px' }}>
          <div style={{ fontSize: '0.7rem', color: '#94a3b8', marginBottom: '2px' }}>Channel</div>
          <div style={{ fontSize: '1.25rem', fontWeight: '700', color: '#e2e8f0' }}>{channel}</div>
        </div>
      </div>
    </div>
  )
}

function AIDiagnosisPanel({ diagnosis, onRemediate }) {
  if (!diagnosis) return null
  const sev = SEVERITY_CONFIG[diagnosis.severity] || SEVERITY_CONFIG.info

  return (
    <div style={{
      background: '#1e293b', borderRadius: '8px', padding: '1rem',
      border: `1px solid ${sev.color}33`,
    }}>
      <h3 style={{ margin: '0 0 0.75rem', fontSize: '0.95rem', color: '#e2e8f0' }}>
        🤖 AI Diagnosis
      </h3>

      {/* Severity + Health Score */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '0.75rem' }}>
        <HealthGauge score={diagnosis.health_score} />
        <div style={{
          padding: '0.35rem 0.75rem', borderRadius: '12px',
          background: sev.bg, color: sev.color, fontSize: '0.8rem', fontWeight: '600',
        }}>
          {sev.icon} {sev.label}
        </div>
      </div>

      {/* Summary */}
      <div style={{
        background: '#0f172a', borderRadius: '6px', padding: '0.75rem',
        marginBottom: '0.75rem', fontSize: '0.825rem', color: '#cbd5e1', lineHeight: '1.5',
      }}>
        {diagnosis.summary}
      </div>

      {/* Root Causes */}
      {diagnosis.root_causes?.length > 0 && (
        <div style={{ marginBottom: '0.75rem' }}>
          <div style={{ fontSize: '0.75rem', fontWeight: '600', color: '#94a3b8', marginBottom: '0.35rem' }}>
            Root Causes
          </div>
          <ul style={{ margin: 0, paddingLeft: '1.25rem', fontSize: '0.8rem', color: '#cbd5e1' }}>
            {diagnosis.root_causes.map((cause, i) => (
              <li key={i} style={{ marginBottom: '0.25rem' }}>{cause}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Recommendations */}
      {diagnosis.recommendations?.length > 0 && (
        <div style={{ marginBottom: '0.75rem' }}>
          <div style={{ fontSize: '0.75rem', fontWeight: '600', color: '#94a3b8', marginBottom: '0.35rem' }}>
            Recommendations
          </div>
          <ul style={{ margin: 0, paddingLeft: '1.25rem', fontSize: '0.8rem', color: '#cbd5e1' }}>
            {diagnosis.recommendations.map((rec, i) => (
              <li key={i} style={{ marginBottom: '0.25rem' }}>{rec}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

function RemediationActions({ actions, onAction }) {
  if (!actions || actions.length === 0) return null
  return (
    <div style={{
      background: '#1e293b', borderRadius: '8px', padding: '1rem',
      border: '1px solid #334155',
    }}>
      <h3 style={{ margin: '0 0 0.75rem', fontSize: '0.95rem', color: '#e2e8f0' }}>
        ⚡ Remediation Actions
      </h3>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
        {actions.map((a, i) => (
          <button
            key={i}
            onClick={() => onAction && onAction(a)}
            style={{
              padding: '0.45rem 0.85rem', borderRadius: '6px', border: '1px solid #475569',
              background: a.risk === 'medium' ? '#451a03' : '#0f172a',
              color: a.risk === 'medium' ? '#fbbf24' : '#e2e8f0',
              cursor: 'pointer', fontSize: '0.8rem', fontWeight: '500',
            }}
          >
            {a.label}
            {a.risk === 'medium' && <span style={{ fontSize: '0.7rem', marginLeft: '4px' }}>⚠️</span>}
          </button>
        ))}
      </div>
    </div>
  )
}

export default function DeviceDiagnosticPanel({ result, onRemediate }) {
  const [actionLoading, setActionLoading] = useState(null)

  if (!result) return null

  if (!result.found) {
    return (
      <div style={{
        background: '#1e293b', borderRadius: '8px', padding: '2rem',
        border: '1px solid #334155', textAlign: 'center', marginTop: '1rem',
      }}>
        <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>❌</div>
        <h3 style={{ color: '#e2e8f0', margin: '0 0 0.5rem' }}>Device Not Found</h3>
        <p style={{ color: '#94a3b8', fontSize: '0.85rem' }}>
          No device matching <code style={{ color: '#e2e8f0' }}>{result.query}</code> was found in the controller.
          <br />Check that the MAC/IP is correct and the device is connected.
        </p>
      </div>
    )
  }

  const handleAction = async (action) => {
    setActionLoading(action.action)
    try {
      if (onRemediate) await onRemediate(action)
      else alert(`${action.label} — queued (Phase 9 demo)`)
    } finally {
      setActionLoading(null)
    }
  }

  return (
    <div style={{ marginTop: '1rem' }}>
      {/* Connection Duration Banner */}
      {result.device?.connection_duration && (
        <div style={{
          textAlign: 'center', color: '#94a3b8', fontSize: '0.8rem',
          marginBottom: '0.75rem',
        }}>
          Connected for {result.device.connection_duration}
        </div>
      )}

      {/* Device Info + AI Diagnosis side by side */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
        gap: '1rem', marginBottom: '1rem',
      }}>
        <InfoCard device={result.device} />
        <AIDiagnosisPanel diagnosis={result.ai_diagnosis} onRemediate={handleAction} />
      </div>

      {/* Signal Metrics */}
      <SignalMetrics metrics={result.metrics} device={result.device} />

      {/* Remediation Actions */}
      <div style={{ marginTop: '1rem' }}>
        <RemediationActions actions={result.remediation_actions} onAction={handleAction} />
      </div>
    </div>
  )
}