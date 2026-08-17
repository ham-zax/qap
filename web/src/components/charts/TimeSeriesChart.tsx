import {
  ColorType,
  LineSeries,
  createChart,
  createSeriesMarkers,
  type IChartApi,
  type IRange,
  type ISeriesApi,
  type MouseEventParams,
  type SeriesMarker,
  type Time,
  type UTCTimestamp,
} from 'lightweight-charts'
import { useEffect, useId, useRef, useState } from 'react'

import {
  findPresentationPointAtTimestamp,
  fromChartVisibleRange,
  timestampFromChartTime,
  toChartVisibleRange,
  toLightweightChartData,
  utcTimestamp,
  type ChartMarker,
  type ChartVisibleRange,
  type TimeSeriesDefinition,
} from './chartData'

interface CursorValue {
  name: string
  unit: string
  value: number
}

interface CursorSnapshot {
  timestamp: string
  values: CursorValue[]
}

function cursorSnapshotAtTimestamp(
  series: readonly TimeSeriesDefinition[],
  timestamp: string,
): CursorSnapshot | null {
  const anchor = series[0]
    ? findPresentationPointAtTimestamp(series[0].points, timestamp)
    : undefined
  if (!anchor) return null
  const values = series.flatMap((definition) => {
    const matched = findPresentationPointAtTimestamp(definition.points, timestamp)
    return matched
      ? [{ name: definition.name, unit: definition.unit, value: matched.value }]
      : []
  })
  return { timestamp: anchor.timestamp, values }
}

interface TimeSeriesChartProps {
  title: string
  description: string
  series: TimeSeriesDefinition[]
  markers?: readonly ChartMarker[]
  height?: number
  onCursorTimeChange?: (timestamp: string | null) => void
  sharedCursorTime?: string | null
  onVisibleRangeChange?: (range: ChartVisibleRange | null) => void
  sharedVisibleRange?: ChartVisibleRange | null
}

const SERIES_COLOR_VARS = [
  '--chart-series-1',
  '--chart-series-2',
  '--chart-series-3',
  '--chart-series-4',
  '--chart-series-5',
] as const
const EMPTY_MARKERS: readonly ChartMarker[] = Object.freeze([])

function cssColor(styles: CSSStyleDeclaration, name: string, fallback: string): string {
  return styles.getPropertyValue(name).trim() || fallback
}

function toSeriesMarkers(
  markers: readonly ChartMarker[],
  colors: { executed: string; selected: string; inactive: string },
): SeriesMarker<UTCTimestamp>[] {
  return markers
    .map((marker) => ({
      time: utcTimestamp(marker.timestamp),
      position: 'aboveBar' as const,
      shape: marker.executed ? ('arrowUp' as const) : ('square' as const),
      color: marker.executed
        ? colors.executed
        : marker.selected
          ? colors.selected
          : colors.inactive,
      text: `${marker.label} - ${marker.executed ? 'executed' : marker.selected ? 'selected' : 'not selected'}`,
    }))
    .sort((left, right) => Number(left.time) - Number(right.time))
}

