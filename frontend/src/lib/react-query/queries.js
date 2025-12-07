import { useMutation } from '@tanstack/react-query'
import { API_ENDPOINTS } from '../../constants'

// Cache for storing scrape results (simple in-memory cache)
// We can keep this here or move it to a separate store if needed
const scrapeCache = new Map()

export const useScrapeMutation = ({ onSuccess, onError }) => {
  return useMutation({
    mutationFn: async ({ url, enableInteractions, interactionStrategy }) => {
      // Check cache first
      const cacheKey = `${url}-${enableInteractions}-${interactionStrategy}`
      if (scrapeCache.has(cacheKey)) {
        const cached = scrapeCache.get(cacheKey)
        // Check if cache is less than 1 hour old
        if (Date.now() - cached.timestamp < 60 * 60 * 1000) {
          return { ...cached.data, fromCache: true }
        }
      }

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
      
      // Store in cache
      scrapeCache.set(cacheKey, { data, timestamp: Date.now() })
      
      return data
    },
    onSuccess,
    onError,
  })
}
