import { render, screen, within } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { LabDiagnosticsTab } from './LabDiagnosticsTab'
import { LabLivePaperPanel } from './LabLivePaperPanel'
import { LabSignalChart } from './LabSignalChart'
import type { LivePaperSession } from './labPaperApi'
import type { LabStudy } from './labStudyApi'

vi.mock('../../components/charts/TimeSeriesChart', () => ({
  TimeSeriesChart: ({
    title,
    description,
    series,
  }: {
    title: string
    description?: string
    series: Array<{ name: string; points: Array<{ value: number }> }>
  }) => (
    <div role="img" aria-label={title} data-description={description ?? ''}>
      <span>{description}</span>
      <span data-testid="series-values">
        {series.map((s) => `${s.name}:${s.points.map((p) => p.value).join(',')}`).join('|')}
      </span>
    </div>
  ),
}))

function basePaperSession(overrides: Partial<LivePaperSession> = {}): LivePaperSession {
  return {
    schema_version: 'qap.lab.paper_session.v2',
    session_id: 'paper-v2',
    actor_id: 'local',
    status: 'active',
    can_step: true,
    step_block_reason: null,
    track_record_mode: 'continuous_forward',
    created_at: '2026-11-16T00:00:00Z',
    updated_at: '2026-11-16T00:05:00Z',
    stopped_at: null,
    coin_a: 'binance:BTC',
    coin_b: 'binance:ETH',
    anchor: 'binance:SOL',
    anchor_mode: 'auto',
    bar: '4h',
    order_rtt_ms: 75,
    max_staleness_ms: 500,
    settings: { method: 'copula' } as unknown as LivePaperSession['settings'],
    decisions_count: 0,
    book_observations_count: 2,
    candle_origin_time: 1794700000,
    last_candle_time: 1794787200,
    pending_target: null,
    market_metadata_provenance: {},
    simple_status: 'Active paper session tracking BTC/ETH.',
    vs_hodl_pct: 0,
    vs_control_pct: 0,
    portfolios: {
      strategy: {
        holdings: { BTC: '0.05', ETH: '1.5' },
        value_usdt: '10000',
        return_pct: 0,
        fees_usdt: '0',
        slippage_usdt: '0',
        rotations: 0,
      },
      hodl: {
        holdings: { BTC: '0.05', ETH: '1.5' },
        value_usdt: '10000',
        return_pct: 0,
        fees_usdt: '0',
        slippage_usdt: '0',
        rotations: 0,
      },
      drift_control: {
        holdings: { BTC: '0.05', ETH: '1.5' },
        value_usdt: '10000',
        return_pct: 0,
        fees_usdt: '0',
        slippage_usdt: '0',
        rotations: 0,
      },
    },
    trades: [],
    latency_audit: [
      {
        step_index: 0,
        attempt_index: 2,
        observation_type: 'book_retry',
        execution_status: 'hold',
        t_exch_us: 1794787200000000,
        t_recv_ns: 1794787200030000000,
        t_decide_ns: 1794787200032000000,
        t_fill_leg1_ns: 1794787200107000000,
        t_fill_leg2_ns: 1794787200182000000,
        actual_fill_leg1_ns: null,
        actual_fill_leg2_ns: null,
        legacy_clock: false,
        order_rtt_ms: 75,
        recv_to_decide_ms: 2.0,
        decide_to_fill_leg1_ms: 75.0,
        decide_to_fill_leg2_ms: 150.0,
        actual_decide_to_fill_leg1_ms: null,
        actual_decide_to_fill_leg2_ms: null,
        book_age_leg1_ms: null,
        book_age_leg2_ms: null,
        signal_preference: null,
        action: 'hold',
        rejected_reasons: [],
      },
    ],
    ...overrides,
  }
}

