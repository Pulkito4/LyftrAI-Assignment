import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { INTERACTION_STRATEGIES } from '@/constants'
import { useState, forwardRef } from 'react'

const UrlInput = forwardRef(({ onScrape, loading, url, setUrl }, ref) => {
  const [enableInteractions, setEnableInteractions] = useState(false)
  const [interactionStrategy, setInteractionStrategy] = useState('auto')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (url.trim()) {
      onScrape(url.trim(), enableInteractions, interactionStrategy)
    }
  }

  return (
    <Card className="bg-card border-border p-8 mb-8 shadow-sm">
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="space-y-2">
          <label htmlFor="url" className="text-sm font-semibold text-foreground">
            URL to Scrape
          </label>
          <input
            ref={ref}
            type="url"
            id="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://example.com"
            required
            disabled={loading}
            className="w-full px-4 py-3 bg-background border border-input rounded-lg text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed transition"
          />
        </div>

        <div className="flex items-center space-x-3 p-3 rounded-lg hover:bg-accent/50 transition">
          <input
            type="checkbox"
            id="interactions"
            checked={enableInteractions}
            onChange={(e) => setEnableInteractions(e.target.checked)}
            disabled={loading}
            className="w-5 h-5 rounded border-input text-primary focus:ring-2 focus:ring-primary disabled:cursor-not-allowed"
          />
          <label htmlFor="interactions" className="text-sm font-medium text-foreground cursor-pointer">
            Enable Interactions
          </label>
        </div>

        {enableInteractions && (
          <div className="space-y-2 animate-in fade-in slide-in-from-top-2 duration-200">
            <label htmlFor="strategy" className="text-sm font-semibold text-foreground">
              Interaction Strategy
            </label>
            <select
              id="strategy"
              value={interactionStrategy}
              onChange={(e) => setInteractionStrategy(e.target.value)}
              disabled={loading}
              className="w-full px-4 py-3 bg-background border border-input rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed transition"
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
          className="w-full py-6 text-lg shadow-md hover:shadow-lg transition-all disabled:opacity-60 disabled:cursor-not-allowed"
        >
          {loading ? 'Scraping...' : 'Scrape Website'}
        </Button>
      </form>
    </Card>
  )
})

export default UrlInput
