import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { LabCompareTable } from './LabCompareTable'
import type { LabAnalysis } from './labContract'
import type { LabCompareResult, LabStudy, LabStudySettings } from './labStudyApi'

afterEach(cleanup)

function fullSettings(overrides: Partial<LabStudySettings>): LabStudy['result']['applied_settings'] {
  return {
    method: 'zscore',
    auto_tune: true,
    lookback: 96,
    entry: 2.0,
    exit: 0.5,
    hedge_method: 'ratio',
    starting_value: '10000',
    initial_weight: '0.5',
    rotation_size: '0.5',
    minimum_hold: 4,
    cooldown: 4,
    fee_bps: '10',
    slippage_bps: '5',
    volume_impact_bps: '10',
    minimum_notional: '1',
    cost_budget_multiple: '2',
    anchor_threshold: 0.002,
    copula_probability: 0.05,
    copula_exit_band: 0.15,
    trend_deadband: 0.002,
    crash_defense_mode: 'coins_only',
    regime_break_drawdown: 0.15,
    fast_window: 12,
    slow_window: 48,
    proof_fraction: 0.3,
    folds: 8,
    minimum_passing_folds: 5,
    minimum_trades: 10,
    significance: 0.05,
    ...overrides,
  } as LabStudy['result']['applied_settings']
}

function makeAnalysis(): LabAnalysis {
  return {
    schema_version: 'qap.api.pair-rotation-analysis.v1',
    coin_a: { id: 'binance:PIXEL', code: 'PIXEL', name: 'Pixels', identity_state: 'resolved' },
    coin_b: { id: 'binance:W', code: 'W', name: 'Wormhole', identity_state: 'resolved' },
    anchor: null,
    identity_confirmed: true,
    bar: '1h',
    window_days: 180,
    band_lookback: 168,
    data_through: '2026-11-16T00:00:00Z',
    bars_used: 4320,
    latest_ratio: 0.39,
    anchor_ranking: [],
    series: {
      time: [1],
      close_a: [0.039],
      close_b: [0.1],
      ratio: [0.39],
      mean: [0.39],
      std: [0.01],
      anchor_close: null,
    },
    measurements: {
      correlation: null,
      cointegration: null,
      hedge_ratio: null,
      half_life: null,
      hurst: null,
      ratio_percentile: null,
      regime: null,
      anchor_a: null,
      anchor_b: null,
      kalman: null,
      granger: null,
      copula: null,
      rolling_dependence: null,
    },
    datasets: [],
  } as unknown as LabAnalysis
}

function makeStudy(
  studyId: string,
  method: 'zscore' | 'copula' | 'trend',
  hedgeMethod: 'kalman' | 'ols' | 'ratio',
  lookback: number,
  ending: number,
): LabStudy {
  const settings = fullSettings({ method, hedge_method: hedgeMethod, lookback })
  return {
    study_id: studyId,
    created_at: '2026-11-16T00:00:00Z',
    pinned: false,
    result: {
      schema_version: 'qap.lab.study.v1',
      analysis: makeAnalysis(),
      requested_settings: settings,
      applied_settings: settings,
      call: {
        status: 'insufficient_history',
        headline: 'No reliable edge right now',
        reason: 'Sample reason',
        target_weight_a: null,
        rotation_fraction: null,
      },
      proof: {
        passes: false,
        data_role: 'validation',
        final_oos_used: false,
        validation_reused: false,
        settings_tried: 3,
        control: 'weekly',
        raw_p_value: 0.08,
        corrected_p_value: 0.08,
        significance: 0.05,
        folds_passing: 5,
        folds_total: 8,
        minimum_passing_folds: 5,
        validation_trades: 24,
        minimum_trades: 10,
        vs_hodl_pct: 12.5,
        vs_control_pct: 6.2,
        cost_paid_pct: 1.2,
        gross_vs_hodl_pct: 13.7,
        tuning_start: '2026-04-01T00:00:00Z',
        tuning_end: '2026-07-01T00:00:00Z',
        proof_start: '2026-07-02T00:00:00Z',
        proof_end: '2026-11-16T00:00:00Z',
        correction: 'Holm-Bonferroni',
        limitations: [],
        cost_gate_passed: true,
        tuning_cost_pct: null,
        tuning_gross_vs_hodl_pct: null,
      },
      statistics: {
        strategy: {
          terminal_value_usdt: String(ending),
          return_pct: 11.4,
          maximum_drawdown_pct: -4.2,
          rotations: 24,
          executed_legs: 48,
          fees_usdt: '120',
          slippage_usdt: '30',
          terminal_holdings: {},
        },
      },
      wealth: {
        time: [1],
        value: { strategy: [ending], hodl: [10000], weekly: [10200], hold_a: [9800], hold_b: [9700] },
        coins_a: { strategy: [100], hodl: [100], weekly: [100], hold_a: [100], hold_b: [100] },
        coins_b: { strategy: [100], hodl: [100], weekly: [100], hold_a: [100], hold_b: [100] },
        terminal_values: { strategy: String(ending), hodl: '10000', weekly: '10200', hold_a: '9800', hold_b: '9700' },
        window_kind: 'validation',
      },
      trades: [],
      folds: [],
      signal: { time: [1], values: [0], upper: 2, lower: -2, unit: 'sigma' },
      code_fingerprint: 'abcdef',
      execution_route: 'two legs via USDT',
      execution_metadata: [],
    },
  }
}

