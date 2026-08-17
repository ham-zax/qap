import { Link } from '@tanstack/react-router'
import type { ReactNode } from 'react'

import { ChartAttribution } from './ChartAttribution'

interface AppShellProps {
  children: ReactNode
}

export function AppShell({ children }: AppShellProps) {
  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">
        Skip to content
      </a>
      <header className="app-header">
        <div>
          <Link className="brand" to="/">
            QAP
          </Link>
          <p>Research evidence workbench</p>
        </div>
        <nav aria-label="Primary navigation">
          <Link to="/experiments">Experiments</Link>
          <Link to="/paper-operations">Paper operations</Link>
        </nav>
      </header>
      <main id="main-content" tabIndex={-1}>
        {children}
      </main>
      <footer>
        <p>
          Read-only local evidence. Portfolio state and economics remain
          authoritative in QAP artifacts.
        </p>
        <ChartAttribution />
      </footer>
    </div>
  )
}
