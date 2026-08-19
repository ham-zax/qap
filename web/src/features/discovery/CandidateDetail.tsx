import { useMutation } from '@tanstack/react-query'
import { useState } from 'react'

import type { QapApiClient } from '../../api/client'
import type { CandidateDetailDto, OperationRefDto } from '../../api/types'
import { Badge, type BadgeTone } from '../../components/ui/Badge'
import { LineageTrail } from '../lineage/LineageTrail'

interface CandidateDetailProps {
  apiClient: QapApiClient
  data: CandidateDetailDto
}

function shortId(value: string) {
  return value.length <= 18 ? value : `${value.slice(0, 10)}…${value.slice(-6)}`
}

function historicalVerdict(
  candidate: CandidateDetailDto['candidate'],
): { description: string; label: string; tone: BadgeTone } {
  if (candidate.economic_gate_status === 'deep_replay_survivor') {
    return {
      label: 'Passed historical research checks',
      tone: 'positive',
      description:
        'This rule cleared its declared historical QAP replay and economic gate.',
    }
  }
  if (candidate.economic_gate_status === 'deep_replay_rejected') {
    return {
      label: 'Did not pass historical research checks',
      tone: 'warning',
      description:
        'The historical evaluation completed, but the rule did not clear the declared gate.',
    }
  }
  if (
    candidate.trial_status !== 'valid' ||
    candidate.deep_replay_status === 'setup_failed' ||
    candidate.deep_replay_status === 'replay_failed'
  ) {
    return {
      label: 'Required research evidence unavailable',
      tone: 'negative',
      description:
        'QAP could not complete the evidence required for a historical conclusion.',
    }
  }
  return {
    label: 'Historical evaluation not completed',
    tone: 'neutral',
    description:
      'The rule was valid at the initial research stage but has no completed historical QAP verdict.',
  }
}

