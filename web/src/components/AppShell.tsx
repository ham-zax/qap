import { Link, useRouterState } from '@tanstack/react-router'
import { AlertTriangle } from 'lucide-react'
import type { ReactNode } from 'react'

import type { WorkspaceStatusDto } from '../api/types'
import { AppShellHeaderModeContext, useLabViewMode } from '../features/lab/labStorage'
import { cn } from '@/lib/utils'
import { Button } from './ui/button'
import { ThemeToggle } from './ui/theme-toggle'
import { ChartAttribution } from './ChartAttribution'
import { ScreenGuide, screenGuideForPath } from './ScreenGuide'

interface AppShellProps {
  children: ReactNode
  workspaceMode?: WorkspaceStatusDto['workspace_mode']
  collectorStatus?: WorkspaceStatusDto['current_evidence_collector_status']
}

function navClass(active: boolean) {
  return cn(
    'inline-flex h-8 items-center justify-center rounded-md px-2.5 text-sm font-medium no-underline transition-colors',
    active
      ? 'bg-secondary text-foreground shadow-xs'
      : 'text-muted-foreground hover:bg-secondary/70 hover:text-foreground',
  )
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
        <header className="app-header flex flex-row items-center justify-between gap-2 border-b border-border py-1.5">
          <div className="flex flex-row items-center gap-3">
            <Link className="brand tracking-tight" to="/">
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
              <Link
                className="inline-flex items-center gap-1 rounded-md border border-warning/35 bg-warning/10 px-2 py-1 text-xs font-medium text-warning no-underline hover:bg-warning/15"
                to="/operations"
              >
                <AlertTriangle className="size-3.5 shrink-0" aria-hidden="true" />
                {collectorStatus === 'failed' ? 'Background collection failed' : 'Background collection is stopped'}
              </Link>
            ) : null}
            {onLab ? (
              <div
                className="inline-flex items-center gap-0.5 rounded-lg border border-border bg-muted p-0.5"
                role="group"
                aria-label="View mode"
              >
                <Button
                  type="button"
                  size="sm"
                  variant={viewMode === 'simple' ? 'secondary' : 'ghost'}
                  aria-pressed={viewMode === 'simple'}
                  onClick={() => setViewMode('simple')}
                  className={cn(
                    'h-7 rounded-md px-2.5 text-xs font-medium',
                    viewMode === 'simple'
                      ? 'bg-background text-foreground shadow-xs'
                      : 'text-muted-foreground hover:text-foreground',
                  )}
                >
                  Simple
                </Button>
                <Button
                  type="button"
                  size="sm"
                  variant={viewMode === 'advanced' ? 'secondary' : 'ghost'}
                  aria-pressed={viewMode === 'advanced'}
                  onClick={() => setViewMode('advanced')}
                  className={cn(
                    'h-7 rounded-md px-2.5 text-xs font-medium',
                    viewMode === 'advanced'
                      ? 'bg-background text-foreground shadow-xs'
                      : 'text-muted-foreground hover:text-foreground',
                  )}
                >
                  Pro
                </Button>
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
