import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { LabDashboard } from './LabDashboard'
import type { LabAnalysis } from './labContract'

vi.mock('../../components/charts/TimeSeriesChart', () => ({
  TimeSeriesChart: ({ title, markers }: { title: string; markers?: Array<{ label: string }> }) => (
    <div role="img" aria-label={title} data-markers={markers?.map((m) => m.label).join('|') ?? ''} />
  ),
}))

const coins = [
  { listing_id: 'binance:BTC', venue: 'binance', trading: true, venue_asset_code: 'BTC', name: 'Bitcoin', identity_state: 'resolved', source: 'venue', call_available: true },
  { listing_id: 'binance:ETH', venue: 'binance', trading: true, venue_asset_code: 'ETH', name: 'Ethereum', identity_state: 'resolved', source: 'venue', call_available: true },
  { listing_id: 'binance:SOL', venue: 'binance', trading: true, venue_asset_code: 'SOL', name: 'Solana', identity_state: 'resolved', source: 'venue', call_available: true },
]

function makeAnalysis(): LabAnalysis {
  return {
    schema_version: 'qap.api.pair-rotation-analysis.v1',
    coin_a: { id: 'binance:BTC', code: 'BTC', name: 'Bitcoin', identity_state: 'resolved' },
    coin_b: { id: 'binance:ETH', code: 'ETH', name: 'Ethereum', identity_state: 'resolved' },
    bar: '15m',
    window_days: 180,
    band_lookback: 672,
    data_through: '2026-10-24T00:00:00Z',
    bars_used: 4,
    identity_confirmed: true,
    anchor: { id: 'binance:SOL', code: 'SOL', name: 'Solana', identity_state: 'resolved' },
    anchor_ranking: [],
    series: {
      time: [1790897400, 1790898300, 1790899200, 1790900100],
      close_a: [60000, 60500, 61000, 61500],
      close_b: [3000, 3010, 3020, 3030],
      ratio: [20, 20.1, 20.2, 20.3],
      mean: [null, 20.05, 20.1, 20.15],
      std: [null, 0.05, 0.08, 0.1],
      anchor_close: [150, 151, 152, 153],
    },
    measurements: {
      correlation: { pearson: 0.85, spearman: 0.84, kendall: 0.67, observations: 500 },
      cointegration: { statistic: -3.9, p_value: 0.015, level: 0.05, passes: true },
      hedge_ratio: { ols: 1.02, tls: 1.04, first_half_ols: 1.0, second_half_ols: 1.03, stable: true },
      half_life: { bars: 32, reverting: true },
      hurst: { exponent: 0.41, reading: 'reverting' },
      ratio_percentile: 78,
      regime: { volatility: 'normal', volatility_percentile: 45, trend: 'ranging', efficiency: 0.2 },
      anchor_a: null,
      anchor_b: null,
      kalman: null,
      granger: null,
      copula: null,
      rolling_dependence: null,
    },
    datasets: [{
      dataset_id: 'exact-btc',
      interval: '15m',
      venue_symbol: 'BTCUSDT',
      semantic_fingerprint: 'b'.repeat(64),
      coverage_start: '2026-04-01T00:00:00Z',
      cutoff: '2026-10-24T00:00:00Z',
    }],
  }
}

const json = (value: unknown, status = 200) =>
  new Response(JSON.stringify(value), { status, headers: { 'Content-Type': 'application/json' } })

const advisorPayload = {
  regime_label: 'mean_reverting',
  simple_summary: 'BTC and ETH tend to snap back together after short-term divergences.',
  pro_summary: 'Regime=mean_reverting; coint_p=0.015; half_life_bars=32; hurst=0.41.',
  bar_warning: '15m candles generate high swap counts where fees often exceed gross spread.',
  suggestions: [
    {
      rank: 1,
      preset_id: 'zscore_kalman',
      title: 'Kalman Z-Score Mean Reversion',
      simple_reason: 'Adapts smoothly to gradual shifts in the pair ratio.',
      pro_reason: 'Kalman hedge with lookback=64, entry=2.0, exit=0.4.',
      recommended_bar: '15m',
      recommended_anchor: null,
      settings: { method: 'zscore', hedge_method: 'kalman', lookback: 64, entry: 2.0, exit: 0.4, rotation_size: '0.25', crash_defense_mode: 'park_anchor' },
    },
  ],
}

