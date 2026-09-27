import { useMutation, useQuery } from '@tanstack/react-query'
import { useState } from 'react'

import type { QapApiClient } from '../../api/client'
import type { QapQueries } from '../../api/queries'
import type {
  CurrentApprovedReadinessDto,
  OperationDto,
  ScanDetailDto,
  WorkspaceStatusDto,
} from '../../api/types'
import { Badge, type BadgeTone } from '../../components/ui/Badge'
import { formatResearchTimestamp } from '../../lib/format'
import { ProductFollowUpAction } from './ProductFollowUpAction'
import { ResearchStageSummary } from './ResearchStageSummary'

type Horizon = 'short' | 'medium' | 'swing'

interface ProductResearchProps {
  apiClient: QapApiClient
  queries: QapQueries
  workspace: WorkspaceStatusDto
}

const TIMEFRAMES: { value: Horizon; label: string; description: string }[] = [
  {
    value: 'short',
    label: 'Short-term',
    description: 'Faster relationship and model windows.',
  },
  {
    value: 'medium',
    label: 'Medium-term',
    description: 'A broader multi-day research window.',
  },
  {
    value: 'swing',
    label: 'Longer-term',
    description: 'The longest Scanner-V1 research window.',
  },
]

function maintenanceTone(
  status: CurrentApprovedReadinessDto['maintenance']['status'],
): BadgeTone {
  if (status === 'running') return 'info'
  if (status === 'failed') return 'warning'
  return 'neutral'
}

function operationTone(status: OperationDto['status']): BadgeTone {
  if (status === 'running') return 'info'
  if (status === 'failed') return 'negative'
  if (status === 'interrupted') return 'warning'
  return 'positive'
}

function operationLabel(status: OperationDto['status']): string {
  if (status === 'running') return 'Research running'
  if (status === 'failed') return 'Task failed'
  if (status === 'interrupted') return 'Task interrupted'
  return 'Research task completed'
}

function completedScanId(operation: OperationDto | undefined): string | null {
  const value = operation?.result?.scan_id
  return typeof value === 'string' ? value : null
}

