import { useId } from 'react'
import type { PortfolioPerformanceDto } from '../../api/types'
import { TimeSeriesChart } from '../../components/charts/TimeSeriesChart'
import {
  exactPointsToPresentation,
  type TimeSeriesDefinition,
} from '../../components/charts/chartData'
import { formatRelativePercent } from '../../lib/format'

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
  const headingId = useId()
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

  const primaryExact = performance.series
    .find((item) => item.name === 'relative::strategy_vs_primary_control')
    ?.points.at(-1)?.value
  const hodlExact = performance.series
    .find((item) => item.name === 'relative::strategy_vs_hodl')
    ?.points.at(-1)?.value

  if (series.length === 0) {
    return (
      <section
        className="rounded-lg border border-border bg-panel p-5 md:p-6"
        aria-labelledby={headingId}
      >
        <h2 id={headingId} className="mb-2 text-lg font-semibold text-foreground">
          Relative wealth through time
        </h2>
        <p className="m-0 text-sm text-secondary">No authoritative relative-wealth series is available.</p>
      </section>
    )
  }

  return (
    <section
      className="rounded-lg border border-border bg-panel p-5 md:p-6"
      aria-labelledby={headingId}
    >
      <h2 id={headingId} className="mb-2 text-lg font-semibold text-foreground">
        Relative wealth through time
      </h2>
      <p className="mt-0 mb-4 max-w-3xl text-sm leading-6 text-secondary">
        Zero is parity. The curves show persisted aligned wealth comparisons after
        the modeled execution economics.
      </p>
      {primaryExact || hodlExact ? (
        <p className="mb-5 flex flex-wrap gap-x-4 gap-y-1 text-sm text-secondary">
          {primaryExact ? (
            <span>
              Latest vs primary control:{' '}
              <strong className="tabular-nums text-foreground" data-exact={primaryExact}>
                {formatRelativePercent(primaryExact).display}
              </strong>
            </span>
          ) : null}
          {hodlExact ? (
            <span>
              Latest vs HODL:{' '}
              <strong className="tabular-nums text-foreground" data-exact={hodlExact}>
                {formatRelativePercent(hodlExact).display}
              </strong>
            </span>
          ) : null}
        </p>
      ) : null}
      <TimeSeriesChart
        title="QAP relative wealth curves"
        description="Zero is parity; positive values favor QAP and negative values favor the named passive or simple control."
        series={series}
      />
    </section>
  )
}
