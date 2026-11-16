import { Link, useRouterState } from '@tanstack/react-router'
import type { ReactNode } from 'react'

import type { WorkspaceStatusDto } from '../api/types'
import { AppShellHeaderModeContext, useLabViewMode } from '../features/lab/labStorage'
import { ChartAttribution } from './ChartAttribution'
import { ScreenGuide, screenGuideForPath } from './ScreenGuide'
import { ThemeToggle } from './ui/ThemeToggle'

interface AppShellProps {
  children: ReactNode
  workspaceMode?: WorkspaceStatusDto['workspace_mode']
  collectorStatus?: WorkspaceStatusDto['current_evidence_collector_status']
}

const navLinkClass =
  'flex min-h-9 items-center justify-center rounded-md px-2.5 py-1.5 text-sm font-semibold no-underline transition-[background-color,color] duration-150'

function navClass(active: boolean) {
  return `${navLinkClass} ${active ? 'bg-subtle text-foreground' : 'text-secondary hover:bg-subtle hover:text-foreground'}`
}

export function AppShell({ children, workspaceMode, collectorStatus }: AppShellProps) {
  const pathname = useRouterState({ select: (state) => state.location.pathname })
  const [viewMode, setViewMode] = useLabViewMode()
  const guide = screenGuideForPath(pathname)
  const onLab = pathname === '/lab'
  const onActivity = pathname === '/operations' || pathname.startsWith('/operations/')
  const collectorWarning = workspaceMode === 'local_market' && collectorStatus && collectorStatus !== 'running'

  return (
    <AppShellHeaderModeContext.Provider value={onLab}>
      <div className="app-shell">
        <a className="skip-link" href="#main-content">
          Skip to content
        </a>
        <header className="app-header flex flex-row items-center justify-between gap-2 border-b border-border py-1">
          <div className="flex flex-row items-center gap-3">
            <Link className="brand" to="/">
              QAP
            </Link>
            <nav className="flex flex-row items-center gap-1" aria-label="Primary navigation">
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
          </div>
          <div className="flex flex-row items-center gap-2">
            {collectorWarning ? (
              <Link className="text-xs text-warning" to="/operations">
                {collectorStatus === 'failed' ? 'Background collection failed' : 'Background collection is stopped'}
              </Link>
            ) : null}
            {onLab ? (
              <div className="bt-segmented" role="group" aria-label="View mode">
                <button type="button" aria-pressed={viewMode === 'simple'} onClick={() => setViewMode('simple')}>
                  Simple
                </button>
                <button type="button" aria-pressed={viewMode === 'advanced'} onClick={() => setViewMode('advanced')}>
                  Pro
                </button>
              </div>
            ) : null}
            <ThemeToggle />
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
    </AppShellHeaderModeContext.Provider>
  )
}
