import type { PortfolioSnapshotDto } from '../../api/types'
import { TimeSeriesChart } from '../../components/charts/TimeSeriesChart'
import type { TimeSeriesDefinition } from '../../components/charts/chartData'

interface AllocationHistoryChartProps {
  snapshot: PortfolioSnapshotDto
}

export function AllocationHistoryChart({ snapshot }: AllocationHistoryChartProps) {
  const assets = Array.from(
    new Set(
      snapshot.allocation_history.flatMap((item) =>
        item.holdings.map((holding) => holding.asset),
      ),
    ),
  )
  const series: TimeSeriesDefinition[] = assets.map((asset) => ({
    name: asset,
    unit: 'portfolio weight',
    points: snapshot.allocation_history.flatMap((item) => {
      const holding = item.holdings.find((candidate) => candidate.asset === asset)
      if (!holding) return []
      const value = Number(holding.weight)
      if (!Number.isFinite(value)) {
        throw new Error(`allocation weight must be finite: ${holding.weight}`)
      }
      return [{ timestamp: item.timestamp, value }]
    }),
  }))

  return (
    <section aria-labelledby="allocation-history-heading">
      <h2 id="allocation-history-heading">Allocation history</h2>
      {series.length > 0 ? (
        <TimeSeriesChart
          title="Allocation history"
          description="One backend-valued portfolio-weight line per owned asset."
          series={series}
        />
      ) : (
        <p>No allocation-history series is available.</p>
      )}
    </section>
  )
}