export function CandidateDetail({ apiClient, data }: CandidateDetailProps) {
  const candidate = data.candidate
  const isProductClaim = data.claim.kind === 'current_approved_retrospective'
  const isPitClaim = data.claim.kind === 'historical_pit'
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
  const verdict = historicalVerdict(candidate)

  return (
    <section className="min-w-0">
      <header className="mb-8 max-w-4xl">
        <p className="mb-2 text-xs font-semibold uppercase tracking-[0.1em] text-accent">
          Research idea
        </p>
        <h1 className="mb-3 text-3xl font-bold tracking-tight text-foreground md:text-4xl">
          {candidate.pair_id}
        </h1>
        <div className="flex flex-wrap gap-2">
          <Badge tone={verdict.tone}>{verdict.label}</Badge>
          <Badge tone="info">{data.claim.label}</Badge>
          <Badge tone="info">{candidate.horizon} timeframe</Badge>
        </div>
        <p className="mt-3 mb-0 text-sm leading-6 text-secondary">
          {verdict.description}
        </p>
      </header>

      <section className="rounded-lg border border-border bg-panel p-5" aria-labelledby="historical-comparison-heading">
        <h2 id="historical-comparison-heading" className="mt-0 text-lg font-semibold text-foreground">
          Historical comparison
        </h2>
        <p className="text-sm leading-6 text-secondary">
          QAP evaluates the relationship policy against matched passive HODL and the
          declared simple rebalancing control. The authoritative result contains the
          exact benchmark values and economic evidence.
        </p>
        {candidate.deep_replay_run_id ? (
          <a
            className="mt-2 inline-flex min-h-11 items-center font-semibold text-accent"
            href={`/experiments/${candidate.deep_replay_run_id}`}
          >
            Review historical result
          </a>
        ) : null}
        {candidate.economic_gate_status === 'deep_replay_survivor' && isPitClaim ? (
          <a
            className="ml-4 mt-2 inline-flex min-h-11 items-center rounded-md bg-accent px-4 font-semibold text-canvas no-underline"
            href="#start-forward-validation"
          >
            Start forward validation
          </a>
        ) : null}
      </section>

      <details className="mt-6 rounded-lg border border-border bg-panel p-5">
        <summary className="min-h-11 cursor-pointer py-2 text-lg font-semibold text-foreground">
          Advanced research and exact evidence
        </summary>
        <div className="mt-4">
      <p className="mb-4 text-sm leading-6 text-secondary">
        Claim: {data.claim.label}
        {data.claim.claim_identity ? ` · ${shortId(data.claim.claim_identity)}` : ''}
      </p>
      <LineageTrail
        items={[
          { label: 'scan', value: candidate.scan_id, href: `/scanner/${candidate.scan_id}` },
          { label: 'candidate', value: candidate.candidate_id },
          ...(candidate.deep_replay_run_id
            ? [
                {
                  label: 'historical QAP',
                  value: candidate.deep_replay_run_id,
                  href: `/experiments/${candidate.deep_replay_run_id}`,
                },
              ]
            : []),
        ]}
      />

      <div className="mt-6 grid gap-5 lg:grid-cols-2">
        <article className="rounded-lg border border-border bg-panel p-5">
          <p className="m-0 text-xs font-semibold uppercase tracking-[0.08em] text-muted">
            Why this rule exists
          </p>
          <ol className="mt-4 space-y-4 pl-5 text-sm leading-6 text-secondary">
            <li>
              <strong className="text-foreground">
                {isProductClaim
                  ? 'Frozen Product scope:'
                  : isPitClaim
                    ? 'PIT scope:'
                    : 'Frozen research scope:'}
              </strong>{' '}
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
        </div>
      </details>

      {candidate.economic_gate_status === 'deep_replay_survivor' && isPitClaim ? (
        <section id="start-forward-validation" className="mt-8 rounded-lg border border-border bg-panel p-5" aria-labelledby="freeze-heading">
          <div className="flex flex-wrap items-end justify-between gap-4">
            <div className="max-w-2xl">
              <h2 id="freeze-heading" className="mt-0 text-lg font-semibold text-foreground">
                Start forward validation
              </h2>
              <p className="mb-0 text-sm leading-6 text-secondary">
                Record the time boundary now, then return later to evaluate genuinely
                later evidence. QAP owns the predefined horizon and membership rules.
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <input
                className="min-h-11 rounded-md border border-border bg-canvas px-3 text-foreground"
                value={freezeAt}
                onChange={(event) => setFreezeAt(event.target.value)}
                placeholder="Freeze UTC"
                aria-label="Forward validation start time in UTC"
              />
              <button
                type="button"
                className="min-h-11 rounded-md bg-accent px-4 font-semibold text-canvas disabled:opacity-50"
                disabled={!freezeAt || freeze.isPending}
                onClick={() => freeze.mutate()}
              >
                {freeze.isPending ? 'Starting…' : 'Start forward validation'}
              </button>
            </div>
          </div>
          {freeze.isError ? <p className="mt-3 text-sm text-negative">{freeze.error.message}</p> : null}
          {operation ? (
            <p className="mt-3 text-sm text-secondary">
              Forward validation is starting.{' '}
              <a className="font-semibold text-accent" href={`/operations/${operation.operation_id}`}>
                View in Activity
              </a>
            </p>
          ) : null}
        </section>
      ) : null}

      {isPitClaim ? (
      <div className="mt-8 grid gap-5 lg:grid-cols-3">
        <section className="rounded-lg border border-border bg-panel p-4">
          <h2 className="mt-0 text-base font-semibold text-foreground">Forward validations</h2>
          {data.forward_cohort_ids.length ? (
            <ul className="space-y-2 pl-5 text-sm">
              {data.forward_cohort_ids.map((id, index) => (
                <li key={id}>
                  <a className="text-accent" href={`/prospective/${id}`} title={id}>
                    Forward validation {index + 1}
                  </a>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-secondary">No forward validation started.</p>
          )}
        </section>

        <section className="rounded-lg border border-border bg-panel p-4">
          <h2 className="mt-0 text-base font-semibold text-foreground">Current capital assessments</h2>
          {data.qualification_ids.length ? (
            <ul className="space-y-2 pl-5 text-sm text-secondary">
              {data.qualification_ids.map((id, index) => (
                <li key={id} title={id}>Assessment {index + 1}</li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-secondary">No current capital assessment.</p>
          )}
        </section>

        <section className="rounded-lg border border-border bg-panel p-4">
          <h2 className="mt-0 text-base font-semibold text-foreground">Portfolio research</h2>
          {data.basket_ids.length ? (
            <ul className="space-y-2 pl-5 text-sm">
              {data.basket_ids.map((id, index) => (
                <li key={id}>
                  <a className="text-accent" href={`/baskets/${id}`} title={id}>
                    Portfolio result {index + 1}
                  </a>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-secondary">Not used by a completed basket.</p>
          )}
        </section>
      </div>
      ) : (
        <section className="mt-8 rounded-lg border border-border bg-panel p-5">
          <h2 className="mt-0 text-lg font-semibold text-foreground">
            Follow-up research
          </h2>
          <p className="mb-0 text-sm leading-6 text-secondary">
            {isProductClaim
              ? 'This current-approved retrospective scan is complete historical evidence. Longitudinal follow-up is not available for this claim yet; review the completed evidence here or start a new Research task.'
              : 'This versioned research claim is preserved as completed evidence. Longitudinal follow-up is not authorized for this claim.'}
          </p>
        </section>
      )}
    </section>
  )
}
