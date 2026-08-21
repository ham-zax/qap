import { useQuery } from '@tanstack/react-query'

import type { QapQueries } from '../../api/queries'
import type {
  ExperimentDetailDto,
  ProductPairStudyContextDto,
  ResearchRecipeRunLineageDto,
} from '../../api/types'
import { ExactNumber } from '../../components/ExactNumber'
import { Badge } from '../../components/ui/Badge'
import {
  formatPercent,
  formatRelativePercent,
  formatResearchTimestamp,
} from '../../lib/format'
import {
  experimentDataRoleLabel,
  humanizeIdentifier,
  researchStatusPresentation,
  researchVerdictHeadline,
} from '../experiments/presentation'

interface PairResearchCompletionProps {
  queries: QapQueries
  context: ProductPairStudyContextDto
  runIds: string[]
  operationId: string
  compilationSha256: string | null
}

function timeframeLabel(horizon: ProductPairStudyContextDto['question']['horizon']): string {
  if (horizon === 'short') return 'Short-term'
  if (horizon === 'medium') return 'Medium-term'
  return 'Longer-term'
}

function configValue(value: unknown): string {
  if (value === null) return 'None'
  if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
    return String(value)
  }
  return JSON.stringify(value) ?? String(value)
}

function conclusionCopy(result: ExperimentDetailDto['result']): string {
  const finalOos = result.data_role === 'final_oos' && result.final_oos_consumed
  const evidenceRole = finalOos ? 'final-OOS' : humanizeIdentifier(result.data_role).toLowerCase()

  if (result.data_role === 'final_oos' && !result.final_oos_consumed) {
    return `Completed ${result.status} evidence, but this artifact does not establish consumed final-OOS evidence.`
  }
  if (result.status === 'negative') {
    return `Completed negative ${evidenceRole} evidence. The run completed normally; negative describes the predeclared economic result, not an application failure.`
  }
  if (result.status === 'positive') {
    return finalOos
      ? 'Completed positive final-OOS evidence under the existing consumed-holdout contract.'
      : `Completed positive ${evidenceRole} evidence. This is not final-OOS confirmation.`
  }
  return finalOos
    ? 'Completed neutral final-OOS evidence under the existing consumed-holdout contract.'
    : `Completed neutral ${evidenceRole} evidence. This is not final-OOS confirmation.`
}

function executionIds(data: ExperimentDetailDto): string[] {
  const execution = data.manifest.execution
  if (execution.mode === 'direct') {
    return execution.execution_instrument_id ? [execution.execution_instrument_id] : []
  }
  return execution.execution_instrument_ids
}

function executionDescription(data: ExperimentDetailDto): string {
  const execution = data.manifest.execution
  if (execution.mode === 'direct') return 'Real direct-market replay'
  return `Real two-leg bridge through ${execution.bridge_asset ?? 'declared bridge'}`
}

function Metric({
  label,
  value,
  unit,
}: {
  label: string
  value: string | null
  unit?: string
}) {
  return (
    <div className="rounded-md border border-border bg-canvas/45 p-4">
      <p className="m-0 text-xs font-medium text-muted">{label}</p>
      <p className="mt-1 mb-0 text-lg font-semibold tabular-nums text-foreground">
        {value === null ? (
          'Not applicable'
        ) : (
          <>
            <ExactNumber value={value} />
            {unit ? <span className="ml-1 text-xs font-medium text-muted">{unit}</span> : null}
          </>
        )}
      </p>
    </div>
  )
}

function PercentMetric({
  label,
  value,
  relative = false,
}: {
  label: string
  value: string | null
  relative?: boolean
}) {
  if (value === null) return <Metric label={label} value={null} />
  const formatted = relative ? formatRelativePercent(value) : formatPercent(value)
  return (
    <div className="rounded-md border border-border bg-canvas/45 p-4">
      <p className="m-0 text-xs font-medium text-muted">{label}</p>
      <p
        className="mt-1 mb-0 text-lg font-semibold tabular-nums text-foreground"
        data-exact={formatted.exact}
      >
        {formatted.display}
      </p>
    </div>
  )
}

