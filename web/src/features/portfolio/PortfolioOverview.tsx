import type {
  ExperimentDetailDto,
  PortfolioPerformanceDto,
  PortfolioSnapshotDto,
} from '../../api/types'
import { ExactNumber } from '../../components/ExactNumber'
import { TableScroll } from '../../components/TableScroll'
import { Badge } from '../../components/ui/Badge'
import { CompositionBars } from '../../components/visuals/CompositionBars'
import {
  formatDecimal,
  formatDuration,
  formatPercent,
  formatRelativePercent,
  formatResearchDate,
} from '../../lib/format'
import {
  experimentDataRoleLabel,
  humanizeIdentifier,
  researchStatusPresentation,
  researchVerdictHeadline,
} from '../experiments/presentation'
import { AllocationHistoryChart } from './AllocationHistoryChart'
import { BenchmarkLadder } from './BenchmarkLadder'
import { BenchmarkRoleTable } from './BenchmarkRoleTable'
import { ExternalFlowContext } from './ExternalFlowContext'
import { InventoryVsHodlTable } from './InventoryVsHodlTable'
import { LogRelativeWealthChart } from './LogRelativeWealthChart'
import { RebalanceDecisionAudit } from './RebalanceDecisionAudit'
import { RelativeWealthChart } from './RelativeWealthChart'

interface PortfolioOverviewProps {
  experiment: ExperimentDetailDto
  snapshot: PortfolioSnapshotDto
  performance: PortfolioPerformanceDto
  selectedDecisionId?: string | null
  onDecisionChange?: (decisionId: string) => void
}

function pairWorkbenchHref(experiment: ExperimentDetailDto): string | null {
  const [assetX, assetY] = experiment.manifest.basket
  if (!assetX || !assetY) return null
  const search = new URLSearchParams({
    orientation: `${assetX}/${assetY}`,
    anchor: experiment.manifest.analysis_anchor ?? 'none',
    view: 'ratio',
  })
  return `/pair/${encodeURIComponent(experiment.run_id)}/${encodeURIComponent(assetX)}/${encodeURIComponent(assetY)}?${search}`
}

function DashboardMetric({
  label,
  value,
  exact,
  detail,
}: {
  label: string
  value: string
  exact?: string
  detail?: string
}) {
  return (
    <div className="rounded-md border border-border bg-canvas/50 p-4">
      <p className="m-0 text-xs font-medium text-muted">{label}</p>
      <p
        className="mt-1 mb-0 text-xl font-semibold tabular-nums text-foreground"
        data-exact={exact}
      >
        {value}
      </p>
      {detail ? <p className="mt-2 mb-0 text-xs leading-5 text-secondary">{detail}</p> : null}
    </div>
  )
}

