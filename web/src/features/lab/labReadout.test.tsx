import { act, render, screen, within } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { TimeSeriesChart } from '../../components/charts/TimeSeriesChart'
import { LabCharts } from './LabCharts'
import type { LabAnalysis } from './labContract'
import { barIndexAt, ratioReadout, wealthReadout, zScore, type LabWealth } from './labReadout'

vi.mock('../../components/charts/TimeSeriesChart', () => ({ TimeSeriesChart: vi.fn(() => null) }))

const T0 = Date.parse('2026-10-01T00:00:00Z') / 1000
const iso = (index: number) => new Date((T0 + index * 900) * 1000).toISOString()

function analysis(overrides: Partial<LabAnalysis['series']> = {}, anchor = true): LabAnalysis {
  return {
    schema_version: 'qap.api.pair-rotation-analysis.v1',
    coin_a: { id: 'binance:BTC', code: 'BTC', name: 'Bitcoin', identity_state: 'resolved' },
    coin_b: { id: 'binance:ETH', code: 'ETH', name: 'Ethereum', identity_state: 'resolved' },
    bar: '15m', window_days: 30, band_lookback: 2, data_through: iso(3), bars_used: 4, identity_confirmed: true,
    anchor: anchor ? { id: 'binance:SOL', code: 'SOL', name: 'Solana', identity_state: 'resolved' } : null,
    anchor_ranking: [],
    series: {
      time: [0, 1, 2, 3].map((index) => T0 + index * 900),
      close_a: [1, 1, 1, 1], close_b: [1, 1, 1, 1],
      ratio: [20, 21, 22, 23.5],
      mean: [null, 20.5, 21.5, 22],
      std: [null, 0, 0.5, 0.75],
      anchor_close: anchor ? [150, 151.25, 152, 0.5] : null,
      ...overrides,
    },
    measurements: { correlation: null, cointegration: null, hedge_ratio: null, half_life: null, hurst: null, ratio_percentile: 100, regime: null, anchor_a: null, anchor_b: null, kalman: null, granger: null, copula: null, rolling_dependence: null },
    datasets: [],
  }
}

const values = (readout: ReturnType<typeof ratioReadout>) => Object.fromEntries(readout!.rows.map((row) => [row.key, row.value]))
const options = { bands: true, anchor: true }

describe('barIndexAt', () => {
  const times = [10, 20, 30]
  it('returns the latest bar without a timestamp and -1 without bars', () => {
    expect(barIndexAt(times, null)).toBe(2)
    expect(barIndexAt([], null)).toBe(-1)
  })
  it('finds exact bars and falls back to the bar at or before the time', () => {
    expect(barIndexAt(times, new Date(20_000).toISOString())).toBe(1)
    expect(barIndexAt(times, new Date(29_000).toISOString())).toBe(1)
    expect(barIndexAt(times, new Date(1_000).toISOString())).toBe(0)
    expect(barIndexAt(times, new Date(99_000).toISOString())).toBe(2)
  })
})

describe('zScore', () => {
  it('divides the distance from the mean by the deviation', () => {
    expect(zScore(23.5, 22, 0.75)).toBe(2)
    expect(zScore(21, 22, 0.5)).toBe(-2)
  })
  it('is unavailable for a missing or zero deviation', () => {
    expect(zScore(21, 20.5, 0)).toBeNull()
    expect(zScore(20, null, null)).toBeNull()
  })
})

