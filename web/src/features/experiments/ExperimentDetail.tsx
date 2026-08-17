import type { ExperimentDetailDto } from '../../api/types'
import { Badge } from '../../components/ui/Badge'
import {
  ComparisonBars,
  type ComparisonBarItem,
} from '../../components/visuals/ComparisonBars'
import { formatPercent, formatRelativePercent, formatResearchDate } from '../../lib/format'
import {
  experimentDataRoleLabel,
  humanizeIdentifier,
  researchComparisonTone,
  researchStatusPresentation,
  researchVerdictHeadline,
} from './presentation'

interface ExperimentDetailProps {
  data: ExperimentDetailDto
}

function pairWorkbenchHref(data: ExperimentDetailDto): string | null {
  const [assetX, assetY] = data.manifest.basket
  if (!assetX || !assetY) return null
  const search = new URLSearchParams({
    orientation: `${assetX}/${assetY}`,
    anchor: data.manifest.analysis_anchor ?? 'none',
    view: 'ratio',
  })
  return `/pair/${encodeURIComponent(data.run_id)}/${encodeURIComponent(assetX)}/${encodeURIComponent(assetY)}?${search}`
}

function heroBorder(tone: ReturnType<typeof researchStatusPresentation>['tone']): string {
  switch (tone) {
    case 'positive':
      return 'border-positive/45'
    case 'negative':
      return 'border-negative/45'
    case 'warning':
      return 'border-warning/45'
    case 'info':
      return 'border-info/45'
    default:
      return 'border-border-strong'
  }
}

function ProvenanceValue({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0">
      <p className="m-0 text-xs font-medium text-muted">{label}</p>
      <code className="mt-1 block max-w-full overflow-x-auto font-mono text-xs text-secondary">
        {value}
      </code>
    </div>
  )
}

