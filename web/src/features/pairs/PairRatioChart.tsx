import { useMemo } from 'react'

import type { PairSeriesDto } from '../../api/types'
import { TimeSeriesChart } from '../../components/charts/TimeSeriesChart'
import type {
  ChartVisibleRange,
  TimeSeriesDefinition,
} from '../../components/charts/chartData'
import type { PairView } from './pairSearch'
import { pairChartMarkers } from './RebalanceMarkerOverlay'

interface PairRatioChartProps {
  data: PairSeriesDto
  view: Exclude<PairView, 'anchor'>
  sharedCursorTime?: string | null
  onCursorTimeChange?: (timestamp: string | null) => void
  sharedVisibleRange?: ChartVisibleRange | null
  onVisibleRangeChange?: (range: ChartVisibleRange | null) => void
}

export function PairRatioChart({
  data,
  view,
  sharedCursorTime,
  onCursorTimeChange,
  sharedVisibleRange,
  onVisibleRangeChange,
}: PairRatioChartProps) {
  const chart = useMemo(() => {
    const [base, quote] = data.requested_orientation.split('/')
    let title: string
    let description: string
    let series: TimeSeriesDefinition[]

    if (view === 'log') {
      title = `${data.requested_orientation} log ratio`
      description = 'Backend-produced natural log of the requested ratio orientation.'
      series = [
        {
          name: data.requested_orientation,
          unit: 'log ratio',
          points: data.log_ratio,
        },
      ]
    } else if (view === 'normalized') {
      title = `${data.requested_orientation} normalized paths`
      description = 'Both requested legs rebased to one at the admitted window start.'
      series = [
        {
          name: base ?? 'base',
          unit: 'normalized path',
          points: data.normalized_base,
        },
        {
          name: quote ?? 'quote',
          unit: 'normalized path',
          points: data.normalized_quote,
        },
      ]
    } else {
      title = `${data.requested_orientation} ratio`
      description = 'Requested quote units per one requested base unit.'
      series = [
        {
          name: data.requested_orientation,
          unit: 'ratio',
          points: data.ratio,
        },
      ]
    }
    return { title, description, series }
  }, [data, view])
  const markers = useMemo(() => pairChartMarkers(data), [data])

  return (
    <TimeSeriesChart
      title={chart.title}
      description={chart.description}
      series={chart.series}
      markers={markers}
      sharedCursorTime={sharedCursorTime}
      onCursorTimeChange={onCursorTimeChange}
      sharedVisibleRange={sharedVisibleRange}
      onVisibleRangeChange={onVisibleRangeChange}
    />
  )
}
