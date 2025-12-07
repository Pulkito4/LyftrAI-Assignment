import { Light as SyntaxHighlighter } from 'react-syntax-highlighter'
import json from 'react-syntax-highlighter/dist/esm/languages/hljs/json'
import { atomOneDark, atomOneLight } from 'react-syntax-highlighter/dist/esm/styles/hljs'
import { useEffect, useState } from 'react'

// Register JSON language
SyntaxHighlighter.registerLanguage('json', json)

function JsonViewer({ data }) {
  const [theme, setTheme] = useState('dark')

  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') || 'dark'
    setTheme(savedTheme)
    
    // Listen for theme changes via custom event
    const handleThemeChange = () => {
      setTheme(localStorage.getItem('theme') || 'dark')
    }
    window.addEventListener('themeChange', handleThemeChange)
    return () => window.removeEventListener('themeChange', handleThemeChange)
  }, [])

  return (
    <div className="rounded-lg overflow-hidden border border-border">
      <SyntaxHighlighter
        language="json"
        style={theme === 'dark' ? atomOneDark : atomOneLight}
        customStyle={{
          margin: 0,
          padding: '1.5rem',
          fontSize: '0.875rem',
          maxHeight: '600px',
          background: theme === 'dark' ? '#0f172a' : '#ffffff', // Match card background
        }}
        wrapLongLines={true}
      >
        {JSON.stringify(data, null, 2)}
      </SyntaxHighlighter>
    </div>
  )
}

export default JsonViewer