export function ExperimentDetail({ data }: ExperimentDetailProps) {
  const { manifest, provenance, result, final_oos_commitment: commitment } = data
  const pairHref = pairWorkbenchHref(data)
  const status = researchStatusPresentation(result.status)
  const primaryComparison = result.strategy_vs_primary_control
    ? formatRelativePercent(result.strategy_vs_primary_control)
    : null
  const hodlComparison = formatRelativePercent(result.strategy_vs_hodl)
  const successThreshold = formatPercent(result.success_threshold)
  const verdict = researchVerdictHeadline(
    result.status,
    result.primary_incremental_benchmark,
    result.strategy_vs_primary_control,
  )
  const comparisons: ComparisonBarItem[] = [
    ...(result.strategy_vs_primary_control && result.primary_incremental_benchmark
      ? [
          {
            label: `Primary control · ${humanizeIdentifier(result.primary_incremental_benchmark)}`,
            value: result.strategy_vs_primary_control,
            tone: researchComparisonTone(result.status, result.strategy_vs_primary_control),
          },
        ]
      : []),
    { label: 'Strict inventory HODL', value: result.strategy_vs_hodl },
    ...(result.strategy_vs_matched_contribution
      ? [
          {
            label: 'Matched-contribution HODL',
            value: result.strategy_vs_matched_contribution,
          },
        ]
      : []),
  ]

  return (
    <article className="min-w-0" aria-labelledby="experiment-detail-heading">
      <div className="mb-4">
        <nav aria-label="Breadcrumb" className="flex flex-wrap items-center gap-2 text-sm text-muted">
          <a className="font-medium text-secondary" href="/experiments">
            Research runs
          </a>
          <span aria-hidden="true">/</span>
          <span aria-current="page">{manifest.experiment_name}</span>
        </nav>
      </div>

      <header
        className={`rounded-lg border bg-panel p-5 md:p-6 ${heroBorder(status.tone)}`}
      >
        <div className="mb-4 flex flex-wrap items-center gap-2">
          <Badge tone={status.tone}>{status.label}</Badge>
          <Badge tone="info">
            {experimentDataRoleLabel(result.data_role, result.final_oos_consumed)}
          </Badge>
        </div>

        <p className="mb-2 text-xs font-semibold uppercase tracking-[0.1em] text-muted">
          Research verdict
        </p>
        <h1
          id="experiment-detail-heading"
          className="mb-3 text-2xl font-bold tracking-tight text-foreground md:text-3xl"
        >
          {manifest.experiment_name}
        </h1>
        <p className="m-0 max-w-4xl text-2xl font-semibold leading-tight text-foreground md:text-3xl">
          {verdict}
        </p>
        <p className="mt-4 mb-0 max-w-3xl text-sm leading-6 text-secondary md:text-base">
          {manifest.description}
        </p>

        <div className="mt-5 grid gap-3 sm:grid-cols-3">
          <div className="rounded-md border border-border bg-canvas/55 p-4">
            <p className="m-0 text-xs font-medium text-muted">
              vs {humanizeIdentifier(result.primary_incremental_benchmark ?? 'primary control')}
            </p>
            <p
              className="mt-1 mb-0 text-2xl font-semibold tabular-nums text-foreground"
              data-exact={primaryComparison?.exact}
            >
              {primaryComparison?.display ?? 'Not applicable'}
            </p>
          </div>
          <div className="rounded-md border border-border bg-canvas/55 p-4">
            <p className="m-0 text-xs font-medium text-muted">vs strict inventory HODL</p>
            <p
              className="mt-1 mb-0 text-2xl font-semibold tabular-nums text-foreground"
              data-exact={hodlComparison.exact}
            >
              {hodlComparison.display}
            </p>
          </div>
          <div className="rounded-md border border-border bg-canvas/55 p-4">
            <p className="m-0 text-xs font-medium text-muted">Predeclared success threshold</p>
            <p
              className="mt-1 mb-0 text-2xl font-semibold tabular-nums text-foreground"
              data-exact={successThreshold.exact}
            >
              {successThreshold.display}
            </p>
          </div>
        </div>

        <nav className="mt-5 flex flex-wrap gap-2" aria-label="Run evidence links">
          <a
            className="inline-flex min-h-11 items-center rounded-md bg-accent px-4 py-2 text-sm font-semibold text-canvas no-underline hover:opacity-90"
            href={`/portfolio/${encodeURIComponent(data.run_id)}`}
          >
            Portfolio economics
          </a>
          {pairHref ? (
            <a
              className="inline-flex min-h-11 items-center rounded-md border border-border-strong bg-subtle px-4 py-2 text-sm font-semibold text-foreground no-underline hover:border-accent"
              href={pairHref}
            >
              Pair evidence
            </a>
          ) : null}
        </nav>
      </header>

      <div className="mt-8 space-y-6">
        <section className="rounded-lg border border-border bg-panel p-5 md:p-6" aria-labelledby="tested-heading">
          <h2 id="tested-heading" className="mb-4 text-lg font-semibold text-foreground">
            What was tested?
          </h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <div>
              <p className="m-0 text-xs text-muted">Basket</p>
              <p className="mt-1 mb-0 font-medium text-foreground">{manifest.basket.join(' · ')}</p>
            </div>
            <div>
              <p className="m-0 text-xs text-muted">Relationship model</p>
              <p className="mt-1 mb-0 font-medium text-foreground">
                {humanizeIdentifier(manifest.relationship.component_id)}
              </p>
            </div>
            <div>
              <p className="m-0 text-xs text-muted">Policy</p>
              <p className="mt-1 mb-0 font-medium text-foreground">
                {humanizeIdentifier(manifest.policy.component_id)}
              </p>
            </div>
            <div>
              <p className="m-0 text-xs text-muted">Anchor</p>
              <p className="mt-1 mb-0 font-medium text-foreground">
                {manifest.analysis_anchor ?? 'None'}
              </p>
            </div>
            <div>
              <p className="m-0 text-xs text-muted">Universe</p>
              <p className="mt-1 mb-0 font-medium text-foreground">
                {humanizeIdentifier(manifest.universe_mode)}
              </p>
            </div>
            <div>
              <p className="m-0 text-xs text-muted">Data window</p>
              <p className="mt-1 mb-0 font-medium text-foreground">
                {formatResearchDate(manifest.data_window.start)} – {formatResearchDate(manifest.data_window.end)}
              </p>
            </div>
          </div>
        </section>

        <section className="rounded-lg border border-border bg-panel p-5 md:p-6" aria-labelledby="benchmark-heading">
          <h2 id="benchmark-heading" className="mb-2 text-lg font-semibold text-foreground">
            Benchmark outcome
          </h2>
          <p className="mt-0 mb-5 max-w-3xl text-sm leading-6 text-secondary">
            Zero is parity. Left of center is underperformance; right of center is outperformance. The research status above remains authoritative.
          </p>
          <ComparisonBars items={comparisons} />
        </section>

        <section className="rounded-lg border border-border bg-panel p-5 md:p-6" aria-labelledby="boundary-heading">
          <h2 id="boundary-heading" className="mb-3 text-lg font-semibold text-foreground">
            Research boundary
          </h2>
          <div className="mb-4 flex flex-wrap gap-2">
            <Badge tone="info">
              {experimentDataRoleLabel(result.data_role, result.final_oos_consumed)}
            </Badge>
          </div>
          {result.data_role === 'final_oos' && result.final_oos_consumed ? (
            <p className="mt-0 max-w-3xl text-sm leading-6 text-secondary">
              This final-OOS window has been consumed. Its result is inspectable evidence, but future adaptations must treat this window as development evidence rather than a fresh holdout.
            </p>
          ) : result.data_role === 'final_oos' ? (
            <p className="mt-0 max-w-3xl text-sm leading-6 text-secondary">
              This run is designated final OOS and has not been marked consumed.
            </p>
          ) : (
            <p className="mt-0 max-w-3xl text-sm leading-6 text-secondary">
              This run is {humanizeIdentifier(result.data_role).toLowerCase()} evidence and does not represent a fresh final-OOS result.
            </p>
          )}
          <div className="grid gap-4 text-sm sm:grid-cols-3">
            <div>
              <p className="m-0 text-xs text-muted">Family attempts</p>
              <p className="mt-1 mb-0 font-medium text-foreground">{data.family_attempt_count}</p>
            </div>
            <div>
              <p className="m-0 text-xs text-muted">Primary metric</p>
              <p className="mt-1 mb-0 font-medium text-foreground">
                {humanizeIdentifier(result.primary_metric)}
              </p>
            </div>
            <div>
              <p className="m-0 text-xs text-muted">Holdout execution</p>
              <p className="mt-1 mb-0 font-medium text-foreground">
                {commitment ? humanizeIdentifier(commitment.execution_status) : 'Not applicable'}
              </p>
            </div>
          </div>
        </section>

        <details className="rounded-lg border border-border bg-panel p-5 md:p-6">
          <summary className="cursor-pointer font-semibold text-foreground">
            Technical provenance
          </summary>
          <div className="mt-5 grid gap-5 sm:grid-cols-2">
            <ProvenanceValue label="Run ID" value={data.run_id} />
            <ProvenanceValue label="Research family" value={result.research_family_id} />
            <ProvenanceValue label="Parent run" value={result.parent_run_id ?? 'none'} />
            <ProvenanceValue label="Git commit" value={provenance.git_commit} />
            <ProvenanceValue
              label="Code snapshot"
              value={provenance.git_dirty ? 'dirty' : 'clean'}
            />
            <ProvenanceValue label="Manifest SHA-256" value={provenance.manifest_sha256} />
            <ProvenanceValue label="Code fingerprint" value={provenance.code_fingerprint} />
            {commitment ? <ProvenanceValue label="Holdout ID" value={commitment.holdout_id} /> : null}
            {provenance.data_fingerprints.map((dataset) => (
              <div key={dataset.dataset_id} className="min-w-0 sm:col-span-2">
                <ProvenanceValue label={`Dataset · ${dataset.dataset_id}`} value={dataset.fingerprint} />
              </div>
            ))}
          </div>
        </details>
      </div>
    </article>
  )
}
