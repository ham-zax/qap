import { Link, useRouterState } from '@tanstack/react-router'
import type { ReactNode } from 'react'

import type { WorkspaceStatusDto } from '../api/types'
import { ChartAttribution } from './ChartAttribution'
import { ScreenGuide, screenGuideForPath } from './ScreenGuide'
import { Badge } from './ui/Badge'

interface AppShellProps {
  children: ReactNode
  workspaceMode?: WorkspaceStatusDto['workspace_mode']
  collectorStatus?: WorkspaceStatusDto['current_evidence_collector_status']
}

const navLinkClass =
  'flex min-h-11 w-auto flex-1 items-center justify-center rounded-md border border-transparent px-3 py-2 text-sm font-semibold text-secondary no-underline transition-[background-color,border-color,color] duration-150 hover:bg-subtle hover:text-foreground data-[status=active]:border-border data-[status=active]:bg-subtle data-[status=active]:text-foreground md:flex-none'

export function AppShell({ children, workspaceMode, collectorStatus }: AppShellProps) {
  const pathname = useRouterState({ select: (state) => state.location.pathname })
  const guide = screenGuideForPath(pathname)

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
          {workspaceMode ? (
            <Badge tone={workspaceMode === 'sample' ? 'warning' : 'neutral'}>
              {workspaceMode === 'sample' ? 'Sample Workspace' : 'Local Market'}
            </Badge>
          ) : null}
          {workspaceMode === 'sample' ? (
            <Badge tone="neutral">Current evidence collection disabled</Badge>
          ) : workspaceMode === 'local_market' && collectorStatus ? (
            <Badge
              tone={
                collectorStatus === 'running'
                  ? 'positive'
                  : collectorStatus === 'failed'
                    ? 'negative'
                    : 'warning'
              }
            >
              {collectorStatus === 'running'
                ? 'Current evidence collector running'
                : collectorStatus === 'failed'
                  ? 'Current evidence collector failed'
                  : 'Current evidence collector not running'}
            </Badge>
          ) : null}
          <Link className="text-xs font-semibold text-muted hover:text-foreground" to="/operations">
            Activity
          </Link>
        </div>
        <nav
          className="flex w-full flex-row flex-wrap gap-2 md:w-auto md:flex-nowrap"
          aria-label="Primary navigation"
        >
          <Link activeOptions={{ exact: true }} className={navLinkClass} to="/">
            Home
          </Link>
          <Link className={navLinkClass} to="/scanner">
            Research
          </Link>
          <Link className={navLinkClass} to="/baskets">
            Portfolios
          </Link>
          <Link className={navLinkClass} to="/experiments">
            History
          </Link>
        </nav>
      </header>
      <main id="main-content" tabIndex={-1}>
        {guide ? <ScreenGuide guide={guide} /> : null}
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