function HoldingsTable({
  title,
  snapshot,
}: {
  title: string
  snapshot: PortfolioSnapshotDto['terminal']
}) {
  return (
    <section className="min-w-0">
      <h3 className="mb-1 text-sm font-semibold text-foreground">{title}</h3>
      <p className="mt-0 mb-3 text-xs text-muted">{snapshot.timestamp}</p>
      <TableScroll label={title}>
        <table aria-label={title}>
          <thead>
            <tr>
              <th scope="col">Asset</th>
              <th scope="col">Quantity</th>
              <th scope="col">Value</th>
              <th scope="col">Weight</th>
            </tr>
          </thead>
          <tbody>
            {snapshot.holdings.map((holding) => (
              <tr key={holding.asset}>
                <th scope="row">{holding.asset}</th>
                <td><ExactNumber value={holding.quantity} /></td>
                <td><ExactNumber value={holding.value} /></td>
                <td><ExactNumber value={holding.weight} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </TableScroll>
    </section>
  )
}

export function PortfolioOverview({
  experiment,
  snapshot,
  performance,
  selectedDecisionId,
  onDecisionChange,
}: PortfolioOverviewProps) {
  const { result } = experiment
  const status = researchStatusPresentation(result.status)
  const primary = result.strategy_vs_primary_control
    ? formatRelativePercent(result.strategy_vs_primary_control)
    : null
  const hodl = formatRelativePercent(result.strategy_vs_hodl)
  const drawdown = formatPercent(performance.maximum_relative_drawdown_vs_hodl)
  const fees = formatDecimal(snapshot.strategy_costs.fees_value)
  const slippage = formatDecimal(snapshot.strategy_costs.slippage_value)
  const turnover = formatDecimal(snapshot.strategy_costs.turnover_value)
  const terminalMaxWeight = formatPercent(snapshot.concentration.terminal_max_weight)
  const primaryLabel = humanizeIdentifier(
    result.primary_incremental_benchmark ?? 'primary control',
  )
  const valueUnit = experiment.manifest.execution?.numeraire_asset ?? 'value units'
  const verdict = researchVerdictHeadline(
    result.status,
    result.primary_incremental_benchmark,
    result.strategy_vs_primary_control,
  )
  const pairHref = pairWorkbenchHref(experiment)

  return (
    <article className="min-w-0" aria-labelledby="portfolio-heading">
      <div className="mb-4">
        <nav aria-label="Breadcrumb" className="flex flex-wrap items-center gap-2 text-sm text-muted">
          <a className="font-medium text-secondary" href="/experiments">Research runs</a>
          <span aria-hidden="true">/</span>
          <a
            className="max-w-[18rem] truncate font-medium text-secondary"
            href={`/experiments/${encodeURIComponent(experiment.run_id)}`}
          >
            {experiment.manifest.experiment_name}
          </a>
          <span aria-hidden="true">/</span>
          <span aria-current="page">Portfolio</span>
        </nav>
      </div>

      <header className={`rounded-lg border bg-panel p-5 md:p-6 ${status.tone === 'negative' ? 'border-negative/45' : status.tone === 'positive' ? 'border-positive/45' : 'border-border-strong'}`}>
        <div className="mb-4 flex flex-wrap items-center gap-2">
          <Badge tone={status.tone}>{status.label}</Badge>
          <Badge tone="info">
            {experimentDataRoleLabel(result.data_role, result.final_oos_consumed)}
          </Badge>
        </div>
        <p className="mb-2 text-xs font-semibold uppercase tracking-[0.1em] text-muted">Portfolio result</p>
        <h1 id="portfolio-heading" className="mb-3 text-2xl font-bold tracking-tight text-foreground md:text-3xl">
          Portfolio economics
        </h1>
        <p className="m-0 max-w-4xl text-2xl font-semibold leading-tight text-foreground md:text-3xl">
          {verdict}
        </p>
        <p className="mt-3 mb-0 max-w-3xl text-sm leading-6 text-secondary">
          {experiment.manifest.experiment_name} · {experiment.manifest.basket.join(' · ')} ·{' '}
          {formatResearchDate(experiment.manifest.data_window.start)} –{' '}
          {formatResearchDate(experiment.manifest.data_window.end)}
        </p>

        <div className="mt-5 grid grid-cols-2 gap-3 lg:grid-cols-4">
          <DashboardMetric
            label={`vs ${primaryLabel}`}
            value={primary?.display ?? 'Not applicable'}
            exact={primary?.exact}
            detail="Primary incremental benchmark"
          />
          <DashboardMetric
            label="vs strict inventory HODL"
            value={hodl.display}
            exact={hodl.exact}
            detail="Primary passive counterfactual"
          />
          <DashboardMetric
            label="Maximum relative drawdown"
            value={drawdown.display}
            exact={drawdown.exact}
            detail="Relative to HODL"
          />
          <DashboardMetric
            label="Execution"
            value={`${snapshot.strategy_costs.fill_count} fills`}
            detail={`Fees ${fees.display} · slippage ${slippage.display} ${valueUnit}`}
          />
        </div>

        {pairHref ? (
          <nav className="mt-5 flex flex-wrap gap-2" aria-label="Portfolio evidence links">
            <a
              className="inline-flex min-h-11 items-center rounded-md border border-border-strong bg-subtle px-4 py-2 text-sm font-semibold text-foreground no-underline hover:border-accent"
              href={pairHref}
            >
              Pair workbench
            </a>
          </nav>
        ) : null}
      </header>

      <div className="mt-6 space-y-6">
        <RelativeWealthChart performance={performance} />

        <BenchmarkLadder experiment={experiment} />

        <details className="rounded-lg border border-border bg-panel p-5 md:p-6">
          <summary className="cursor-pointer font-semibold text-foreground">
            Compare all benchmark roles
          </summary>
          <div className="mt-5">
            <BenchmarkRoleTable roles={result.roles} />
          </div>
        </details>

        <section
          className="rounded-lg border border-border bg-panel p-5 md:p-6"
          aria-labelledby="allocation-heading"
        >
          <h2 id="allocation-heading" className="mb-2 text-lg font-semibold text-foreground">
            Portfolio composition
          </h2>
          <p className="mt-0 mb-5 max-w-3xl text-sm leading-6 text-secondary">
            Starting and terminal composition use the backend-provided portfolio weights;
            they are not reconstructed from quantities in the browser.
          </p>
          <div className="grid gap-5 lg:grid-cols-2">
            <div className="rounded-md border border-border bg-canvas/35 p-4">
              <div className="mb-3 flex flex-wrap items-baseline justify-between gap-2">
                <h3 className="m-0 text-sm font-semibold text-foreground">Starting allocation</h3>
                <span className="text-xs text-muted">{formatResearchDate(snapshot.starting.timestamp)}</span>
              </div>
              <CompositionBars
                label="Starting allocation"
                items={snapshot.starting.holdings.map((holding) => ({
                  asset: holding.asset,
                  weight: holding.weight,
                }))}
              />
            </div>
            <div className="rounded-md border border-border bg-canvas/35 p-4">
              <div className="mb-3 flex flex-wrap items-baseline justify-between gap-2">
                <h3 className="m-0 text-sm font-semibold text-foreground">Terminal allocation</h3>
                <span className="text-xs text-muted">{formatResearchDate(snapshot.terminal.timestamp)}</span>
              </div>
              <CompositionBars
                label="Terminal allocation"
                items={snapshot.terminal.holdings.map((holding) => ({
                  asset: holding.asset,
                  weight: holding.weight,
                }))}
              />
            </div>
          </div>

          <details className="mt-5 rounded-md border border-border bg-canvas/35 p-4">
            <summary className="cursor-pointer font-semibold text-foreground">Exact holdings</summary>
            <div className="mt-5 grid min-w-0 gap-5 lg:grid-cols-2">
              <HoldingsTable title="Starting holdings" snapshot={snapshot.starting} />
              <HoldingsTable title="Terminal holdings" snapshot={snapshot.terminal} />
            </div>
          </details>
        </section>

        <AllocationHistoryChart snapshot={snapshot} />

        <InventoryVsHodlTable snapshot={snapshot} valueUnit={valueUnit} />

        <section
          className="rounded-lg border border-border bg-panel p-5 md:p-6"
          aria-labelledby="risk-cost-heading"
        >
          <h2 id="risk-cost-heading" className="mb-2 text-lg font-semibold text-foreground">
            Risk and execution
          </h2>
          <p className="mt-0 mb-5 max-w-3xl text-sm leading-6 text-secondary">
            Persisted diagnostics summarize how long QAP trailed its controls and the
            modeled execution burden carried by the strategy.
          </p>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            <DashboardMetric
              label="Time below HODL"
              value={formatDuration(performance.time_below_hodl_seconds)}
              detail="Elapsed admitted evaluation time below strict inventory HODL"
            />
            {performance.time_below_primary_control_seconds !== null ? (
              <DashboardMetric
                label="Time below primary control"
                value={formatDuration(performance.time_below_primary_control_seconds)}
                detail={`Elapsed time below ${primaryLabel}`}
              />
            ) : null}
            <DashboardMetric
              label="Terminal max weight"
              value={terminalMaxWeight.display}
              exact={terminalMaxWeight.exact}
              detail="Largest terminal asset weight"
            />
            <DashboardMetric label="Fees" value={`${fees.display} ${valueUnit}`} exact={fees.exact} />
            <DashboardMetric label="Slippage" value={`${slippage.display} ${valueUnit}`} exact={slippage.exact} />
            <DashboardMetric label="Turnover" value={`${turnover.display} ${valueUnit}`} exact={turnover.exact} />
          </div>
        </section>

        <ExternalFlowContext experiment={experiment} />

        <RebalanceDecisionAudit
          decisions={snapshot.rebalance_audit}
          selectedDecisionId={selectedDecisionId}
          onSelectDecision={onDecisionChange}
        />

        <details className="rounded-lg border border-border bg-panel p-5 md:p-6">
          <summary className="cursor-pointer font-semibold text-foreground">
            Advanced compounding view
          </summary>
          <div className="mt-5">
            <LogRelativeWealthChart experiment={experiment} performance={performance} />
          </div>
        </details>
      </div>
    </article>
  )
}
