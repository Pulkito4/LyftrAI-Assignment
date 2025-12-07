import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { Toaster } from 'sonner'
import { QueryProvider } from './lib/react-query/QueryProvider'
import './index.css'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <QueryProvider>
      <Toaster position="top-center" richColors />
      <App />
    </QueryProvider>
  </StrictMode>,
)