const studyPayload = {
  study_id: 'study-cockpit-1',
  created_at: '2026-10-24T00:00:00Z',
  pinned: false,
  result: {
    schema_version: 'qap.lab.study.v1',
    analysis: { coin_a: { id: 'binance:BTC', code: 'BTC', name: 'Bitcoin', identity_state: 'resolved' }, coin_b: { id: 'binance:ETH', code: 'ETH', name: 'Ethereum', identity_state: 'resolved' } },
    requested_settings: { method: 'copula', hedge_method: 'ratio', lookback: 120, entry: 2.0, exit: 0.5, rotation_size: '0.25', crash_defense_mode: 'park_usdt' },
    applied_settings: { method: 'copula', hedge_method: 'ratio', lookback: 120, entry: 2.0, exit: 0.5, rotation_size: '0.25', crash_defense_mode: 'park_usdt' },
    call: { status: 'into_a', headline: 'Rotate ETH → BTC', reason: 'Spread tail triggered.', target_weight_a: '0.625', rotation_fraction: '0.25' },
    proof: {
      passes: true, data_role: 'validation', final_oos_used: false, validation_reused: false, settings_tried: 4,
      control: 'weekly', raw_p_value: 0.015, corrected_p_value: 0.025, significance: 0.05, folds_passing: 4,
      folds_total: 5, minimum_passing_folds: 3, validation_trades: 18, minimum_trades: 10, vs_hodl_pct: 3.4,
      vs_control_pct: 1.9, tuning_start: '2026-04-01T00:00:00Z', tuning_end: '2026-07-01T00:00:00Z',
      proof_start: '2026-07-02T00:00:00Z', proof_end: '2026-10-24T00:00:00Z', correction: 'Holm-Bonferroni.', limitations: [],
    },
    signal: {
      time: [1790897400, 1790898300, 1790899200, 1790900100],
      values: [-1.1, -2.3, 0.2, 2.4],
      upper: 2.0,
      lower: -2.0,
      unit: 'sigma',
    },
    wealth: {
      time: [1790897400, 1790898300],
      value: { strategy: [10000, 10340], hodl: [10000, 10000], weekly: [10000, 10150], hold_a: [10000, 10200], hold_b: [10000, 9900] },
      coins_a: { strategy: [0.1666, 0.1723], hodl: [0.1666, 0.1666], weekly: [0.1666, 0.1691], hold_a: [0.1666, 0.1666], hold_b: [0.1666, 0.1650] },
      coins_b: { strategy: [3.3333, 3.4466], hodl: [3.3333, 3.3333], weekly: [3.3333, 3.3833], hold_a: [3.3333, 3.4000], hold_b: [3.3333, 3.3333] },
      terminal_values: { strategy: '10340', hodl: '10000', weekly: '10150', hold_a: '10200', hold_b: '9900' },
      window_kind: 'validation',
    },
    trades: [
      {
        decision_index: 1,
        fill_index: 2,
        time: '2026-10-02T00:15:00Z',
        direction: 'into_a',
        route: 'ETH -> USDT -> BTC',
        fees_usdt: '4.50',
        slippage_usdt: '1.25',
        fills: [{ market: 'ETHUSDT', side: 'sell', base_quantity: '0.5', base_asset: 'binance:ETH', quote_asset: 'binance:USDT', execution_price: '3010', reference_price: '3010', fee: '1.50', fee_asset: 'binance:USDT' }],
      },
    ],
    folds: [{
      fold: 1,
      training_start: '2026-04-01T00:00:00Z',
      training_end: '2026-07-01T00:00:00Z',
      test_start: '2026-07-02T00:00:00Z',
      test_end: '2026-08-01T00:00:00Z',
      strategy_return_pct: 1.8,
      control_return_pct: 0.9,
      passes: true,
    }],
    statistics: {
      strategy: {
        terminal_value_usdt: '10340.00',
        return_pct: 3.4,
        maximum_drawdown_pct: -2.15,
        rotations: 18,
        executed_legs: 36,
        fees_usdt: '42.10',
        slippage_usdt: '11.40',
        terminal_holdings: { 'binance:BTC': '0.112', 'binance:ETH': '1.24' },
      },
    },
    code_fingerprint: 'abcdef1234567890',
    execution_route: 'two legs via USDT',
    execution_metadata: [],
  },
}

