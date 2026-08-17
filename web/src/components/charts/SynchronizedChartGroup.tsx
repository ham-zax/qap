import { useCallback, useState } from 'react'

import { TimeSeriesChart } from './TimeSeriesChart'
import type {
  ChartMarker,
  ChartVisibleRange,
  TimeSeriesDefinition,
} from './chartData'

export interface SynchronizedChartSpec {
  key: string
  title: string
  description: string
  series: TimeSeriesDefinition[]
  markers?: ChartMarker[]
  height?: number
}

interface SynchronizedChartGroupProps {
  charts: SynchronizedChartSpec[]
  label: string
}

export function SynchronizedChartGroup({
  charts,
  label,
}: SynchronizedChartGroupProps) {
  const [cursorTime, setCursorTime] = useState<string | null>(null)
  const [visibleRange, setVisibleRange] = useState<ChartVisibleRange | null>(null)
  const handleCursorTime = useCallback((timestamp: string | null) => {
    setCursorTime(timestamp)
  }, [])
  const handleVisibleRange = useCallback((range: ChartVisibleRange | null) => {
    setVisibleRange((current) => {
      if (
        current?.from === range?.from &&
        current?.to === range?.to
      ) {
        return current
      }
      return range
    })
  }, [])

  return (
    <section className="synchronized-chart-group" aria-label={label}>
      <p aria-live="polite">
        Shared cursor: {cursorTime ?? 'move across any chart to synchronize time'}
      </p>
      {charts.map((chart) => (
        <TimeSeriesChart
          key={chart.key}
          title={chart.title}
          description={chart.description}
          series={chart.series}
          markers={chart.markers}
          height={chart.height}
          sharedCursorTime={cursorTime}
          onCursorTimeChange={handleCursorTime}
          sharedVisibleRange={visibleRange}
          onVisibleRangeChange={handleVisibleRange}
        />
      ))}
    </section>
  )
}
