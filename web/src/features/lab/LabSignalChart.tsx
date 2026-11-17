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
      const upperPoints = signal.time.flatMap((time, idx) => {
        const value = signal.values[idx]
        if (value == null) return []
        const bound = signal.upper_series?.[idx] ?? signal.upper
        return bound == null ? [] : [{ timestamp: new Date(time * 1000).toISOString(), value: bound }]
      })
      const lowerPoints = signal.time.flatMap((time, idx) => {
        const value = signal.values[idx]
        if (value == null) return []
        const bound = signal.lower_series?.[idx] ?? signal.lower
        return bound == null ? [] : [{ timestamp: new Date(time * 1000).toISOString(), value: bound }]
      })
      base.push(
        { name: 'Upper trigger', unit: signal.unit, points: upperPoints, dashed: true, colorToken: '--qap-border-strong' },
        { name: 'Lower trigger', unit: signal.unit, points: lowerPoints, dashed: true, colorToken: '--qap-border-strong' },
      )
    }
    return base
  }, [signal, showTriggers])

  if (series.length === 0) return null

  const provenanceText =
    signal.provenance === 'walk_forward_stitched'
      ? 'Walk-forward stitched executed signal'
      : signal.provenance === 'context_only'
        ? 'Context-only signal preview'
        : 'Legacy saved study (signal provenance not recorded)'
  const variableText = signal.signal_variable ? `${signal.signal_variable} (${signal.unit})` : signal.unit

  return (
    <div className="lab-signal-subpane">
      <TimeSeriesChart
        title="Active signal"
        description={`${provenanceText}: ${variableText} with entry thresholds (${Number(signal.lower.toFixed(4))} / ${Number(signal.upper.toFixed(4))}).`}
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
