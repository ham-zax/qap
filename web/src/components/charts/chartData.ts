import type { IRange, LineData, Time, UTCTimestamp } from 'lightweight-charts'

export interface ExactChartPoint {
  timestamp: string
  value: string
}

export interface PresentationChartPoint {
  timestamp: string
  value: number
}

export interface TimeSeriesDefinition {
  name: string
  unit: string
  points: PresentationChartPoint[]
}

export interface ChartMarker {
  timestamp: string
  label: string
  selected: boolean
  executed: boolean
}

export interface ChartVisibleRange {
  from: string
  to: string
}

export function exactPointsToPresentation(
  points: readonly ExactChartPoint[],
): PresentationChartPoint[] {
  return points.map((point) => {
    const value = Number(point.value)
    if (!Number.isFinite(value)) {
      throw new Error(`chart value must be a finite presentation number: ${point.value}`)
    }
    return { timestamp: point.timestamp, value }
  })
}

export function utcTimestamp(timestamp: string): UTCTimestamp {
  const milliseconds = Date.parse(timestamp)
  if (!Number.isFinite(milliseconds)) {
    throw new Error(`chart point requires a valid ISO timestamp: ${timestamp}`)
  }
  return Math.floor(milliseconds / 1000) as UTCTimestamp
}

export function toLightweightChartData(
  points: readonly PresentationChartPoint[],
): LineData<UTCTimestamp>[] {
  let previous: number | null = null
  return points.map((point) => {
    const seconds = utcTimestamp(point.timestamp)
    if (!Number.isFinite(point.value)) {
      throw new Error(`chart value must be finite: ${point.value}`)
    }
    if (previous !== null && Number(seconds) <= previous) {
      throw new Error('chart timestamps must be strictly increasing')
    }
    previous = Number(seconds)
    return { time: seconds, value: point.value }
  })
}

export function findPresentationPointAtTimestamp(
  points: readonly PresentationChartPoint[],
  timestamp: string,
): PresentationChartPoint | undefined {
  const target = Number(utcTimestamp(timestamp))
  return points.find(
    (point) => Number(utcTimestamp(point.timestamp)) === target,
  )
}

export function timestampFromChartTime(value: Time): string {
  if (typeof value === 'number') {
    return new Date(Number(value) * 1000).toISOString()
  }
  if (typeof value === 'string') {
    return new Date(value).toISOString()
  }
  return new Date(Date.UTC(value.year, value.month - 1, value.day)).toISOString()
}

export function toChartVisibleRange(
  range: ChartVisibleRange,
): IRange<UTCTimestamp> {
  return {
    from: utcTimestamp(range.from),
    to: utcTimestamp(range.to),
  }
}

export function fromChartVisibleRange(
  range: IRange<Time> | null,
): ChartVisibleRange | null {
  if (range === null) return null
  return {
    from: timestampFromChartTime(range.from),
    to: timestampFromChartTime(range.to),
  }
}
