import { useState } from 'react'
import UrlInput from './components/UrlInput'
import ResultViewer from './components/ResultViewer'
import { API_ENDPOINTS, SCRAPE_TIMEOUT_MESSAGE } from './constants'

function App() {
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleScrape = async (url, enableInteractions, interactionStrategy) => {
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await fetch(API_ENDPOINTS.SCRAPE, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          url,
          enable_interactions: enableInteractions,
          interaction_strategy: interactionStrategy,
        }),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex flex-col bg-slate-950">
      <header className="bg-linear-to-r from-blue-600 to-purple-600 shadow-lg">
        <div className="container mx-auto px-4 py-8 text-center">
          <h1 className="text-4xl font-bold text-white mb-2">🕷️ LyftrAI Assignment</h1>
          <p className="text-lg text-white/90">Advanced web scraping with static and dynamic rendering</p>
        </div>
      </header>

      <main className="flex-1 container mx-auto px-4 py-8 max-w-7xl">
        <UrlInput onScrape={handleScrape} loading={loading} />
        
        {error && (
          <div className="bg-red-500/10 border border-red-500 rounded-lg p-6 my-8">
            <h3 className="text-red-500 text-xl font-semibold mb-2">❌ Error</h3>
            <p className="text-slate-300">{error}</p>
          </div>
        )}

        {loading && (
          <div className="text-center py-16">
            <div className="w-16 h-16 border-4 border-slate-700 border-t-blue-500 rounded-full animate-spin mx-auto mb-6"></div>
            <p className="text-slate-400 text-lg">{SCRAPE_TIMEOUT_MESSAGE}</p>
          </div>
        )}

        {result && !loading && (
          <ResultViewer result={result} />
        )}
      </main>

      <footer className="bg-slate-900 border-t border-slate-800 text-center py-6">
        <p className="text-slate-400">Built for LyftrAI Assignment | Depth ≥ 3 Interactions Supported</p>
      </footer>
    </div>
  )
}

export default App
