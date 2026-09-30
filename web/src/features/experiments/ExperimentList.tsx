import type {
  BasketListDto,
  ExperimentListDto,
  ForwardCohortListDto,
  PaperOperationSummaryDto,
  RunSummaryDto,
  ScanListDto,
} from '../../api/types'
import { Badge } from '../../components/ui/Badge'
import { formatRelativePercent, formatResearchTimestamp } from '../../lib/format'
import {
  experimentDataRoleLabel,
  humanizeIdentifier,
  researchStatusPresentation,
} from './presentation'

interface ExperimentListProps {
  data?: ExperimentListDto
  experiments?: ExperimentListDto
  scans?: ScanListDto
  validations?: ForwardCohortListDto
  baskets?: BasketListDto
  paperOperations?: PaperOperationSummaryDto[]
}

function shortId(value: string): string {
  if (value.length <= 20) return value
  return `${value.slice(0, 10)}…${value.slice(-6)}`
}

function ExperimentCard({ run }: { run: RunSummaryDto }) {
  const title = run.experiment_name ?? run.run_id
  const headingId = `experiment-${run.run_id}-heading`

  if (run.artifact_status === 'invalid') {
    return (
      <article
        aria-labelledby={headingId}
        className="min-w-0 rounded-lg border border-negative/45 bg-panel p-4 md:p-5"
      >
        <div className="mb-4 flex flex-wrap items-center gap-2">
          <Badge tone="negative">Invalid artifact</Badge>
        </div>
        <h3 id={headingId} className="mb-2 text-base font-semibold text-foreground">
          {title}
        </h3>
        <p className="m-0 text-sm leading-6 text-secondary">
          {run.error?.message ?? 'The persisted evidence could not be validated.'}
        </p>
        <p className="mt-4 mb-0 break-all text-xs text-muted" title={run.run_id}>
          Run {shortId(run.run_id)}
        </p>
      </article>
    )
  }

  const status = researchStatusPresentation(run.status)
  const comparison = run.incremental_vs_primary_control
    ? formatRelativePercent(run.incremental_vs_primary_control)
    : null

  return (
    <article
      aria-labelledby={headingId}
      className="flex min-w-0 flex-col rounded-lg border border-border bg-panel p-4 md:p-5"
    >
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <Badge tone={status.tone}>{status.label}</Badge>
        <Badge tone="info">
          {experimentDataRoleLabel(run.data_role, run.final_oos_consumed)}
        </Badge>
      </div>
      <h3 id={headingId} className="mb-3 text-base font-semibold text-foreground">
        {title}
      </h3>
      <div className="mb-5">
        <p className="m-0 text-xs font-semibold uppercase tracking-[0.08em] text-muted">
          Primary comparison
        </p>
        {comparison ? (
          <p className="mt-1 mb-0 flex flex-wrap items-baseline gap-x-2 gap-y-1 text-secondary">
            <span
              className="text-2xl font-semibold tabular-nums text-foreground"
              data-exact={comparison.exact}
              title={`Exact: ${comparison.exact}`}
            >
              {comparison.display}
            </span>
            <span>
              vs {humanizeIdentifier(run.primary_incremental_benchmark ?? 'primary control')}
            </span>
          </p>
        ) : (
          <p className="mt-1 mb-0 text-sm text-secondary">No primary comparison recorded.</p>
        )}
      </div>
      <div className="grid grid-cols-2 gap-x-4 gap-y-3 border-y border-border py-4 text-sm">
        <div className="min-w-0">
          <p className="m-0 text-xs text-muted">Portfolio</p>
          <p className="mt-1 mb-0 font-medium text-foreground">
            {run.basket?.join(' · ') ?? 'Unavailable'}
          </p>
        </div>
        <div className="min-w-0">
          <p className="m-0 text-xs text-muted">Relationship model</p>
          <p className="mt-1 mb-0 font-medium text-foreground">
            {humanizeIdentifier(run.relationship_id ?? 'Unavailable')}
          </p>
        </div>
        <div className="min-w-0">
          <p className="m-0 text-xs text-muted">Policy</p>
          <p className="mt-1 mb-0 font-medium text-foreground">
            {humanizeIdentifier(run.policy_id ?? 'Unavailable')}
          </p>
        </div>
      </div>
      <div className="mt-4 flex flex-wrap gap-x-3 gap-y-1 text-xs text-muted">
        {run.created_timestamp ? (
          <span>{formatResearchTimestamp(run.created_timestamp)}</span>
        ) : null}
        <span className="break-all" title={run.run_id}>
          Run {shortId(run.run_id)}
        </span>
        {run.research_family_id ? <span>Family {run.research_family_id}</span> : null}
        {run.family_attempt_count ? (
          <span>
            {run.family_attempt_count} family {run.family_attempt_count === 1 ? 'attempt' : 'attempts'}
          </span>
        ) : null}
        {run.git_dirty ? <span>Dirty snapshot</span> : null}
      </div>
      <a
        className="mt-5 inline-flex min-h-11 w-fit items-center rounded-md bg-accent px-4 py-2 text-sm font-semibold text-canvas no-underline hover:opacity-90"
        href={`/experiments/${encodeURIComponent(run.run_id)}`}
      >
        Review research run
      </a>
    </article>
  )
}

