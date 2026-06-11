import { useState, useCallback } from 'react'

export function useHermes() {
  const [response, setResponse] = useState(null)
  const [loading, setLoading] = useState(false)

  const ask = useCallback(async (question) => {
    setLoading(true)
    // Stub — Phase 6 will wire to Hermes Agent
    setTimeout(() => {
      setResponse(`AI analysis for: "${question}" — coming in Phase 6.`)
      setLoading(false)
    }, 500)
  }, [])

  return { response, loading, ask }
}
