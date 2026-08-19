import { useMutation, useQuery } from '@tanstack/react-query'
import { useState } from 'react'

import type { QapApiClient } from '../../api/client'
import type {
  CapturePublicEvidenceRequestDto,
  ForwardCohortDetailDto,
  OperationRefDto,
} from '../../api/types'
import { Badge } from '../../components/ui/Badge'
import { formatResearchTimestamp } from '../../lib/format'
import { LineageTrail } from '../lineage/LineageTrail'
import { ProspectiveAssessmentResults } from './ProspectiveAssessmentResults'
import { ProspectiveEvidenceSections } from './ProspectiveEvidenceSections'

interface ProspectiveDetailProps {
  apiClient: QapApiClient
  data: ForwardCohortDetailDto
}

type ReadinessRequest = {
  checkpointId: string
  asOf: string
}

function shortId(value: string) {
  return value.length <= 18 ? value : `${value.slice(0, 10)}…${value.slice(-6)}`
}

function outcomeLabel(status: string) {
  if (status === 'matured') return 'Forward window matured'
  if (status === 'partial') return 'Forward evidence still accumulating'
  if (status === 'pending') return 'Forward evidence pending'
  if (status === 'invalid') return 'Forward evidence invalid or unavailable'
  return status
}

function captureKindLabel(kind: 'l1' | 'depth' | 'metadata') {
  if (kind === 'l1') return 'top-of-book observations'
  if (kind === 'depth') return 'depth observations'
  return 'market metadata'
}