const activePaperSession = {
  session_id: 'paper-1',
  actor_id: 'local',
  status: 'active',
  created_at: '2026-10-24T00:00:00Z',
  updated_at: '2026-10-24T00:01:00Z',
  stopped_at: null,
  coin_a: 'binance:BTC',
  coin_b: 'binance:ETH',
  anchor: null,
  bar: '15m',
  order_rtt_ms: 75,
  max_staleness_ms: 500,
  settings: studyPayload.result.applied_settings,
  simple_status: 'Monitoring L2 books; 1 rotation filled.',
  vs_hodl_pct: 0.42,
  vs_control_pct: 0.18,
  decisions_count: 3,
  portfolios: {
    strategy: { value_usdt: '10042.00', return_pct: 0.42, holdings: {}, fees_usdt: '1.20', slippage_usdt: '0.35', rotations: 1 },
    hodl: { value_usdt: '10000.00', return_pct: 0.0, holdings: {}, fees_usdt: '0', slippage_usdt: '0', rotations: 0 },
    drift_control: { value_usdt: '10024.00', return_pct: 0.24, holdings: {}, fees_usdt: '0.50', slippage_usdt: '0.10', rotations: 1 },
  },
  trades: [{ step_index: 1, decision_time: '2026-10-24T00:01:00Z', direction: 'into_a', route: 'ETH -> USDT -> BTC', fees_usdt: '1.20', slippage_usdt: '0.35', rejected_reasons: [], fills: [] }],
  latency_audit: [{
    step_index: 1,
    t_exch_us: 1790900100000000,
    t_recv_ns: 1790900100012000000,
    t_decide_ns: 1790900100012500000,
    t_fill_leg1_ns: 1790900100087500000,
    t_fill_leg2_ns: 1790900100162500000,
    recv_to_decide_ms: 0.5,
    decide_to_fill_leg1_ms: 75.0,
    decide_to_fill_leg2_ms: 150.0,
    order_rtt_ms: 75.0,
    book_age_leg1_ms: 12.0,
    book_age_leg2_ms: 14.0,
    signal_preference: 0.5,
    action: 'into_a',
    rejected_reasons: [],
  }],
}

beforeEach(() => localStorage.clear())
afterEach(() => { vi.unstubAllGlobals(); vi.restoreAllMocks() })

