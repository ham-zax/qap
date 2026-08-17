import type { ExperimentListDto, RunSummaryDto } from '../../api/types'
import { Badge, type BadgeTone } from '../../components/ui/Badge'
import { formatRelativePercent, formatResearchTimestamp } from '../../lib/format'

interface ExperimentListProps {
  data: ExperimentListDto
}

function label(value: string | null | undefined): string {
  if (!value) return 'Unknown'
  return value
    .split('_')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ')
}

function statusPresentation(status: string | null | undefined): {
  label: string
  tone: BadgeTone
} {
  switch (status) {
    case 'positive':
      return { label: 'Positive evidence', tone: 'positive' }
    case 'negative':
      return { label: 'Negative evidence', tone: 'negative' }
    case 'neutral':
      return { label: 'Neutral evidence', tone: 'neutral' }
    case 'rejected':
      return { label: 'Rejected', tone: 'warning' }
    default:
      return { label: label(status), tone: 'neutral' }
  }
}

function dataRoleLabel(
  role: string | null | undefined,
  consumed: boolean | null | undefined,
): string {
  if (role === 'final_oos') {
    return `Final OOS · ${consumed ? 'consumed' : 'unconsumed'}`
  }
  return label(role)
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
        <h2 id={headingId} className="mb-2 text-base font-semibold text-foreground">
          {title}
        </h2>
        <p className="m-0 text-sm leading-6 text-secondary">
          {run.error?.message ?? 'The persisted evidence could not be validated.'}
        </p>
        <p className="mt-4 mb-0 break-all text-xs text-muted" title={run.run_id}>
          Run {shortId(run.run_id)}
        </p>
      </article>
    )
  }

  const status = statusPresentation(run.status)
  const comparison = run.incremental_vs_primary_control
    ? formatRelativePercent(run.incremental_vs_primary_control)
    : null

  return (
    <article
      aria-labelledby={headingId}
      className="flex min-w-0 flex-col rounded-lg border border-border bg-panel p-4 transition-[border-color,background-color] duration-150 hover:border-border-strong md:p-5"
    >
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <Badge tone={status.tone}>{status.label}</Badge>
        <Badge tone="info">
          {dataRoleLabel(run.data_role, run.final_oos_consumed)}
        </Badge>
      </div>

      <h2 id={headingId} className="mb-3 text-base font-semibold text-foreground">
        {title}
      </h2>

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
            <span>vs {label(run.primary_incremental_benchmark ?? 'primary control')}</span>
          </p>
        ) : (
          <p className="mt-1 mb-0 text-sm text-secondary">No primary comparison recorded.</p>
        )}
      </div>

      <div className="grid grid-cols-2 gap-x-4 gap-y-3 border-y border-border py-4 text-sm">
        <div className="min-w-0">
          <p className="m-0 text-xs text-muted">Basket</p>
          <p className="mt-1 mb-0 font-medium text-foreground">
            {run.basket?.join(' · ') ?? 'Unavailable'}
          </p>
        </div>
        <div className="min-w-0">
          <p className="m-0 text-xs text-muted">Model</p>
          <p className="mt-1 mb-0 font-medium text-foreground">
            {label(run.relationship_id ?? 'Unavailable')}
          </p>
        </div>
        <div className="min-w-0">
          <p className="m-0 text-xs text-muted">Policy</p>
          <p className="mt-1 mb-0 font-medium text-foreground">
            {label(run.policy_id ?? 'Unavailable')}
          </p>
        </div>
        <div className="min-w-0">
          <p className="m-0 text-xs text-muted">Anchor</p>
          <p className="mt-1 mb-0 font-medium text-foreground">
            {run.analysis_anchor ?? 'None'}
          </p>
        </div>
      </div>

      <div className="mt-4 flex flex-wrap gap-x-3 gap-y-1 text-xs text-muted">
        {run.created_timestamp ? (
          <span>{formatResearchTimestamp(run.created_timestamp)}</span>
        ) : null}
        {run.research_family_id ? <span>Family {run.research_family_id}</span> : null}
        {run.sibling_trial_count ? <span>{run.sibling_trial_count} sibling trials</span> : null}
        {run.git_dirty ? <span>Dirty snapshot</span> : null}
        <span className="break-all" title={run.run_id}>
          Run {shortId(run.run_id)}
        </span>
      </div>

      <a
        className="mt-5 inline-flex min-h-11 w-fit items-center rounded-md bg-accent px-4 py-2 text-sm font-semibold text-canvas no-underline transition-opacity duration-150 hover:opacity-90"
        href={`/experiments/${encodeURIComponent(run.run_id)}`}
      >
        View result
      </a>
    </article>
  )
}

export function ExperimentList({ data }: ExperimentListProps) {
  if (data.items.length === 0) {
    return <p>No persisted experiments are available.</p>
  }

  return (
    <section aria-labelledby="experiment-list-heading" className="min-w-0">
      <header className="mb-8 max-w-3xl">
        <p className="mb-2 text-xs font-semibold uppercase tracking-[0.1em] text-accent">
          Research evidence
        </p>
        <h1
          id="experiment-list-heading"
          className="mb-3 text-3xl font-bold tracking-tight text-foreground md:text-4xl"
        >
          Research runs
        </h1>
        <p className="m-0 text-sm leading-6 text-secondary md:text-base">
          Scan persisted outcomes by verdict and primary benchmark. Open a run for the full economic and technical evidence.
        </p>
      </header>

      <div className="grid gap-5 lg:grid-cols-2">
        {data.items.map((run) => (
          <ExperimentCard key={run.run_id} run={run} />
        ))}
      </div>
    </section>
  )
}
