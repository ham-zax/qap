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

const SERIES_COLORS = ['#78a9ff', '#68d391', '#f6d365', '#c4a7e7', '#ff9b9b']
const EMPTY_MARKERS: readonly ChartMarker[] = Object.freeze([])

function toSeriesMarkers(
  markers: readonly ChartMarker[],
): SeriesMarker<UTCTimestamp>[] {
  return markers
    .map((marker) => ({
      time: utcTimestamp(marker.timestamp),
      position: 'aboveBar' as const,
      shape: marker.executed ? ('arrowUp' as const) : ('square' as const),
      color: marker.executed
        ? '#68d391'
        : marker.selected
          ? '#f6d365'
          : '#aeb8c7',
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
  const [cursor, setCursor] = useState<CursorSnapshot | null>(null)
  const titleId = useId()

  useEffect(() => {
    const container = containerRef.current
    if (!container || typeof ResizeObserver === 'undefined') return

    const chart = createChart(container, {
      autoSize: true,
      height,
      layout: {
        attributionLogo: true,
        background: { type: ColorType.Solid, color: '#121720' },
        textColor: '#aeb8c7',
      },
      grid: {
        horzLines: { color: '#242d3b' },
        vertLines: { color: '#242d3b' },
      },
      rightPriceScale: {
        borderColor: '#303a4a',
      },
      timeScale: {
        borderColor: '#303a4a',
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
        color: SERIES_COLORS[index % SERIES_COLORS.length],
        lineWidth: 2,
        title: `${definition.name} (${definition.unit})`,
      })
      api.setData(toLightweightChartData(definition.points))
      return { definition, api }
    })
    seriesRef.current = chartSeries.map((item) => item.api)

    const markerPlugin =
      markers.length > 0 && chartSeries[0]
        ? createSeriesMarkers(chartSeries[0].api, toSeriesMarkers(markers))
        : null

    chart.timeScale().fitContent()
    const crosshairHandler = (parameter: MouseEventParams<Time>) => {
      if (parameter.time === undefined) {
        setCursor(null)
        if (!applyingSharedCursor.current) onCursorTimeChange?.(null)
        return
      }
      const timestamp = timestampFromChartTime(parameter.time)
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
      chart.clearCrosshairPosition()
    } else {
      const point = series[0]
        ? findPresentationPointAtTimestamp(
            series[0].points,
            sharedCursorTime,
          )
        : undefined
      if (point) {
        chart.setCrosshairPosition(
          point.value,
          utcTimestamp(sharedCursorTime),
          firstSeries,
        )
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
      <div className="chart-canvas" ref={containerRef} />
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