export function TimeSeriesChart({
  title,
  description,
  series,
  markers = EMPTY_MARKERS,
  height = 320,
  onCursorTimeChange,
  sharedCursorTime,
  onVisibleRangeChange,
  sharedVisibleRange,
}: TimeSeriesChartProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  const seriesRef = useRef<Array<ISeriesApi<'Line'>>>([])
  const applyingSharedCursor = useRef(false)
  const applyingSharedRange = useRef(false)
  const lastCursorTime = useRef<string | null>(null)
  const [cursor, setCursor] = useState<CursorSnapshot | null>(null)
  const titleId = useId()

  useEffect(() => {
    const container = containerRef.current
    if (!container || typeof ResizeObserver === 'undefined') return

    const styles = getComputedStyle(document.documentElement)
    const seriesColors = SERIES_COLOR_VARS.map((name, index) =>
      cssColor(styles, name, ['#78a9ff', '#c4a7e7', '#7dd3c7', '#f6d365', '#9fb7ff'][index] ?? '#78a9ff'),
    )
    const borderColor = cssColor(styles, '--border-default', '#303a4a')
    const chart = createChart(container, {
      autoSize: true,
      height,
      layout: {
        attributionLogo: true,
        background: {
          type: ColorType.Solid,
          color: cssColor(styles, '--surface-panel', '#121720'),
        },
        textColor: cssColor(styles, '--text-muted', '#9ca8b8'),
      },
      grid: {
        horzLines: { color: cssColor(styles, '--chart-grid', '#242d3b') },
        vertLines: { color: cssColor(styles, '--chart-grid', '#242d3b') },
      },
      rightPriceScale: {
        borderColor,
      },
      timeScale: {
        borderColor,
        timeVisible: true,
        secondsVisible: false,
      },
    })
    chartRef.current = chart

    const chartSeries: Array<{
      definition: TimeSeriesDefinition
      api: ISeriesApi<'Line'>
    }> = series.map((definition, index) => {
      const api = chart.addSeries(LineSeries, {
        color: seriesColors[index % seriesColors.length],
        lineWidth: 2,
        title: `${definition.name} (${definition.unit})`,
      })
      api.setData(toLightweightChartData(definition.points))
      return { definition, api }
    })
    seriesRef.current = chartSeries.map((item) => item.api)

    const markerPlugin =
      markers.length > 0 && chartSeries[0]
        ? createSeriesMarkers(
            chartSeries[0].api,
            toSeriesMarkers(markers, {
              executed: cssColor(styles, '--status-positive', '#68d391'),
              selected: cssColor(styles, '--status-warning', '#f6d365'),
              inactive: cssColor(styles, '--text-muted', '#9ca8b8'),
            }),
          )
        : null

    chart.timeScale().fitContent()
    const crosshairHandler = (parameter: MouseEventParams<Time>) => {
      if (parameter.time === undefined) {
        if (onCursorTimeChange && lastCursorTime.current) {
          const snapshot = cursorSnapshotAtTimestamp(series, lastCursorTime.current)
          const anchor = snapshot?.values[0]
          if (snapshot && anchor) {
            applyingSharedCursor.current = true
            chart.setCrosshairPosition(
              anchor.value,
              utcTimestamp(snapshot.timestamp),
              chartSeries[0].api,
            )
            setCursor(snapshot)
            queueMicrotask(() => {
              applyingSharedCursor.current = false
            })
            return
          }
        }
        lastCursorTime.current = null
        setCursor(null)
        if (!applyingSharedCursor.current) onCursorTimeChange?.(null)
        return
      }
      const timestamp = timestampFromChartTime(parameter.time)
      lastCursorTime.current = timestamp
      const values = chartSeries.flatMap(({ definition, api }) => {
        const datum = parameter.seriesData.get(api)
        if (!datum || typeof datum !== 'object' || !('value' in datum)) return []
        const value = datum.value
        return typeof value === 'number'
          ? [{ name: definition.name, unit: definition.unit, value }]
          : []
      })
      setCursor({ timestamp, values })
      if (!applyingSharedCursor.current) onCursorTimeChange?.(timestamp)
    }
    chart.subscribeCrosshairMove(crosshairHandler)
    const visibleRangeHandler = (range: IRange<Time> | null) => {
      if (!applyingSharedRange.current) {
        onVisibleRangeChange?.(fromChartVisibleRange(range))
      }
    }
    chart.timeScale().subscribeVisibleTimeRangeChange(visibleRangeHandler)

    return () => {
      chart.unsubscribeCrosshairMove(crosshairHandler)
      chart.timeScale().unsubscribeVisibleTimeRangeChange(visibleRangeHandler)
      markerPlugin?.detach()
      chart.remove()
      chartRef.current = null
      seriesRef.current = []
    }
  }, [
    height,
    markers,
    onCursorTimeChange,
    onVisibleRangeChange,
    series,
  ])

  useEffect(() => {
    const chart = chartRef.current
    const firstSeries = seriesRef.current[0]
    if (!chart || !firstSeries || sharedCursorTime === undefined) return
    applyingSharedCursor.current = true
    if (sharedCursorTime === null) {
      lastCursorTime.current = null
      chart.clearCrosshairPosition()
      setCursor(null)
    } else {
      const snapshot = cursorSnapshotAtTimestamp(series, sharedCursorTime)
      const anchor = snapshot?.values[0]
      if (snapshot && anchor) {
        lastCursorTime.current = snapshot.timestamp
        chart.setCrosshairPosition(
          anchor.value,
          utcTimestamp(snapshot.timestamp),
          firstSeries,
        )
        setCursor(snapshot)
      } else {
        lastCursorTime.current = null
        chart.clearCrosshairPosition()
        setCursor(null)
      }
    }
    queueMicrotask(() => {
      applyingSharedCursor.current = false
    })
  }, [series, sharedCursorTime])

  useEffect(() => {
    const chart = chartRef.current
    if (!chart || sharedVisibleRange == null) return
    applyingSharedRange.current = true
    chart.timeScale().setVisibleRange(toChartVisibleRange(sharedVisibleRange))
    queueMicrotask(() => {
      applyingSharedRange.current = false
    })
  }, [sharedVisibleRange])

  return (
    <figure className="time-series-chart" aria-labelledby={titleId}>
      <figcaption>
        <h3 id={titleId}>{title}</h3>
        <p>{description}</p>
        <ul className="chart-legend" aria-label={`${title} series`}>
          {series.map((item) => {
            const last = item.points.at(-1)
            return (
              <li key={item.name}>
                {item.name} ({item.unit}) - latest {last?.value ?? 'unavailable'}
              </li>
            )
          })}
        </ul>
      </figcaption>
      <div className="chart-canvas" ref={containerRef} style={{ height }} />
      <div className="chart-tooltip" role="status">
        {cursor ? (
          <>
            <strong>{cursor.timestamp}</strong>
            {cursor.values.map((item) => (
              <span key={item.name}>
                {item.name}: {item.value} {item.unit}
              </span>
            ))}
          </>
        ) : (
          <span>Move across the chart to inspect timestamped values.</span>
        )}
      </div>
    </figure>
  )
}
