import type {
  ExperimentDetailDto,
  PortfolioPerformanceDto,
} from '../../api/types'
import { TimeSeriesChart } from '../../components/charts/TimeSeriesChart'
import {
  exactPointsToPresentation,
  type TimeSeriesDefinition,
} from '../../components/charts/chartData'

interface LogRelativeWealthChartProps {
  experiment: ExperimentDetailDto
  performance: PortfolioPerformanceDto
}

const PRESENTATION_SERIES: Record<
  string,
  Pick<TimeSeriesDefinition, 'name' | 'unit'>
> = {
  'log_relative::strategy_vs_hodl': {
    name: 'QAP vs HODL',
    unit: 'cumulative net log-relative wealth',
  },
  'log_relative::strategy_vs_primary_control': {
    name: 'QAP vs primary control',
    unit: 'cumulative net log-relative wealth',
  },
  'log_relative::strategy_vs_matched_contribution': {
    name: 'QAP vs matched contribution',
    unit: 'cumulative net log-relative wealth',
  },
}

function evidenceBoundary(experiment: ExperimentDetailDto): string {
  const { result } = experiment
  const role =
    result.data_role === 'final_oos'
      ? 'Final OOS'
      : result.data_role
          .split('_')
          .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
          .join(' ')
  const consumed =
    result.data_role === 'final_oos'
      ? ` - ${result.final_oos_consumed ? 'consumed' : 'unconsumed'}`
      : ''
  return `Evidence boundary: ${role}${consumed}; research family ${result.research_family_id}.`
}

export function LogRelativeWealthChart({
  experiment,
  performance,
}: LogRelativeWealthChartProps) {
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

  return (
    <section className="min-w-0" aria-labelledby="log-relative-wealth-heading">
      <h2 id="log-relative-wealth-heading" className="mb-2 text-lg font-semibold text-foreground">
        Log relative wealth through time
      </h2>
      <p className="mt-0 mb-5 text-sm text-secondary">{evidenceBoundary(experiment)}</p>
      {series.length > 0 ? (
        <TimeSeriesChart
          title="Cumulative net log-relative wealth"
          description="Backend-produced aligned log-relative paths. Zero is parity; sustained negative values show compounding below the named control."
          series={series}
        />
      ) : (
        <p className="m-0 text-sm text-secondary">No authoritative log-relative wealth series is available.</p>
      )}
    </section>
  )
}
