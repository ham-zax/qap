import { useMutation } from '@tanstack/react-query'
import { useState } from 'react'

import type { QapApiClient } from '../../api/client'
import type { CandidateDetailDto, OperationRefDto } from '../../api/types'
import { Badge } from '../../components/ui/Badge'

interface CandidateDetailProps {
  apiClient: QapApiClient
  data: CandidateDetailDto
}

function shortId(value: string) {
  return value.length <= 18 ? value : `${value.slice(0, 10)}…${value.slice(-6)}`
}

export function CandidateDetail({ apiClient, data }: CandidateDetailProps) {
  const candidate = data.candidate
  const [freezeAt, setFreezeAt] = useState('')
  const [operation, setOperation] = useState<OperationRefDto | null>(null)
  const freeze = useMutation({
    mutationFn: () =>
      apiClient.freezeForwardCohort({
        scan_id: candidate.scan_id,
        horizon: candidate.horizon as 'short' | 'medium' | 'swing',
        freeze_at: freezeAt,
      }),
    onSuccess: setOperation,
  })
  const [assetX, assetY] = candidate.pair_id.split('/')
  const manual = candidate.manual_pinned || candidate.manual_selected

  return (
    <section className="min-w-0">
      <header className="mb-8 max-w-4xl">
        <p className="mb-2 text-xs font-semibold uppercase tracking-[0.1em] text-accent">
          Candidate lineage
        </p>
        <h1 className="mb-3 text-3xl font-bold tracking-tight text-foreground md:text-4xl">
          {candidate.pair_id}
        </h1>
        <div className="flex flex-wrap gap-2">
          <Badge tone={candidate.trial_status === 'valid' ? 'positive' : 'negative'}>
            scout {candidate.trial_status}
          </Badge>
          {candidate.economic_gate_status ? (
            <Badge
              tone={
                candidate.economic_gate_status.includes('survivor')
                  ? 'positive'
                  : 'warning'
              }
            >
              {candidate.economic_gate_status}
            </Badge>
          ) : null}
          {manual ? <Badge tone="warning">manual / pinned lineage</Badge> : null}
          {candidate.automatic_selected ? <Badge tone="info">automatic selection</Badge> : null}
        </div>
        <p className="mt-3 mb-0 break-all text-sm text-muted">
          Candidate {candidate.candidate_id}
        </p>
      </header>

      <div className="grid gap-5 lg:grid-cols-2">
        <article className="rounded-lg border border-border bg-panel p-5">
          <p className="m-0 text-xs font-semibold uppercase tracking-[0.08em] text-muted">
            Why this rule exists
          </p>
          <ol className="mt-4 space-y-4 pl-5 text-sm leading-6 text-secondary">
            <li>
              <strong className="text-foreground">PIT scope:</strong>{' '}
              {candidate.venue} / {candidate.horizon}, from scan{' '}
              <a className="text-accent" href={`/scanner/${candidate.scan_id}`}>
                {shortId(candidate.scan_id)}
              </a>
              .
            </li>
            <li>
              <strong className="text-foreground">Graph admission:</strong>{' '}
              {candidate.automatic_neighbor_selected
                ? 'selected by the frozen SSD neighbor graph'
                : candidate.manual_pinned
                  ? 'included by an explicit manual pin'
                  : 'not an automatic neighbor selection'}
              .
            </li>
            <li>
              <strong className="text-foreground">Fixed trial:</strong>{' '}
              {candidate.model_family}, {candidate.template_id}, {candidate.resolution},
              orientation {candidate.orientation}.
            </li>
            <li>
              <strong className="text-foreground">Scout:</strong>{' '}
              {candidate.trial_status}
              {candidate.failure_reason ? ` — ${candidate.failure_reason}` : ''}.
              {candidate.scout_relative_wealth_proxy !== null
                ? ` Relative-wealth proxy ${candidate.scout_relative_wealth_proxy.toFixed(5)}.`
                : ''}
            </li>
            <li>
              <strong className="text-foreground">Promotion/replay:</strong>{' '}
              {candidate.promotion_status ?? 'not promoted'}; deep replay{' '}
              {candidate.deep_replay_status ?? 'not attempted'}
              {candidate.replay_failure_reason
                ? ` — ${candidate.replay_failure_reason}`
                : ''}
              .
            </li>
          </ol>
        </article>

        <article className="rounded-lg border border-border bg-panel p-5">
          <p className="m-0 text-xs font-semibold uppercase tracking-[0.08em] text-muted">
            Authoritative evidence links
          </p>
          <div className="mt-4 space-y-3 text-sm">
            {candidate.deep_replay_run_id ? (
              <>
                <a
                  className="flex min-h-11 items-center rounded-md border border-border px-3 font-semibold text-accent"
                  href={`/experiments/${candidate.deep_replay_run_id}`}
                >
                  Historical QAP experiment
                </a>
                <a
                  className="flex min-h-11 items-center rounded-md border border-border px-3 font-semibold text-accent"
                  href={`/portfolio/${candidate.deep_replay_run_id}`}
                >
                  Portfolio economics
                </a>
                {assetX && assetY ? (
                  <a
                    className="flex min-h-11 items-center rounded-md border border-border px-3 font-semibold text-accent"
                    href={`/pair/${candidate.deep_replay_run_id}/${assetX}/${assetY}?orientation=${encodeURIComponent(candidate.orientation)}&anchor=none`}
                  >
                    Pair relationship workbench
                  </a>
                ) : null}
              </>
            ) : (
              <p className="text-secondary">
                No completed authoritative historical QAP replay is attached to this
                candidate.
              </p>
            )}
          </div>
        </article>
      </div>

      {candidate.economic_gate_status === 'deep_replay_survivor' ? (
        <section className="mt-8 rounded-lg border border-border bg-panel p-5" aria-labelledby="freeze-heading">
          <div className="flex flex-wrap items-end justify-between gap-4">
            <div className="max-w-2xl">
              <h2 id="freeze-heading" className="mt-0 text-lg font-semibold text-foreground">
                Freeze prospective cohort
              </h2>
              <p className="mb-0 text-sm leading-6 text-secondary">
                Freezing is a scan/horizon operation. The backend enrolls the admitted
                survivors and records automatic/manual membership before future outcomes.
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <input
                className="min-h-11 rounded-md border border-border bg-canvas px-3 text-foreground"
                value={freezeAt}
                onChange={(event) => setFreezeAt(event.target.value)}
                placeholder="Freeze UTC"
                aria-label="Freeze UTC"
              />
              <button
                type="button"
                className="min-h-11 rounded-md bg-accent px-4 font-semibold text-canvas disabled:opacity-50"
                disabled={!freezeAt || freeze.isPending}
                onClick={() => freeze.mutate()}
              >
                {freeze.isPending ? 'Starting…' : 'Freeze cohort'}
              </button>
            </div>
          </div>
          {freeze.isError ? <p className="mt-3 text-sm text-negative">{freeze.error.message}</p> : null}
          {operation ? (
            <p className="mt-3 text-sm text-secondary">
              Freeze operation started.{' '}
              <a className="font-semibold text-accent" href={`/operations/${operation.operation_id}`}>
                Track {shortId(operation.operation_id)}
              </a>
            </p>
          ) : null}
        </section>
      ) : null}

      <div className="mt-8 grid gap-5 lg:grid-cols-3">
        <section className="rounded-lg border border-border bg-panel p-4">
          <h2 className="mt-0 text-base font-semibold text-foreground">Prospective cohorts</h2>
          {data.forward_cohort_ids.length ? (
            <ul className="space-y-2 pl-5 text-sm">
              {data.forward_cohort_ids.map((id) => (
                <li key={id}>
                  <a className="text-accent" href={`/prospective/${id}`}>
                    {shortId(id)}
                  </a>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-secondary">No forward cohort membership.</p>
          )}
        </section>

        <section className="rounded-lg border border-border bg-panel p-4">
          <h2 className="mt-0 text-base font-semibold text-foreground">Qualifications</h2>
          {data.qualification_ids.length ? (
            <ul className="space-y-2 pl-5 text-sm text-secondary">
              {data.qualification_ids.map((id) => (
                <li key={id} title={id}>{shortId(id)}</li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-secondary">No current-capital qualification.</p>
          )}
        </section>

        <section className="rounded-lg border border-border bg-panel p-4">
          <h2 className="mt-0 text-base font-semibold text-foreground">Basket membership</h2>
          {data.basket_ids.length ? (
            <ul className="space-y-2 pl-5 text-sm">
              {data.basket_ids.map((id) => (
                <li key={id}>
                  <a className="text-accent" href={`/baskets/${id}`}>
                    {shortId(id)}
                  </a>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-secondary">Not used by a completed basket.</p>
          )}
        </section>
      </div>
    </section>
  )
}
