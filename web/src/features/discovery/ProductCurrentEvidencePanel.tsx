import { useMutation, useQuery } from '@tanstack/react-query'
import { useState } from 'react'

import type { QapApiClient } from '../../api/client'
import type {
  OperationRefDto,
  ResearchIdeaCurrentEvidenceDto,
} from '../../api/types'
import { Badge, type BadgeTone } from '../../components/ui/Badge'
import { formatResearchTimestamp } from '../../lib/format'

interface ProductCurrentEvidencePanelProps {
  apiClient: QapApiClient
  scanId: string
  candidateId: string
}

function statePresentation(state: ResearchIdeaCurrentEvidenceDto['state']): {
  label: string
  tone: BadgeTone
} {
  if (state === 'contract_ready') {
    return { label: 'Current evidence contract ready', tone: 'positive' }
  }
  if (state === 'coverage_incomplete') {
    return { label: 'Current evidence still accumulating', tone: 'info' }
  }
  if (state === 'collecting') {
    return { label: 'Collection active', tone: 'info' }
  }
  if (state === 'evidence_unavailable') {
    return { label: 'Current evidence unavailable', tone: 'warning' }
  }
  return { label: 'Collection not started', tone: 'neutral' }
}

function CollectorStatus({
  status,
}: {
  status: ResearchIdeaCurrentEvidenceDto['collector_status']
}) {
  const tone: BadgeTone =
    status === 'running' ? 'positive' : status === 'failed' ? 'negative' : 'warning'
  const label =
    status === 'running'
      ? 'Collector running'
      : status === 'failed'
        ? 'Collector failed'
        : 'Collector not running'
  return <Badge tone={tone}>{label}</Badge>
}

function SlotStat({
  label,
  value,
}: {
  label: string
  value: ResearchIdeaCurrentEvidenceDto['l1_slots']
}) {
  return (
    <article className="rounded-md border border-border bg-canvas/35 p-4">
      <p className="m-0 text-xs font-semibold uppercase tracking-[0.08em] text-muted">
        {label}
      </p>
      <p className="mt-2 mb-0 text-sm text-secondary">
        <strong className="text-foreground">{value.captured}</strong> captured ·{' '}
        {value.missed} missed · {value.scheduled} scheduled
      </p>
    </article>
  )
}