export function ProductResearch({
  apiClient,
  queries,
  workspace,
}: ProductResearchProps) {
  const [horizon, setHorizon] = useState<Horizon>('short')
  const [operationId, setOperationId] = useState<string | null>(null)
  const readiness = useQuery({
    ...queries.currentApprovedReadiness(horizon),
    enabled: workspace.workspace_mode === 'local_market',
  })
  const launch = useMutation({
    mutationFn: () => {
      if (!readiness.data?.ready_for_research) {
        throw new Error('This timeframe is not ready for research yet.')
      }
      return apiClient.runCurrentApprovedResearch({
        horizon,
        readiness_id: readiness.data.readiness_id,
      })
    },
    onSuccess: (operation) => setOperationId(operation.operation_id),
  })
  const operation = useQuery({
    queryKey: ['operation', operationId ?? 'none'],
    queryFn: () => apiClient.getOperation(operationId ?? ''),
    enabled: operationId !== null,
    refetchInterval: (query) =>
      query.state.data?.status === 'running' ? 1_000 : false,
  })
  const scanId = completedScanId(operation.data)
  const completedScan = useQuery({
    ...queries.scan(scanId ?? ''),
    enabled: Boolean(scanId),
  })
  const completedCandidates = useQuery({
    ...queries.scanCandidates(scanId ?? ''),
    enabled: Boolean(scanId),
  })

  if (workspace.workspace_mode === 'sample') {
    return (
      <section className="rounded-lg border border-warning/45 bg-panel p-5">
        <Badge tone="warning">Sample Workspace</Badge>
        <h2 className="mt-3 mb-2 text-xl font-semibold text-foreground">
          Example evidence, not your Local Market
        </h2>
        <p className="m-0 max-w-3xl text-sm leading-6 text-secondary">
          The current-approved readiness policy applies only to Local Market.
          Sample Workspace remains available for inspecting bundled research evidence and
          the strict historical Point-in-Time flow under Advanced Research below.
        </p>
      </section>
    )
  }

  return (
    <div className="space-y-6">
      <p className="m-0 max-w-4xl text-sm leading-6 text-secondary">
        Scan the assets you explicitly approved on supported Spot venues. QAP freezes the eligible scope and safe data cutoff before the scan starts.
      </p>

      <section className="rounded-lg border border-border bg-panel p-5" aria-labelledby="timeframe-heading">
        <h2 id="timeframe-heading" className="mt-0 text-lg font-semibold text-foreground">
          Research timeframe
        </h2>
        <div className="grid gap-3 md:grid-cols-3" role="radiogroup" aria-label="Research timeframe">
          {TIMEFRAMES.map((item) => (
            <label
              key={item.value}
              className="flex min-h-24 cursor-pointer gap-3 rounded-md border border-border p-4"
            >
              <input
                type="radio"
                name="research-timeframe"
                value={item.value}
                checked={horizon === item.value}
                disabled={launch.isPending || operation.data?.status === 'running'}
                onChange={() => {
                  setHorizon(item.value)
                  setOperationId(null)
                }}
              />
              <span>
                <strong className="block text-sm text-foreground">{item.label}</strong>
                <span className="mt-1 block text-xs leading-5 text-muted">
                  {item.description}
                </span>
              </span>
            </label>
          ))}
        </div>
      </section>

      {readiness.data?.ready_for_research ? (
        <details className="rounded-lg border border-border bg-panel px-5 py-3">
          <summary className="min-h-11 cursor-pointer py-2 text-sm font-semibold text-secondary">
            Ready · {readiness.data.ready_asset_count} assets · data through {readiness.data.safe_cutoff ? formatResearchTimestamp(readiness.data.safe_cutoff) : 'available cutoff'}
          </summary>
          <ReadinessPanel readiness={readiness.data} isLoading={false} error={null} />
        </details>
      ) : <ReadinessPanel readiness={readiness.data} isLoading={readiness.isPending} error={readiness.error} />}

      <section className="rounded-lg border border-border bg-panel p-5" aria-labelledby="find-ideas-heading">
        <h2 id="find-ideas-heading" className="mt-0 text-lg font-semibold text-foreground">
          Scan my universe
        </h2>
        <p className="text-sm leading-6 text-secondary">
          QAP will use the exact approved scope, immutable market-data generations, and safe
          cutoff shown above. You do not enter an analysis date in the normal Research flow.
        </p>
        <button
          type="button"
          className="mt-2 min-h-11 rounded-md bg-accent px-5 py-2 font-semibold text-canvas disabled:opacity-50"
          disabled={
            !readiness.data?.ready_for_research ||
            launch.isPending ||
            operation.data?.status === 'running'
          }
          onClick={() => launch.mutate()}
        >
          {launch.isPending ? 'Starting…' : 'Scan my universe'}
        </button>
        {!readiness.data?.ready_for_research && !readiness.isPending ? (
          <p className="mt-3 mb-0 text-sm text-secondary">
            This timeframe is not ready for research yet. Review the exclusions above
            or manage the Research Universe.
          </p>
        ) : null}
        {launch.isError ? (
          <p className="mt-3 mb-0 text-sm text-negative">{launch.error.message}</p>
        ) : null}
      </section>

      {operationId ? (
        <OperationState operation={operation.data} operationId={operationId} />
      ) : null}

      {scanId && completedScan.data ? (
        <CompletedProductResult
          apiClient={apiClient}
          data={completedScan.data}
          candidates={completedCandidates.data}
        />
      ) : null}
    </div>
  )
}

