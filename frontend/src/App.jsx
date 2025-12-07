import { useState, useEffect, useRef } from 'react'
import { useScrapeMutation } from './lib/react-query/queries'
import UrlInput from './components/UrlInput'
import ResultViewer from './components/ResultViewer'
import { SCRAPE_TIMEOUT_MESSAGE } from './constants'
import { Moon, Sun, History, Trash2, AlertCircle, Loader2 } from 'lucide-react'
import { toast } from 'sonner'

function App() {
  const [url, setUrl] = useState('')
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [recentScrapes, setRecentScrapes] = useState([])
  const [theme, setTheme] = useState('dark')
  const urlInputRef = useRef(null)

  // Load recent scrapes and theme from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem('recentScrapes')
    if (saved) {
      setRecentScrapes(JSON.parse(saved))
    }
    const savedTheme = localStorage.getItem('theme') || 'dark'
    setTheme(savedTheme)
    if (savedTheme === 'dark') {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [])

  // React Query mutation for scraping
  const scrapeMutation = useScrapeMutation({
    onSuccess: (data, variables) => {
      setResult(data)
      setError(null)
      
      // Add to recent scrapes
      const newScrape = {
        url: variables.url,
        title: data.meta.title,
        timestamp: Date.now(),
        id: Date.now().toString(),
      }
      const updated = [newScrape, ...recentScrapes.filter(s => s.url !== variables.url)].slice(0, 10)
      setRecentScrapes(updated)
      localStorage.setItem('recentScrapes', JSON.stringify(updated))
      
      toast.success('Scraping completed successfully!', {
        description: `Extracted data from ${new URL(variables.url).hostname}`
      })
    },
    onError: (err) => {
      setError(err.message)
      setResult(null)
      toast.error('Scraping failed', {
        description: err.message
      })
    },
  })

  const handleScrape = (scrapeUrl, enableInteractions, interactionStrategy) => {
    scrapeMutation.mutate({ url: scrapeUrl, enableInteractions, interactionStrategy })
  }

  const clearHistory = () => {
    setRecentScrapes([])
    localStorage.removeItem('recentScrapes')
    toast.info('History cleared')
  }

  const toggleTheme = () => {
    const newTheme = theme === 'dark' ? 'light' : 'dark'
    setTheme(newTheme)
    localStorage.setItem('theme', newTheme)
    if (newTheme === 'dark') {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
    // Dispatch custom event for child components
    window.dispatchEvent(new Event('themeChange'))
  }

  return (
    <div className="min-h-screen flex flex-col bg-background text-foreground transition-colors font-sans">
      <header className="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold bg-linear-to-r from-primary to-purple-600 bg-clip-text text-transparent">
              LyftrAI
            </h1>
            <span className="text-xs font-medium px-2 py-1 rounded-full bg-primary/10 text-primary">
              v1.0
            </span>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 bg-secondary/50 p-1 rounded-full border border-border">
              <button
                onClick={() => theme !== 'light' && toggleTheme()}
                className={`p-1.5 rounded-full transition-all ${theme === 'light' ? 'bg-background shadow-sm text-yellow-500' : 'text-muted-foreground hover:text-foreground'}`}
              >
                <Sun size={16} />
              </button>
              <button
                onClick={() => theme !== 'dark' && toggleTheme()}
                className={`p-1.5 rounded-full transition-all ${theme === 'dark' ? 'bg-background shadow-sm text-blue-400' : 'text-muted-foreground hover:text-foreground'}`}
              >
                <Moon size={16} />
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="flex-1 flex">
        {/* Recent Scrapes Sidebar */}
        <aside className="w-72 bg-card border-r border-border hidden md:flex flex-col h-[calc(100vh-73px)] sticky top-[73px]">
          <div className="p-4 border-b border-border flex justify-between items-center">
            <div className="flex items-center gap-2 text-sm font-semibold text-muted-foreground">
              <History size={16} />
              <span>HISTORY</span>
            </div>
            {recentScrapes.length > 0 && (
              <button 
                onClick={clearHistory}
                className="text-xs text-muted-foreground hover:text-destructive transition-colors p-1 rounded hover:bg-destructive/10"
                title="Clear History"
              >
                <Trash2 size={14} />
              </button>
            )}
          </div>
          
          <div className="flex-1 overflow-y-auto p-2 space-y-1">
            {recentScrapes.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground text-sm px-4">
                <p>No recent scrapes.</p>
                <p className="text-xs mt-1 opacity-70">Your history will appear here.</p>
              </div>
            ) : (
              recentScrapes.map((scrape) => (
                <button
                  key={scrape.id}
                  onClick={() => {
                    setUrl(scrape.url)
                    window.scrollTo({ top: 0, behavior: 'smooth' })
                    urlInputRef.current?.focus()
                  }}
                  className="w-full text-left p-3 rounded-lg hover:bg-accent transition-colors group border border-transparent hover:border-border relative"
                >
                  <div className="font-medium truncate mb-1 text-sm group-hover:text-primary transition-colors pr-2">
                    {scrape.title || 'Untitled Page'}
                  </div>
                  <div className="text-muted-foreground text-xs truncate flex justify-between items-center">
                    <span>{new URL(scrape.url).hostname}</span>
                    <span className="opacity-50 text-[10px]">{new Date(scrape.timestamp).toLocaleDateString()}</span>
                  </div>
                </button>
              ))
            )}
          </div>
        </aside>

        <main className="flex-1 container mx-auto px-4 py-8 max-w-5xl">
          <div className="mb-8 text-center">
            <h2 className="text-3xl font-bold mb-2">Web Scraper</h2>
            <p className="text-muted-foreground">Extract data from any website with intelligent dynamic rendering</p>
          </div>

          <UrlInput 
            ref={urlInputRef}
            onScrape={handleScrape} 
            loading={scrapeMutation.isPending} 
            url={url}
            setUrl={setUrl}
          />
          
          {error && (
            <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-6 my-8 flex items-start gap-4 animate-in fade-in slide-in-from-top-2">
              <div className="p-2 bg-destructive/20 rounded-full text-destructive shrink-0">
                <AlertCircle size={24} />
              </div>
              <div>
                <h3 className="text-destructive font-semibold mb-1">Scraping Failed</h3>
                <p className="text-muted-foreground text-sm">{error}</p>
                <p className="text-xs text-muted-foreground mt-2">Check the URL and try again. If the issue persists, the site might be blocking automated access.</p>
              </div>
            </div>
          )}

          {scrapeMutation.isPending && (
            <div className="py-12 px-6 bg-card/50 rounded-xl border border-border border-dashed animate-in fade-in">
              <div className="max-w-md mx-auto">
                <div className="mb-6">
                  <div className="h-2 w-full bg-secondary rounded-full overflow-hidden">
                    <div className="h-full bg-primary animate-progress-indeterminate origin-left"></div>
                  </div>
                  <p className="text-center text-sm text-muted-foreground mt-2">{SCRAPE_TIMEOUT_MESSAGE}</p>
                </div>
                
                <div className="space-y-4">
                  <div className="flex items-center gap-3 text-sm text-muted-foreground">
                    <div className="w-2 h-2 bg-primary rounded-full animate-pulse"></div>
                    <span>Analyzing page structure...</span>
                  </div>
                  <div className="flex items-center gap-3 text-sm text-muted-foreground">
                    <div className="w-2 h-2 bg-primary rounded-full animate-pulse delay-300"></div>
                    <span>Handling dynamic content & interactions...</span>
                  </div>
                  <div className="flex items-center gap-3 text-sm text-muted-foreground">
                    <div className="w-2 h-2 bg-primary rounded-full animate-pulse delay-700"></div>
                    <span>Extracting metadata and content...</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {result && !scrapeMutation.isPending && (
            <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
              {result.fromCache && (
                <div className="flex items-center gap-2 text-xs text-primary bg-primary/10 w-fit px-3 py-1 rounded-full mb-4 border border-primary/20">
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>
                  Loaded from cache
                </div>
              )}
              <ResultViewer result={result} />
            </div>
          )}
        </main>
      </div>

      <footer className="border-t border-border py-8 mt-auto bg-card/30">
        <div className="container mx-auto px-4 text-center text-sm text-muted-foreground">
          <p>© {new Date().getFullYear()} LyftrAI Assignment.</p>
        </div>
      </footer>
    </div>
  )
}

export default App
