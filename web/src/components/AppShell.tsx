import { Link } from '@tanstack/react-router'
import type { ReactNode } from 'react'

import { ChartAttribution } from './ChartAttribution'

interface AppShellProps {
  children: ReactNode
}

const navLinkClass =
  'flex min-h-11 w-auto flex-1 items-center justify-center rounded-md border border-transparent px-3 py-2 text-sm font-semibold text-secondary no-underline transition-[background-color,border-color,color] duration-150 hover:bg-subtle hover:text-foreground data-[status=active]:border-border data-[status=active]:bg-subtle data-[status=active]:text-foreground md:flex-none'

export function AppShell({ children }: AppShellProps) {
  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">
        Skip to content
      </a>
      <header className="app-header flex flex-col gap-3 border-b border-border py-4 md:flex-row md:items-center md:justify-between">
        <div className="flex flex-row flex-wrap items-baseline gap-x-3 gap-y-1">
          <Link className="brand" to="/">
            QAP
          </Link>
          <p className="text-xs text-muted sm:text-sm">Research evidence workbench</p>
        </div>
        <nav className="flex w-full flex-row gap-2 md:w-auto" aria-label="Primary navigation">
          <Link className={navLinkClass} to="/scanner">
            Discovery
          </Link>
          <Link className={navLinkClass} to="/prospective">
            Prospective
          </Link>
          <Link className={navLinkClass} to="/experiments">
            Research runs
          </Link>
          <Link className={navLinkClass} to="/paper-operations">
            Paper operations
          </Link>
        </nav>
      </header>
      <main id="main-content" tabIndex={-1}>
        {children}
      </main>
      <footer>
        <p>
          Local research application. Portfolio state, economics, and scientific
          evidence remain authoritative in QAP artifacts.
        </p>
        <ChartAttribution />
      </footer>
    </div>
  )
}