describe('LabCompareTable', () => {
  it('displays matching preset names to distinguish multiple presets sharing one method', () => {
    const studyA = makeStudy('s1', 'zscore', 'kalman', 409, 11146.93)
    const studyB = makeStudy('s2', 'copula', 'ratio', 96, 8289.37)
    const studyC = makeStudy('s3', 'zscore', 'ols', 120, 5325.52)

    const compare: LabCompareResult = {
      best_study_id: 's1',
      studies: [studyA, studyB, studyC],
      advisor: {
        regime_label: 'mean_reverting',
        simple_summary: 'Mean-reversion rotation presets are favored.',
        pro_summary: 'Regime=mean_reverting',
        bar_warning: null,
        suggestions: [
          {
            rank: 1,
            preset_id: 'kalman_zscore',
            title: 'Drawdown-Shielded Kalman Reversion',
            simple_reason: 'Tracks shifting spread.',
            pro_reason: 'Kalman 409',
            recommended_bar: '1h',
            recommended_anchor: null,
            settings: fullSettings({ method: 'zscore', hedge_method: 'kalman', lookback: 409 }),
          },
          {
            rank: 2,
            preset_id: 'copula_tail',
            title: '4h Tail Copula + Benchmark Defense',
            simple_reason: 'Waits for 2% tails.',
            pro_reason: 'Copula 96',
            recommended_bar: '4h',
            recommended_anchor: null,
            settings: fullSettings({ method: 'copula', hedge_method: 'ratio', lookback: 96 }),
          },
          {
            rank: 3,
            preset_id: 'conservative_ols',
            title: 'Conservative Wide-Band OLS (2.5σ)',
            simple_reason: 'Wide bands.',
            pro_reason: 'OLS 120',
            recommended_bar: '1h',
            recommended_anchor: null,
            settings: fullSettings({ method: 'zscore', hedge_method: 'ols', lookback: 120 }),
          },
        ],
      },
    }

    const onOpenStudy = vi.fn()
    render(<LabCompareTable compare={compare} onOpenStudy={onOpenStudy} onClose={vi.fn()} />)

    expect(screen.getByText('Drawdown-Shielded Kalman Reversion')).toBeVisible()
    expect(screen.getByText('4h Tail Copula + Benchmark Defense')).toBeVisible()
    expect(screen.getByText('Conservative Wide-Band OLS (2.5σ)')).toBeVisible()
    expect(screen.getByText('zscore · kalman · 409')).toBeVisible()
    expect(screen.getByText('zscore · ols · 120')).toBeVisible()

    fireEvent.click(screen.getAllByRole('button', { name: 'Inspect' })[0]!)
    expect(onOpenStudy).toHaveBeenCalledWith('s1')
  })
})