export function ProspectiveDetail({ apiClient, data }: ProspectiveDetailProps) {
  const latestCheckpoint = data.checkpoints.at(-1)
  const firstFreeze = data.freezes[0]
  const [advanceThrough, setAdvanceThrough] = useState('')
  const [assessmentAsOf, setAssessmentAsOf] = useState('')
  const [capital, setCapital] = useState('')
  const [checkpointId, setCheckpointId] = useState(
    latestCheckpoint?.checkpoint_id ?? '',
  )
  const [readinessRequest, setReadinessRequest] =
    useState<ReadinessRequest | null>(null)
  const [lastOperation, setLastOperation] = useState<OperationRefDto | null>(null)

  const advance = useMutation({
    mutationFn: () =>
      apiClient.advanceForwardCohort(data.summary.cohort_id, {
        through: advanceThrough,
      }),
    onSuccess: setLastOperation,
  })
  const capture = useMutation({
    mutationFn: (command: CapturePublicEvidenceRequestDto) =>
      apiClient.capturePublicEvidence(command),
    onSuccess: (operation) => {
      setLastOperation(operation)
      setReadinessRequest(null)
    },
  })
  const qualify = useMutation({
    mutationFn: () =>
      apiClient.qualifyCandidate({
        cohort_id: data.summary.cohort_id,
        checkpoint_id: checkpointId,
        as_of: assessmentAsOf,
        requested_capital: capital,
      }),
    onSuccess: setLastOperation,
  })

  const readiness = useQuery({
    queryKey: [
      'forward-capture-readiness',
      data.summary.cohort_id,
      readinessRequest?.checkpointId ?? '',
      readinessRequest?.asOf ?? '',
    ],
    queryFn: () =>
      apiClient.getForwardCaptureReadiness(data.summary.cohort_id, {
        checkpointId: readinessRequest?.checkpointId ?? '',
        asOf: readinessRequest?.asOf ?? '',
      }),
    enabled: readinessRequest !== null,
    retry: false,
  })

  const readinessIsCurrent =
    readinessRequest?.checkpointId === checkpointId &&
    readinessRequest?.asOf === assessmentAsOf
  const currentReadiness = readinessIsCurrent ? readiness.data : undefined
  const nextMissingKind = currentReadiness?.missing_capture_kinds[0]
  const canAssess = currentReadiness?.ready === true

  function checkCurrentEvidence() {
    if (!checkpointId || !assessmentAsOf) return
    setReadinessRequest({ checkpointId, asOf: assessmentAsOf })
  }

  function updateCurrentEvidence() {
    if (!currentReadiness || !nextMissingKind) return
    capture.mutate({
      venue: currentReadiness.venue,
      venue_symbol: currentReadiness.venue_symbol,
      base_asset: currentReadiness.base_asset,
      quote_asset: currentReadiness.quote_asset,
      kind: nextMissingKind,
    })
  }

  return (
    <section className="min-w-0">
      <header className="mb-8 max-w-4xl">
        <p className="mb-2 text-xs font-semibold uppercase tracking-[0.1em] text-accent">
          Forward validation
        </p>
        <h1 className="mb-3 text-3xl font-bold tracking-tight text-foreground md:text-4xl">
          {data.summary.horizon ?? 'Forward'} validation
        </h1>
        <p className="m-0 text-sm leading-6 text-secondary md:text-base">
          Follow research ideas frozen before later evidence, then evaluate current
          market evidence for a hypothetical amount. Historical, forward, and current
          evidence remain separate.
        </p>
      </header>

      {firstFreeze ? (
        <LineageTrail
          items={[
            {
              label: 'historical research',
              value: firstFreeze.source_scan_id,
              href: `/scanner/${firstFreeze.source_scan_id}`,
            },
            { label: 'forward validation', value: data.summary.cohort_id },
          ]}
        />
      ) : null}

      {lastOperation ? (
        <p className="mb-6 rounded-md border border-positive/40 bg-subtle p-3 text-sm text-secondary">
          Background work started.{' '}
          <a
            className="font-semibold text-accent"
            href={`/operations/${lastOperation.operation_id}`}
          >
            Track {shortId(lastOperation.operation_id)} in Activity
          </a>
        </p>
      ) : null}

      <section
        className="mb-6 rounded-lg border border-border bg-panel p-5"
        aria-labelledby="boundary-heading"
      >
        <h2 id="boundary-heading" className="mt-0 text-xl font-semibold text-foreground">
          What was frozen, and what happened later
        </h2>
        <div className="grid gap-4 md:grid-cols-[1fr_auto_1fr] md:items-center">
          <div className="rounded-md border border-border bg-canvas/40 p-4">
            <p className="m-0 text-xs font-semibold uppercase tracking-[0.08em] text-muted">
              Frozen historical research
            </p>
            <p className="mt-2 mb-1 font-semibold text-foreground">
              {data.freezes.length} research idea{data.freezes.length === 1 ? '' : 's'}
            </p>
            <p className="m-0 text-sm text-secondary">
              Frozen{' '}
              {data.summary.freeze_at
                ? formatResearchTimestamp(data.summary.freeze_at)
                : 'before forward evidence'}
            </p>
          </div>
          <span className="text-center text-xs font-semibold uppercase tracking-[0.08em] text-muted">
            Later evidence only →
          </span>
          <div className="rounded-md border border-border bg-canvas/40 p-4">
            <p className="m-0 text-xs font-semibold uppercase tracking-[0.08em] text-muted">
              Forward evidence
            </p>
            <p className="mt-2 mb-1 font-semibold text-foreground">
              {latestCheckpoint
                ? outcomeLabel(latestCheckpoint.outcome_status)
                : 'No forward checkpoint yet'}
            </p>
            <p className="m-0 text-sm text-secondary">
              {firstFreeze
                ? `${formatResearchTimestamp(firstFreeze.forward_start)} → ${formatResearchTimestamp(firstFreeze.forward_end)}`
                : 'The frozen validation horizon is applied by QAP.'}
            </p>
          </div>
        </div>
      </section>

      <div className="grid gap-5 xl:grid-cols-3">
        <section
          className="rounded-lg border border-border bg-panel p-5"
          aria-labelledby="advance-heading"
        >
          <p className="m-0 text-xs font-semibold uppercase tracking-[0.08em] text-muted">
            Step 1
          </p>
          <h2 id="advance-heading" className="mt-2 text-lg font-semibold text-foreground">
            Update forward evidence
          </h2>
          <p className="text-sm leading-6 text-secondary">
            QAP keeps the frozen horizon and maturity rules. Choose only how far through
            available information to update.
          </p>
          <label className="block text-sm font-medium text-secondary">
            Update through UTC
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
            {advance.isPending ? 'Starting…' : 'Update forward evidence'}
          </button>
          {advance.isError ? (
            <p className="text-sm text-negative">{advance.error.message}</p>
          ) : null}
        </section>

        <section
          className="rounded-lg border border-border bg-panel p-5"
          aria-labelledby="current-evidence-heading"
        >
          <p className="m-0 text-xs font-semibold uppercase tracking-[0.08em] text-muted">
            Step 2
          </p>
          <h2
            id="current-evidence-heading"
            className="mt-2 text-lg font-semibold text-foreground"
          >
            Current market evidence
          </h2>
          <p className="text-sm leading-6 text-secondary">
            QAP checks the selected checkpoint and as-of against its authoritative
            capture contract before asking you to update anything.
          </p>
          <select
            className="min-h-11 w-full rounded-md border border-border bg-canvas px-3 text-sm text-foreground"
            value={checkpointId}
            onChange={(event) => setCheckpointId(event.target.value)}
            aria-label="Current evidence checkpoint"
          >
            <option value="">Select forward checkpoint</option>
            {data.checkpoints.map((checkpoint) => (
              <option key={checkpoint.checkpoint_id} value={checkpoint.checkpoint_id}>
                #{checkpoint.checkpoint_index} ·{' '}
                {formatResearchTimestamp(checkpoint.information_end)}
              </option>
            ))}
          </select>
          <input
            className="mt-2 min-h-11 w-full rounded-md border border-border bg-canvas px-3 text-foreground"
            value={assessmentAsOf}
            onChange={(event) => setAssessmentAsOf(event.target.value)}
            placeholder="Current evidence as-of UTC"
            aria-label="Current evidence as-of"
          />
          <button
            type="button"
            className="mt-3 min-h-11 rounded-md border border-border px-4 font-semibold text-foreground disabled:opacity-50"
            disabled={!checkpointId || !assessmentAsOf || readiness.isFetching}
            onClick={checkCurrentEvidence}
          >
            {readiness.isFetching ? 'Checking…' : 'Check current market evidence'}
          </button>

          {readiness.isError && readinessIsCurrent ? (
            <p className="text-sm text-negative">{readiness.error.message}</p>
          ) : null}
          {currentReadiness ? (
            <div className="mt-4 rounded-md border border-border bg-canvas/40 p-4">
              <Badge tone={currentReadiness.ready ? 'positive' : 'warning'}>
                {currentReadiness.ready ? 'Current evidence ready' : 'Evidence needs updates'}
              </Badge>
              <dl className="mt-3 grid grid-cols-2 gap-3 text-sm">
                <div>
                  <dt className="text-xs text-muted">Top of book</dt>
                  <dd className="m-0 mt-1 font-semibold text-foreground">
                    {currentReadiness.l1_captured_slots}/{currentReadiness.l1_expected_slots}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs text-muted">Depth</dt>
                  <dd className="m-0 mt-1 font-semibold text-foreground">
                    {currentReadiness.depth_captured_slots}/{currentReadiness.depth_expected_slots}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs text-muted">Market metadata</dt>
                  <dd className="m-0 mt-1 font-semibold text-foreground">
                    {currentReadiness.metadata_available ? 'Available' : 'Missing'}
                  </dd>
                </div>
              </dl>
              {!currentReadiness.ready && nextMissingKind ? (
                <>
                  <p className="mt-3 text-sm text-secondary">
                    Next bounded update: {captureKindLabel(nextMissingKind)}.
                  </p>
                  <button
                    type="button"
                    className="min-h-11 rounded-md bg-accent px-4 font-semibold text-canvas disabled:opacity-50"
                    disabled={capture.isPending}
                    onClick={updateCurrentEvidence}
                  >
                    {capture.isPending ? 'Starting…' : 'Update current market evidence'}
                  </button>
                </>
              ) : null}
            </div>
          ) : null}
          {capture.isError ? (
            <p className="text-sm text-negative">{capture.error.message}</p>
          ) : null}
        </section>

        <section
          className="rounded-lg border border-border bg-panel p-5"
          aria-labelledby="assessment-heading"
        >
          <p className="m-0 text-xs font-semibold uppercase tracking-[0.08em] text-muted">
            Step 3
          </p>
          <h2 id="assessment-heading" className="mt-2 text-lg font-semibold text-foreground">
            Current capital assessment
          </h2>
          <p className="text-sm leading-6 text-secondary">
            Enter the hypothetical amount only after current market evidence is ready.
            QAP owns capacity, costs, constraints, and research classification.
          </p>
          <label className="block text-sm font-medium text-secondary">
            Amount to evaluate
            <input
              className="mt-2 min-h-11 w-full rounded-md border border-border bg-canvas px-3 text-foreground"
              value={capital}
              onChange={(event) => setCapital(event.target.value)}
              placeholder="Hypothetical capital"
              inputMode="decimal"
            />
          </label>
          {!canAssess ? (
            <p className="mt-3 text-xs leading-5 text-muted">
              Check current market evidence for this checkpoint and as-of before running
              the assessment.
            </p>
          ) : null}
          <button
            type="button"
            className="mt-3 min-h-11 rounded-md bg-accent px-4 font-semibold text-canvas disabled:opacity-50"
            disabled={!canAssess || !capital || qualify.isPending}
            onClick={() => qualify.mutate()}
          >
            {qualify.isPending ? 'Starting…' : 'Evaluate amount'}
          </button>
          <p className="mt-4 mb-0 text-xs leading-5 text-muted">
            Research assessment only — QAP does not place or authorize live trades.
          </p>
          {qualify.isError ? (
            <p className="text-sm text-negative">{qualify.error.message}</p>
          ) : null}
        </section>
      </div>

      <ProspectiveAssessmentResults qualifications={data.qualifications} />

      <ProspectiveEvidenceSections
        apiClient={apiClient}
        data={data}
        currentReadiness={currentReadiness}
        onCaptureStarted={(operation) => {
          setLastOperation(operation)
          setReadinessRequest(null)
        }}
      />
    </section>
  )
}
