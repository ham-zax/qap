import type {
  ExperimentDetailDto,
  PortfolioPerformanceDto,
  PortfolioSnapshotDto,
} from '../../api/types'
import { ExactNumber } from '../../components/ExactNumber'
import { MetricCard } from '../../components/MetricCard'
import { TableScroll } from '../../components/TableScroll'
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
}

function dataRoleLabel(role: string, consumed: boolean): string {
  if (role === 'final_oos') {
    return `Final OOS - ${consumed ? 'consumed' : 'unconsumed'}`
  }
  return role
    .split('_')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ')
}

function HoldingsTable({
  title,
  snapshot,
}: {
  title: string
  snapshot: PortfolioSnapshotDto['terminal']
}) {
  return (
    <section>
      <h3>{title}</h3>
      <p>{snapshot.timestamp}</p>
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
}: PortfolioOverviewProps) {
  const { result } = experiment

  return (
    <article aria-labelledby="portfolio-heading">
      <header>
        <p>{dataRoleLabel(result.data_role, result.final_oos_consumed)}</p>
        <h1 id="portfolio-heading">Portfolio economics</h1>
        <p>
          {experiment.manifest.experiment_name} - {result.research_family_id}
        </p>
        <p>
          Universe: {experiment.manifest.universe_mode}; basket:{' '}
          {experiment.manifest.basket.join(' / ')}; anchor:{' '}
          {experiment.manifest.analysis_anchor ?? 'none'}
        </p>
      </header>

      <BenchmarkLadder experiment={experiment} />
      <BenchmarkRoleTable roles={result.roles} />
      <ExternalFlowContext experiment={experiment} />
      <RelativeWealthChart performance={performance} />
      <LogRelativeWealthChart experiment={experiment} performance={performance} />

      <section aria-labelledby="risk-cost-heading">
        <h2 id="risk-cost-heading">Risk and execution diagnostics</h2>
        <div className="metric-grid">
          <MetricCard
            label="Maximum relative drawdown vs HODL"
            value={<ExactNumber value={performance.maximum_relative_drawdown_vs_hodl} />}
          />
          <MetricCard
            label="Time below HODL"
            value={`${performance.time_below_hodl_seconds} seconds`}
            detail="Elapsed admitted evaluation time with QAP wealth below strict inventory HODL."
          />
          {performance.time_below_primary_control_seconds !== null ? (
            <MetricCard
              label="Time below primary control"
              value={`${performance.time_below_primary_control_seconds} seconds`}
              detail={`Elapsed admitted evaluation time below ${performance.primary_incremental_benchmark ?? 'the primary simple control'}.`}
            />
          ) : null}
          <MetricCard
            label="Terminal maximum weight"
            value={<ExactNumber value={snapshot.concentration.terminal_max_weight} />}
          />
          <MetricCard
            label="Terminal concentration (HHI)"
            value={<ExactNumber value={snapshot.concentration.terminal_herfindahl} />}
          />
          <MetricCard label="Rebalance fills" value={snapshot.strategy_costs.fill_count} />
        </div>
        <p>Fees: <ExactNumber value={snapshot.strategy_costs.fees_value} /></p>
        <p>Slippage: <ExactNumber value={snapshot.strategy_costs.slippage_value} /></p>
        <p>Turnover: <ExactNumber value={snapshot.strategy_costs.turnover_value} /></p>
      </section>

      <section aria-labelledby="holdings-heading">
        <h2 id="holdings-heading">Owned inventory</h2>
        <div className="holdings-grid">
          <HoldingsTable title="Starting holdings" snapshot={snapshot.starting} />
          <HoldingsTable title="Terminal holdings" snapshot={snapshot.terminal} />
        </div>
      </section>

      <InventoryVsHodlTable snapshot={snapshot} />
      <AllocationHistoryChart snapshot={snapshot} />
      <RebalanceDecisionAudit decisions={snapshot.rebalance_audit} />
    </article>
  )
}
