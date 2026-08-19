import type {
  BasketDetailDto,
  ExperimentDetailDto,
  PortfolioPerformanceDto,
  PortfolioSnapshotDto,
} from '../../api/types'
import { Badge } from '../../components/ui/Badge'
import { CompositionBars } from '../../components/visuals/CompositionBars'
import {
  formatDecimal,
  formatDuration,
  formatPercent,
  formatRelativePercent,
  formatResearchTimestamp,
} from '../../lib/format'
import { humanizeIdentifier } from '../experiments/presentation'
import { LineageTrail } from '../lineage/LineageTrail'
import { InventoryVsHodlTable } from '../portfolio/InventoryVsHodlTable'
import { BasketGraph } from './BasketGraph'

interface BasketDetailProps {
  basket: BasketDetailDto
  experiment: ExperimentDetailDto | null
  portfolio: PortfolioSnapshotDto | null
  performance?: PortfolioPerformanceDto | null
}

function shortId(value: string) {
  return value.length <= 18 ? value : `${value.slice(0, 10)}…${value.slice(-6)}`
}

function gatePresentation(
  artifactStatus: string,
  economicGateStatus: string | null | undefined,
): {
  label: string
  tone: 'positive' | 'info' | 'negative'
  explanation: string
} {
  if (artifactStatus !== 'valid') {
    return {
      label: 'Research artifact invalid',
      tone: 'negative',
      explanation:
        'QAP could not publish a valid portfolio research artifact. The recorded error remains authoritative.',
    }
  }
  if (economicGateStatus === 'basket_development_survivor') {
    return {
      label: 'Passed basket development gates',
      tone: 'positive',
      explanation:
        'QAP completed the portfolio replay and the persisted basket development gate classified it as a survivor.',
    }
  }
  if (economicGateStatus === 'basket_development_rejected') {
    return {
      label: 'Did not pass basket development gates',
      tone: 'info',
      explanation:
        'QAP completed the portfolio replay, but the persisted basket development gate rejected it. This is completed negative research, not an application error.',
    }
  }
  return {
    label: 'Portfolio research result',
    tone: 'info',
    explanation:
      'QAP published portfolio research evidence. The exact persisted gate status is available in the audit disclosure below.',
  }
}

function roleLabel(role: string) {
  if (role === 'strategy') return 'Portfolio strategy'
  if (role === 'hodl') return 'Buy-and-hold benchmark'
  return role.replaceAll('_', ' ')
}

function relationshipLabel(edge: BasketDetailDto['selected_edges'][number]) {
  if (edge.manual_pinned) return 'Manual research relationship'
  if (edge.deep_replay_status === 'setup_failed') return 'Indirect research relationship'
  if (edge.automatic_neighbor_selected) return 'Scanner-neighbor relationship'
  return 'Selected research relationship'
}

function sourcePresentation(summary: BasketDetailDto['summary']) {
  const claim = summary.source_claim
  const label = claim?.label ?? 'Versioned Research Claim'
  if (claim?.kind === 'current_approved_retrospective') {
    return {
      label,
      tone: 'positive' as const,
      boundary: summary.source_as_of
        ? `Data through ${formatResearchTimestamp(summary.source_as_of)}`
        : 'Data boundary unavailable',
      explanation:
        'This portfolio uses the frozen data boundary of Current Approved Market Research. It is not labeled as a historical point-in-time universe claim.',
    }
  }
  if (claim?.kind === 'historical_pit') {
    return {
      label,
      tone: 'warning' as const,
      boundary: summary.source_as_of
        ? `Historical universe as of ${formatResearchTimestamp(summary.source_as_of)}`
        : 'Historical boundary unavailable',
      explanation:
        'This portfolio preserves the strict Historical Point-in-Time Research source as an Advanced research path.',
    }
  }
  return {
    label,
    tone: 'neutral' as const,
    boundary: summary.source_as_of
      ? `Research boundary ${formatResearchTimestamp(summary.source_as_of)}`
      : 'Research boundary unavailable',
    explanation: 'This portfolio preserves the backend-declared versioned research claim.',
  }
}

