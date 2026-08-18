import { useMutation } from '@tanstack/react-query'
import { useMemo, useState } from 'react'

import type { QapApiClient } from '../../api/client'
import type {
  CapturePublicEvidenceRequestDto,
  ForwardCohortDetailDto,
  OperationRefDto,
} from '../../api/types'
import { Badge } from '../../components/ui/Badge'
import { formatResearchTimestamp } from '../../lib/format'
import { LineageTrail } from '../lineage/LineageTrail'

interface ProspectiveDetailProps {
  apiClient: QapApiClient
  data: ForwardCohortDetailDto
}

function shortId(value: string) {
  return value.length <= 18 ? value : `${value.slice(0, 10)}…${value.slice(-6)}`
}

function stateTone(state: string): 'positive' | 'warning' | 'negative' | 'info' {
  if (state === 'tradable_now') return 'positive'
  if (state === 'small_capacity') return 'warning'
  if (state === 'research_only') return 'info'
  return 'negative'
}

export function ProspectiveDetail({ apiClient, data }: ProspectiveDetailProps) {
  const [advanceThrough, setAdvanceThrough] = useState('')
  const [qualificationAsOf, setQualificationAsOf] = useState('')
  const [capital, setCapital] = useState('')
  const [checkpointId, setCheckpointId] = useState(
    data.checkpoints.at(-1)?.checkpoint_id ?? '',
  )
  const firstFreeze = data.freezes[0]
  const [capture, setCapture] = useState<CapturePublicEvidenceRequestDto>({
    venue: (firstFreeze?.venue ?? 'binance') as 'binance' | 'gate',
    venue_symbol: '',
    base_asset: firstFreeze?.pair_id.split('/')[0] ?? '',
    quote_asset: 'USDT',
    kind: 'l1',
  })
  const [lastOperation, setLastOperation] = useState<OperationRefDto | null>(null)

  const advance = useMutation({
    mutationFn: () =>
      apiClient.advanceForwardCohort(data.summary.cohort_id, {
        through: advanceThrough,
      }),
    onSuccess: setLastOperation,
  })
  const captureMutation = useMutation({
    mutationFn: () => apiClient.capturePublicEvidence(capture),
    onSuccess: setLastOperation,
  })
  const qualify = useMutation({
    mutationFn: () =>
      apiClient.qualifyCandidate({
        cohort_id: data.summary.cohort_id,
        checkpoint_id: checkpointId,
        as_of: qualificationAsOf,
        requested_capital: capital,
      }),
    onSuccess: setLastOperation,
  })

  const automatic = useMemo(
    () => data.freezes.filter((item) => item.automatic_selected),
    [data.freezes],
  )
  const manual = useMemo(
    () => data.freezes.filter((item) => item.manual_selected && !item.automatic_selected),
    [data.freezes],
  )

  return (
    <section className="min-w-0">
      <header className="mb-8 max-w-4xl">
        <p className="mb-2 text-xs font-semibold uppercase tracking-[0.1em] text-accent">
          Prospective cohort
        </p>
        <h1 className="mb-3 text-3xl font-bold tracking-tight text-foreground md:text-4xl">
          {data.summary.horizon ?? 'Forward'} evidence
        </h1>
        <div className="flex flex-wrap gap-2">
          <Badge tone="info">
            {data.summary.automatic_member_count ?? 0} automatic
          </Badge>
          <Badge tone="warning">{data.summary.manual_member_count ?? 0} manual</Badge>
          <Badge tone="info">{data.checkpoints.length} checkpoints</Badge>
        </div>
        {data.summary.freeze_at ? (
          <p className="mt-3 mb-0 text-sm text-secondary">
            Cohort frozen {formatResearchTimestamp(data.summary.freeze_at)} ·{' '}
            <span className="break-all">{data.summary.cohort_id}</span>
          </p>
        ) : null}
      </header>

      {firstFreeze ? (
        <LineageTrail
          items={[
            {
              label: 'scan',
              value: firstFreeze.source_scan_id,
              href: `/scanner/${firstFreeze.source_scan_id}`,
            },
            { label: 'cohort', value: data.summary.cohort_id },
          ]}
        />
      ) : null}

      {lastOperation ? (
        <p className="mb-6 rounded-md border border-positive/40 bg-subtle p-3 text-sm text-secondary">
          Operation started.{' '}
          <a className="font-semibold text-accent" href={`/operations/${lastOperation.operation_id}`}>
            Track {shortId(lastOperation.operation_id)}
          </a>
        </p>
      ) : null}

      <div className="grid gap-5 xl:grid-cols-3">
        <section className="rounded-lg border border-border bg-panel p-5" aria-labelledby="advance-heading">
          <h2 id="advance-heading" className="mt-0 text-lg font-semibold text-foreground">
            Advance evidence
          </h2>
          <p className="text-sm leading-6 text-secondary">
            Each candidate matures on its own frozen resolution/horizon boundary.
          </p>
          <label className="block text-sm font-medium text-secondary">
            Through UTC
            <input
              className="mt-2 min-h-11 w-full rounded-md border border-border bg-canvas px-3 text-foreground"
              value={advanceThrough}
              onChange={(event) => setAdvanceThrough(event.target.value)}
              placeholder="2026-08-25T00:00:00Z"
            />
          </label>
          <button
            type="button"
            className="mt-3 min-h-11 rounded-md bg-accent px-4 font-semibold text-canvas disabled:opacity-50"
            disabled={!advanceThrough || advance.isPending}
            onClick={() => advance.mutate()}
          >
            {advance.isPending ? 'Starting…' : 'Advance cohort'}
          </button>
          {advance.isError ? <p className="text-sm text-negative">{advance.error.message}</p> : null}
        </section>

        <section className="rounded-lg border border-border bg-panel p-5" aria-labelledby="capture-heading">
          <h2 id="capture-heading" className="mt-0 text-lg font-semibold text-foreground">
            One-shot public capture
          </h2>
          <p className="text-sm leading-6 text-secondary">
            No scheduling is implied. Capture L1, shallow depth, or public market metadata now.
          </p>
          <div className="grid gap-2">
            <select
              className="min-h-11 rounded-md border border-border bg-canvas px-3 text-sm text-foreground"
              value={capture.kind}
              onChange={(event) => setCapture({ ...capture, kind: event.target.value as CapturePublicEvidenceRequestDto['kind'] })}
              aria-label="Capture kind"
            >
              <option value="l1">L1 / book ticker</option>
              <option value="depth">Shallow depth</option>
              <option value="metadata">Market metadata</option>
            </select>
            <select
              className="min-h-11 rounded-md border border-border bg-canvas px-3 text-sm text-foreground"
              value={capture.venue}
              onChange={(event) => setCapture({ ...capture, venue: event.target.value as 'binance' | 'gate' })}
              aria-label="Capture venue"
            >
              <option value="binance">binance</option>
              <option value="gate">gate</option>
            </select>
            <input
              className="min-h-11 rounded-md border border-border bg-canvas px-3 text-foreground"
              value={capture.venue_symbol}
              onChange={(event) => setCapture({ ...capture, venue_symbol: event.target.value })}
              placeholder="Venue symbol, e.g. BTCUSDT"
              aria-label="Venue symbol"
            />
            <div className="grid grid-cols-2 gap-2">
              <input
                className="min-h-11 rounded-md border border-border bg-canvas px-3 text-foreground"
                value={capture.base_asset}
                onChange={(event) => setCapture({ ...capture, base_asset: event.target.value.toUpperCase() })}
                placeholder="Base"
                aria-label="Base asset"
              />
              <input
                className="min-h-11 rounded-md border border-border bg-canvas px-3 text-foreground"
                value={capture.quote_asset}
                onChange={(event) => setCapture({ ...capture, quote_asset: event.target.value.toUpperCase() })}
                placeholder="Quote"
                aria-label="Quote asset"
              />
            </div>
          </div>
          <button
            type="button"
            className="mt-3 min-h-11 rounded-md border border-border px-4 font-semibold text-foreground disabled:opacity-50"
            disabled={!capture.venue_symbol || !capture.base_asset || !capture.quote_asset || captureMutation.isPending}
            onClick={() => captureMutation.mutate()}
          >
            {captureMutation.isPending ? 'Starting…' : 'Capture now'}
          </button>
          {captureMutation.isError ? <p className="text-sm text-negative">{captureMutation.error.message}</p> : null}
        </section>

        <section className="rounded-lg border border-border bg-panel p-5" aria-labelledby="qualification-heading">
          <h2 id="qualification-heading" className="mt-0 text-lg font-semibold text-foreground">
            Qualify explicit capital
          </h2>
          <p className="text-sm leading-6 text-secondary">
            QAP derives current state, the causal capture window, capacity, costs, and all frozen policy details.
          </p>
          <select
            className="min-h-11 w-full rounded-md border border-border bg-canvas px-3 text-sm text-foreground"
            value={checkpointId}
            onChange={(event) => setCheckpointId(event.target.value)}
            aria-label="Qualification checkpoint"
          >
            <option value="">Select checkpoint</option>
            {data.checkpoints.map((checkpoint) => (
              <option key={checkpoint.checkpoint_id} value={checkpoint.checkpoint_id}>
                #{checkpoint.checkpoint_index} · {formatResearchTimestamp(checkpoint.information_end)}
              </option>
            ))}
          </select>
          <input
            className="mt-2 min-h-11 w-full rounded-md border border-border bg-canvas px-3 text-foreground"
            value={qualificationAsOf}
            onChange={(event) => setQualificationAsOf(event.target.value)}
            placeholder="Current UTC as-of"
            aria-label="Qualification as-of"
          />
          <input
            className="mt-2 min-h-11 w-full rounded-md border border-border bg-canvas px-3 text-foreground"
            value={capital}
            onChange={(event) => setCapital(event.target.value)}
            placeholder="Hypothetical capital"
            inputMode="decimal"
            aria-label="Requested capital"
          />
          <button
            type="button"
            className="mt-3 min-h-11 rounded-md bg-accent px-4 font-semibold text-canvas disabled:opacity-50"
            disabled={!checkpointId || !qualificationAsOf || !capital || qualify.isPending}
            onClick={() => qualify.mutate()}
          >
            {qualify.isPending ? 'Starting…' : 'Qualify'}
          </button>
          {qualify.isError ? <p className="text-sm text-negative">{qualify.error.message}</p> : null}
        </section>
      </div>

      <section className="mt-8" aria-labelledby="members-heading">
        <div className="flex flex-wrap items-baseline justify-between gap-3">
          <h2 id="members-heading" className="text-xl font-semibold text-foreground">
            Frozen members
          </h2>
          <span className="text-sm text-muted">Automatic evidence stays separate from manual/pinned evidence.</span>
        </div>
        <div className="mt-4 grid gap-5 lg:grid-cols-2">
          <MemberGroup title="Automatic scanner selections" items={automatic} />
          <MemberGroup title="Manual-only selections" items={manual} />
        </div>
      </section>

      <section className="mt-8" aria-labelledby="checkpoints-heading">
        <h2 id="checkpoints-heading" className="text-xl font-semibold text-foreground">Forward checkpoints</h2>
        {data.checkpoints.length === 0 ? (
          <p className="text-secondary">No completed forward checkpoint yet.</p>
        ) : (
          <div className="mt-4 overflow-x-auto rounded-lg border border-border bg-panel">
            <table className="w-full min-w-[52rem] text-left text-sm">
              <thead className="bg-subtle text-xs uppercase tracking-[0.06em] text-muted">
                <tr><th className="px-4 py-3">Candidate</th><th className="px-4 py-3">Maturity</th><th className="px-4 py-3">Outcome</th><th className="px-4 py-3">Economics</th><th className="px-4 py-3">QAP</th></tr>
              </thead>
              <tbody>
                {data.checkpoints.map((checkpoint) => (
                  <tr key={checkpoint.checkpoint_id} className="border-t border-border">
                    <td className="px-4 py-3 font-medium text-foreground">{shortId(checkpoint.candidate_id)}</td>
                    <td className="px-4 py-3 text-secondary">#{checkpoint.checkpoint_index} · {formatResearchTimestamp(checkpoint.information_end)}</td>
                    <td className="px-4 py-3"><Badge tone={checkpoint.outcome_status === 'invalid' ? 'negative' : 'info'}>{checkpoint.outcome_status}</Badge></td>
                    <td className="px-4 py-3 text-secondary">baseline {String(checkpoint.baseline_economic_gates_passed ?? '—')} · adverse {String(checkpoint.adverse_economic_gates_passed ?? '—')}</td>
                    <td className="px-4 py-3">{checkpoint.qap_run_id ? <a className="text-accent" href={`/experiments/${checkpoint.qap_run_id}`}>Experiment</a> : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="mt-8" aria-labelledby="qualifications-heading">
        <h2 id="qualifications-heading" className="text-xl font-semibold text-foreground">Current actionability claims</h2>
        {data.qualifications.length === 0 ? (
          <p className="text-secondary">No qualification has been published. Missing capture evidence is not treated as actionability.</p>
        ) : (
          <div className="mt-4 grid gap-4 lg:grid-cols-2">
            {data.qualifications.map((qualification) => (
              <article key={qualification.qualification_id} className="rounded-lg border border-border bg-panel p-5">
                <div className="flex flex-wrap gap-2">
                  <Badge tone={stateTone(qualification.state)}>{qualification.state}</Badge>
                  <Badge tone={qualification.capture_contract_satisfied ? 'positive' : 'warning'}>
                    capture {qualification.capture_contract_satisfied ? 'complete' : 'incomplete'}
                  </Badge>
                </div>
                <h3 className="mt-4 mb-1 text-base font-semibold text-foreground">{qualification.reason}</h3>
                <p className="mt-1 text-sm text-secondary">
                  As of {formatResearchTimestamp(qualification.as_of)} · requested {qualification.requested_capital}
                </p>
                <dl className="mt-4 grid grid-cols-2 gap-3 text-sm">
                  <div><dt className="text-xs text-muted">Captured observations</dt><dd className="m-0 mt-1 font-semibold text-foreground">{qualification.capture_snapshot_ids.length}</dd></div>
                  <div><dt className="text-xs text-muted">Capital ceiling</dt><dd className="m-0 mt-1 font-semibold text-foreground">{qualification.candidate_capital_ceiling ?? 'unknown'}</dd></div>
                  <div><dt className="text-xs text-muted">Safe buy</dt><dd className="m-0 mt-1 text-secondary">{qualification.q_safe_buy ?? 'unknown'}</dd></div>
                  <div><dt className="text-xs text-muted">Safe sell</dt><dd className="m-0 mt-1 text-secondary">{qualification.q_safe_sell ?? 'unknown'}</dd></div>
                </dl>
                <p className="mt-4 mb-0 text-xs leading-5 text-muted">
                  eligibility {String(qualification.eligibility_resolved)} · two-way market {String(qualification.current_two_way_trading)} · order constraints {String(qualification.order_constraints_satisfied)} · baseline/adverse gates {String(qualification.requested_baseline_gate_passed ?? '—')}/{String(qualification.requested_adverse_gate_passed ?? '—')}
                </p>
              </article>
            ))}
          </div>
        )}
      </section>
    </section>
  )
}

function MemberGroup({ title, items }: { title: string; items: ForwardCohortDetailDto['freezes'] }) {
  return (
    <article className="rounded-lg border border-border bg-panel p-5">
      <h3 className="mt-0 text-base font-semibold text-foreground">{title}</h3>
      {items.length === 0 ? (
        <p className="text-sm text-secondary">None.</p>
      ) : (
        <ul className="space-y-3 pl-5 text-sm text-secondary">
          {items.map((freeze) => (
            <li key={freeze.freeze_id}>
              <a className="font-semibold text-accent" href={`/candidate/${freeze.source_scan_id}/${freeze.candidate_id}`}>
                {freeze.pair_id}
              </a>{' '}
              · {freeze.resolution} · {formatResearchTimestamp(freeze.forward_start)} → {formatResearchTimestamp(freeze.forward_end)}
            </li>
          ))}
        </ul>
      )}
    </article>
  )
}
