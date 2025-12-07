import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import SectionList from './SectionList'
import JsonViewer from './JsonViewer'
import { DOWNLOAD_FILE_PREFIX, DOWNLOAD_FILE_EXTENSION } from '@/constants'
import { FileText, Link2, MousePointer, ArrowDown, Download, AlertTriangle, Code } from 'lucide-react'

function ResultViewer({ result }) {
  const downloadJson = () => {
    const blob = new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    const sanitizedTitle = result.meta.title.replace(/[^a-z0-9]/gi, '-').toLowerCase()
    a.download = `${DOWNLOAD_FILE_PREFIX}${sanitizedTitle}${DOWNLOAD_FILE_EXTENSION}`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  // Filter out fallback "errors" which are just informational
  const displayErrors = result.errors ? result.errors.filter(e => e.phase !== 'fallback') : []

  return (
    <Card className="bg-card border-border p-8">
      <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-6 mb-8 pb-8 border-b-2 border-border">
        <div className="flex-1">
          <h2 className="text-3xl font-bold text-primary mb-2">{result.meta.title}</h2>
          <p className="text-muted-foreground text-sm break-all mb-4">{result.url}</p>
          <div className="flex flex-wrap gap-3">
            <span className="bg-secondary px-3 py-1.5 rounded-lg text-sm font-medium text-secondary-foreground flex items-center gap-2">
              <FileText className="w-4 h-4" />
              {result.sections.length} sections
            </span>
            <span className="bg-secondary px-3 py-1.5 rounded-lg text-sm font-medium text-secondary-foreground flex items-center gap-2">
              <Link2 className="w-4 h-4" />
              {result.interactions.pages.length} pages
            </span>
            <span className="bg-secondary px-3 py-1.5 rounded-lg text-sm font-medium text-secondary-foreground flex items-center gap-2">
              <MousePointer className="w-4 h-4" />
              {Array.isArray(result.interactions.clicks) ? result.interactions.clicks.length : 0} clicks
            </span>
            <span className="bg-secondary px-3 py-1.5 rounded-lg text-sm font-medium text-secondary-foreground flex items-center gap-2">
              <ArrowDown className="w-4 h-4" />
              {result.interactions.scrolls} scrolls
            </span>
          </div>
        </div>
        <Button 
          onClick={downloadJson} 
          className="bg-green-600 hover:bg-green-700 text-white font-semibold px-6 py-3 whitespace-nowrap flex items-center gap-2"
        >
          <Download className="w-4 h-4" />
          Download JSON
        </Button>
      </div>

      {displayErrors.length > 0 && (
        <div className="bg-yellow-500/10 border border-yellow-500 rounded-lg p-6 mb-8">
          <h3 className="text-yellow-500 text-xl font-semibold mb-3 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5" />
            Warnings/Errors
          </h3>
          <div className="space-y-2">
            {displayErrors.map((err, idx) => (
              <div key={idx} className="flex gap-4">
                <span className="text-yellow-400 font-semibold shrink-0">[{err.phase}]</span>
                <span className="text-muted-foreground">{err.message}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <Tabs defaultValue="sections" className="w-full">
        <TabsList className="grid w-full grid-cols-3 bg-secondary/50 p-1">
          <TabsTrigger 
            value="sections" 
            className="data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-sm hover:bg-background/50 hover:text-foreground transition-all duration-200 flex items-center gap-2"
          >
            <FileText className="w-4 h-4" />
            Sections ({result.sections.length})
          </TabsTrigger>
          <TabsTrigger 
            value="json" 
            className="data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-sm hover:bg-background/50 hover:text-foreground transition-all duration-200 flex items-center gap-2"
          >
            <Code className="w-4 h-4" />
            Raw JSON
          </TabsTrigger>
          <TabsTrigger 
            value="interactions" 
            className="data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-sm hover:bg-background/50 hover:text-foreground transition-all duration-200 flex items-center gap-2"
          >
            <MousePointer className="w-4 h-4" />
            Interactions
          </TabsTrigger>
        </TabsList>

        <TabsContent value="sections" className="mt-6">
          <SectionList sections={result.sections} />
        </TabsContent>

        <TabsContent value="json" className="mt-6">
          <JsonViewer data={result} />
        </TabsContent>

        <TabsContent value="interactions" className="mt-6 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <Card className="bg-card border-border p-6">
              <div className="flex items-center gap-3 mb-2">
                <MousePointer className="w-5 h-5 text-primary" />
                <h3 className="text-muted-foreground text-sm font-medium">Clicks Performed</h3>
              </div>
              <p className="text-3xl font-bold text-primary">{Array.isArray(result.interactions.clicks) ? result.interactions.clicks.length : 0}</p>
            </Card>
            
            <Card className="bg-card border-border p-6">
              <div className="flex items-center gap-3 mb-2">
                <ArrowDown className="w-5 h-5 text-primary" />
                <h3 className="text-muted-foreground text-sm font-medium">Scrolls Performed</h3>
              </div>
              <p className="text-3xl font-bold text-primary">{result.interactions.scrolls}</p>
            </Card>
            
            <Card className="bg-card border-border p-6">
              <div className="flex items-center gap-3 mb-2">
                <Link2 className="w-5 h-5 text-primary" />
                <h3 className="text-muted-foreground text-sm font-medium">Pages Visited</h3>
              </div>
              <p className="text-3xl font-bold text-primary">{result.interactions.pages.length}</p>
            </Card>
          </div>

          <Card className="bg-card border-border p-6">
            <h3 className="text-primary text-xl font-semibold mb-4">Pages Visited ({result.interactions.pages.length})</h3>
            <ul className="space-y-2">
              {result.interactions.pages.map((page, idx) => (
                <li key={idx} className="bg-secondary/50 p-3 rounded-lg">
                  <a 
                    href={page} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-primary hover:text-primary/80 hover:underline break-all"
                  >
                    {page}
                  </a>
                </li>
              ))}
            </ul>
          </Card>
        </TabsContent>
      </Tabs>
    </Card>
  )
}

export default ResultViewer