describe('AR-8 Lab recovery, timing, and provenance states', () => {
  it('shows duplicate-candle book checks without advancing candle decisions or fabricating fills', () => {
    render(
      <LabLivePaperPanel
        session={basePaperSession({ decisions_count: 0, book_observations_count: 3 })}
        busy={false}
        error={null}
        canStart
        onStart={vi.fn()}
        onStep={vi.fn()}
        onStop={vi.fn()}
      />,
    )

    expect(screen.getByText('3 book checks')).toBeVisible()
    expect(screen.getByText('0 / 0')).toBeVisible()
    const latency = screen.getByLabelText('Execution latencies')
    expect(within(latency).getByText('Configured RTT (75 ms) vs Measured Simulation Delay')).toBeVisible()
    expect(within(latency).getAllByText('No fill')).toHaveLength(2)
  })

  it('shows partial execution recovery banner and measured delayed fill timings', () => {
    render(
      <LabLivePaperPanel
        session={basePaperSession({
          decisions_count: 1,
          pending_target: {
            target_id: 'paper-v2-t1-1',
            target_weights: { ETH: '1.0', USDT: '0.0' },
            status: 'partial',
            reason: 'signal_rotation',
            attempts: 1,
            fills_count: 1,
          },
          latency_audit: [
            {
              ...basePaperSession().latency_audit[0]!,
              step_index: 1,
              observation_type: 'new_candle',
              execution_status: 'partial',
              actual_fill_leg1_ns: 1794787200882000000,
              actual_fill_leg2_ns: null,
              actual_decide_to_fill_leg1_ms: 850.0,
              actual_decide_to_fill_leg2_ms: null,
              book_age_leg1_ms: 0.0,
              action: 'swap',
              rejected_reasons: ['stale_leg2'],
            },
          ],
        })}
        busy={false}
        error={null}
        canStart
        onStart={vi.fn()}
        onStep={vi.fn()}
        onStop={vi.fn()}
      />,
    )

    expect(screen.getByText(/Partial rotation pending retry \(partial, 1 fill\(s\) recorded\)/)).toBeVisible()
    expect(screen.getByRole('button', { name: 'Retry Pending Swap' })).toBeVisible()
    expect(screen.getByText('850.0 ms')).toBeVisible()
    expect(screen.getByText('No fill')).toBeVisible()
  })

  it('blocks stepping for legacy v1 sessions and offers recovery actions', () => {
    render(
      <LabLivePaperPanel
        session={basePaperSession({
          schema_version: 'qap.lab.paper_session.v1',
          can_step: false,
          step_block_reason: 'Legacy v1 paper session uses untimed closes. Start a new session.',
          latency_audit: [
            {
              ...basePaperSession().latency_audit[0]!,
              legacy_clock: true,
              decide_to_fill_leg1_ms: 75.0,
              decide_to_fill_leg2_ms: 150.0,
            },
          ],
        })}
        busy={false}
        error={null}
        canStart
        onStart={vi.fn()}
        onStep={vi.fn()}
        onStop={vi.fn()}
      />,
    )

    expect(screen.getByText(/Legacy v1 paper session uses untimed closes/)).toBeVisible()
    expect(screen.getByText('Legacy nominal clock')).toBeVisible()
    expect(screen.queryByRole('button', { name: 'Step 3s' })).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Stop Session' })).toBeVisible()
    expect(screen.getByRole('button', { name: 'Start New Session' })).toBeVisible()
  })

  it('displays stitched walk-forward signal provenance and distinguishes legacy studies', () => {
    const { rerender } = render(
      <LabSignalChart
        signal={{
          time: [1794787200, 1794801600],
          values: [1.7, 2.5],
          upper: 2.4,
          lower: -2.4,
          upper_series: [1.6, 2.4],
          lower_series: [-1.6, -2.4],
          unit: 'z-score',
          provenance: 'walk_forward_stitched',
          signal_variable: 'ols log-price residual z-score',
        }}
      />,
    )
    expect(screen.getByText(/Walk-forward stitched executed signal: ols log-price residual z-score/)).toBeVisible()
    expect(screen.getByTestId('series-values')).toHaveTextContent('Upper trigger:1.6,2.4')

    rerender(
      <LabSignalChart
        signal={{
          time: [1794787200, 1794801600],
          values: [1.7, 2.5],
          upper: 2.0,
          lower: -2.0,
          unit: 'z-score',
        }}
      />,
    )
    expect(screen.getByText(/Legacy saved study \(signal provenance not recorded\)/)).toBeVisible()

    const minimalStudy = {
      study_id: 's1',
      created_at: '2026-11-16T00:00:00Z',
      pinned: false,
      result: {
        folds: [],
        proof: {
          passes: false,
          data_role: 'validation',
          final_oos_used: false,
          validation_reused: false,
          settings_tried: 1,
          control: 'weekly',
          raw_p_value: 0.42,
          corrected_p_value: 0.42,
          significance: 0.05,
          folds_passing: 2,
          folds_total: 8,
          minimum_passing_folds: 5,
          validation_trades: 10,
          minimum_trades: 10,
          vs_hodl_pct: -1.0,
          vs_control_pct: -1.0,
          cost_paid_pct: 1.5,
          gross_vs_hodl_pct: 0.5,
          cost_gate_passed: false,
          tuning_cost_pct: 1.2,
          tuning_gross_vs_hodl_pct: 0.8,
          tuning_start: '2026-01-01T00:00:00Z',
          tuning_end: '2026-06-01T00:00:00Z',
          proof_start: '2026-06-01T00:00:00Z',
          proof_end: '2026-11-01T00:00:00Z',
          correction: 'SPA',
          limitations: [],
        },
      },
    } as unknown as LabStudy

    render(<LabDiagnosticsTab analysis={null} study={minimalStudy} viewMode="advanced" />)
    expect(screen.getByText(/Legacy \(missing stitched provenance\)/)).toBeVisible()
  })
})
