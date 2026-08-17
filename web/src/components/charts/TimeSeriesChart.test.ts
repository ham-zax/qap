import { describe, expect, it } from 'vitest'

import {
  exactPointsToPresentation,
  findPresentationPointAtTimestamp,
  fromChartVisibleRange,
  toChartVisibleRange,
  toLightweightChartData,
} from './chartData'

describe('TimeSeriesChart data mapping', () => {
  it('converts exact API strings only at the presentation boundary', () => {
    const exact = [
      { timestamp: '2025-01-01T00:00:00Z', value: '0.00000000000000000001' },
      { timestamp: '2025-01-01T01:00:00Z', value: '-0.0125' },
    ]

    const presentation = exactPointsToPresentation(exact)

    expect(exact[0]?.value).toBe('0.00000000000000000001')
    expect(presentation).toEqual([
      { timestamp: '2025-01-01T00:00:00Z', value: 1e-20 },
      { timestamp: '2025-01-01T01:00:00Z', value: -0.0125 },
    ])
  })

  it('maps ISO timestamps to ordered UTC chart points', () => {
    const mapped = toLightweightChartData([
      { timestamp: '2025-01-01T00:00:00Z', value: 1.5 },
      { timestamp: '2025-01-01T01:00:00Z', value: 2.5 },
    ])

    expect(mapped).toEqual([
      { time: 1735689600, value: 1.5 },
      { time: 1735693200, value: 2.5 },
    ])
  })

  it('matches synchronized cursors by instant instead of ISO formatting', () => {
    const point = { timestamp: '2025-01-01T00:00:00Z', value: 1.5 }

    expect(
      findPresentationPointAtTimestamp(
        [point],
        '2025-01-01T00:00:00.000Z',
      ),
    ).toBe(point)
  })

  it('round-trips synchronized visible ranges through chart time values', () => {
    const range = {
      from: '2025-01-01T00:00:00.000Z',
      to: '2025-01-02T00:00:00.000Z',
    }

    const chartRange = toChartVisibleRange(range)

    expect(chartRange).toEqual({ from: 1735689600, to: 1735776000 })
    expect(fromChartVisibleRange(chartRange)).toEqual(range)
    expect(fromChartVisibleRange(null)).toBeNull()
  })

  it('rejects invalid timestamps and non-finite presentation values', () => {
    expect(() =>
      toLightweightChartData([{ timestamp: 'not-a-date', value: 1 }]),
    ).toThrow('valid ISO timestamp')
    expect(() =>
      exactPointsToPresentation([
        { timestamp: '2025-01-01T00:00:00Z', value: 'Infinity' },
      ]),
    ).toThrow('finite presentation number')
  })
})
