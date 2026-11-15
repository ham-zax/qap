import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { LabEvidence } from './LabEvidence'
import type { LabAnalysis, LabMeasurements } from './labContract'

const empty: LabMeasurements = {
  correlation: null, cointegration: null, hedge_ratio: null, half_life: null, hurst: null, ratio_percentile: 50,
  regime: null, anchor_a: null, anchor_b: null, kalman: null, granger: null, copula: null, rolling_dependence: null,
}

function analysis(measurements: Partial<LabMeasurements> = {}): LabAnalysis {
  return {
    schema_version: 'qap.api.pair-rotation-analysis.v1',
    coin_a: { id: 'binance:BTC', code: 'BTC', name: 'Bitcoin', identity_state: 'resolved' },
    coin_b: { id: 'binance:ETH', code: 'ETH', name: 'Ethereum', identity_state: 'resolved' },
    bar: '1h', window_days: 90, band_lookback: 168, data_through: '2026-10-24T00:00:00Z', bars_used: 2160,
    identity_confirmed: true, anchor: null, anchor_ranking: [],
    series: { time: [], close_a: [], close_b: [], ratio: [], mean: [], std: [], anchor_close: null },
    measurements: { ...empty, ...measurements },
    datasets: [],
  }
}

const reading = (label: string) => screen.getByText(label, { selector: '.lab-reading-label' }).parentElement?.querySelector('.lab-reading-value')?.textContent

describe('LabEvidence dependence readings', () => {
  it('renders Kalman, both Granger directions, copula tails and rolling correlation', () => {
    render(<LabEvidence analysis={analysis({
      kalman: { beta: 1.25, standard_error: 0.02, beta_change: -0.1 },
      granger: {
        a_to_b: { lag_bars: 2, p_value: 0.012, passes: true },
        b_to_a: { lag_bars: 1, p_value: 0.8, passes: false },
        max_lag: 4, observations: 2159,
      },
      copula: { family: 'student', lower_tail: 0.31, upper_tail: 0.31, observations: 2158 },
      rolling_dependence: { window_bars: 168, latest: 0.82, low: 0.4, high: 0.93 },
    })} />)
    expect(reading('Balance ratio today')).toBe('1.25 ± 0.02, moved -0.1')
    expect(reading('BTC moves first')).toBe('p = 0.012 at lag 2')
    expect(reading('ETH moves first')).toBe('p = 0.8 at lag 1')
    expect(reading('Crash or jump together')).toBe('down 0.31, up 0.31')
    expect(screen.getByText('Copula tail dependence (student family), fitted on the latest 2158 returns.')).not.toBeNull()
    expect(reading('Recent togetherness')).toBe('0.82, range 0.4 to 0.93')
    expect(screen.queryByText(/not available in this slice/)).toBeNull()
  })

  it('shows unavailable fits as Unavailable, never as zero', () => {
    render(<LabEvidence analysis={analysis()} />)
    for (const label of ['Balance ratio today', 'BTC moves first', 'ETH moves first', 'Crash or jump together', 'Recent togetherness']) {
      expect(reading(label)).toBe('Unavailable')
    }
  })
})
