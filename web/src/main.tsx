import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'

import { App, createQapApp } from './app'
import { initializeTheme } from './lib/theme'
import '@fontsource-variable/geist'
import '@fontsource-variable/geist-mono'
import './styles/global.css'

const rootElement = document.getElementById('root')
if (!rootElement) {
  throw new Error('QAP root element is missing')
}

initializeTheme()

const app = createQapApp({
  baseUrl: import.meta.env.VITE_QAP_API_BASE_URL ?? '',
})

createRoot(rootElement).render(
  <StrictMode>
    <App {...app} />
  </StrictMode>,
)