export function ProductCurrentEvidencePanel({
  apiClient,
  scanId,
  candidateId,
}: ProductCurrentEvidencePanelProps) {
  const [capital, setCapital] = useState('')
  const [assessment, setAssessment] = useState<OperationRefDto | null>(null)
  const evidence = useQuery({
    queryKey: ['product-current-evidence', scanId, candidateId],
    queryFn: () => apiClient.getProductResearchIdeaCurrentEvidence(scanId, candidateId),
    refetchInterval: (query) => {
      const state = query.state.data?.state
      return state && state !== 'not_collecting' ? 30_000 : false
    },
  })
  const start = useMutation({
    mutationFn: () => apiClient.startProductResearchIdeaCurrentEvidence(scanId, candidateId),
    onSuccess: () => {
      void evidence.refetch()
    },
  })
  const stop = useMutation({
    mutationFn: () => apiClient.stopProductResearchIdeaCurrentEvidence(scanId, candidateId),
    onSuccess: () => {
      void evidence.refetch()
    },
  })
  const assess = useMutation({
    mutationFn: () =>
      apiClient.assessProductResearchIdeaAmount(scanId, candidateId, {
        requested_capital: capital,
      }),
    onSuccess: setAssessment,
  })

  if (evidence.isPending) {
    return (
      <section className="mt-8 rounded-lg border border-border bg-panel p-5">
        <p className="m-0 text-sm text-secondary">Reading current public-evidence state…</p>
      </section>
    )
  }
  if (evidence.isError || !evidence.data) {
    return (
      <section className="mt-8 rounded-lg border border-negative/40 bg-panel p-5">
        <Badge tone="negative">Current evidence unavailable</Badge>
        <p className="mt-3 mb-0 text-sm text-negative">
          {evidence.error?.message ?? 'Current public-evidence state could not be read.'}
        </p>
      </section>
    )
  }

  const data = evidence.data
  const presentation = statePresentation(data.state)
  const canAssess = data.state === 'contract_ready' && !data.assessment_blocker

  return (
    <section className="mt-8 rounded-lg border border-border bg-panel p-5" aria-labelledby="current-public-evidence-heading">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="max-w-3xl">
          <p className="m-0 text-xs font-semibold uppercase tracking-[0.08em] text-muted">
            Current public-market evidence
          </p>
          <h2 id="current-public-evidence-heading" className="mt-2 mb-2 text-xl font-semibold text-foreground">
            Evidence collected over real elapsed time
          </h2>
          <p className="m-0 text-sm leading-6 text-secondary">
            QAP records one scheduled public observation per required UTC slot. Missed
            slots stay missing after downtime; they are never reconstructed from historical
            order-book archives.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Badge tone={presentation.tone}>{presentation.label}</Badge>
          <CollectorStatus status={data.collector_status} />
        </div>
      </div>

      {data.collector_failure_reason ? (
        <p className="mt-4 rounded-md border border-negative/40 p-3 text-sm text-negative">
          {data.collector_failure_reason}
        </p>
      ) : null}

      {data.state === 'not_collecting' ? (
        <div className="mt-5">
          <p className="text-sm leading-6 text-secondary">
            Start collection for this Research Idea. If another idea uses the same exact
            frozen venue instrument, QAP reuses the instrument schedule rather than creating
            duplicate required slots.
          </p>
          <button
            type="button"
            className="min-h-11 rounded-md bg-accent px-4 font-semibold text-canvas disabled:opacity-50"
            disabled={start.isPending}
            onClick={() => start.mutate()}
          >
            {start.isPending ? 'Starting collection…' : 'Start current-evidence collection'}
          </button>
        </div>
      ) : (
        <>
          <div className="mt-5 grid gap-3 sm:grid-cols-2">
            <SlotStat label="Top-of-book · 60-second UTC slots" value={data.l1_slots} />
            <SlotStat label="Depth · 5-minute UTC slots" value={data.depth_slots} />
          </div>
          <div className="mt-4 grid gap-3 text-sm text-secondary md:grid-cols-3">
            <p className="m-0">
              Collection started:{' '}
              <strong className="text-foreground">
                {data.collecting_since
                  ? formatResearchTimestamp(data.collecting_since)
                  : 'unavailable'}
              </strong>
            </p>
            <p className="m-0">
              Latest observation:{' '}
              <strong className="text-foreground">
                {data.latest_observation
                  ? formatResearchTimestamp(data.latest_observation)
                  : 'none yet'}
              </strong>
            </p>
            <p className="m-0">
              Instrument:{' '}
              <strong className="text-foreground">
                {data.venue && data.venue_symbol
                  ? `${data.venue} · ${data.venue_symbol}`
                  : 'unavailable'}
              </strong>
            </p>
          </div>

          {data.readiness ? (
            <section className="mt-5 rounded-md border border-border bg-canvas/35 p-4">
              <h3 className="m-0 text-base font-semibold text-foreground">
                Existing QAP capture contract
              </h3>
              <p className="mt-2 mb-0 text-sm text-secondary">
                Through {formatResearchTimestamp(data.readiness.as_of)} · top of book{' '}
                {data.readiness.l1_captured_slots}/{data.readiness.l1_expected_slots} · depth{' '}
                {data.readiness.depth_captured_slots}/{data.readiness.depth_expected_slots} ·
                metadata {data.readiness.metadata_available ? 'available' : 'missing'}.
              </p>
              <p className="mt-2 mb-0 text-xs leading-5 text-muted">
                Coverage is evaluated by QAP&apos;s existing qualification policy. This page
                does not calculate its own readiness threshold.
              </p>
            </section>
          ) : null}

          <button
            type="button"
            className="mt-5 min-h-11 rounded-md border border-border px-4 font-semibold text-foreground disabled:opacity-50"
            disabled={stop.isPending}
            onClick={() => stop.mutate()}
          >
            {stop.isPending ? 'Stopping collection…' : 'Stop current-evidence collection'}
          </button>
        </>
      )}

      {start.isError ? <p className="mt-3 text-sm text-negative">{start.error.message}</p> : null}
      {stop.isError ? <p className="mt-3 text-sm text-negative">{stop.error.message}</p> : null}

      {data.state !== 'not_collecting' ? (
        <section className="mt-6 border-t border-border pt-5" aria-labelledby="amount-assessment-heading">
          <h3 id="amount-assessment-heading" className="m-0 text-lg font-semibold text-foreground">
            Hypothetical-capital assessment
          </h3>
          <p className="mt-2 text-sm leading-6 text-secondary">
            QAP enables an amount only when the existing current-evidence contract is ready
            and the frozen market-data sources are current at an exact backend boundary.
          </p>
          {data.assessment_blocker ? (
            <p className="rounded-md border border-border bg-canvas/35 p-3 text-sm text-secondary">
              {data.assessment_blocker}
            </p>
          ) : null}
          <label className="block max-w-sm text-sm font-medium text-secondary">
            Amount to evaluate
            <input
              className="mt-2 min-h-11 w-full rounded-md border border-border bg-canvas px-3 text-foreground disabled:opacity-50"
              value={capital}
              disabled={!canAssess}
              onChange={(event) => setCapital(event.target.value)}
              inputMode="decimal"
              placeholder="Hypothetical capital"
            />
          </label>
          <button
            type="button"
            className="mt-3 min-h-11 rounded-md bg-accent px-4 font-semibold text-canvas disabled:opacity-50"
            disabled={!canAssess || !capital || assess.isPending}
            onClick={() => assess.mutate()}
          >
            {assess.isPending ? 'Starting assessment…' : 'Evaluate amount'}
          </button>
          <p className="mt-3 mb-0 text-xs leading-5 text-muted">
            Research assessment only — QAP does not place or authorize live trades.
          </p>
          {assess.isError ? (
            <p className="mt-3 mb-0 text-sm text-negative">{assess.error.message}</p>
          ) : null}
          {assessment ? (
            <p className="mt-3 mb-0 text-sm text-secondary">
              Assessment is running through QAP&apos;s existing qualification operation.{' '}
              <a className="font-semibold text-accent" href={`/operations/${assessment.operation_id}`}>
                View in Activity
              </a>
            </p>
          ) : null}
        </section>
      ) : null}

      {data.plan_id ? (
        <details className="mt-5 text-xs text-muted">
          <summary className="min-h-11 cursor-pointer py-2 font-semibold text-accent">
            Exact collection lineage
          </summary>
          <p className="m-0 break-all">Plan: {data.plan_id}</p>
          <p className="mt-1 mb-0 break-all">Active cohort: {data.active_cohort_id}</p>
          <p className="mt-1 mb-0 break-all">Active freeze: {data.active_freeze_id}</p>
          <p className="mt-1 mb-0">
            Readiness boundary:{' '}
            {data.readiness_as_of
              ? formatResearchTimestamp(data.readiness_as_of)
              : 'not available yet'}
          </p>
        </details>
      ) : null}
    </section>
  )
}
