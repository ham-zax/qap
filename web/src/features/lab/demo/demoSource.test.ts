import { describe, expect, it } from 'vitest'
import { demoAnalysis } from './demoSource'

describe('Sample benchmark selection', () => {
  it('keeps None distinct from automatic selection', () => {
    const request = { coin_a: 'binance:ARB', coin_b: 'binance:OP', bar: '1d' as const, days: 30 as const, band_lookback: 14 }
    const direct = demoAnalysis({ ...request, anchor: 'none' })
    expect(direct.anchor).toBeNull()
    expect(direct.series.anchor_close).toBeNull()
    expect(direct.measurements.anchor_a).toBeNull()
    expect(demoAnalysis({ ...request, anchor: null }).anchor).not.toBeNull()
  })
})