function TechnicalLineage({
  data,
  lineage,
}: {
  data: ExperimentDetailDto
  lineage: ResearchRecipeRunLineageDto | undefined
}) {
  return (
    <details className="mt-5 rounded-md border border-border bg-canvas/35 p-4">
      <summary className="min-h-10 cursor-pointer py-2 text-sm font-semibold text-accent">
        Exact evidence and technical provenance
      </summary>
      <div className="mt-4 grid gap-4 text-xs text-muted sm:grid-cols-2">
        <div className="min-w-0">
          <p className="m-0 font-semibold text-foreground">Run ID</p>
          <p className="mt-1 mb-0 break-all font-mono">{data.run_id}</p>
        </div>
        <div className="min-w-0">
          <p className="m-0 font-semibold text-foreground">Manifest SHA-256</p>
          <p className="mt-1 mb-0 break-all font-mono">{data.provenance.manifest_sha256}</p>
        </div>
        {data.provenance.data_fingerprints.map((dataset) => (
          <div key={dataset.dataset_id} className="min-w-0 sm:col-span-2">
            <p className="m-0 font-semibold text-foreground">Dataset · {dataset.dataset_id}</p>
            <p className="mt-1 mb-0 break-all font-mono">{dataset.fingerprint}</p>
          </div>
        ))}
      </div>

      {lineage?.matches.length ? (
        <div className="mt-5 border-t border-border pt-4">
          <p className="m-0 text-sm font-semibold text-foreground">Recipe / compilation lineage</p>
          <div className="mt-3 space-y-3 text-xs text-muted">
            {lineage.matches.map((match) => (
              <div
                key={match.compilation.compilation_sha256}
                className="rounded-md border border-border p-3"
              >
                <p className="m-0 break-all">
                  Recipe: <span className="font-mono">{match.recipe.recipe_sha256}</span>
                </p>
                <p className="mt-2 mb-0 break-all">
                  Compilation:{' '}
                  <span className="font-mono">{match.compilation.compilation_sha256}</span>
                </p>
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </details>
  )
}

function PairResearchRunResult({
  queries,
  runId,
  index,
  total,
  operationId,
}: {
  queries: QapQueries
  runId: string
  index: number
  total: number
  operationId: string
}) {
  const experiment = useQuery(queries.experiment(runId))
  const lineage = useQuery(queries.researchRecipeRunLineage(runId))

  if (experiment.isPending) {
    return (
      <section className="rounded-lg border border-border bg-panel p-5">
        <Badge tone="info">Loading completed run</Badge>
        <p className="mt-3 mb-0 text-sm text-secondary">Reading exact experiment evidence…</p>
      </section>
    )
  }

  if (experiment.isError) {
    return (
      <section className="rounded-lg border border-warning/45 bg-panel p-5">
        <Badge tone="warning">Inline evidence unavailable</Badge>
        <p className="mt-3 mb-0 text-sm leading-6 text-secondary">
          The operation returned this exact run, but its Experiment detail could not be loaded
          inline. The Pair Study evidence above remains valid independently.
        </p>
        <a className="mt-3 inline-flex min-h-11 items-center font-semibold text-accent" href={`/experiments/${encodeURIComponent(runId)}`}>
          Open exact Experiment detail
        </a>
      </section>
    )
  }

  const data = experiment.data
  const { manifest, result } = data
  const status = researchStatusPresentation(result.status)
  const strategy = result.roles.find((role) => role.role === 'strategy')
  const hodl = result.roles.find((role) => role.role === 'hodl')
  const primaryControlId = result.primary_incremental_benchmark
  const primaryControl = primaryControlId
    ? result.roles.find((role) => role.role === `control:${primaryControlId}`)
    : undefined
  const methodParameters = Object.entries(manifest.relationship.config ?? {}).filter(
    ([key]) =>
      key !== 'base_asset' && key !== 'quote_asset' && key !== 'evidence_instrument_ids',
  )
  const policyParameters = Object.entries(manifest.policy.config ?? {}).filter(
    ([key]) => key !== 'base_asset' && key !== 'quote_asset',
  )
  const ids = executionIds(data)
  const instruments = manifest.instruments.filter((instrument) =>
    ids.includes(instrument.instrument_id),
  )
  const verdict = researchVerdictHeadline(
    result.status,
    result.primary_incremental_benchmark,
    result.strategy_vs_primary_control,
  )
  const numeraire = manifest.execution.numeraire_asset

  return (
    <article className="rounded-lg border border-border-strong bg-panel p-5 md:p-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="m-0 text-xs font-semibold uppercase tracking-[0.08em] text-muted">
            Exact variant {index + 1} of {total}
          </p>
          <h4 className="mt-2 mb-1 text-xl font-semibold text-foreground">
            {humanizeIdentifier(manifest.relationship.component_id)}
          </h4>
          <p className="m-0 text-xs text-muted">{manifest.experiment_name}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Badge tone={status.tone}>{status.label}</Badge>
          <Badge tone="info">
            {experimentDataRoleLabel(result.data_role, result.final_oos_consumed)}
          </Badge>
        </div>
      </div>

      <section className="mt-6 border-t border-border pt-5" aria-label="Experiment declaration">
        <p className="m-0 text-xs font-semibold uppercase tracking-[0.08em] text-accent">
          Experiment
        </p>
        <div className="mt-3 grid gap-4 md:grid-cols-3">
          <div>
            <p className="m-0 text-xs text-muted">Relationship method</p>
            <p className="mt-1 mb-0 font-semibold text-foreground">
              {humanizeIdentifier(manifest.relationship.component_id)}
            </p>
          </div>
          <div>
            <p className="m-0 text-xs text-muted">Decision rule</p>
            <p className="mt-1 mb-0 font-semibold text-foreground">
              {humanizeIdentifier(manifest.policy.component_id)}
            </p>
          </div>
          <div>
            <p className="m-0 text-xs text-muted">Economic expression</p>
            <p className="mt-1 mb-0 font-semibold text-foreground">
              {executionDescription(data)}
            </p>
          </div>
        </div>
        {methodParameters.length ? (
          <div className="mt-4">
            <p className="m-0 text-xs font-semibold uppercase tracking-[0.08em] text-muted">
              Relationship parameters
            </p>
            <div className="mt-2 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              {methodParameters.map(([key, value]) => (
                <div key={key} className="rounded-md border border-border bg-canvas/35 p-3">
                  <p className="m-0 text-xs text-muted">{humanizeIdentifier(key)}</p>
                  <p className="mt-1 mb-0 text-sm font-semibold text-foreground">
                    {configValue(value)}
                  </p>
                </div>
              ))}
            </div>
          </div>
        ) : null}
        {policyParameters.length ? (
          <div className="mt-4">
            <p className="m-0 text-xs font-semibold uppercase tracking-[0.08em] text-muted">
              Decision parameters
            </p>
            <div className="mt-2 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              {policyParameters.map(([key, value]) => (
                <div key={key} className="rounded-md border border-border bg-canvas/35 p-3">
                  <p className="m-0 text-xs text-muted">{humanizeIdentifier(key)}</p>
                  <p className="mt-1 mb-0 text-sm font-semibold text-foreground">
                    {configValue(value)}
                  </p>
                </div>
              ))}
            </div>
          </div>
        ) : null}
        <p className="mt-4 mb-0 text-sm leading-6 text-secondary">
          {instruments.length
            ? `Exact execution instruments: ${instruments.map((instrument) => `${instrument.venue} / ${instrument.venue_symbol}`).join(' · ')}.`
            : 'No execution instrument list is available in this manifest.'}
        </p>
      </section>

      <section className="mt-6 border-t border-border pt-5" aria-label="Experiment economics">
        <p className="m-0 text-xs font-semibold uppercase tracking-[0.08em] text-accent">
          Economics
        </p>
        <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <Metric label="Strategy terminal value" value={strategy?.terminal_value ?? null} unit={numeraire} />
          <Metric label="Strict HODL terminal value" value={hodl?.terminal_value ?? null} unit={numeraire} />
          <Metric
            label={primaryControlId ? `${humanizeIdentifier(primaryControlId)} terminal value` : 'Primary control terminal value'}
            value={primaryControl?.terminal_value ?? null}
            unit={numeraire}
          />
          <Metric label="Strategy fills" value={strategy ? String(strategy.fill_count) : null} />
          <PercentMetric label="Strategy vs HODL" value={result.strategy_vs_hodl} relative />
          <PercentMetric
            label="Strategy vs primary control"
            value={result.strategy_vs_primary_control ?? null}
            relative
          />
          <Metric label="Fees" value={strategy?.fees_value ?? null} unit={numeraire} />
          <Metric label="Slippage" value={strategy?.slippage_value ?? null} unit={numeraire} />
          <Metric label="Turnover" value={strategy?.turnover_value ?? null} unit={numeraire} />
          <PercentMetric
            label="Maximum relative drawdown vs HODL"
            value={result.maximum_relative_drawdown_vs_hodl}
          />
          <PercentMetric label="Predeclared success threshold" value={result.success_threshold} />
        </div>
      </section>

      <section className="mt-6 border-t border-border pt-5" aria-label="Experiment conclusion">
        <p className="m-0 text-xs font-semibold uppercase tracking-[0.08em] text-accent">
          Conclusion
        </p>
        <div className="mt-3 rounded-md border border-border bg-subtle p-4">
          <p className="m-0 text-lg font-semibold text-foreground">{verdict}</p>
          <p className="mt-2 mb-0 text-sm leading-6 text-secondary">
            {conclusionCopy(result)}
          </p>
        </div>
      </section>

      <nav className="mt-5 flex flex-wrap gap-3" aria-label={`Evidence for variant ${index + 1}`}>
        <a className="inline-flex min-h-11 items-center font-semibold text-accent" href={`/experiments/${encodeURIComponent(runId)}`}>
          Experiment detail
        </a>
        <a className="inline-flex min-h-11 items-center font-semibold text-accent" href={`/operations/${encodeURIComponent(operationId)}`}>
          Activity
        </a>
      </nav>

      {lineage.isError ? (
        <p className="mt-4 mb-0 text-xs text-warning">
          Recipe lineage could not be loaded inline. The exact Experiment detail remains available.
        </p>
      ) : null}
      <TechnicalLineage data={data} lineage={lineage.data} />
    </article>
  )
}

