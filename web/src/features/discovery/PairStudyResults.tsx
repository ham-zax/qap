import { useMemo, useState } from 'react'

import type {
  CapabilityMetadataV1,
  ProductPairStudyContextDto,
  ProductPairStudySeriesDto,
} from '../../api/types'
import { TimeSeriesChart } from '../../components/charts/TimeSeriesChart'
import type { TimeSeriesDefinition } from '../../components/charts/chartData'
import { Badge } from '../../components/ui/Badge'
import {
  formatDecimal,
  formatResearchTimestamp,
  formatSignedDecimal,
} from '../../lib/format'

type ChartView = 'ratio' | 'log' | 'normalized' | 'reference'

type ObservationStatus = 'valid' | 'insufficient_history' | 'insufficient_variance'

function formatNumber(value: number | undefined, signed = false): string {
  if (value === undefined) return 'Unavailable at this cutoff'
  const formatter = signed ? formatSignedDecimal : formatDecimal
  return formatter(String(value), 6).display
}

function observationTone(status: ObservationStatus) {
  return status === 'valid' ? 'positive' : 'warning'
}

function observationStatus(status: ObservationStatus): string {
  if (status === 'valid') return 'Valid'
  if (status === 'insufficient_history') return 'Insufficient history'
  return 'Insufficient variance'
}

function relationshipCapability(
  capabilities: readonly CapabilityMetadataV1[],
  componentId: string,
): CapabilityMetadataV1 | undefined {
  return capabilities.find(
    (item) => item.kind === 'relationship' && item.component_id === componentId,
  )
}

function PathCard({
  path,
  fallback,
}: {
  path: ProductPairStudyContextDto['data']['asset_a_path']
  fallback: string
}) {
  if (!path) {
    return (
      <div className="rounded-md border border-warning/40 bg-panel p-4">
        <strong className="text-foreground">{fallback}</strong>
        <p className="mt-1 mb-0 text-sm text-secondary">Data still needs setup.</p>
      </div>
    )
  }
  return (
    <div className="rounded-md border border-border bg-panel p-4">
      <div className="flex items-center justify-between gap-3">
        <strong className="text-foreground">
          {path.base_asset}/{path.quote_asset}
        </strong>
        <Badge tone="positive">Ready</Badge>
      </div>
      <p className="mt-2 mb-0 text-sm text-secondary">
        {path.venue_symbol} · {path.interval} · through{' '}
        {formatResearchTimestamp(path.coverage_end_exclusive)}
      </p>
    </div>
  )
}

function chartDefinition(
  view: ChartView,
  data: ProductPairStudySeriesDto,
): { title: string; description: string; series: TimeSeriesDefinition[] } | null {
  const orientation = data.question.orientation
  if (view === 'log') {
    return {
      title: `${orientation} log ratio`,
      description: 'Backend-produced natural log of the selected Pair Study ratio.',
      series: [{ name: orientation, unit: 'log ratio', points: data.log_ratio }],
    }
  }
  if (view === 'normalized') {
    return {
      title: `${orientation} normalized paths`,
      description:
        'Backend-produced selected asset paths rebased to one at the study window start.',
      series: [
        {
          name: data.question.asset_a,
          unit: 'normalized path',
          points: data.normalized_base,
        },
        {
          name: data.question.asset_b,
          unit: 'normalized path',
          points: data.normalized_quote,
        },
      ],
    }
  }
  if (view === 'reference') {
    if (!data.analysis_reference) return null
    return {
      title: `${data.question.asset_a} and ${data.question.asset_b} relative to ${data.analysis_reference.asset}`,
      description:
        'Descriptive backend reference series only. This does not add the reference asset to execution.',
      series: [
        {
          name: `${data.question.asset_a}/${data.analysis_reference.asset}`,
          unit: 'reference ratio',
          points: data.analysis_reference.base_to_reference,
        },
        {
          name: `${data.question.asset_b}/${data.analysis_reference.asset}`,
          unit: 'reference ratio',
          points: data.analysis_reference.quote_to_reference,
        },
      ],
    }
  }
  return {
    title: `${orientation} ratio`,
    description: 'Backend-produced ratio from synchronized same-venue USDT observations.',
    series: [{ name: orientation, unit: 'ratio', points: data.ratio }],
  }
}