function ReadinessPanel({
  readiness,
  isLoading,
  error,
}: {
  readiness: CurrentApprovedReadinessDto | undefined
  isLoading: boolean
  error: Error | null
}) {
  if (isLoading) {
    return (
      <section className="rounded-lg border border-border bg-panel p-5">
        <p className="m-0 text-sm text-secondary">Checking backend research readiness…</p>
      </section>
    )
  }
  if (error) {
    return (
      <section className="rounded-lg border border-negative/45 bg-panel p-5">
        <Badge tone="negative">Readiness unavailable</Badge>
        <p className="mt-3 mb-0 text-sm text-negative">{error.message}</p>
      </section>
    )
  }
  if (!readiness) return null

  const excluded = readiness.assets.filter((asset) => asset.approved && !asset.ready)
  const directLimitations = readiness.direct_markets.filter(
    (market) => market.status !== 'ready',
  )
  const timeframe = TIMEFRAMES.find((item) => item.value === readiness.horizon)?.label

  return (
    <section className="rounded-lg border border-border bg-panel p-5" aria-labelledby="readiness-heading">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="m-0 text-xs font-semibold uppercase tracking-[0.08em] text-muted">
            Data readiness
          </p>
          <h2 id="readiness-heading" className="mt-2 mb-2 text-xl font-semibold text-foreground">
            {timeframe ?? readiness.horizon}
          </h2>
        </div>
        <div className="flex flex-wrap gap-2">
          <Badge tone={readiness.ready_for_research ? 'positive' : 'warning'}>
            {readiness.ready_for_research ? 'Ready for research' : 'Not ready yet'}
          </Badge>
          <Badge tone={maintenanceTone(readiness.maintenance.status)}>
            Data {readiness.maintenance.status}
          </Badge>
        </div>
      </div>

      <div className="mt-4 grid gap-4 sm:grid-cols-3">
        <ReadinessStat label="Approved assets" value={readiness.approved_asset_count} />
        <ReadinessStat label="Ready assets" value={readiness.ready_asset_count} />
        <ReadinessStat label="Ready venue paths" value={readiness.ready_path_count} />
      </div>
      <p className="mt-4 mb-0 text-sm leading-6 text-secondary">
        Data through:{' '}
        <strong className="text-foreground">
          {readiness.safe_cutoff
            ? formatResearchTimestamp(readiness.safe_cutoff)
            : 'No safe cutoff available'}
        </strong>
      </p>

      {readiness.reasons.length ? (
        <div className="mt-4 space-y-2">
          {readiness.reasons.map((reason) => (
            <ReasonRow key={`${reason.code}-${reason.detail}`} reason={reason} />
          ))}
        </div>
      ) : null}

      {excluded.length ? (
        <div className="mt-5">
          <h3 className="m-0 text-sm font-semibold text-foreground">Approved assets not ready</h3>
          <div className="mt-3 grid gap-3 lg:grid-cols-2">
            {excluded.map((asset) => (
              <article key={asset.canonical_asset_id} className="rounded-md border border-border p-4">
                <p className="m-0 font-semibold text-foreground">{asset.canonical_asset_id}</p>
                <div className="mt-2 space-y-2">
                  {asset.reasons.map((reason) => (
                    <ReasonRow key={`${reason.code}-${reason.detail}`} reason={reason} compact />
                  ))}
                </div>
              </article>
            ))}
          </div>
        </div>
      ) : null}

      {directLimitations.length ? (
        <details className="mt-5 border-t border-border pt-4">
          <summary className="min-h-11 cursor-pointer py-2 text-sm font-semibold text-accent">
            Deeper replay availability
          </summary>
          <p className="mt-2 text-sm leading-6 text-secondary">
            A missing same-venue direct market or its history limits deep replay for that
            pair. It does not make either approved asset invalid.
          </p>
          <div className="space-y-3">
            {directLimitations.map((market) => (
              <article
                key={`${market.venue}-${market.asset_a}-${market.asset_b}`}
                className="rounded-md border border-border p-3 text-sm"
              >
                <p className="m-0 font-semibold text-foreground">
                  {market.asset_a}/{market.asset_b} · {market.venue}
                </p>
                <p className="mt-1 mb-0 text-secondary">
                  {market.status.replaceAll('_', ' ')}
                </p>
                {market.reasons.map((reason) => (
                  <p key={`${reason.code}-${reason.detail}`} className="mt-1 mb-0 text-xs text-muted">
                    {reason.detail}
                  </p>
                ))}
              </article>
            ))}
          </div>
        </details>
      ) : null}

      <div className="mt-5 flex flex-wrap gap-4 border-t border-border pt-4 text-sm">
        <a className="font-semibold text-accent" href="/universe">
          Manage Research Universe
        </a>
        <details>
          <summary className="cursor-pointer font-semibold text-accent">Research details</summary>
          <div className="mt-2 space-y-1 break-all text-xs text-muted">
            <p className="m-0">Claim: {readiness.claim_label}</p>
            <p className="m-0">Readiness ID: {readiness.readiness_id}</p>
            <p className="m-0">Claim identity: {readiness.claim_identity}</p>
            <p className="m-0">Protocol: {readiness.scanner_protocol_id}</p>
          </div>
        </details>
      </div>
    </section>
  )
}

function ReadinessStat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-md border border-border p-3">
      <p className="m-0 text-xs text-muted">{label}</p>
      <p className="mt-1 mb-0 text-2xl font-semibold tabular-nums text-foreground">{value}</p>
    </div>
  )
}

function ReasonRow({
  reason,
  compact = false,
}: {
  reason: CurrentApprovedReadinessDto['reasons'][number]
  compact?: boolean
}) {
  return (
    <p
      className={`${compact ? 'text-xs' : 'text-sm'} m-0 rounded-md border border-border px-3 py-2 text-secondary`}
    >
      <strong className="text-foreground">{reason.code.replaceAll('_', ' ')}</strong>
      {' — '}
      {reason.detail}
    </p>
  )
}

