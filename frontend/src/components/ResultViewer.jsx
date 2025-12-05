import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import SectionList from './SectionList'
import JsonViewer from './JsonViewer'
import { DOWNLOAD_FILE_PREFIX, DOWNLOAD_FILE_EXTENSION } from '@/constants'

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

  return (
    <Card className="bg-slate-900 border-slate-800 p-8">
      <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-6 mb-8 pb-8 border-b-2 border-slate-800">
        <div className="flex-1">
          <h2 className="text-3xl font-bold text-blue-400 mb-2">{result.meta.title}</h2>
          <p className="text-slate-400 text-sm break-all mb-4">{result.url}</p>
          <div className="flex flex-wrap gap-3">
            <span className="bg-slate-950 px-3 py-1.5 rounded-lg text-sm font-medium text-slate-300">
              📑 {result.sections.length} sections
            </span>
            <span className="bg-slate-950 px-3 py-1.5 rounded-lg text-sm font-medium text-slate-300">
              🔗 {result.interactions.pages.length} pages
            </span>
            <span className="bg-slate-950 px-3 py-1.5 rounded-lg text-sm font-medium text-slate-300">
              🖱️ {result.interactions.clicks.length} clicks
            </span>
            <span className="bg-slate-950 px-3 py-1.5 rounded-lg text-sm font-medium text-slate-300">
              📜 {result.interactions.scrolls} scrolls
            </span>
          </div>
        </div>
        <Button 
          onClick={downloadJson} 
          className="bg-green-600 hover:bg-green-700 text-white font-semibold px-6 py-3 whitespace-nowrap"
        >
          💾 Download JSON
        </Button>
      </div>

      {result.errors && result.errors.length > 0 && (
        <div className="bg-yellow-500/10 border border-yellow-500 rounded-lg p-6 mb-8">
          <h3 className="text-yellow-500 text-xl font-semibold mb-3">⚠️ Warnings/Errors</h3>
          <div className="space-y-2">
            {result.errors.map((err, idx) => (
              <div key={idx} className="flex gap-4">
                <span className="text-yellow-400 font-semibold shrink-0">[{err.phase}]</span>
                <span className="text-slate-300">{err.message}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <Tabs defaultValue="sections" className="w-full">
        <TabsList className="grid w-full grid-cols-3 bg-slate-950">
          <TabsTrigger value="sections" className="data-[state=active]:bg-blue-600">
            📑 Sections ({result.sections.length})
          </TabsTrigger>
          <TabsTrigger value="json" className="data-[state=active]:bg-blue-600">
            📄 Raw JSON
          </TabsTrigger>
          <TabsTrigger value="interactions" className="data-[state=active]:bg-blue-600">
            🔄 Interactions
          </TabsTrigger>
        </TabsList>

        <TabsContent value="sections" className="mt-6">
          <SectionList sections={result.sections} />
        </TabsContent>

        <TabsContent value="json" className="mt-6">
          <JsonViewer data={result} />
        </TabsContent>

        <TabsContent value="interactions" className="mt-6 space-y-6">
          <Card className="bg-slate-950 border-slate-800 p-6">
            <h3 className="text-blue-400 text-xl font-semibold mb-4">Pages Visited ({result.interactions.pages.length})</h3>
            <ul className="space-y-2">
              {result.interactions.pages.map((page, idx) => (
                <li key={idx} className="bg-slate-900 p-3 rounded-lg">
                  <a 
                    href={page} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-blue-400 hover:text-blue-300 hover:underline break-all"
                  >
                    {page}
                  </a>
                </li>
              ))}
            </ul>
          </Card>

          {result.interactions.clicks.length > 0 && (
            <Card className="bg-slate-950 border-slate-800 p-6">
              <h3 className="text-blue-400 text-xl font-semibold mb-4">Clicks ({result.interactions.clicks.length})</h3>
              <ul className="space-y-2">
                {result.interactions.clicks.map((click, idx) => (
                  <li key={idx} className="bg-slate-900 p-3 rounded-lg text-slate-300">{click}</li>
                ))}
              </ul>
            </Card>
          )}

          {result.interactions.scrolls > 0 && (
            <Card className="bg-slate-950 border-slate-800 p-6">
              <h3 className="text-blue-400 text-xl font-semibold mb-4">Scrolls</h3>
              <p className="text-slate-300">Scrolled {result.interactions.scrolls} times</p>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </Card>
  )
}

export default ResultViewer