export function PairResearchCompletion({
  queries,
  context,
  runIds,
  operationId,
  compilationSha256,
}: PairResearchCompletionProps) {
  return (
    <section className="mt-8 rounded-lg border border-border-strong bg-subtle p-5 md:p-6" aria-labelledby="pair-research-completion-heading">
      <p className="m-0 text-xs font-semibold uppercase tracking-[0.08em] text-accent">
        Research completion
      </p>
      <h3 id="pair-research-completion-heading" className="mt-2 mb-2 text-2xl font-semibold text-foreground">
        {context.question.orientation} · {timeframeLabel(context.question.horizon)}
      </h3>
      <p className="m-0 text-sm leading-6 text-secondary">
        {context.question.venue === 'gate' ? 'Gate' : 'Binance'} · {context.question.interval}
        {context.question.safe_cutoff
          ? ` · Data through ${formatResearchTimestamp(context.question.safe_cutoff)}`
          : ''}
      </p>

      <div className="mt-5 grid gap-4 md:grid-cols-2">
        <div className="rounded-md border border-border bg-panel p-4">
          <p className="m-0 text-xs font-semibold uppercase tracking-[0.08em] text-muted">
            Question
          </p>
          <p className="mt-2 mb-0 font-semibold text-foreground">
            What is happening between {context.question.asset_a} and {context.question.asset_b}?
          </p>
          <p className="mt-2 mb-0 text-sm leading-6 text-secondary">
            Orientation {context.question.orientation}; {timeframeLabel(context.question.horizon).toLowerCase()} evidence on the selected {context.question.venue} venue.
          </p>
        </div>
        <div className="rounded-md border border-border bg-panel p-4">
          <p className="m-0 text-xs font-semibold uppercase tracking-[0.08em] text-muted">
            Relationship
          </p>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <Badge tone={context.data.status === 'ready' ? 'positive' : 'warning'}>
              {context.data.status === 'ready' ? 'Pair Study ready' : 'Pair Study needs setup'}
            </Badge>
          </div>
          <p className="mt-2 mb-0 text-sm leading-6 text-secondary">
            The exact Pair Study evidence above remains the relationship layer for these runs.
            Economic results below do not replace or recompute it.
          </p>
        </div>
      </div>

      <div className="mt-6 flex flex-wrap items-center justify-between gap-3 border-t border-border pt-5">
        <div>
          <p className="m-0 font-semibold text-foreground">
            {runIds.length} completed predeclared {runIds.length === 1 ? 'variant' : 'variants'}
          </p>
          <p className="mt-1 mb-0 text-sm text-secondary">
            Each result is shown independently. QAP does not select a winner between sibling development variants here.
          </p>
        </div>
        <a className="inline-flex min-h-11 items-center font-semibold text-accent" href={`/operations/${encodeURIComponent(operationId)}`}>
          Open Activity
        </a>
      </div>

      <div className="mt-5 space-y-5">
        {runIds.map((runId, index) => (
          <PairResearchRunResult
            key={runId}
            queries={queries}
            runId={runId}
            index={index}
            total={runIds.length}
            operationId={operationId}
          />
        ))}
      </div>

      <section className="mt-6 rounded-lg border border-border bg-panel p-5" aria-labelledby="pair-research-limitations-heading">
        <h4 id="pair-research-limitations-heading" className="m-0 text-lg font-semibold text-foreground">
          Limitations
        </h4>
        <ul className="mt-3 mb-0 space-y-2 pl-5 text-sm leading-6 text-secondary">
          <li>Development replay is not final-OOS confirmation unless an exact run artifact is explicitly Final OOS and consumed.</li>
          <li>Historical research does not grant live-trading authority or establish current market capacity/tradability.</li>
          <li>Residual / OLS evidence is not a formal cointegration test, and no Student-t Copula evidence is claimed here.</li>
          <li>Terminal wealth differences do not by themselves establish causal attribution to one asset or relationship.</li>
        </ul>
      </section>

      <details className="mt-5 rounded-md border border-border bg-panel p-4 text-xs text-muted">
        <summary className="min-h-10 cursor-pointer py-2 font-semibold text-accent">
          Completion lineage
        </summary>
        <p className="mt-3 mb-0 break-all">Operation: {operationId}</p>
        <p className="mt-2 mb-0 break-all">
          Compilation: {compilationSha256 ?? 'Unavailable from operation result'}
        </p>
      </details>
    </section>
  )
}