export function PairStudyResults({
  context,
  series,
  capabilities,
  busy,
  bridgeAuthorityBusy,
  bridgeAuthorityError,
  onGrantBridgeAuthority,
  onVenueChange,
}: {
  context: ProductPairStudyContextDto
  series: ProductPairStudySeriesDto | null
  capabilities: readonly CapabilityMetadataV1[]
  busy: boolean
  bridgeAuthorityBusy: boolean
  bridgeAuthorityError: string | null
  onGrantBridgeAuthority: () => void
  onVenueChange: (venue: 'binance' | 'gate') => void
}) {
  const [chartView, setChartView] = useState<ChartView>('ratio')
  const relationship = context.relationship
  const logCapability = relationshipCapability(capabilities, 'rolling_log_ratio_zscore')
  const residualCapability = relationshipCapability(capabilities, 'residual_mean_reversion')
  const copulaCapability = relationshipCapability(capabilities, 'student_t_copula')
  const chart = useMemo(
    () => (series ? chartDefinition(chartView, series) : null),
    [chartView, series],
  )
  const timeframe =
    context.question.horizon === 'medium'
      ? 'Medium-term'
      : context.question.horizon === 'short'
        ? 'Short-term'
        : 'Longer-term'

  return (
    <section
      className="mt-6 rounded-lg border border-border-strong bg-subtle p-5 md:p-6"
      aria-labelledby="pair-study-result-heading"
    >
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="m-0 text-xs font-semibold uppercase tracking-[0.08em] text-accent">
            Pair Study
          </p>
          <h3
            id="pair-study-result-heading"
            className="mt-2 mb-1 text-2xl font-semibold text-foreground"
          >
            {context.question.orientation} · {timeframe}
          </h3>
          <p className="m-0 text-sm text-secondary">
            {context.question.venue === 'gate' ? 'Gate' : 'Binance'} ·{' '}
            {context.question.interval}
            {context.question.safe_cutoff
              ? ` · Data through ${formatResearchTimestamp(context.question.safe_cutoff)}`
              : ''}
          </p>
        </div>
        <Badge tone={context.data.status === 'ready' ? 'positive' : 'warning'}>
          {context.data.status === 'ready' ? 'Relationship ready' : 'Data setup needed'}
        </Badge>
      </div>

      {context.question.available_venues.length > 1 ? (
        <div className="mt-4 flex flex-wrap items-center gap-2 text-sm">
          <span className="font-medium text-secondary">Study venue</span>
          {context.question.available_venues.map((venue) => (
            <button
              key={venue}
              type="button"
              disabled={busy || venue === context.question.venue}
              className="min-h-10 rounded-md border border-border px-3 font-semibold text-accent disabled:cursor-default disabled:text-foreground disabled:opacity-70"
              onClick={() => onVenueChange(venue)}
            >
              {venue === 'gate' ? 'Gate' : 'Binance'}
            </button>
          ))}
        </div>
      ) : null}

      {context.analysis_lens ? (
        <section className="mt-5 rounded-md border border-border bg-panel p-4" aria-label="Analysis reference">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="m-0 text-sm font-semibold text-foreground">
                Relative to {context.analysis_lens.asset}
              </p>
              <p className="mt-1 mb-0 text-xs leading-5 text-muted">
                Descriptive analysis reference only; it does not change the economic pair,
                scanner scope, or execution authority.
              </p>
            </div>
            <Badge tone={context.analysis_lens.status === 'ready' ? 'positive' : 'warning'}>
              {context.analysis_lens.status === 'ready'
                ? 'Reference ready'
                : context.analysis_lens.status === 'needs_data'
                  ? 'Reference data needed'
                  : 'Reference unavailable'}
            </Badge>
          </div>
          {context.analysis_lens.reason ? (
            <p className="mt-3 mb-0 text-sm text-secondary">
              {context.analysis_lens.reason.message}
            </p>
          ) : null}
        </section>
      ) : null}

      <section className="mt-6" aria-labelledby="relationship-data-heading">
        <h4
          id="relationship-data-heading"
          className="m-0 text-base font-semibold text-foreground"
        >
          Relationship data
        </h4>
        <p className="mt-1 mb-0 text-sm leading-6 text-secondary">
          These are real same-venue {context.question.coordinate_asset} paths used as the
          analytical measurement coordinate. They do not imply a direct{' '}
          {context.question.orientation} exchange market.
        </p>
        <div className="mt-4 grid gap-3 md:grid-cols-2">
          <PathCard
            path={context.data.asset_a_path}
            fallback={`${context.question.asset_a}/${context.question.coordinate_asset}`}
          />
          <PathCard
            path={context.data.asset_b_path}
            fallback={`${context.question.asset_b}/${context.question.coordinate_asset}`}
          />
        </div>
        {context.data.reasons.length ? (
          <ul className="mt-4 space-y-2 pl-5 text-sm text-secondary">
            {context.data.reasons.map((reason) => (
              <li key={`${reason.code}:${reason.message}`}>{reason.message}</li>
            ))}
          </ul>
        ) : null}
      </section>

      {relationship ? (
        <>
          <section className="mt-7" aria-labelledby="relationship-values-heading">
            <h4
              id="relationship-values-heading"
              className="m-0 text-base font-semibold text-foreground"
            >
              Current relationship
            </h4>
            <dl className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
              <div className="rounded-md border border-border bg-panel p-4">
                <dt className="text-xs text-muted">Raw ratio</dt>
                <dd className="mt-2 mb-0 text-lg font-semibold text-foreground">
                  {formatNumber(relationship.raw_ratio_current)}
                </dd>
              </div>
              <div className="rounded-md border border-border bg-panel p-4">
                <dt className="text-xs text-muted">Log ratio</dt>
                <dd className="mt-2 mb-0 text-lg font-semibold text-foreground">
                  {formatNumber(relationship.log_ratio_current, true)}
                </dd>
              </div>
              <div className="rounded-md border border-border bg-panel p-4">
                <dt className="text-xs text-muted">{context.question.asset_a} normalized</dt>
                <dd className="mt-2 mb-0 text-lg font-semibold text-foreground">
                  {formatNumber(relationship.normalized_base_current)}
                </dd>
              </div>
              <div className="rounded-md border border-border bg-panel p-4">
                <dt className="text-xs text-muted">{context.question.asset_b} normalized</dt>
                <dd className="mt-2 mb-0 text-lg font-semibold text-foreground">
                  {formatNumber(relationship.normalized_quote_current)}
                </dd>
              </div>
            </dl>
          </section>

          <section
            className="mt-7 grid gap-4 xl:grid-cols-2"
            aria-label="Relationship models"
          >
            <article className="rounded-md border border-border bg-panel p-5">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h4 className="m-0 text-base font-semibold text-foreground">
                    Rolling log-ratio z-score
                  </h4>
                  <p className="mt-1 mb-0 text-xs text-muted">
                    {relationship.rolling_log_ratio.model_id} · v
                    {relationship.rolling_log_ratio.model_version}
                  </p>
                </div>
                <Badge tone={observationTone(relationship.rolling_log_ratio.status)}>
                  {observationStatus(relationship.rolling_log_ratio.status)}
                </Badge>
              </div>
              <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
                <div>
                  <dt className="text-xs text-muted">Current score</dt>
                  <dd className="mt-1 mb-0 font-semibold text-foreground">
                    {formatNumber(relationship.rolling_log_ratio.values.score, true)}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs text-muted">Window</dt>
                  <dd className="mt-1 mb-0 font-semibold text-foreground">
                    {relationship.rolling_log_ratio.window_observations} bars
                  </dd>
                </div>
                <div>
                  <dt className="text-xs text-muted">Required / coverage</dt>
                  <dd className="mt-1 mb-0 font-semibold text-foreground">
                    {relationship.rolling_log_ratio.required_observations} /{' '}
                    {relationship.rolling_log_ratio.coverage_observations}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs text-muted">Capability</dt>
                  <dd className="mt-1 mb-0 font-semibold text-foreground">
                    {logCapability?.capability ?? 'Backend evidence available'}
                  </dd>
                </div>
              </dl>
            </article>

            <article className="rounded-md border border-border bg-panel p-5">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h4 className="m-0 text-base font-semibold text-foreground">
                    Residual / OLS z-score
                  </h4>
                  <p className="mt-1 mb-0 text-xs text-muted">
                    {relationship.residual_ols.model_id} · v
                    {relationship.residual_ols.model_version} ·{' '}
                    {relationship.residual_ols.orientation}
                  </p>
                </div>
                <Badge tone={observationTone(relationship.residual_ols.status)}>
                  {observationStatus(relationship.residual_ols.status)}
                </Badge>
              </div>
              <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
                <div>
                  <dt className="text-xs text-muted">Alpha</dt>
                  <dd className="mt-1 mb-0 font-semibold text-foreground">
                    {formatNumber(relationship.residual_ols.values.alpha, true)}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs text-muted">Beta</dt>
                  <dd className="mt-1 mb-0 font-semibold text-foreground">
                    {formatNumber(relationship.residual_ols.values.beta, true)}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs text-muted">Residual z-score</dt>
                  <dd className="mt-1 mb-0 font-semibold text-foreground">
                    {formatNumber(relationship.residual_ols.values.score, true)}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs text-muted">Required / coverage</dt>
                  <dd className="mt-1 mb-0 font-semibold text-foreground">
                    {relationship.residual_ols.required_observations} /{' '}
                    {relationship.residual_ols.coverage_observations}
                  </dd>
                </div>
              </dl>
              <p className="mt-4 mb-0 text-xs leading-5 text-muted">
                {residualCapability?.capability ?? 'Backend evidence available'} relationship
                capability. This is rolling log-price OLS residual evidence, not a formal
                cointegration test.
              </p>
            </article>
          </section>

          {series ? (
            <section className="mt-7" aria-labelledby="pair-study-chart-heading">
              <div className="flex flex-wrap items-end justify-between gap-3">
                <div>
                  <h4
                    id="pair-study-chart-heading"
                    className="m-0 text-base font-semibold text-foreground"
                  >
                    Relationship chart
                  </h4>
                  <p className="mt-1 mb-0 text-sm text-secondary">
                    All plotted values come from the Pair Study series endpoint.
                  </p>
                </div>
                <div
                  className="flex flex-wrap gap-2"
                  role="group"
                  aria-label="Relationship chart view"
                >
                  {([
                    ['ratio', 'Ratio'],
                    ['log', 'Log ratio'],
                    ['normalized', 'Normalized paths'],
                    ...(series.analysis_reference
                      ? ([['reference', `Relative to ${series.analysis_reference.asset}`]] as const)
                      : []),
                  ] as const).map(([value, label]) => (
                    <button
                      key={value}
                      type="button"
                      aria-pressed={chartView === value}
                      className={`min-h-10 rounded-md border px-3 text-sm font-semibold ${
                        chartView === value
                          ? 'border-accent bg-accent text-canvas'
                          : 'border-border text-accent'
                      }`}
                      onClick={() => setChartView(value)}
                    >
                      {label}
                    </button>
                  ))}
                </div>
              </div>
              {chart ? (
                <div className="mt-4">
                  <TimeSeriesChart
                    title={chart.title}
                    description={chart.description}
                    series={chart.series}
                  />
                </div>
              ) : null}
            </section>
          ) : null}
        </>
      ) : null}

      <section
        className="mt-7 rounded-md border border-border bg-panel p-5"
        aria-labelledby="method-truth-heading"
      >
        <h4 id="method-truth-heading" className="m-0 text-base font-semibold text-foreground">
          What QAP can test
        </h4>
        <div className="mt-4 grid gap-3 md:grid-cols-3">
          <div>
            <Badge tone="positive">{logCapability?.capability ?? 'supported'}</Badge>
            <p className="mt-2 mb-0 text-sm text-secondary">
              Rolling log-ratio relationship evidence
            </p>
          </div>
          <div>
            <Badge tone="positive">{residualCapability?.capability ?? 'supported'}</Badge>
            <p className="mt-2 mb-0 text-sm text-secondary">
              Residual / OLS relationship evidence
            </p>
          </div>
          <div>
            <Badge tone="warning">{copulaCapability?.capability ?? 'unimplemented'}</Badge>
            <p className="mt-2 mb-0 text-sm text-secondary">
              Student-t Copula is known but not implemented. That is not evidence against
              this pair.
            </p>
          </div>
        </div>
      </section>

      <section
        className="mt-7 rounded-md border border-border bg-panel p-5"
        aria-labelledby="economic-replay-heading"
      >
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h4
              id="economic-replay-heading"
              className="m-0 text-base font-semibold text-foreground"
            >
              Economic replay is a separate question
            </h4>
            <p className="mt-2 mb-0 text-sm leading-6 text-secondary">
              Relationship readiness does not require a direct {context.question.orientation}{' '}
              market.
            </p>
          </div>
          <Badge
            tone={context.economic_expression.direct_status === 'ready' ? 'positive' : 'neutral'}
          >
            Direct market {context.economic_expression.direct_status}
          </Badge>
        </div>
        <p className="mt-4 mb-0 text-sm leading-6 text-secondary">
          {context.economic_expression.direct_status === 'ready'
            ? 'A real direct market is ready and remains QAP’s preferred economic expression for this pair.'
            : context.economic_expression.bridge_status === 'ready'
              ? `No ready direct ${context.question.orientation} market is required: QAP can replay the pair through the exact selected ${context.question.asset_a}/USDT and ${context.question.asset_b}/USDT Spot legs.`
              : context.economic_expression.bridge_status === 'needs_transient_authority'
                ? `The exact selected ${context.question.asset_a}/USDT and ${context.question.asset_b}/USDT Spot legs are ready, but economic replay is blocked until temporary USDT ownership is explicitly allowed for research replay.`
                : `No honest economic expression is ready yet. The ${context.question.orientation} relationship evidence above remains valid.`}
        </p>
        {context.economic_expression.direct_status !== 'ready' &&
        context.economic_expression.bridge_status === 'needs_transient_authority' ? (
          <div className="mt-4 rounded-md border border-warning/45 bg-subtle p-4">
            <p className="m-0 text-sm leading-6 text-secondary">
              This permission does not approve USDT as a portfolio target. It only allows QAP
              to hold real bridge residue temporarily while research-only two-leg Spot replay
              executes through the selected venue.
            </p>
            <button
              type="button"
              className="mt-3 min-h-11 rounded-md bg-accent px-4 font-semibold text-canvas disabled:opacity-50"
              disabled={bridgeAuthorityBusy || busy}
              onClick={onGrantBridgeAuthority}
            >
              {bridgeAuthorityBusy
                ? 'Saving permission…'
                : 'Allow temporary USDT in research replay'}
            </button>
            {bridgeAuthorityError ? (
              <p className="mt-3 mb-0 text-sm text-negative">{bridgeAuthorityError}</p>
            ) : null}
          </div>
        ) : context.economic_expression.direct_status !== 'ready' &&
          context.economic_expression.bridge_status === 'ready' ? (
          <p className="mt-2 mb-0 text-sm leading-6 text-secondary">
            Two-leg replay uses real exchange fills and the existing multi-asset bridge
            executor. QAP does not synthesize {context.question.orientation} candles or fills.
          </p>
        ) : null}
      </section>

      <details className="mt-7 rounded-md border border-border bg-panel p-4">
        <summary className="min-h-10 cursor-pointer py-2 font-semibold text-accent">
          Technical provenance
        </summary>
        <div className="mt-4 grid gap-4 text-xs text-muted lg:grid-cols-2">
          {[context.data.asset_a_path, context.data.asset_b_path]
            .filter((path) => path !== null)
            .map((path) => (
              <div key={path.dataset_id} className="min-w-0">
                <p className="m-0 font-semibold text-foreground">
                  {path.base_asset}/{path.quote_asset} · {path.venue_symbol}
                </p>
                <p className="mt-2 mb-0 break-all">Dataset: {path.dataset_id}</p>
                <p className="mt-1 mb-0 break-all">
                  Generation: {path.semantic_fingerprint}
                </p>
                <p className="mt-1 mb-0 break-all">Data: {path.relative_path}</p>
                <p className="mt-1 mb-0 break-all">
                  Provenance: {path.provenance_relative_path}
                </p>
              </div>
            ))}
        </div>
      </details>
    </section>
  )
}
