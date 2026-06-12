import { useState, useEffect, useRef, useCallback } from 'react'

const SEARCH_HISTORY_KEY = 'aruba_search_history'
const MAX_HISTORY = 10

export default function SearchBar({ onSearch }) {
  const [query, setQuery] = useState('')
  const [history, setHistory] = useState([])
  const [showHistory, setShowHistory] = useState(false)
  const [loading, setLoading] = useState(false)
  const inputRef = useRef(null)
  const debounceRef = useRef(null)

  // Load search history from localStorage
  useEffect(() => {
    try {
      const saved = localStorage.getItem(SEARCH_HISTORY_KEY)
      if (saved) setHistory(JSON.parse(saved))
    } catch {
      // ignore parse errors
    }
  }, [])

  // Keyboard shortcut: Ctrl+K to focus search
  useEffect(() => {
    const handler = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault()
        inputRef.current?.focus()
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [])

  // Save to history in localStorage
  const saveToHistory = useCallback((q) => {
    if (!q.trim()) return
    setHistory((prev) => {
      const filtered = prev.filter((h) => h !== q.trim())
      const updated = [q.trim(), ...filtered].slice(0, MAX_HISTORY)
      localStorage.setItem(SEARCH_HISTORY_KEY, JSON.stringify(updated))
      return updated
    })
  }, [])

  const performSearch = useCallback((searchQuery) => {
    if (!searchQuery.trim()) return
    setLoading(true)
    saveToHistory(searchQuery)
    setShowHistory(false)
    onSearch(searchQuery.trim())
    // Loading will be cleared by parent via callback or timeout
    setTimeout(() => setLoading(false), 500)
  }, [onSearch, saveToHistory])

  const handleSubmit = (e) => {
    e.preventDefault()
    performSearch(query)
  }

  const handleInputChange = (e) => {
    const value = e.target.value
    setQuery(value)
    setShowHistory(value.length === 0 && history.length > 0)

    // Debounced search
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => {
      if (value.trim().length > 0) {
        performSearch(value)
      }
    }, 300)
  }

  const handleHistoryClick = (item) => {
    setQuery(item)
    setShowHistory(false)
    performSearch(item)
  }

  const handleClearHistory = (e) => {
    e.stopPropagation()
    setHistory([])
    localStorage.removeItem(SEARCH_HISTORY_KEY)
  }

  return (
    <div style={{ position: 'relative', flex: 1, maxWidth: '500px' }}>
      <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '0.5rem' }}>
        <div style={{ position: 'relative', flex: 1 }}>
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={handleInputChange}
            onFocus={() => setShowHistory(query.length === 0 && history.length > 0)}
            onBlur={() => setTimeout(() => setShowHistory(false), 200)}
            placeholder="Search by MAC or IP... (Ctrl+K)"
            style={{
              width: '100%',
              padding: '0.5rem 0.75rem',
              paddingRight: '2.5rem',
              borderRadius: '6px',
              border: '1px solid #334155',
              background: '#0f172a',
              color: '#e2e8f0',
              fontSize: '0.875rem',
              outline: 'none',
            }}
          />
          {loading && (
            <span style={{
              position: 'absolute',
              right: '8px',
              top: '50%',
              transform: 'translateY(-50%)',
              fontSize: '0.75rem',
              color: '#64748b',
            }}>⏳</span>
          )}
          {!loading && (
            <span style={{
              position: 'absolute',
              right: '8px',
              top: '50%',
              transform: 'translateY(-50%)',
              fontSize: '0.75rem',
              color: '#64748b',
            }}>🔍</span>
          )}
        </div>
        <button
          type="submit"
          style={{
            padding: '0.5rem 1rem',
            borderRadius: '6px',
            border: 'none',
            background: '#3b82f6',
            color: '#fff',
            cursor: 'pointer',
            fontSize: '0.875rem',
            fontWeight: '600',
          }}
        >
          Search
        </button>
      </form>

      {/* Search History Dropdown */}
      {showHistory && history.length > 0 && (
        <div style={{
          position: 'absolute',
          top: '100%',
          left: 0,
          right: 0,
          background: '#1e293b',
          border: '1px solid #334155',
          borderRadius: '6px',
          marginTop: '4px',
          zIndex: 100,
          maxHeight: '200px',
          overflowY: 'auto',
        }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            padding: '0.5rem 0.75rem',
            borderBottom: '1px solid #334155',
            fontSize: '0.75rem',
            color: '#94a3b8',
          }}>
            <span>Search History</span>
            <button
              onClick={handleClearHistory}
              style={{
                background: 'none',
                border: 'none',
                color: '#94a3b8',
                cursor: 'pointer',
                fontSize: '0.75rem',
              }}
            >
              Clear All
            </button>
          </div>
          {history.map((item, idx) => (
            <div
              key={idx}
              onClick={() => handleHistoryClick(item)}
              style={{
                padding: '0.5rem 0.75rem',
                cursor: 'pointer',
                fontSize: '0.875rem',
                color: '#e2e8f0',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
              }}
              onMouseEnter={(e) => (e.target.style.background = '#334155')}
              onMouseLeave={(e) => (e.target.style.background = 'transparent')}
            >
              <span style={{ color: '#64748b' }}>🕐</span>
              {item}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}