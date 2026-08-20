import { useState } from 'react'

import type { QapApiClient } from '../../api/client'
import type { QapQueries } from '../../api/queries'
import type {
  ScanListDto,
  ScannerProtocolDto,
  WorkspaceStatusDto,
} from '../../api/types'
import { Badge } from '../../components/ui/Badge'
import { formatResearchTimestamp } from '../../lib/format'
import { DiscoveryHome } from './DiscoveryHome'
import { ExperimentLab } from './ExperimentLab'
import { PairResearch } from './PairResearch'
import { ProductResearch } from './ProductResearch'

interface ResearchHomeProps {
  apiClient: QapApiClient
  queries: QapQueries
  workspace: WorkspaceStatusDto
  protocol: ScannerProtocolDto
  scans: ScanListDto
}

function timeframeLabel(value: string): string {
  if (value === 'short') return 'Short-term'
  if (value === 'medium') return 'Medium-term'
  if (value === 'swing') return 'Longer-term'
  return value
}

export function ResearchHome({
  apiClient,
  queries,
  workspace,
  protocol,
  scans,
}: ResearchHomeProps) {
  const [activeTask, setActiveTask] = useState<'pair' | 'scan' | 'lab'>('pair')

  return (
    <section className="min-w-0">
      <header className="mb-8 max-w-4xl">
        <p className="mb-2 text-xs font-semibold uppercase tracking-[0.1em] text-accent">
          Research
        </p>
        <h1 className="mb-3 text-3xl font-bold tracking-tight text-foreground md:text-4xl">
          Start from the research question
        </h1>
        <p className="m-0 text-sm leading-6 text-secondary md:text-base">
          Research one pair directly, scan the approved universe, or use Experiment Lab
          when you need an explicit typed recipe. Scientific and economic decisions remain
          backend-owned.
        </p>
      </header>

      <nav
        className="mb-6 flex flex-wrap gap-2 rounded-lg border border-border bg-panel p-2"
        aria-label="Research task"
      >
        {([
          ['pair', 'Research a pair'],
          ['scan', 'Scan my universe'],
          ['lab', 'Experiment Lab'],
        ] as const).map(([value, label]) => (
          <button
            key={value}
            type="button"
            aria-pressed={activeTask === value}
            className={`min-h-11 rounded-md px-4 text-sm font-semibold transition-colors ${
              activeTask === value
                ? 'bg-accent text-canvas'
                : 'text-secondary hover:bg-subtle hover:text-foreground'
            }`}
            onClick={() => setActiveTask(value)}
          >
            {label}
          </button>
        ))}
      </nav>

      {activeTask === 'pair' ? (
        <PairResearch apiClient={apiClient} queries={queries} workspace={workspace} />
      ) : activeTask === 'scan' ? (
        <section aria-labelledby="universal-scan-heading">
          <div className="mb-4 max-w-4xl">
            <p className="m-0 text-xs font-semibold uppercase tracking-[0.08em] text-muted">
              Discovery
            </p>
            <h2 id="universal-scan-heading" className="mt-2 mb-2 text-2xl font-semibold text-foreground">
              Scan my universe
            </h2>
            <p className="m-0 text-sm leading-6 text-secondary">
              Run the existing current-approved scanner over the ready approved scope, one
              Product timeframe at a time. Scanner stages and Research Ideas remain
              backend-owned.
            </p>
          </div>
          <ProductResearch apiClient={apiClient} queries={queries} workspace={workspace} />
        </section>
      ) : (
        <ExperimentLab apiClient={apiClient} queries={queries} workspace={workspace} />
      )}

      <section className="mt-10" aria-labelledby="previous-research-heading">
        <div className="mb-4 max-w-3xl">
          <p className="m-0 text-xs font-semibold uppercase tracking-[0.08em] text-muted">
            Completed evidence
          </p>
          <h2 id="previous-research-heading" className="mt-2 mb-2 text-xl font-semibold text-foreground">
            Previous research
          </h2>
          <p className="m-0 text-sm leading-6 text-secondary">
            Each completed scan keeps the claim and data boundary that were frozen when it
            ran. Current workspace changes do not rewrite old evidence.
          </p>
        </div>
        {scans.items.length === 0 ? (
          <p className="rounded-lg border border-border bg-panel p-5 text-sm text-secondary">
            No completed research scans are available yet.
          </p>
        ) : (
          <div className="grid gap-4 lg:grid-cols-2">
            {scans.items.map((scan) => (
              <article key={scan.scan_id} className="rounded-lg border border-border bg-panel p-5">
                <div className="flex flex-wrap gap-2">
                  <Badge tone={scan.artifact_status === 'valid' ? 'info' : 'negative'}>
                    {scan.artifact_status === 'valid'
                      ? scan.claim?.label ?? 'Research evidence'
                      : 'Evidence unavailable'}
                  </Badge>
                  {scan.survivor_count != null ? (
                    <Badge tone={scan.survivor_count > 0 ? 'positive' : 'neutral'}>
                      {scan.survivor_count} Research Idea
                      {scan.survivor_count === 1 ? '' : 's'}
                    </Badge>
                  ) : null}
                </div>
                <h3 className="mt-3 mb-2 text-base font-semibold text-foreground">
                  {scan.horizons.map(timeframeLabel).join(' / ') || 'Unknown timeframe'} ·{' '}
                  {scan.venues.join(' / ') || 'Unknown venue'}
                </h3>
                {scan.eligible_information_end ? (
                  <p className="m-0 text-sm text-secondary">
                    {scan.claim?.kind === 'current_approved_retrospective'
                      ? 'Data through '
                      : scan.claim?.kind === 'historical_pit'
                        ? 'Historical cutoff '
                        : 'Data boundary '}
                    {formatResearchTimestamp(scan.eligible_information_end)}
                  </p>
                ) : null}
                <p className="mt-2 mb-0 text-sm text-secondary">
                  {scan.candidate_count ?? 0} fixed rule evaluations ·{' '}
                  {scan.selected_replay_count ?? 0} selected for deep replay
                </p>
                {scan.error ? (
                  <p className="mt-2 text-sm text-negative">{scan.error.message}</p>
                ) : null}
                <a
                  className="mt-4 inline-flex min-h-11 items-center font-semibold text-accent"
                  href={`/scanner/${scan.scan_id}`}
                >
                  Review completed research
                </a>
              </article>
            ))}
          </div>
        )}
      </section>

      <details className="mt-10 rounded-lg border border-border bg-panel p-5">
        <summary className="min-h-11 cursor-pointer py-2 text-lg font-semibold text-accent">
          Advanced Research · historical point-in-time scanner
        </summary>
        <div className="mt-5 border-t border-border pt-5">
          <DiscoveryHome
            apiClient={apiClient}
            protocol={protocol}
            scans={scans}
            embedded
          />
        </div>
      </details>
    </section>
  )
}
