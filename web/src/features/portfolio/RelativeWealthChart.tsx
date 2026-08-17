import type { PortfolioPerformanceDto } from '../../api/types'
import { TimeSeriesChart } from '../../components/charts/TimeSeriesChart'
import {
  exactPointsToPresentation,
  type TimeSeriesDefinition,
} from '../../components/charts/chartData'

interface RelativeWealthChartProps {
  performance: PortfolioPerformanceDto
}

const PRESENTATION_SERIES: Record<
  string,
  Pick<TimeSeriesDefinition, 'name' | 'unit'>
> = {
  'relative::strategy_vs_hodl': {
    name: 'QAP vs HODL',
    unit: 'relative wealth',
  },
  'relative_unitized::strategy_vs_hodl': {
    name: 'Flow-adjusted QAP vs HODL',
    unit: 'relative unitized wealth',
  },
  'relative::strategy_vs_primary_control': {
    name: 'QAP vs primary control',
    unit: 'relative wealth',
  },
}

export function RelativeWealthChart({ performance }: RelativeWealthChartProps) {
  const series = performance.series.flatMap((item) => {
    const presentation = PRESENTATION_SERIES[item.name]
    return presentation
      ? [
          {
            ...presentation,
            points: exactPointsToPresentation(item.points),
          },
        ]
      : []
  })

  if (series.length === 0) {
    return (
      <section aria-labelledby="relative-wealth-heading">
        <h2 id="relative-wealth-heading">Relative wealth through time</h2>
        <p>No authoritative relative-wealth series is available.</p>
      </section>
    )
  }

  return (
    <section aria-labelledby="relative-wealth-heading">
      <h2 id="relative-wealth-heading">Relative wealth through time</h2>
      <p>
        Backend-produced aligned wealth comparisons. Chart numbers are
        presentation copies; exact values remain in the API and metric cards.
      </p>
      <TimeSeriesChart
        title="QAP relative wealth curves"
        description="Zero is parity; positive values favor QAP and negative values favor the named passive or simple control."
        series={series}
      />
    </section>
  )
}