export function ExperimentList({
  data,
  experiments,
  scans,
  validations,
  baskets,
  paperOperations,
}: ExperimentListProps) {
  const researchRuns = experiments ?? data
  const scanItems = scans?.items ?? []
  const validationItems = validations?.items ?? []
  const basketItems = baskets?.items ?? []
  const paperItems = paperOperations ?? []
  const runItems = researchRuns?.items ?? []

  return (
    <section aria-labelledby="history-heading" className="min-w-0">
      <header className="mb-8 max-w-4xl">
        <p className="mb-2 text-xs font-semibold uppercase tracking-[0.1em] text-accent">
          History
        </p>
        <h1
          id="history-heading"
          className="mb-3 text-3xl font-bold tracking-tight text-foreground md:text-4xl"
        >
          Research history
        </h1>
        <p className="m-0 text-sm leading-6 text-secondary md:text-base">
          Revisit research ideas, forward validations, portfolio results, QAP research
          runs, and paper evidence. These are persisted evidence records; background task
          execution belongs in Activity.
        </p>
      </header>

      <ResultSection
        eyebrow="Research Ideas"
        title="Research scans"
        description="Completed scanner research and the Research Ideas it contains."
        empty={scanItems.length === 0}
        emptyText="No completed research scans are available yet."
      >
        {scanItems.map((scan) => (
          <article key={scan.scan_id} className="rounded-lg border border-border bg-panel p-5">
            <div className="flex flex-wrap gap-2">
              <Badge tone={scan.artifact_status === 'valid' ? 'info' : 'negative'}>
                {scan.artifact_status === 'valid'
                  ? scan.claim?.label ?? 'Research evidence'
                  : 'Invalid artifact'}
              </Badge>
            </div>
            <h3 className="mt-4 mb-2 text-base font-semibold text-foreground">
              {scan.survivor_count ?? 0} surviving research idea
              {(scan.survivor_count ?? 0) === 1 ? '' : 's'}
            </h3>
            <p className="m-0 text-sm text-secondary">
              {scan.eligible_information_end
                ? `${scan.claim?.kind === 'current_approved_retrospective' ? 'Data through' : scan.claim?.kind === 'historical_pit' ? 'Historical cutoff' : 'Data boundary'} ${formatResearchTimestamp(scan.eligible_information_end)}`
                : 'Data boundary unavailable'}
              {' · '}
              {scan.candidate_count ?? 0} fixed rule evaluations
            </p>
            {scan.error ? (
              <p className="mt-3 text-sm text-negative">{scan.error.message}</p>
            ) : null}
            <a
              className="mt-4 inline-flex min-h-11 items-center font-semibold text-accent"
              href={`/scanner/${scan.scan_id}`}
            >
              Review research ideas
            </a>
            <p className="mt-2 mb-0 text-xs text-muted">Research {shortId(scan.scan_id)}</p>
          </article>
        ))}
      </ResultSection>

      <ResultSection
        eyebrow="Forward validation"
        title="Later evidence"
        description="Frozen research ideas followed into predefined forward evidence and current capital assessments."
        empty={validationItems.length === 0}
        emptyText="No forward validations are available yet."
      >
        {validationItems.map((validation) => (
          <article
            key={validation.cohort_id}
            className="rounded-lg border border-border bg-panel p-5"
          >
            <div className="flex flex-wrap gap-2">
              <Badge tone={validation.artifact_status === 'valid' ? 'info' : 'negative'}>
                {validation.artifact_status === 'valid'
                  ? 'Forward validation'
                  : 'Invalid artifact'}
              </Badge>
              {validation.horizon ? <Badge tone="info">{validation.horizon}</Badge> : null}
            </div>
            <h3 className="mt-4 mb-2 text-base font-semibold text-foreground">
              {validation.checkpoint_count ?? 0} forward checkpoint
              {(validation.checkpoint_count ?? 0) === 1 ? '' : 's'}
            </h3>
            <p className="m-0 text-sm text-secondary">
              {validation.freeze_at
                ? `Frozen ${formatResearchTimestamp(validation.freeze_at)}`
                : 'Freeze time unavailable'}
              {' · '}
              {validation.qualification_count ?? 0} capital assessment
              {(validation.qualification_count ?? 0) === 1 ? '' : 's'}
            </p>
            {validation.error ? (
              <p className="mt-3 text-sm text-negative">{validation.error.message}</p>
            ) : null}
            <a
              className="mt-4 inline-flex min-h-11 items-center font-semibold text-accent"
              href={`/prospective/${validation.cohort_id}`}
            >
              Review forward validation
            </a>
            <p className="mt-2 mb-0 text-xs text-muted">
              Validation {shortId(validation.cohort_id)}
            </p>
          </article>
        ))}
      </ResultSection>

      <ResultSection
        eyebrow="Portfolio results"
        title="Portfolio research"
        description="Completed portfolio research, including negative economic conclusions as valid evidence."
        empty={basketItems.length === 0}
        emptyText="No portfolio research results are available yet."
      >
        {basketItems.map((basket) => {
          const survived = basket.economic_gate_status === 'basket_development_survivor'
          const rejected = basket.economic_gate_status === 'basket_development_rejected'
          return (
            <article key={basket.basket_id} className="rounded-lg border border-border bg-panel p-5">
              <div className="flex flex-wrap gap-2">
                {basket.artifact_status === 'invalid' ? (
                  <Badge tone="negative">Invalid artifact</Badge>
                ) : survived ? (
                  <Badge tone="positive">Passed basket development gates</Badge>
                ) : rejected ? (
                  <Badge tone="info">Did not pass basket development gates</Badge>
                ) : (
                  <Badge tone="info">Completed portfolio research</Badge>
                )}
              </div>
              <h3 className="mt-4 mb-2 text-base font-semibold text-foreground">
                {basket.economic_assets.join(' · ') || `Portfolio ${shortId(basket.basket_id)}`}
              </h3>
              <p className="m-0 text-sm text-secondary">
                {basket.horizon ?? 'horizon unavailable'} ·{' '}
                {basket.decision_resolution ?? 'resolution unavailable'}
              </p>
              {basket.error ? (
                <p className="mt-3 text-sm text-negative">{basket.error.message}</p>
              ) : null}
              <a
                className="mt-4 inline-flex min-h-11 items-center font-semibold text-accent"
                href={`/baskets/${basket.basket_id}`}
              >
                Review portfolio result
              </a>
            </article>
          )
        })}
      </ResultSection>

      <ResultSection
        eyebrow="Research runs"
        title="QAP economic evidence"
        description="Persisted QAP outcomes with their declared benchmark comparison and specialist evidence routes."
        empty={runItems.length === 0}
        emptyText="No persisted QAP research runs are available yet."
      >
        {runItems.map((run) => (
          <ExperimentCard key={run.run_id} run={run} />
        ))}
      </ResultSection>

      <ResultSection
        eyebrow="Paper evidence"
        title="Operational dry runs"
        description="Forward-paper execution and reconciliation evidence. It is not candidate or deployment evidence."
        empty={paperItems.length === 0}
        emptyText="No paper evidence is available yet."
      >
        {paperItems.map((paper) => (
          <article
            key={paper.operation_id}
            className="rounded-lg border border-border bg-panel p-5"
          >
            <div className="flex flex-wrap gap-2">
              {paper.artifact_status === 'invalid' ? (
                <Badge tone="negative">Invalid artifact</Badge>
              ) : (
                <Badge tone={paper.reconciliation_matches === true ? 'info' : 'warning'}>
                  {paper.reconciliation_matches === true
                    ? 'Reconciled paper evidence'
                    : 'Paper reconciliation mismatch'}
                </Badge>
              )}
              <Badge tone="info">Operational dry run</Badge>
            </div>
            <h3 className="mt-4 mb-2 text-base font-semibold text-foreground">
              Forward-paper evidence
            </h3>
            <p className="m-0 text-sm text-secondary">
              {paper.execution_timestamp
                ? formatResearchTimestamp(paper.execution_timestamp)
                : 'Execution time unavailable'}
              {paper.fill_count == null ? '' : ` · ${paper.fill_count} fills`}
            </p>
            {paper.error ? (
              <p className="mt-3 text-sm text-negative">{paper.error.message}</p>
            ) : null}
            <p className="mt-3 mb-0 text-xs font-medium text-warning">
              Not candidate or deployment evidence
            </p>
            <a
              className="mt-4 inline-flex min-h-11 items-center font-semibold text-accent"
              href={`/paper-operations/${paper.operation_id}`}
            >
              Review paper evidence
            </a>
          </article>
        ))}
      </ResultSection>
    </section>
  )
}

function ResultSection({
  eyebrow,
  title,
  description,
  empty,
  emptyText,
  children,
}: {
  eyebrow: string
  title: string
  description: string
  empty: boolean
  emptyText: string
  children: React.ReactNode
}) {
  return (
    <section className="mt-10" aria-labelledby={`result-section-${title.replaceAll(' ', '-')}`}>
      <div className="mb-4 max-w-3xl">
        <p className="m-0 text-xs font-semibold uppercase tracking-[0.08em] text-muted">
          {eyebrow}
        </p>
        <h2
          id={`result-section-${title.replaceAll(' ', '-')}`}
          className="mt-2 mb-2 text-xl font-semibold text-foreground"
        >
          {title}
        </h2>
        <p className="m-0 text-sm leading-6 text-secondary">{description}</p>
      </div>
      {empty ? (
        <p className="text-sm text-secondary">{emptyText}</p>
      ) : (
        <div className="grid gap-5 lg:grid-cols-2">{children}</div>
      )}
    </section>
  )
}
