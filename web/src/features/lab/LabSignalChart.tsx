import { useMemo } from 'react'
import { TimeSeriesChart } from '../../components/charts/TimeSeriesChart'
import type { ChartVisibleRange, TimeSeriesDefinition } from '../../components/charts/chartData'
import type { LabStudy } from './labStudyApi'

export type LabSignalSeries = LabStudy['result']['signal']

interface LabSignalChartProps {
  signal: LabSignalSeries
  showTriggers?: boolean
  sharedCursorTime?: string | null
  onCursorTimeChange?: (timestamp: string | null) => void
  sharedVisibleRange?: ChartVisibleRange | null
  onVisibleRangeChange?: (range: ChartVisibleRange | null) => void
}

export function LabSignalChart({
  signal,
  showTriggers = true,
  sharedCursorTime,
  onCursorTimeChange,
  sharedVisibleRange,
  onVisibleRangeChange,
}: LabSignalChartProps) {
  const series = useMemo<TimeSeriesDefinition[]>(() => {
    const activePoints = signal.time.flatMap((time, idx) => {
      const value = signal.values[idx]
      return value == null ? [] : [{ timestamp: new Date(time * 1000).toISOString(), value }]
    })
    if (activePoints.length === 0) return []
    const base: TimeSeriesDefinition[] = [
      { name: 'Active signal', unit: signal.unit, points: activePoints, colorToken: '--chart-series-1' },
    ]
    if (showTriggers) {
      const upperPoints = activePoints.map((pt) => ({ timestamp: pt.timestamp, value: signal.upper }))
      const lowerPoints = activePoints.map((pt) => ({ timestamp: pt.timestamp, value: signal.lower }))
      base.push(
        { name: 'Upper trigger', unit: signal.unit, points: upperPoints, dashed: true, colorToken: '--qap-border-strong' },
        { name: 'Lower trigger', unit: signal.unit, points: lowerPoints, dashed: true, colorToken: '--qap-border-strong' },
      )
    }
    return base
  }, [signal, showTriggers])

  if (series.length === 0) return null

  return (
    <div className="lab-signal-subpane">
      <TimeSeriesChart
        title="Active signal"
        description={`Synchronized strategy signal (${signal.unit}) with entry thresholds (${Number(signal.lower.toFixed(4))} / ${Number(signal.upper.toFixed(4))}).`}
        series={series}
        height={180}
        sharedCursorTime={sharedCursorTime}
        onCursorTimeChange={onCursorTimeChange}
        sharedVisibleRange={sharedVisibleRange}
        onVisibleRangeChange={onVisibleRangeChange}
      />
    </div>
  )
}
