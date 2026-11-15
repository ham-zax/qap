import { Link, useRouterState } from '@tanstack/react-router'
import type { ReactNode } from 'react'

import type { WorkspaceStatusDto } from '../api/types'
import { ChartAttribution } from './ChartAttribution'
import { ScreenGuide, screenGuideForPath } from './ScreenGuide'
import { ThemeToggle } from './ui/ThemeToggle'

interface AppShellProps {
  children: ReactNode
  workspaceMode?: WorkspaceStatusDto['workspace_mode']
  collectorStatus?: WorkspaceStatusDto['current_evidence_collector_status']
}

const navLinkClass =
  'flex min-h-10 flex-1 items-center justify-center rounded-md px-3 py-1.5 text-sm font-semibold no-underline transition-[background-color,color] duration-150 md:flex-none'

function navClass(active: boolean) {
  return `${navLinkClass} ${active ? 'bg-subtle text-foreground' : 'text-secondary hover:bg-subtle hover:text-foreground'}`
}

export function AppShell({ children, workspaceMode, collectorStatus }: AppShellProps) {
  const pathname = useRouterState({ select: (state) => state.location.pathname })
  const guide = screenGuideForPath(pathname)
  const onLab = pathname === '/lab'
  const onActivity = pathname === '/operations' || pathname.startsWith('/operations/')

  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">
        Skip to content
      </a>
      <header className="app-header flex flex-col gap-3 border-b border-border py-3 md:flex-row md:items-center md:justify-between">
        <div className="flex flex-row flex-wrap items-center gap-x-4 gap-y-1">
          <Link className="brand" to="/">
            QAP
          </Link>
          {workspaceMode ? (
            <span className="rounded-full border border-border px-2 py-0.5 text-xs text-muted">
              {workspaceMode === 'sample' ? 'Read-only examples' : 'Local workspace'}
            </span>
          ) : null}
          {workspaceMode === 'local_market' && collectorStatus && collectorStatus !== 'running' ? (
            <Link className="text-xs text-warning" to="/operations">
              {collectorStatus === 'failed' ? 'Background collection failed' : 'Background collection is stopped'}
            </Link>
          ) : null}
        </div>
        <div className="flex w-full flex-col gap-2 md:w-auto md:flex-row md:items-center md:gap-4">
          <nav className="flex w-full flex-row gap-1 md:w-auto" aria-label="Primary navigation">
            <Link className={navClass(onLab)} aria-current={onLab ? 'page' : undefined} to="/lab">
              Lab
            </Link>
            <Link
              className={navClass(onActivity)}
              aria-current={onActivity ? 'page' : undefined}
              to="/operations"
            >
              Activity
            </Link>
          </nav>
          <div className="flex items-center justify-end gap-3">
            <ThemeToggle />
          </div>
        </div>
      </header>
      <main id="main-content" tabIndex={-1}>
        {children}
        {guide ? <ScreenGuide guide={guide} /> : null}
      </main>
      <footer>
        <p>Research only. Trades are simulated. No real orders are placed.</p>
        <ChartAttribution />
      </footer>
    </div>
  )
}
