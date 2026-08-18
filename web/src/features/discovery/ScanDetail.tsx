import { useMutation } from '@tanstack/react-query'
import { useMemo, useState } from 'react'

import type { QapApiClient } from '../../api/client'
import type {
  CandidateListDto,
  OperationRefDto,
  ScanDetailDto,
} from '../../api/types'
import { Badge } from '../../components/ui/Badge'
import { formatResearchTimestamp } from '../../lib/format'

interface ScanDetailProps {
  apiClient: QapApiClient
  data: ScanDetailDto
  candidates: CandidateListDto
}

function shortId(value: string) {
  return value.length <= 18 ? value : `${value.slice(0, 10)}…${value.slice(-6)}`
}

export function ScanDetail({ apiClient, data, candidates }: ScanDetailProps) {
  const scopes = data.graph_scopes
  const [scopeKey, setScopeKey] = useState(
    scopes.length ? `${scopes[0].venue}:${scopes[0].horizon}` : '',
  )
  const [operation, setOperation] = useState<OperationRefDto | null>(null)
  const scope = useMemo(
    () =>
      scopes.find((item) => `${item.venue}:${item.horizon}` === scopeKey) ?? null,
    [scopeKey, scopes],
  )
  const mutation = useMutation({
    mutationFn: () => {
      if (!scope) throw new Error('Select a venue/horizon scope first.')
      return apiClient.generateAssetMomentum(data.summary.scan_id, {
        venue: scope.venue as 'binance' | 'gate',
        horizon: scope.horizon as 'short' | 'medium' | 'swing',
      })
    },
    onSuccess: setOperation,
  })

  const validCandidates = candidates.items.filter(
    (candidate) => candidate.trial_status === 'valid',
  )
  const failures = candidates.items.filter(
    (candidate) => candidate.trial_status !== 'valid',
  )

  return (
    <section className="min-w-0">
      <header className="mb-8 max-w-4xl">
        <p className="mb-2 text-xs font-semibold uppercase tracking-[0.1em] text-accent">
          Discovery evidence
        </p>
        <h1 className="mb-3 text-3xl font-bold tracking-tight text-foreground md:text-4xl">
          Scan {shortId(data.summary.scan_id)}
        </h1>
        <div className="flex flex-wrap gap-2">
          <Badge tone={data.summary.artifact_status === 'valid' ? 'positive' : 'negative'}>
            {data.summary.artifact_status}
          </Badge>
          <Badge tone="info">{candidates.items.length} trials</Badge>
          <Badge tone="info">{data.summary.survivor_count ?? 0} survivors</Badge>
        </div>
        {data.summary.as_of ? (
          <p className="mt-3 mb-0 text-sm text-secondary">
            Frozen as of {formatResearchTimestamp(data.summary.as_of)} ·{' '}
            {data.summary.venues.join(' / ')} · {data.summary.horizons.join(' / ')}
          </p>
        ) : null}
      </header>

      <div className="grid gap-5 lg:grid-cols-3">
        {data.graph_scopes.map((graph) => (
          <article key={`${graph.venue}-${graph.horizon}`} className="rounded-lg border border-border bg-panel p-4">
            <p className="m-0 text-xs font-semibold uppercase tracking-[0.08em] text-muted">
              {graph.venue} / {graph.horizon}
            </p>
            <p className="mt-2 mb-0 text-2xl font-semibold text-foreground">
              {graph.eligible_asset_count}
            </p>
            <p className="mt-1 mb-0 text-sm text-secondary">PIT-admitted assets</p>
            <p className="mt-3 mb-0 text-xs text-muted">
              {graph.total_valid_pair_comparisons} valid pair comparisons · {graph.graph_interval}
            </p>
          </article>
        ))}
      </div>

      <section className="mt-8 rounded-lg border border-border bg-panel p-5" aria-labelledby="momentum-heading">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="mb-1 text-xs font-semibold uppercase tracking-[0.08em] text-muted">Asset-native evidence</p>
            <h2 id="momentum-heading" className="m-0 text-xl font-semibold text-foreground">Relative momentum</h2>
          </div>
          {scopes.length ? (
            <div className="flex flex-wrap gap-2">
              <select
                aria-label="Momentum scope"
                className="min-h-11 rounded-md border border-border bg-canvas px-3 text-sm text-foreground"
                value={scopeKey}
                onChange={(event) => setScopeKey(event.target.value)}
              >
                {scopes.map((item) => (
                  <option key={`${item.venue}-${item.horizon}`} value={`${item.venue}:${item.horizon}`}>
                    {item.venue} / {item.horizon}
                  </option>
                ))}
              </select>
              <button
                type="button"
                className="min-h-11 rounded-md bg-accent px-4 text-sm font-semibold text-canvas disabled:opacity-50"
                disabled={!scope || mutation.isPending}
                onClick={() => mutation.mutate()}
              >
                {mutation.isPending ? 'Starting…' : 'Generate momentum'}
              </button>
            </div>
          ) : null}
        </div>
        <p className="mt-3 text-sm leading-6 text-secondary">
          Resolution and formation duration are frozen by Scanner V1. This action submits only the completed scan, venue, and horizon.
        </p>
        {mutation.isError ? <p className="text-sm text-negative">{mutation.error.message}</p> : null}
        {operation ? (
          <p className="rounded-md border border-positive/40 bg-subtle p-3 text-sm text-secondary">
            Momentum operation started.{' '}
            <a className="font-semibold text-accent" href={`/operations/${operation.operation_id}`}>
              Track {shortId(operation.operation_id)}
            </a>
          </p>
        ) : null}
        {data.momentum_generations.length === 0 ? (
          <p className="text-sm text-secondary">No persisted momentum generation yet.</p>
        ) : (
          <div className="mt-4 grid gap-4 xl:grid-cols-2">
            {data.momentum_generations.map((generation) => (
              <article key={generation.momentum_scan_id} className="rounded-md border border-border p-4">
                <div className="flex flex-wrap gap-2">
                  <Badge tone="positive">Persisted</Badge>
                  <Badge tone="info">{generation.venue} / {generation.horizon}</Badge>
                </div>
                <p className="mt-3 mb-0 text-sm text-secondary">
                  {generation.resolution} · {Math.round(generation.formation_seconds / 86400)}d formation · {generation.observations.length} observations
                </p>
                <div className="mt-3 overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead className="text-xs text-muted">
                      <tr><th className="py-2 pr-3">Rank</th><th className="py-2 pr-3">Asset</th><th className="py-2">Relative momentum</th></tr>
                    </thead>
                    <tbody>
                      {generation.observations
                        .filter((item) => item.status === 'valid')
                        .sort((left, right) => (left.rank ?? 9999) - (right.rank ?? 9999))
                        .slice(0, 8)
                        .map((item) => (
                          <tr key={item.asset_id} className="border-t border-border">
                            <td className="py-2 pr-3 tabular-nums">{item.rank ?? '—'}</td>
                            <td className="py-2 pr-3 font-medium text-foreground">{item.asset_id}</td>
                            <td className="py-2 tabular-nums text-secondary">{item.relative_momentum?.toFixed(5) ?? '—'}</td>
                          </tr>
                        ))}
                    </tbody>
                  </table>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>

      <section className="mt-8" aria-labelledby="candidate-heading">
        <div className="flex flex-wrap items-baseline justify-between gap-3">
          <h2 id="candidate-heading" className="text-xl font-semibold text-foreground">Candidate trials</h2>
          <span className="text-sm text-muted">{validCandidates.length} valid · {failures.length} invalid/failed</span>
        </div>
        <div className="mt-4 overflow-x-auto rounded-lg border border-border bg-panel">
          <table className="w-full min-w-[52rem] text-left text-sm">
            <thead className="bg-subtle text-xs uppercase tracking-[0.06em] text-muted">
              <tr>
                <th className="px-4 py-3">Pair</th>
                <th className="px-4 py-3">Rule</th>
                <th className="px-4 py-3">Scout</th>
                <th className="px-4 py-3">Selection</th>
                <th className="px-4 py-3">Deep replay</th>
                <th className="px-4 py-3">Evidence</th>
              </tr>
            </thead>
            <tbody>
              {candidates.items.map((candidate) => (
                <tr key={candidate.candidate_id} className="border-t border-border align-top">
                  <td className="px-4 py-3">
                    <p className="m-0 font-semibold text-foreground">{candidate.pair_id}</p>
                    <p className="mt-1 mb-0 text-xs text-muted">{candidate.orientation}</p>
                  </td>
                  <td className="px-4 py-3 text-secondary">
                    {candidate.model_family}<br />{candidate.template_id} · {candidate.resolution}
                  </td>
                  <td className="px-4 py-3">
                    <Badge tone={candidate.trial_status === 'valid' ? 'positive' : 'negative'}>{candidate.trial_status}</Badge>
                    {candidate.failure_reason ? <p className="mt-1 mb-0 text-xs text-negative">{candidate.failure_reason}</p> : null}
                  </td>
                  <td className="px-4 py-3 text-secondary">
                    {candidate.automatic_selected ? 'automatic' : candidate.manual_selected ? 'manual' : 'not promoted'}
                    {candidate.manual_pinned ? <p className="mt-1 mb-0 text-xs text-muted">manual pin</p> : null}
                  </td>
                  <td className="px-4 py-3 text-secondary">
                    {candidate.deep_replay_status ?? 'not attempted'}
                    {candidate.economic_gate_status ? <p className="mt-1 mb-0 text-xs text-muted">{candidate.economic_gate_status}</p> : null}
                  </td>
                  <td className="px-4 py-3">
                    <a className="font-semibold text-accent" href={`/candidate/${data.summary.scan_id}/${candidate.candidate_id}`}>Inspect lineage</a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="mt-8" aria-labelledby="universe-heading">
        <h2 id="universe-heading" className="text-xl font-semibold text-foreground">Point-in-time universe</h2>
        <div className="mt-4 overflow-x-auto rounded-lg border border-border bg-panel">
          <table className="w-full min-w-[46rem] text-left text-sm">
            <thead className="bg-subtle text-xs uppercase tracking-[0.06em] text-muted">
              <tr><th className="px-4 py-3">Asset</th><th className="px-4 py-3">Scope</th><th className="px-4 py-3">Eligibility</th><th className="px-4 py-3">Coverage</th></tr>
            </thead>
            <tbody>
              {data.universe.map((asset) => (
                <tr key={`${asset.venue}-${asset.horizon}-${asset.asset_id}`} className="border-t border-border">
                  <td className="px-4 py-3 font-semibold text-foreground">{asset.asset_id}<span className="ml-2 text-xs font-normal text-muted">{asset.venue_symbol}</span></td>
                  <td className="px-4 py-3 text-secondary">{asset.venue} / {asset.horizon}</td>
                  <td className="px-4 py-3 text-secondary">{asset.automatic_eligible ? 'automatic eligible' : asset.forensic_research_allowed ? 'forensic only' : asset.eligibility_reason}</td>
                  <td className="px-4 py-3 tabular-nums text-secondary">{(asset.bar_coverage * 100).toFixed(1)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </section>
  )
}
