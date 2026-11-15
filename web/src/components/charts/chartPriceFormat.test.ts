import { describe, expect, it } from 'vitest'
import { chartPriceFormat } from './chartData'

describe('Chart price precision', () => {
  it('keeps small crypto ratios distinguishable from zero', () => {
    const format = chartPriceFormat([
      { timestamp: '2026-01-01', value: 0.000001 },
      { timestamp: '2026-01-02', value: 0.000002 },
    ])
    expect((0.000001).toFixed(format.precision)).not.toBe((0.000002).toFixed(format.precision))
    expect(format.minMove).toBeLessThan(0.000001)
  })

  it('retains tiny changes around a larger price', () => {
    const format = chartPriceFormat([
      { timestamp: '2026-01-01', value: 1 },
      { timestamp: '2026-01-02', value: 1.0000001 },
    ])
    expect((1).toFixed(format.precision)).not.toBe((1.0000001).toFixed(format.precision))
  })
})
