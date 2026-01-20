import React, { useState, useEffect } from 'react'
import SearchForm from './components/SearchForm'
import ResultCard from './components/ResultCard'
import './App.css'

function App() {
  const [results, setResults] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const [stats, setStats] = useState(null)
  const [searchParams, setSearchParams] = useState(null)

  useEffect(() => {
    fetchStats()
  }, [])

  const fetchStats = async () => {
    try {
      const response = await fetch('/api/stats')
      if (response.ok) {
        const data = await response.json()
        setStats(data)
      }
    } catch (error) {
      console.error('Stats fetch error:', error)
    }
  }

  const handleSearch = async (params) => {
    setIsLoading(true)
    setError(null)
    setSearchParams(params)

    try {
      const response = await fetch('/api/search/form', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params)
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Arama hatasi')
      }

      const data = await response.json()
      setResults(data)
    } catch (error) {
      setError(error.message)
      setResults(null)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="app">
      <header className="header">
        <div className="header-content">
          <div className="logo">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 2L2 7l10 5 10-5-10-5z"/>
              <path d="M2 17l10 5 10-5"/>
              <path d="M2 12l10 5 10-5"/>
            </svg>
            <h1>Trafo Matcher</h1>
          </div>
          <div className="status">
            {stats && (
              <span className="status-badge connected">
                {stats.total_designs} Dizayn
              </span>
            )}
          </div>
        </div>
      </header>

      <main className="main-content">
        <div className="search-panel">
          <SearchForm
            onSearch={handleSearch}
            isLoading={isLoading}
            stats={stats}
          />
        </div>

        <div className="results-panel">
          {error && (
            <div className="error-message">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10"/>
                <path d="M12 8v4"/>
                <path d="M12 16h.01"/>
              </svg>
              {error}
            </div>
          )}

          {results && (
            <div className="results-container">
              <div className="results-header">
                <h2>{results.matches?.length || 0} Sonuc Bulundu</h2>
                {searchParams && (
                  <div className="search-summary">
                    {Object.entries(searchParams)
                      .filter(([key, value]) => key !== 'max_results' && value)
                      .map(([key, value]) => (
                        <span key={key} className="param-tag">
                          {key.replace(/_/g, ' ')}: {value}
                        </span>
                      ))}
                  </div>
                )}
              </div>

              <div className="results-list">
                {results.matches?.map((match, idx) => (
                  <ResultCard key={idx} result={match} rank={idx + 1} />
                ))}
              </div>

              {results.matches?.length === 0 && (
                <div className="no-results">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="11" cy="11" r="8"/>
                    <path d="M21 21l-4.35-4.35"/>
                    <path d="M8 8l6 6"/>
                    <path d="M14 8l-6 6"/>
                  </svg>
                  <p>Kriterlere uygun dizayn bulunamadi.</p>
                  <p className="hint">Farkli parametreler deneyin veya toleransi artirin.</p>
                </div>
              )}
            </div>
          )}

          {!results && !error && (
            <div className="welcome-message">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="11" cy="11" r="8"/>
                <path d="M21 21l-4.35-4.35"/>
              </svg>
              <h2>Trafo Dizayn Arama</h2>
              <p>Soldaki formu kullanarak benzer trafo dizaynlarini bulun.</p>
              <div className="features">
                <div className="feature">
                  <strong>Hizli Arama</strong>
                  <span>Veritabanindan aninda sonuc</span>
                </div>
                <div className="feature">
                  <strong>Benzerlik Skoru</strong>
                  <span>Parametrelere gore eslesme yuzdesi</span>
                </div>
                <div className="feature">
                  <strong>Detayli Bilgi</strong>
                  <span>Tum elektriksel ve mekanik parametreler</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}

export default App