function EconomicMetric({
  label,
  value,
  detail,
}: {
  label: string
  value: string
  detail: string
}) {
  return (
    <div className="rounded-md border border-border bg-canvas/40 p-4">
      <p className="m-0 text-xs font-semibold text-muted">{label}</p>
      <p className="mt-1 mb-0 text-lg font-semibold tabular-nums text-foreground">{value}</p>
      <p className="mt-2 mb-0 text-xs leading-5 text-secondary">{detail}</p>
    </div>
  )
}

export function BasketDetail({ basket, experiment, portfolio, performance }: BasketDetailProps) {
  const summary = basket.summary
  const source = sourcePresentation(summary)
  const graphAudits = (portfolio?.rebalance_audit ?? []).filter((audit) =>
    audit.evidence_ids.some((id) => id.startsWith('basket-')),
  )
  const lastGraphAudit = graphAudits.at(-1) ?? null
  const bridgeHoldings =
    portfolio?.terminal.holdings.filter(
      (holding) => !summary.economic_assets.includes(holding.asset),
    ) ?? []
  const graphEdges = basket.selected_edges.map((edge) => ({
    pair: edge.pair_id,
    label: relationshipLabel(edge),
  }))
  const verdict = gatePresentation(summary.artifact_status, summary.economic_gate_status)
  const result = experiment?.result
  const primary = result?.strategy_vs_primary_control
    ? formatRelativePercent(result.strategy_vs_primary_control)
    : null
  const hodl = result ? formatRelativePercent(result.strategy_vs_hodl) : null
  const matchedContribution = result?.strategy_vs_matched_contribution
    ? formatRelativePercent(result.strategy_vs_matched_contribution)
    : null
  const primaryLabel = humanizeIdentifier(
    result?.primary_incremental_benchmark ?? 'primary control',
  )
  const drawdown = performance
    ? formatPercent(performance.maximum_relative_drawdown_vs_hodl)
    : null
  const fees = portfolio ? formatDecimal(portfolio.strategy_costs.fees_value) : null
  const slippage = portfolio ? formatDecimal(portfolio.strategy_costs.slippage_value) : null
  const turnover = portfolio ? formatDecimal(portfolio.strategy_costs.turnover_value) : null
  const terminalMaxWeight = portfolio
    ? formatPercent(portfolio.concentration.terminal_max_weight)
    : null
  const terminalHhi = portfolio
    ? formatDecimal(portfolio.concentration.terminal_herfindahl, 3)
    : null
  const valueUnit = experiment?.manifest.execution?.numeraire_asset ?? 'value units'

  return (
    <section className="min-w-0">
      <header className="mb-8 max-w-4xl">
        <p className="mb-2 text-xs font-semibold uppercase tracking-[0.1em] text-accent">
          Portfolio research result
        </p>
        <h1 className="mb-3 text-3xl font-bold tracking-tight text-foreground md:text-4xl">
          {summary.economic_assets.join(' · ') || `Portfolio ${shortId(summary.basket_id)}`}
        </h1>
        <p className="m-0 text-sm leading-6 text-secondary md:text-base">
          Read the persisted economic verdict first, compare the authoritative QAP
          benchmark roles, then inspect the graph decision and execution evidence.
        </p>
      </header>

      <LineageTrail
        items={[
          ...(summary.source_scan_id
            ? [
                {
                  label: source.label,
                  value: summary.source_scan_id,
                  href: `/scanner/${summary.source_scan_id}`,
                },
              ]
            : []),
          { label: 'portfolio research', value: summary.basket_id },
          ...(summary.qap_run_id
            ? [
                {
                  label: 'QAP result',
                  value: summary.qap_run_id,
                  href: `/experiments/${summary.qap_run_id}`,
                },
              ]
            : []),
        ]}
      />

      <article className="mt-6 rounded-lg border border-border bg-panel p-5">
        <div className="flex flex-wrap gap-2">
          <Badge tone={verdict.tone}>{verdict.label}</Badge>
          <Badge tone={source.tone}>{source.label}</Badge>
          {summary.forensic ? <Badge tone="warning">Forensic research</Badge> : null}
        </div>
        <h2 className="mt-4 mb-2 text-xl font-semibold text-foreground">
          Research verdict
        </h2>
        <p className="m-0 max-w-4xl text-sm leading-6 text-secondary">
          {verdict.explanation}
        </p>
        <p className="mt-3 mb-0 max-w-4xl text-sm leading-6 text-secondary">
          <strong className="text-foreground">{source.boundary}.</strong>{' '}
          {source.explanation}
        </p>
        {summary.error ? (
          <p className="mt-3 mb-0 text-sm text-negative">{summary.error.message}</p>
        ) : null}
        <p className="mt-4 mb-0 text-xs leading-5 text-muted">
          Research result only — QAP does not place or authorize live trades.
        </p>
      </article>

      <section className="mt-8" aria-labelledby="benchmark-heading">
        <div className="max-w-3xl">
          <p className="m-0 text-xs font-semibold uppercase tracking-[0.08em] text-muted">
            Authoritative QAP comparison
          </p>
          <h2 id="benchmark-heading" className="mt-2 text-xl font-semibold text-foreground">
            Objective and economic evidence
          </h2>
          <p className="text-sm leading-6 text-secondary">
            QAP keeps the run's declared matched HODL/control frame. These comparisons,
            costs, allocations, and concentration diagnostics come from persisted QAP
            artifacts; the browser does not replace them with a generic return score.
          </p>
        </div>
        {experiment && portfolio ? (
          <>
            <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
              <EconomicMetric
                label={`Strategy vs ${primaryLabel}`}
                value={primary?.display ?? 'Not applicable'}
                detail="Declared primary incremental control"
              />
              <EconomicMetric
                label="Strategy vs strict inventory HODL"
                value={hodl?.display ?? 'Unavailable'}
                detail="Persisted passive inventory counterfactual"
              />
              {matchedContribution ? (
                <EconomicMetric
                  label="Strategy vs matched-contribution HODL"
                  value={matchedContribution.display}
                  detail="Persisted matched-contribution static HODL comparison"
                />
              ) : null}
              <EconomicMetric
                label="Maximum relative drawdown"
                value={drawdown?.display ?? 'Unavailable'}
                detail="Relative to HODL"
              />
              <EconomicMetric
                label="Execution"
                value={`${portfolio.strategy_costs.fill_count} fills`}
                detail={`Fees ${fees?.display ?? '—'} · slippage ${slippage?.display ?? '—'} ${valueUnit}`}
              />
              {performance ? (
                <EconomicMetric
                  label="Time below HODL"
                  value={formatDuration(performance.time_below_hodl_seconds)}
                  detail="Elapsed admitted evaluation time"
                />
              ) : null}
              {performance?.time_below_primary_control_seconds !== null &&
              performance?.time_below_primary_control_seconds !== undefined ? (
                <EconomicMetric
                  label="Time below primary control"
                  value={formatDuration(performance.time_below_primary_control_seconds)}
                  detail={`Elapsed time below ${primaryLabel}`}
                />
              ) : null}
              <EconomicMetric
                label="Turnover"
                value={`${turnover?.display ?? '—'} ${valueUnit}`}
                detail="Persisted modeled strategy turnover"
              />
              <EconomicMetric
                label="Terminal concentration"
                value={`${terminalMaxWeight?.display ?? '—'} max weight`}
                detail={`HHI ${terminalHhi?.display ?? '—'}`}
              />
            </div>

            <div className="mt-5 grid gap-4 lg:grid-cols-2">
              <article className="rounded-lg border border-border bg-panel p-4">
                <h3 className="mt-0 mb-3 text-sm font-semibold text-foreground">
                  Starting allocation
                </h3>
                <CompositionBars
                  label="Starting allocation"
                  items={portfolio.starting.holdings.map((holding) => ({
                    asset: holding.asset,
                    weight: holding.weight,
                  }))}
                />
              </article>
              <article className="rounded-lg border border-border bg-panel p-4">
                <h3 className="mt-0 mb-3 text-sm font-semibold text-foreground">
                  Terminal allocation
                </h3>
                <CompositionBars
                  label="Terminal allocation"
                  items={portfolio.terminal.holdings.map((holding) => ({
                    asset: holding.asset,
                    weight: holding.weight,
                  }))}
                />
              </article>
            </div>

            <details className="mt-5 rounded-lg border border-border bg-panel p-4">
              <summary className="cursor-pointer font-semibold text-foreground">
                Compare exact QAP benchmark roles
              </summary>
              <div className="mt-4 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                {experiment.result.roles.map((role) => (
                  <article key={role.role} className="rounded-md border border-border p-4">
                    <p className="m-0 text-sm font-semibold text-foreground">
                      {roleLabel(role.role)}
                    </p>
                    <p className="mt-1 mb-0 font-mono text-[11px] text-muted">{role.role}</p>
                    <p className="mt-3 mb-0 text-lg font-semibold tabular-nums text-foreground">
                      {role.terminal_value}
                    </p>
                    <p className="mt-1 mb-0 text-xs leading-5 text-secondary">
                      fees {role.fees_value} · slippage {role.slippage_value} · fills{' '}
                      {role.fill_count}
                    </p>
                  </article>
                ))}
              </div>
            </details>

            <div className="mt-5">
              <InventoryVsHodlTable snapshot={portfolio} valueUnit={valueUnit} />
            </div>
          </>
        ) : (
          <p className="text-secondary">
            The authoritative QAP experiment or portfolio projection is unavailable.
          </p>
        )}
      </section>

      <section className="mt-8" aria-labelledby="decision-heading">
        <h2 id="decision-heading" className="text-xl font-semibold text-foreground">
          Why QAP chose this portfolio state
        </h2>
        <div className="mt-4 grid gap-6 xl:grid-cols-[minmax(20rem,0.9fr)_minmax(0,1.1fr)]">
          <article className="rounded-lg border border-border bg-panel p-5">
            <p className="m-0 text-xs font-semibold uppercase tracking-[0.08em] text-muted">
              Authoritative graph decision
            </p>
            {lastGraphAudit ? (
              <>
                <p className="mt-3 text-sm leading-6 text-secondary">
                  {lastGraphAudit.reason}
                </p>
                <h3 className="mt-5 text-sm font-semibold text-foreground">
                  Persisted target weights
                </h3>
                <div className="mt-3 grid gap-3 sm:grid-cols-2">
                  {Object.entries(lastGraphAudit.target_weights ?? {}).map(([asset, weight]) => (
                    <div key={asset} className="rounded-md border border-border p-3">
                      <p className="m-0 text-xs text-muted">{asset}</p>
                      <p className="mt-1 mb-0 font-semibold tabular-nums text-foreground">
                        {weight}
                      </p>
                    </div>
                  ))}
                </div>
                <p className="mt-4 mb-0 text-xs leading-5 text-muted">
                  Resolver opinion and targets are shown only after ordinary QAP replay.
                  React does not recompute them.
                </p>
              </>
            ) : (
              <p className="text-sm text-secondary">
                No graph decision audit is available for this terminal run.
              </p>
            )}
          </article>

          <article className="rounded-lg border border-border bg-panel p-5">
            <p className="m-0 text-xs font-semibold uppercase tracking-[0.08em] text-muted">
              Relationships used
            </p>
            <BasketGraph assets={[...summary.economic_assets]} edges={graphEdges} />
            <div className="mt-4 space-y-3">
              {basket.selected_edges.map((edge) => (
                <details key={edge.candidate_id} className="rounded-md border border-border p-3">
                  <summary className="cursor-pointer text-sm font-semibold text-foreground">
                    {edge.pair_id} · {relationshipLabel(edge)}
                  </summary>
                  <p className="mt-3 mb-0 text-xs leading-5 text-secondary">
                    Exact rule: <span className="font-mono">{edge.model_family}</span> ·{' '}
                    <span className="font-mono">{edge.template_id}</span> · orientation{' '}
                    <span className="font-mono">{edge.candidate_orientation}</span>
                    {edge.manual_pinned ? ' · manual pin' : ''}
                    {edge.deep_replay_status === 'setup_failed'
                      ? ' · indirect/scout-only'
                      : ''}
                  </p>
                  <a
                    className="mt-2 inline-flex text-xs font-semibold text-accent"
                    href={`/candidate/${summary.source_scan_id}/${edge.candidate_id}`}
                  >
                    Open relationship evidence
                  </a>
                </details>
              ))}
            </div>
          </article>
        </div>
      </section>

      {bridgeHoldings.length ? (
        <section
          className="mt-8 rounded-lg border border-border bg-panel p-5"
          aria-labelledby="bridge-heading"
        >
          <h2 id="bridge-heading" className="mt-0 text-lg font-semibold text-foreground">
            Execution-only bridge residue
          </h2>
          <p className="text-sm text-secondary">
            Bridge holdings remain separate from the declared economic portfolio.
          </p>
          {bridgeHoldings.map((holding) => (
            <p key={holding.asset} className="mb-0 text-sm text-secondary">
              <strong className="text-foreground">{holding.asset}</strong> · quantity{' '}
              {holding.quantity} · value {holding.value}
            </p>
          ))}
        </section>
      ) : null}

      <details className="mt-8 rounded-lg border border-border bg-panel p-5">
        <summary className="cursor-pointer font-semibold text-foreground">
          Exact research and execution audit
        </summary>
        <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2 lg:grid-cols-3">
          <div>
            <dt className="text-xs text-muted">Source research claim</dt>
            <dd className="m-0 mt-1 text-secondary">{source.label}</dd>
          </div>
          <div>
            <dt className="text-xs text-muted">Source scan</dt>
            <dd className="m-0 mt-1 break-all font-mono text-xs text-secondary">
              {summary.source_scan_id ?? 'unknown'}
            </dd>
          </div>
          <div>
            <dt className="text-xs text-muted">Scope</dt>
            <dd className="m-0 mt-1 text-secondary">
              {summary.venue ?? '—'} · {summary.horizon ?? '—'} ·{' '}
              {summary.decision_resolution ?? '—'}
            </dd>
          </div>
          <div>
            <dt className="text-xs text-muted">Exact economic gate</dt>
            <dd className="m-0 mt-1 font-mono text-xs text-secondary">
              {summary.economic_gate_status ?? 'none'}
            </dd>
          </div>
          <div>
            <dt className="text-xs text-muted">Attempt status</dt>
            <dd className="m-0 mt-1 font-mono text-xs text-secondary">
              {summary.attempt_status ?? 'none'}
            </dd>
          </div>
          <div>
            <dt className="text-xs text-muted">QAP run</dt>
            <dd className="m-0 mt-1 break-all font-mono text-xs text-secondary">
              {summary.qap_run_id ?? 'none'}
            </dd>
          </div>
          <div>
            <dt className="text-xs text-muted">Basket ID</dt>
            <dd className="m-0 mt-1 break-all font-mono text-xs text-secondary">
              {summary.basket_id}
            </dd>
          </div>
          <div>
            <dt className="text-xs text-muted">Source scanner protocol</dt>
            <dd className="m-0 mt-1 break-all font-mono text-xs text-secondary">
              {summary.source_scanner_protocol_id ?? 'unknown'}
            </dd>
          </div>
          <div>
            <dt className="text-xs text-muted">Basket protocol</dt>
            <dd className="m-0 mt-1 break-all font-mono text-xs text-secondary">
              {summary.basket_protocol_id ?? 'unknown'}
            </dd>
          </div>
          <div>
            <dt className="text-xs text-muted">Asset-momentum lineage</dt>
            <dd className="m-0 mt-1 text-secondary">
              {summary.source_claim?.kind === 'current_approved_retrospective'
                ? 'Not used for Product basket creation'
                : (summary.source_momentum_scan_id ?? 'none')}
            </dd>
          </div>
        </dl>
        <details className="mt-5 rounded-md border border-border bg-canvas/35 p-4">
          <summary className="cursor-pointer text-sm font-semibold text-foreground">
            Protocol and claim identities
          </summary>
          <dl className="mt-4 grid gap-3 text-xs sm:grid-cols-2">
            <div>
              <dt className="text-muted">Source scanner protocol identity</dt>
              <dd className="m-0 mt-1 break-all font-mono text-secondary">
                {summary.source_scanner_protocol_identity ?? 'unknown'}
              </dd>
            </div>
            <div>
              <dt className="text-muted">Basket protocol identity</dt>
              <dd className="m-0 mt-1 break-all font-mono text-secondary">
                {summary.basket_protocol_identity ?? 'unknown'}
              </dd>
            </div>
            <div>
              <dt className="text-muted">Research claim identity</dt>
              <dd className="m-0 mt-1 break-all font-mono text-secondary">
                {summary.source_claim?.claim_identity ?? 'none'}
              </dd>
            </div>
            <div>
              <dt className="text-muted">Research scope identity</dt>
              <dd className="m-0 mt-1 break-all font-mono text-secondary">
                {summary.source_claim?.scope_identity ?? 'none'}
              </dd>
            </div>
          </dl>
        </details>
        {basket.execution_generations?.length ? (
          <details className="mt-3 rounded-md border border-border bg-canvas/35 p-4">
            <summary className="cursor-pointer text-sm font-semibold text-foreground">
              Frozen Product execution generations
            </summary>
            <p className="mt-3 text-xs leading-5 text-muted">
              Exact physical paths and fingerprints are audit lineage only. They are not
              portfolio-selection controls.
            </p>
            <div className="mt-3 space-y-3">
              {basket.execution_generations.map((generation) => (
                <div key={generation.asset_id} className="rounded-md border border-border p-3">
                  <p className="m-0 text-xs font-semibold text-foreground">
                    {generation.asset_id} · {generation.dataset_id}
                  </p>
                  <p className="mt-2 mb-0 break-all font-mono text-[11px] text-secondary">
                    {generation.relative_path}
                  </p>
                  <p className="mt-1 mb-0 break-all font-mono text-[11px] text-muted">
                    {generation.source_artifact_fingerprint}
                  </p>
                </div>
              ))}
            </div>
          </details>
        ) : null}
        {lastGraphAudit ? (
          <div className="mt-5 border-t border-border pt-4">
            <p className="m-0 text-xs font-semibold uppercase tracking-[0.08em] text-muted">
              Decision evidence IDs
            </p>
            <ul className="mt-2 space-y-1 pl-5 text-xs text-secondary">
              {lastGraphAudit.evidence_ids
                .filter((id) => id.startsWith('basket-'))
                .map((id) => (
                  <li key={id} className="break-all font-mono">
                    {id}
                  </li>
                ))}
            </ul>
          </div>
        ) : null}
      </details>

      {summary.qap_run_id ? (
        <nav className="mt-8 flex flex-wrap gap-3" aria-label="Portfolio evidence links">
          <a
            className="inline-flex min-h-11 items-center rounded-md bg-accent px-4 font-semibold text-canvas"
            href={`/experiments/${summary.qap_run_id}`}
          >
            Full research result
          </a>
          <a
            className="inline-flex min-h-11 items-center rounded-md border border-border px-4 font-semibold text-accent"
            href={`/portfolio/${summary.qap_run_id}`}
          >
            Portfolio economics
          </a>
        </nav>
      ) : null}
    </section>
  )
}
