import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  Target, Navigation, FileText, DollarSign, HelpCircle, 
  List, Grid, Circle, Hash, Type, Link2, Image, ListOrdered, Table 
} from 'lucide-react'
import { SECTION_TYPE_ICONS, MAX_ITEMS_TO_DISPLAY, TEXT_PREVIEW_LENGTH } from '@/constants'

function SectionList({ sections }) {
  const getSectionIcon = (type) => {
    const iconMap = {
      Target, Navigation, FileText, DollarSign, HelpCircle, List, Grid, Circle
    }
    const iconName = SECTION_TYPE_ICONS[type] || SECTION_TYPE_ICONS.unknown
    const Icon = iconMap[iconName] || Circle
    return <Icon className="w-4 h-4" />
  }

  if (sections.length === 0) {
    return (
      <div className="text-center py-12 text-slate-400">
        <p>No sections found in the scraped content.</p>
      </div>
    )
  }

  return (
    <Accordion type="single" collapsible className="space-y-4">
      {sections.map((section) => (
        <AccordionItem 
          key={section.id} 
          value={section.id}
          className="bg-slate-950 border border-slate-800 rounded-lg overflow-hidden hover:border-blue-500 transition"
        >
          <AccordionTrigger className="px-6 py-4 hover:bg-slate-900 transition">
            <div className="flex flex-col items-start gap-2 text-left">
              <span className="text-xs font-semibold text-slate-400 uppercase flex items-center gap-2">
                {getSectionIcon(section.type)} {section.type}
              </span>
              <h3 className="text-lg text-slate-200 font-medium">{section.label}</h3>
            </div>
          </AccordionTrigger>

          <AccordionContent className="px-6 py-4 space-y-6 border-t border-slate-800">
            <Tabs defaultValue="readable" className="w-full">
              <TabsList className="grid w-full grid-cols-2 bg-slate-900">
                <TabsTrigger value="readable">Human Readable</TabsTrigger>
                <TabsTrigger value="json">Raw JSON</TabsTrigger>
              </TabsList>
              
              <TabsContent value="readable" className="space-y-6 mt-6">
                <div className="space-y-3">
                  <h4 className="text-blue-400 font-semibold">Content Summary</h4>
                  <div className="flex flex-wrap gap-2">
                    <span className="bg-slate-900 px-3 py-1.5 rounded text-sm text-slate-300 flex items-center gap-1.5">
                      <Hash className="w-4 h-4" /> Headings: {section.content.headings.length}
                    </span>
                    <span className="bg-slate-900 px-3 py-1.5 rounded text-sm text-slate-300 flex items-center gap-1.5">
                      <Type className="w-4 h-4" /> Text: {section.content.text.length} chars
                    </span>
                    <span className="bg-slate-900 px-3 py-1.5 rounded text-sm text-slate-300 flex items-center gap-1.5">
                      <Link2 className="w-4 h-4" /> Links: {section.content.links.length}
                    </span>
                    <span className="bg-slate-900 px-3 py-1.5 rounded text-sm text-slate-300 flex items-center gap-1.5">
                      <Image className="w-4 h-4" /> Images: {section.content.images.length}
                    </span>
                    <span className="bg-slate-900 px-3 py-1.5 rounded text-sm text-slate-300 flex items-center gap-1.5">
                      <ListOrdered className="w-4 h-4" /> Lists: {section.content.lists.length}
                    </span>
                    <span className="bg-slate-900 px-3 py-1.5 rounded text-sm text-slate-300 flex items-center gap-1.5">
                      <Table className="w-4 h-4" /> Tables: {section.content.tables.length}
                    </span>
                  </div>
                </div>

            {section.content.headings.length > 0 && (
              <div className="space-y-3">
                <h4 className="text-blue-400 font-semibold">Headings</h4>
                <ul className="space-y-2">
                  {section.content.headings.slice(0, MAX_ITEMS_TO_DISPLAY.HEADINGS).map((heading, idx) => (
                    <li key={idx} className="bg-slate-900 p-3 rounded text-slate-300">
                      {heading}
                    </li>
                  ))}
                  {section.content.headings.length > MAX_ITEMS_TO_DISPLAY.HEADINGS && (
                    <li className="text-slate-500 italic">
                      ... and {section.content.headings.length - MAX_ITEMS_TO_DISPLAY.HEADINGS} more
                    </li>
                  )}
                </ul>
              </div>
            )}

            {section.content.text && (
              <div className="space-y-3">
                <h4 className="text-blue-400 font-semibold">Text Content</h4>
                <p className="bg-slate-900 p-4 rounded leading-relaxed text-slate-300">
                  {section.content.text.slice(0, TEXT_PREVIEW_LENGTH)}
                  {section.content.text.length > TEXT_PREVIEW_LENGTH && '...'}
                </p>
              </div>
            )}

            {section.content.links.length > 0 && (
              <div className="space-y-3">
                <h4 className="text-blue-400 font-semibold">Links ({section.content.links.length})</h4>
                <ul className="space-y-2">
                  {section.content.links.slice(0, MAX_ITEMS_TO_DISPLAY.LINKS).map((link, idx) => (
                    <li key={idx} className="bg-slate-900 p-3 rounded">
                      <a 
                        href={link.href} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-blue-400 hover:text-blue-300 hover:underline break-all"
                      >
                        {link.text || link.href}
                      </a>
                    </li>
                  ))}
                  {section.content.links.length > MAX_ITEMS_TO_DISPLAY.LINKS && (
                    <li className="text-slate-500 italic">
                      ... and {section.content.links.length - MAX_ITEMS_TO_DISPLAY.LINKS} more
                    </li>
                  )}
                </ul>
              </div>
            )}

            {section.content.images.length > 0 && (
              <div className="space-y-3">
                <h4 className="text-blue-400 font-semibold">Images ({section.content.images.length})</h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {section.content.images.slice(0, MAX_ITEMS_TO_DISPLAY.IMAGES).map((img, idx) => (
                    <div key={idx} className="space-y-2">
                      <img 
                        src={img.src} 
                        alt={img.alt} 
                        loading="lazy"
                        className="w-full h-32 object-cover rounded-lg bg-slate-900"
                      />
                      {img.alt && (
                        <p className="text-xs text-slate-400 truncate">{img.alt}</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

                <div className="space-y-3">
                  <h4 className="text-blue-400 font-semibold">Raw HTML</h4>
                  <pre className="bg-slate-900 p-4 rounded-lg overflow-x-auto text-sm leading-relaxed text-slate-300 max-h-80 overflow-y-auto">
                    {section.rawHtml}
                    {section.truncated && <span className="text-yellow-400 italic">{'\n'}... (truncated)</span>}
                  </pre>
                </div>
              </TabsContent>
              
              <TabsContent value="json" className="mt-6">
                <pre className="bg-slate-900 p-4 rounded-lg overflow-x-auto text-sm leading-relaxed text-slate-300 max-h-[600px] overflow-y-auto">
                  {JSON.stringify(section, null, 2)}
                </pre>
              </TabsContent>
            </Tabs>
          </AccordionContent>
        </AccordionItem>
      ))}
    </Accordion>
  )
}

export default SectionList
