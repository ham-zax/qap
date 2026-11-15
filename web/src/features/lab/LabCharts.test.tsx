import { act, fireEvent, render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { TimeSeriesChart } from '../../components/charts/TimeSeriesChart'
import type { ChartVisibleRange } from '../../components/charts/chartData'
import { LabCharts } from './LabCharts'
import type { LabAnalysis, LabBar } from './labContract'

vi.mock('../../components/charts/TimeSeriesChart', () => ({
  TimeSeriesChart: vi.fn(() => null),
}))

function analysis(bar: LabBar = '15m'): LabAnalysis {
  const minutes = { '15m': 15, '1h': 60, '4h': 240, '1d': 1440 }[bar]
  const count = 180 * 1440 / minutes
  const end = Date.parse('2026-10-24T00:00:00Z') / 1000
  const time = Array.from({ length: count }, (_, i) => end - (count - i - 1) * minutes * 60)
  const values = time.map((_, i) => 5 + i / count)
  return {
    schema_version: 'qap.api.pair-rotation-analysis.v1',
    coin_a: { id: 'binance:BTC', code: 'BTC', name: 'Bitcoin', identity_state: 'resolved' },
    coin_b: { id: 'binance:W', code: 'W', name: 'Wormhole', identity_state: 'resolved' },
    bar, window_days: 180, band_lookback: 672, data_through: '2026-10-24T00:00:00Z', bars_used: count,
    identity_confirmed: true,
    anchor: { id: 'binance:ETH', code: 'ETH', name: 'Ethereum', identity_state: 'resolved' },
    anchor_ranking: [],
    series: { time, close_a: values, close_b: values, ratio: values, mean: values, std: values, anchor_close: values },
    measurements: { correlation: null, cointegration: null, hedge_ratio: null, half_life: null, hurst: null, ratio_percentile: 100, regime: null, anchor_a: null, anchor_b: null, kalman: null, granger: null, copula: null, rolling_dependence: null },
    datasets: [],
  }
}

function chartProps() {
  const calls = vi.mocked(TimeSeriesChart).mock.calls
  const props = calls.at(-1)?.[0]
  if (!props?.onVisibleRangeChange) throw new Error('Relationship chart must report its visible range')
  return props
}

function reportRange(range: ChartVisibleRange | null) {
  act(() => chartProps().onVisibleRangeChange!(range))
}

const latestRange = { from: '2026-10-09T00:00:00Z', to: '2026-10-24T00:00:00Z' }

beforeEach(() => vi.clearAllMocks())

describe('LabCharts visible dates', () => {
  it('explains the empty wealth chart and names the relationship lines', () => {
    render(<LabCharts analysis={analysis()} />)
    expect(screen.getByText('Not tested yet')).toBeVisible()
    expect(screen.getByText('After a test, this chart shows your money over time for rotating, just holding, and a simple scheduled rebalance.')).toBeVisible()
    expect(chartProps().series.map((series) => series.name)).toEqual([
      'BTC per W', 'Usual level', 'Normal range, bottom', 'Normal range, top', 'ETH',
    ])
  })

  it.each(['15m', '1h', '4h', '1d'] as const)('shows actual visible dates for %s without removing points', (bar) => {
    const data = analysis(bar)
    render(<LabCharts analysis={data} />)
    expect(screen.queryByText(/^Showing /)).not.toBeInTheDocument()
    const props = chartProps()
    expect(props.series).toHaveLength(5)
    for (const series of props.series) expect(series.points).toHaveLength(data.bars_used)

    reportRange(latestRange)

    expect(screen.getByText('Showing 9 Oct 2026–24 Oct 2026 (UTC). Scroll or drag for earlier data.')).toBeVisible()
    // Updating the caption must not recreate the chart and reset its scroll position.
    expect(chartProps().series).toBe(props.series)
    expect(chartProps().onVisibleRangeChange).toBe(props.onVisibleRangeChange)
  })

  it('updates after scrolling and removes the earlier-data hint at the start', () => {
    const data = analysis()
    render(<LabCharts analysis={data} />)
    reportRange(latestRange)
    reportRange({ from: '2026-09-01T00:00:00Z', to: '2026-09-16T00:00:00Z' })
    expect(screen.getByText('Showing 1 Sept 2026–16 Sept 2026 (UTC). Scroll or drag for earlier data.')).toBeVisible()
    expect(screen.queryByText(/Showing 9 Oct/)).not.toBeInTheDocument()

    reportRange({ from: new Date(data.series.time[0]! * 1000).toISOString(), to: data.data_through })
    expect(screen.getByText(/^Showing /)).not.toHaveTextContent('Scroll or drag for earlier data.')
  })

  it('uses UTC dates and includes years across a year boundary', () => {
    render(<LabCharts analysis={analysis()} />)
    reportRange({ from: '2025-12-31T23:30:00-02:00', to: '2027-01-01T00:00:00Z' })
    expect(screen.getByText(/^Showing /)).toHaveTextContent('Showing 1 Jan 2026–1 Jan 2027 (UTC).')
  })

  it('clears the caption when the chart reports no visible range', () => {
    render(<LabCharts analysis={analysis()} />)
    reportRange(latestRange)
    reportRange(null)
    expect(screen.queryByText(/^Showing /)).not.toBeInTheDocument()
  })

  it('tracks the recreated chart after bands or anchor change', () => {
    render(<LabCharts analysis={analysis()} />)
    reportRange(latestRange)
    fireEvent.click(screen.getByRole('checkbox', { name: 'Usual level and normal range' }))
    expect(chartProps().series.map((series) => series.name)).toEqual(['BTC per W', 'ETH'])
    expect(screen.queryByText(/^Showing /)).not.toBeInTheDocument()
    reportRange(latestRange)
    expect(screen.getByText(/^Showing /)).toBeVisible()

    fireEvent.click(screen.getByRole('checkbox', { name: 'Anchor' }))
    expect(chartProps().series.map((series) => series.name)).toEqual(['BTC per W'])
    reportRange({ from: '2026-10-20T00:00:00Z', to: latestRange.to })
    expect(screen.getByText(/^Showing /)).toHaveTextContent('Showing 20 Oct 2026–24 Oct 2026 (UTC).')
  })

  it('does not retain the old range when analysis changes and works without an anchor', () => {
    const first = render(<LabCharts analysis={analysis()} />)
    reportRange(latestRange)
    const next = { ...analysis('1d'), anchor: null }
    first.rerender(<LabCharts analysis={next} />)
    expect(screen.queryByText(/^Showing /)).not.toBeInTheDocument()
    expect(screen.getByRole('checkbox', { name: 'Anchor' })).toBeDisabled()
    reportRange(latestRange)
    expect(screen.getByText(/^Showing /)).toBeVisible()
  })
})
