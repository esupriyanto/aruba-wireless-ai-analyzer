import { useState, useEffect, useCallback } from 'react'
import axios from 'axios'

const API = '/api/v1'

export function useAruba() {
  const [clients, setClients] = useState([])
  const [aps, setAps] = useState([])
  const [alerts, setAlerts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [lastUpdated, setLastUpdated] = useState(null)

  const fetchAll = useCallback(async () => {
    try {
      const [cRes, aRes, alRes] = await Promise.all([
        axios.get(`${API}/clients/`),
        axios.get(`${API}/access-points/`),
        axios.get(`${API}/events/alerts`),
      ])
      setClients(cRes.data.clients || [])
      setAps(aRes.data.access_points || [])
      setAlerts(alRes.data.alerts || [])
      setLastUpdated(new Date())
      setError(null)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchAll()
    const interval = setInterval(fetchAll, 30000)
    return () => clearInterval(interval)
  }, [fetchAll])

  return { clients, aps, alerts, loading, error, lastUpdated, refetch: fetchAll }
}