describe('Three-column Finance Cockpit (/lab)', () => {
  it('submits customized strategy settings, toggles Simple/Advanced, switches wealth units, and inspects drawer & scorecard', async () => {
    const studyPosts: Array<{ settings?: Record<string, unknown> }> = []
    let pinnedState = false

    vi.stubGlobal('fetch', vi.fn(async (input: string | URL | Request, init?: RequestInit) => {
      const url = new URL(String(input), 'http://localhost')
      if (url.pathname.endsWith('/coins')) return json({ directory_status: 'observed', coins })
      if (url.pathname.endsWith('/open')) return json({ operation_id: 'op-1' }, 202)
      if (url.pathname.includes('/operations/')) return json({ status: 'completed' })
      if (url.pathname.endsWith('/advisor')) return json(advisorPayload)
      if (url.pathname.endsWith('/studies') && init?.method === 'POST') {
        const body = JSON.parse(String(init.body)) as { settings?: Record<string, unknown> }
        studyPosts.push(body)
        return json({ ...studyPayload, pinned: pinnedState })
      }
      if (url.pathname.endsWith('/studies')) {
        return json({
          studies: [{
            study_id: 'study-cockpit-1',
            created_at: '2026-10-24T00:00:00Z',
            pinned: pinnedState,
            coin_a: { id: 'binance:BTC', code: 'BTC', name: 'Bitcoin', identity_state: 'resolved' },
            coin_b: { id: 'binance:ETH', code: 'ETH', name: 'Ethereum', identity_state: 'resolved' },
            method: 'copula',
            data_through: '2026-10-24T00:00:00Z',
            headline: 'Rotate ETH → BTC',
          }],
          next_offset: null,
        })
      }
      if (url.pathname.endsWith('/pin')) {
        pinnedState = true
        return json({ ...studyPayload, pinned: true })
      }
      if (url.pathname.endsWith('/paper-sessions') && !init?.method) return json({ sessions: [], next_offset: null })
      return json(makeAnalysis())
    }))

    render(<LabDashboard />)

    // Smart Strategy Advisor loads in Simple mode first
    expect(await screen.findByText('BTC and ETH tend to snap back together after short-term divergences.')).toBeVisible()
    expect(screen.getByText(/15m candles generate high swap counts/)).toBeVisible()

    // Switch strategy method to Spread Copula and customize sizing & crash defense
    fireEvent.click(screen.getByRole('button', { name: 'Spread Copula' }))
    fireEvent.change(screen.getByLabelText('Tail probability'), { target: { value: '0.03' } })
    fireEvent.click(screen.getByRole('button', { name: '50%' }))
    fireEvent.change(screen.getByLabelText('Crash defense'), { target: { value: 'park_usdt' } })

    fireEvent.click(screen.getByRole('button', { name: 'Apply & Run Test' }))

    expect(await screen.findByRole('heading', { name: 'Rotate ETH → BTC' })).toBeVisible()
    expect(studyPosts).toHaveLength(1)
    expect(studyPosts[0]?.settings).toMatchObject({
      method: 'copula',
      copula_probability: 0.03,
      rotation_size: 0.25,
      crash_defense_mode: 'park_usdt',
    })

    // Dirty badge appears when a knob moves after running a study
    fireEvent.click(screen.getByRole('button', { name: '75%' }))
    expect(screen.getByText('Settings changed')).toBeVisible()

    // Ratio chart receives trade markers
    expect(screen.getByRole('img', { name: 'BTC per ETH' })).toHaveAttribute('data-markers', 'Buy BTC')

    // Toggle Simple -> Advanced: pro summary & active signal sub-chart appear
    const viewGroup = screen.getByRole('group', { name: 'View mode' })
    fireEvent.click(within(viewGroup).getByRole('button', { name: 'Advanced' }))
    expect(screen.getByText(/Regime=mean_reverting; coint_p=0.015/)).toBeVisible()
    expect(screen.getByRole('img', { name: 'Active signal' })).toBeVisible()

    // Toggle Wealth units: USDT Value -> BTC Units -> ETH Units
    const unitGroup = screen.getByRole('group', { name: 'Wealth unit' })
    fireEvent.click(within(unitGroup).getByRole('button', { name: 'BTC Units' }))
    expect(screen.getByText('0.1723 BTC')).toBeVisible()
    fireEvent.click(within(unitGroup).getByRole('button', { name: 'ETH Units' }))
    expect(screen.getByText('3.4466 ETH')).toBeVisible()

    // Backtest Scorecard displays statistics
    const scorecard = screen.getByRole('region', { name: 'Backtest scorecard' })
    expect(within(scorecard).getByText('-2.15%')).toBeVisible()
    expect(within(scorecard).getByText('18')).toBeVisible()
    expect(within(scorecard).getByText('42.10 USDT')).toBeVisible()
    expect(within(scorecard).getByText('11.40 USDT')).toBeVisible()

    // Expand Trade/Fold drawer and inspect tabs
    fireEvent.click(screen.getByText(/Where the data comes from & audit trail/))
    expect(screen.getByText('ETH -> USDT -> BTC')).toBeVisible()
    fireEvent.click(screen.getByRole('tab', { name: /Walk-Forward Folds/ }))
    expect(screen.getByText('+1.80%')).toBeVisible()
    expect(screen.getByText('2026-07-02 → 2026-08-01')).toBeVisible()

    // Pin saved study
    fireEvent.click(screen.getByRole('button', { name: 'Pin BTC/ETH' }))
    await waitFor(() => expect(screen.getByRole('button', { name: 'Unpin BTC/ETH' })).toBeVisible())
  })

  it('compares presets via /studies/compare and operates Live L2 Paper session controls', async () => {
    let paperStepCount = 0
    vi.stubGlobal('fetch', vi.fn(async (input: string | URL | Request, init?: RequestInit) => {
      const url = new URL(String(input), 'http://localhost')
      if (url.pathname.endsWith('/coins')) return json({ directory_status: 'observed', coins })
      if (url.pathname.endsWith('/open')) return json({ operation_id: 'op-1' }, 202)
      if (url.pathname.includes('/operations/')) return json({ status: 'completed' })
      if (url.pathname.endsWith('/advisor')) return json(advisorPayload)
      if (url.pathname.endsWith('/studies')) return json({ studies: [], next_offset: null })
      if (url.pathname.endsWith('/studies/compare')) {
        return json({
          advisor: advisorPayload,
          best_study_id: 'study-cockpit-1',
          studies: [studyPayload],
        })
      }
      if (url.pathname.endsWith('/paper-sessions') && !init?.method) return json({ sessions: [], next_offset: null })
      if (url.pathname.endsWith('/paper-sessions') && init?.method === 'POST') return json(activePaperSession, 201)
      if (url.pathname.endsWith('/step')) {
        paperStepCount += 1
        return json({ ...activePaperSession, decisions_count: 3 + paperStepCount, vs_hodl_pct: 0.55 })
      }
      if (url.pathname.endsWith('/stop')) {
        return json({ ...activePaperSession, status: 'stopped', simple_status: 'Session stopped.' })
      }
      return json(makeAnalysis())
    }))

    render(<LabDashboard />)
    expect(await screen.findByText('BTC and ETH tend to snap back together after short-term divergences.')).toBeVisible()

    // Compare All Presets
    fireEvent.click(screen.getByRole('button', { name: 'Compare All Presets' }))
    const compareRegion = await screen.findByRole('region', { name: 'Preset comparison' })
    expect(within(compareRegion).getByText('+3.40%')).toBeVisible()
    expect(within(compareRegion).getByText('Best')).toBeVisible()

    // Live L2 Paper Monitor: Start -> Step -> Stop
    const paperRegion = screen.getByRole('region', { name: 'Live L2 paper monitor' })
    fireEvent.click(within(paperRegion).getByRole('button', { name: 'Start Live Paper' }))
    expect(await within(paperRegion).findByText('+0.42%')).toBeVisible()
    expect(within(paperRegion).getByText('75.0 ms')).toBeVisible()

    fireEvent.click(within(paperRegion).getByRole('button', { name: 'Step 3s' }))
    expect(await within(paperRegion).findByText('+0.55%')).toBeVisible()

    fireEvent.click(within(paperRegion).getByRole('button', { name: 'Stop Session' }))
    expect(await within(paperRegion).findByText('Stopped')).toBeVisible()
  })
})