describe('ratioReadout', () => {
  it('shows the latest bar when nothing is hovered', () => {
    const readout = ratioReadout(analysis(), null, options)!
    expect(readout.latest).toBe(true)
    expect(readout.time).toBe('2026-10-01 00:45 UTC')
    expect(values(readout)).toEqual({ ratio: '23.5', mean: '22', upper: '23.5', lower: '20.5', z: '+2.00', anchor: '0.5 USDT' })
    expect(readout.rows[0]!.label).toBe('BTC per ETH')
  })

  it('reads the hovered bar', () => {
    const readout = ratioReadout(analysis(), iso(2), options)!
    expect(readout.latest).toBe(false)
    expect(readout.time).toBe('2026-10-01 00:30 UTC')
    expect(values(readout)).toEqual({ ratio: '22', mean: '21.5', upper: '22.5', lower: '20.5', z: '+1.00', anchor: '152.00 USDT' })
  })

  it('marks warm-up and zero-deviation bars unavailable', () => {
    expect(values(ratioReadout(analysis(), iso(0), options))).toMatchObject({ mean: 'Unavailable', upper: 'Unavailable', lower: 'Unavailable', z: 'Unavailable' })
    expect(values(ratioReadout(analysis(), iso(1), options))).toMatchObject({ mean: '20.5', upper: '20.5', z: 'Unavailable' })
  })

  it('omits the anchor row without an anchor and swatches only drawn lines', () => {
    const readout = ratioReadout(analysis({}, false), null, { bands: false, anchor: false })!
    expect(readout.rows.map((row) => row.key)).toEqual(['ratio', 'mean', 'upper', 'lower', 'z'])
    expect(readout.rows.filter((row) => row.swatch).map((row) => row.key)).toEqual(['ratio'])
  })

  it('returns null for an empty series', () => {
    expect(ratioReadout(analysis({ time: [], ratio: [], mean: [], std: [] }), null, options)).toBeNull()
  })
})

describe('wealthReadout', () => {
  const wealth: LabWealth = {
    time: [T0, T0 + 900, T0 + 1800],
    value: { strategy: [10000, 10100.5, 10250.123], hodl: [10000, 9990, 10100], hold_a: [1, 1, 1], weekly: [10000, 10010, 10050] },
    coins_a: {}, coins_b: {},
    terminal_values: { strategy: '10250.4', hodl: '10100', weekly: '10050' },
    window_kind: 'validation',
  }
  it('shows strategy, HODL and the control for the hovered bar', () => {
    const readout = wealthReadout(wealth, new Date((T0 + 900) * 1000).toISOString())!
    expect(readout.rows.map((row) => [row.label, row.value])).toEqual([
      ['Rotating', '10,100.50 USDT'], ['Just holding', '9,990.00 USDT'], ['Rebalance weekly', '10,010.00 USDT'],
    ])
  })
  it('uses the recorded terminal values on the latest bar', () => {
    expect(wealthReadout(wealth, null)!.rows[0]!.value).toBe('10,250.40 USDT')
  })
})

describe('LabCharts readout', () => {
  beforeEach(() => vi.clearAllMocks())
  const chartProps = () => vi.mocked(TimeSeriesChart).mock.calls.at(-1)![0]

  it('gives screen readers the latest values and follows the hovered bar visually', () => {
    render(<LabCharts analysis={analysis()} />)
    const readout = render(<>{chartProps().readout}</>)
    const sentence = 'BTC per ETH, latest bar 2026-10-01 00:45 UTC: BTC per ETH 23.5, Usual level 22, Normal range, top 23.5, Normal range, bottom 20.5, How unusual +2.00, SOL 0.5 USDT.'
    expect(readout.getByText(sentence).classList.contains('sr-only')).toBe(true)
    expect(readout.getByText('Latest bar')).not.toBeNull()

    act(() => chartProps().onHoverTimeChange!(iso(2)))
    readout.rerender(<>{chartProps().readout}</>)
    const strip = readout.container.querySelector('.lab-readout-strip') as HTMLElement
    expect(strip.getAttribute('aria-hidden')).toBe('true')
    expect(within(strip).getByText('Hovered bar')).not.toBeNull()
    expect(within(strip).getByText('152.00 USDT')).not.toBeNull()
    expect(readout.getByText(sentence)).not.toBeNull()

    act(() => chartProps().onHoverTimeChange!(null))
    readout.rerender(<>{chartProps().readout}</>)
    expect(within(strip).getByText('Latest bar')).not.toBeNull()
    expect(screen.queryByText(/rotate|buy|sell/i)).toBeNull()
  })
})