function OperationState({
  operation,
  operationId,
}: {
  operation: OperationDto | undefined
  operationId: string
}) {
  if (!operation) {
    return (
      <section className="rounded-lg border border-info/45 bg-panel p-5">
        <Badge tone="info">Starting</Badge>
        <p className="mt-3 mb-0 text-sm text-secondary">
          QAP accepted the background research task. Activity will show its authoritative
          lifecycle state.
        </p>
        <a className="mt-3 inline-flex min-h-11 items-center font-semibold text-accent" href={`/operations/${operationId}`}>
          View in Activity
        </a>
      </section>
    )
  }
  return (
    <section className="rounded-lg border border-border bg-panel p-5" aria-labelledby="task-state-heading">
      <div className="flex flex-wrap items-center gap-2">
        <Badge tone={operationTone(operation.status)}>{operationLabel(operation.status)}</Badge>
      </div>
      <h2 id="task-state-heading" className="mt-3 mb-2 text-lg font-semibold text-foreground">
        {operation.status === 'running' ? 'QAP is scanning the frozen approved scope' : 'Background task state'}
      </h2>
      <p className="m-0 text-sm leading-6 text-secondary">
        {operation.status === 'running'
          ? 'The durable operation is running. QAP does not publish temporary scanner-stage counts, percentages, or an ETA while the scan is incomplete.'
          : operation.status === 'completed'
            ? 'The task completed and its immutable scanner evidence can now be read.'
            : operation.status === 'failed'
              ? 'The task failed operationally. This is not a negative scientific research result.'
              : 'The task was interrupted before completion. No scientific conclusion is implied.'}
      </p>
      <a className="mt-3 inline-flex min-h-11 items-center font-semibold text-accent" href={`/operations/${operationId}`}>
        View in Activity
      </a>
    </section>
  )
}

function CompletedProductResult({
  apiClient,
  data,
  candidates,
}: {
  apiClient: QapApiClient
  data: ScanDetailDto
  candidates: Awaited<ReturnType<QapApiClient['listScanCandidates']>> | undefined
}) {
  const claim = data.summary.claim
  const ideaCount = data.summary.survivor_count
  const ideas =
    candidates?.items.filter(
      (candidate) => candidate.economic_gate_status === 'deep_replay_survivor',
    ) ?? []

  return (
    <section className="rounded-lg border border-border bg-subtle p-5" aria-labelledby="completed-research-heading">
      <p className="m-0 text-xs font-semibold uppercase tracking-[0.08em] text-muted">
        Completed research
      </p>
      <h2 id="completed-research-heading" className="mt-2 mb-2 text-xl font-semibold text-foreground">
        {claim?.label ?? 'Research evidence'}
      </h2>
      <p className="m-0 text-sm leading-6 text-secondary">
        Data through{' '}
        {data.summary.eligible_information_end
          ? formatResearchTimestamp(data.summary.eligible_information_end)
          : 'an unavailable cutoff'}
        . {ideaCount === 0
          ? 'No Research Ideas survived the declared historical replay gates.'
          : ideaCount == null
            ? 'Research Idea count is unavailable.'
            : `${ideaCount} Research Idea${ideaCount === 1 ? '' : 's'} survived the declared historical replay gates.`}
      </p>
      <div className="mt-5">
        <ResearchStageSummary
          stages={data.stages}
          claimKind={claim?.kind ?? 'versioned_other'}
        />
      </div>
      <div className="mt-6">
        <h3 className="m-0 text-lg font-semibold text-foreground">Research Ideas</h3>
        {ideaCount === 0 ? (
          <p className="mt-3 rounded-md border border-border bg-panel p-4 text-sm leading-6 text-secondary">
            No Research Idea survived the declared historical replay and economic gates.
            This is valid negative evidence, not a task failure.
          </p>
        ) : ideas.length ? (
          <div className="mt-3 grid gap-3 lg:grid-cols-2">
            {ideas.map((candidate) => (
              <a
                key={candidate.candidate_id}
                className="rounded-md border border-positive/45 bg-panel p-4 font-semibold text-accent no-underline"
                href={`/candidate/${data.summary.scan_id}/${candidate.candidate_id}`}
              >
                <span className="block text-foreground">{candidate.pair_id}</span>
                <span className="mt-1 block text-xs font-normal text-secondary">
                  {candidate.venue} · {candidate.horizon} · passed declared historical gates
                </span>
              </a>
            ))}
          </div>
        ) : (
          <p className="mt-3 text-sm text-secondary">
            Research Idea records are loading from the completed immutable scan.
          </p>
        )}
      </div>
      {(ideaCount ?? 0) > 0 ? (
        <ProductFollowUpAction
          apiClient={apiClient}
          scanId={data.summary.scan_id}
          followUp={data.product_follow_up}
        />
      ) : null}
      <a
        className="mt-5 inline-flex min-h-11 items-center font-semibold text-accent"
        href={`/scanner/${data.summary.scan_id}`}
      >
        Review Research Ideas and full evidence
      </a>
    </section>
  )
}
