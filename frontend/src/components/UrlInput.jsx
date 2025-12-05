import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { INTERACTION_STRATEGIES } from '@/constants'

function UrlInput({ onScrape, loading }) {
  const [url, setUrl] = useState('')
  const [enableInteractions, setEnableInteractions] = useState(false)
  const [interactionStrategy, setInteractionStrategy] = useState('auto')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (url.trim()) {
      onScrape(url.trim(), enableInteractions, interactionStrategy)
    }
  }

  return (
    <Card className="bg-slate-900 border-slate-800 p-8 mb-8">
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="space-y-2">
          <label htmlFor="url" className="text-sm font-semibold text-slate-200">
            URL to Scrape
          </label>
          <input
            type="url"
            id="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://example.com"
            required
            disabled={loading}
            className="w-full px-4 py-3 bg-slate-950 border border-slate-700 rounded-lg text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed transition"
          />
        </div>

        <div className="flex items-center space-x-3 p-3 rounded-lg hover:bg-slate-800 transition">
          <input
            type="checkbox"
            id="interactions"
            checked={enableInteractions}
            onChange={(e) => setEnableInteractions(e.target.checked)}
            disabled={loading}
            className="w-5 h-5 rounded border-slate-700 text-blue-500 focus:ring-2 focus:ring-blue-500 disabled:cursor-not-allowed"
          />
          <label htmlFor="interactions" className="text-sm font-medium text-slate-200 cursor-pointer">
            Enable Interactions (Depth ≥ 3)
          </label>
        </div>

        {enableInteractions && (
          <div className="space-y-2 animate-in fade-in slide-in-from-top-2 duration-200">
            <label htmlFor="strategy" className="text-sm font-semibold text-slate-200">
              Interaction Strategy
            </label>
            <select
              id="strategy"
              value={interactionStrategy}
              onChange={(e) => setInteractionStrategy(e.target.value)}
              disabled={loading}
              className="w-full px-4 py-3 bg-slate-950 border border-slate-700 rounded-lg text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed transition"
            >
              {INTERACTION_STRATEGIES.map((strategy) => (
                <option key={strategy.value} value={strategy.value}>
                  {strategy.label}
                </option>
              ))}
            </select>
          </div>
        )}

        <Button 
          type="submit" 
          disabled={loading}
          className="w-full bg-linear-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-semibold py-6 text-lg shadow-lg hover:shadow-xl transition-all disabled:opacity-60 disabled:cursor-not-allowed"
        >
          {loading ? 'Scraping...' : '🚀 Scrape Website'}
        </Button>
      </form>
    </Card>
  )
}

export default UrlInput
