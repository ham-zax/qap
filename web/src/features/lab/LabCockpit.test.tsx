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
  { listing_id: 'binance:BNB', venue: 'binance', trading: true, venue_asset_code: 'BNB', name: 'BNB', identity_state: 'resolved', source: 'venue', call_available: true },
  { listing_id: 'binance:DOGE', venue: 'binance', trading: true, venue_asset_code: 'DOGE', name: 'Dogecoin', identity_state: 'resolved', source: 'venue', call_available: true },
  { listing_id: 'binance:LINK', venue: 'binance', trading: true, venue_asset_code: 'LINK', name: 'Chainlink', identity_state: 'resolved', source: 'venue', call_available: true },
]

function makeAnalysis(): LabAnalysis {
  return {
    schema_version: 'qap.api.pair-rotation-analysis.v1',
    coin_a: { id: 'binance:BTC', code: 'BTC', name: 'Bitcoin', identity_state: 'resolved' },
    coin_b: { id: 'binance:ETH', code: 'ETH', name: 'Ethereum', identity_state: 'resolved' },
    bar: '1h',
    window_days: 180,
    band_lookback: 168,
    data_through: '2026-10-24T00:00:00Z',
    bars_used: 4320,
    identity_confirmed: true,
    anchor: { id: 'binance:SOL', code: 'SOL', name: 'Solana', identity_state: 'resolved' },
    anchor_ranking: [{ anchor: { id: 'binance:SOL', code: 'SOL', name: 'Solana', identity_state: 'resolved' }, beta_a: 1.0, beta_b: 0.9, joint_explained: 0.61 }],
    series: {
      time: [1790897400, 1790898300, 1790899200, 1790900100],
      close_a: [60000, 60500, 61000, 61500],
      close_b: [3000, 3010, 3020, 3030],
      ratio: [20, 20.1, 20.2, 20.3],
      mean: [20, 20.05, 20.1, 20.15],
      std: [0.05, 0.05, 0.08, 0.1],
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
      kalman: { beta: 0.99, standard_error: 0.05, beta_change: 0.01 },
      granger: null,
      copula: { family: 'student', lower_tail: 0.48, upper_tail: 0.48, observations: 2000 },
      rolling_dependence: null,
    },
    datasets: [{
      dataset_id: 'exact-btc',
      interval: '1h',
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
  simple_summary: 'BTC and ETH snap back together after short-term divergences.',
  pro_summary: 'Regime=mean_reverting; coint_p=0.015; half_life_bars=32; hurst=0.41.',
  bar_warning: null,
  suggestions: [
    {
      rank: 1,
      preset_id: 'zscore_kalman',
      title: 'Kalman Z-Score Mean Reversion',
      simple_reason: 'Buys the coin that lags behind its usual ratio.',
      pro_reason: 'Kalman hedge with lookback=64, entry=2.0, exit=0.4.',
      recommended_bar: '1h',
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
    analysis: makeAnalysis(),
    requested_settings: { method: 'copula', hedge_method: 'ratio', lookback: 120, entry: 2.0, exit: 0.5, rotation_size: '0.25', crash_defense_mode: 'park_usdt' },
    applied_settings: { method: 'copula', hedge_method: 'ratio', lookback: 120, entry: 2.0, exit: 0.5, rotation_size: '0.25', crash_defense_mode: 'park_usdt' },
    call: { status: 'into_a', headline: 'Rotate ETH → BTC', reason: 'Spread tail triggered.', target_weight_a: '0.625', rotation_fraction: '0.25' },
    proof: {
      passes: true, data_role: 'validation', final_oos_used: false, validation_reused: false, settings_tried: 4,
      control: 'weekly', raw_p_value: 0.015, corrected_p_value: 0.025, significance: 0.05, folds_passing: 4,
      folds_total: 5, minimum_passing_folds: 3, validation_trades: 18, minimum_trades: 10, vs_hodl_pct: 3.4,
      vs_control_pct: 1.9, cost_paid_pct: 1.12, gross_vs_hodl_pct: 4.52,
      tuning_start: '2026-04-01T00:00:00Z', tuning_end: '2026-07-01T00:00:00Z',
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
        terminal_holdings: { 'binance:BTC': '0.1723', 'binance:ETH': '0' },
      },
    },
    code_fingerprint: 'abcdef1234567890',
    execution_route: 'two legs via USDT',
    execution_metadata: [],
  },
}

const activePaperSession = {
  schema_version: 'qap.lab.paper_session.v1',
  session_id: 'paper-1',
  actor_id: 'local',
  status: 'active',
  created_at: '2026-10-24T00:00:00Z',
  updated_at: '2026-10-24T00:05:00Z',
  stopped_at: null,
  coin_a: 'binance:BTC',
  coin_b: 'binance:ETH',
  anchor: 'binance:SOL',
  bar: '1h',
  order_rtt_ms: 75,
  max_staleness_ms: 500,
  starting_value: '10000',
  settings: { method: 'copula' },
  decisions_count: 3,
  simple_status: 'Active paper tracking on BTC/ETH.',
  vs_hodl_pct: 0.42,
  vs_control_pct: 0.31,
  portfolios: {
    strategy: { holdings: { BTC: '0.16', ETH: '0' }, value_usdt: '10042.00', return_pct: 0.42, fees_usdt: '2.00', slippage_usdt: '0.50', rotations: 1 },
    hodl: { holdings: { BTC: '0.08', ETH: '1.6' }, value_usdt: '10000.00', return_pct: 0, fees_usdt: '0', slippage_usdt: '0', rotations: 0 },
    drift_control: { holdings: { BTC: '0.08', ETH: '1.6' }, value_usdt: '10011.00', return_pct: 0.11, fees_usdt: '0', slippage_usdt: '0', rotations: 0 },
  },
  trades: [],
  latency_audit: [{
    step_index: 1,
    t_exch_us: 1790897400000000,
    t_recv_ns: 1790897400045000000,
    t_decide_ns: 1790897400047000000,
    t_fill_leg1_ns: 1790897400122000000,
    t_fill_leg2_ns: 1790897400197000000,
    order_rtt_ms: 75,
    recv_to_decide_ms: 2.0,
    decide_to_fill_leg1_ms: 75.0,
    decide_to_fill_leg2_ms: 150.0,
    book_age_leg1_ms: 12.4,
    book_age_leg2_ms: 18.2,
    signal_preference: 1,
    action: 'swap',
    rejected_reasons: [],
  }],
}

beforeEach(() => localStorage.clear())
afterEach(() => { vi.unstubAllGlobals(); vi.restoreAllMocks() })

describe('Lab Binance Terminal + Bottom Tabs', () => {
  it('opens in Simple preset mode by default, unlocks Pro knobs, switches Wealth units, and navigates bottom tabs', async () => {
    const studyPosts: Array<{ settings?: Record<string, unknown> }> = []
    let pinnedState = false

    vi.stubGlobal('fetch', vi.fn(async (input: string | URL | Request, init?: RequestInit) => {
      const url = new URL(String(input), 'http://localhost')
      if (url.pathname.endsWith('/coins')) return json({ directory_status: 'observed', coins })
      if (url.pathname.endsWith('/advisor')) return json(advisorPayload)
      if (url.pathname.endsWith('/studies') && init?.method === 'POST') {
        studyPosts.push(JSON.parse(String(init.body)))
        return json(studyPayload)
      }
      if (url.pathname.endsWith('/studies') && !init?.method) {
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

    // Simple mode renders Advisor preset card and hides raw Pro inputs
    expect(await screen.findByText('Kalman Z-Score Mean Reversion')).toBeVisible()
    expect(screen.queryByLabelText(/Tail Entry Rank/)).not.toBeInTheDocument()

    // Overview KPI tiles appear with variable-scoped trader terms
    expect(screen.getByText('Log-Return Correlation')).toBeVisible()
    expect(screen.getByText('Log-Ratio Half-Life')).toBeVisible()

    // Switch Simple -> Pro: full trader controls unlock
    const viewGroup = screen.getByRole('group', { name: 'View mode' })
    fireEvent.click(within(viewGroup).getByRole('button', { name: 'Pro' }))

    fireEvent.click(screen.getByRole('button', { name: 'Spread Copula' }))
    fireEvent.change(screen.getByLabelText(/Tail Entry Rank/), { target: { value: '0.03' } })
    fireEvent.click(within(screen.getByRole('group', { name: 'Swap size' })).getByRole('button', { name: '50%' }))
    fireEvent.change(screen.getByLabelText(/Crash Stop/), { target: { value: 'park_usdt' } })

    fireEvent.click(screen.getByRole('button', { name: 'Test Strategy ($10,000)' }))

    expect(await screen.findByText('Validated Edge (4/5 Folds)')).toBeVisible()
    expect(screen.getByText('$10,000 → $10,340')).toBeVisible()
    expect(studyPosts[0]?.settings).toMatchObject({
      method: 'copula',
      copula_probability: 0.03,
      rotation_size: 0.25,
      crash_defense_mode: 'park_usdt',
    })

    // Ratio chart receives trade markers and Pro signal oscillator pane appears
    expect(screen.getByRole('img', { name: 'BTC per ETH' })).toHaveAttribute('data-markers', 'Swap → BTC')
    expect(screen.getByRole('img', { name: 'Active signal' })).toBeVisible()

    // Unsaved changes badge appears when Swap Size changes after test
    fireEvent.click(within(screen.getByRole('group', { name: 'Swap size' })).getByRole('button', { name: '75%' }))
    expect(screen.getByText('Unsaved changes')).toBeVisible()

    // Switch above-the-fold chart tab to Wealth Curve ($10,000) and toggle units
    fireEvent.click(screen.getByRole('tab', { name: /Wealth Curve/ }))
    const unitGroup = screen.getByRole('group', { name: 'Wealth unit' })
    fireEvent.click(within(unitGroup).getByRole('button', { name: 'BTC Units' }))
    expect(screen.getByText('0.1723 BTC')).toBeVisible()
    fireEvent.click(within(unitGroup).getByRole('button', { name: 'ETH Units' }))
    expect(screen.getByText('3.4466 ETH')).toBeVisible()

    // Inspect bottom tabs: Simulated Swaps, Pro Diagnostics, Saved Runs
    fireEvent.click(screen.getByRole('tab', { name: /Simulated Swaps/ }))
    expect(screen.getByText('ETH -> USDT -> BTC')).toBeVisible()

    fireEvent.click(screen.getByRole('tab', { name: 'Pro Diagnostics' }))
    expect(screen.getByText('+1.80%')).toBeVisible()
    expect(screen.getByText(/2026-07-02/)).toBeVisible()

    fireEvent.click(screen.getByRole('tab', { name: /Saved Runs/ }))
    fireEvent.click(screen.getByRole('button', { name: 'Pin BTC/ETH' }))
    await waitFor(() => expect(screen.getByRole('button', { name: 'Unpin BTC/ETH' })).toBeVisible())
  })

  it('auto-switches to Compare Strategies tab on preset comparison and runs Live Paper inside the Live Paper tab', async () => {
    let paperStepCount = 0
    vi.stubGlobal('fetch', vi.fn(async (input: string | URL | Request, init?: RequestInit) => {
      const url = new URL(String(input), 'http://localhost')
      if (url.pathname.endsWith('/coins')) return json({ directory_status: 'observed', coins })
      if (url.pathname.endsWith('/advisor')) return json(advisorPayload)
      if (url.pathname.endsWith('/studies')) return json({ studies: [], next_offset: null })
      if (url.pathname.endsWith('/studies/compare')) {
        return json({ advisor: advisorPayload, best_study_id: 'study-cockpit-1', studies: [studyPayload] })
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
    expect(await screen.findByText('Kalman Z-Score Mean Reversion')).toBeVisible()

    // Compare All Presets auto-switches bottom tab to Compare Strategies
    fireEvent.click(screen.getByRole('button', { name: 'Compare All Presets' }))
    const compareRegion = await screen.findByRole('region', { name: 'Preset comparison' })
    expect(within(compareRegion).getByText('+3.40%')).toBeVisible()
    expect(within(compareRegion).getByText('Best')).toBeVisible()

    // Switch bottom tab to Live Paper: Start -> Step -> Stop
    fireEvent.click(screen.getByRole('tab', { name: /Live Paper/ }))
    const paperRegion = screen.getByRole('region', { name: 'Live L2 paper monitor' })
    fireEvent.click(within(paperRegion).getByRole('button', { name: 'Start Live Paper' }))
    expect(await within(paperRegion).findByText('+0.42%')).toBeVisible()
    expect(within(paperRegion).getByText('45.0 ms')).toBeVisible()

    fireEvent.click(within(paperRegion).getByRole('button', { name: 'Step 3s' }))
    expect(await within(paperRegion).findByText('+0.55%')).toBeVisible()

    fireEvent.click(within(paperRegion).getByRole('button', { name: 'Stop Session' }))
    expect(await within(paperRegion).findByText('Stopped')).toBeVisible()
  })

  it('auto-switches to 1m for Anchor Lead-Lag, reveals drawdown slider, and opens InfoTip popovers', async () => {
    vi.stubGlobal('fetch', vi.fn(async (input: string | URL | Request) => {
      const url = new URL(String(input), 'http://localhost')
      if (url.pathname.endsWith('/coins')) return json({ directory_status: 'observed', coins })
      if (url.pathname.endsWith('/advisor')) return json(advisorPayload)
      if (url.pathname.endsWith('/studies')) return json({ studies: [], next_offset: null })
      if (url.pathname.endsWith('/paper-sessions')) return json({ sessions: [], next_offset: null })
      return json(makeAnalysis())
    }))

    render(<LabDashboard />)
    expect(await screen.findByText('Kalman Z-Score Mean Reversion')).toBeVisible()

    // InfoTip opens on click
    fireEvent.click(screen.getByRole('button', { name: 'Benchmark guidance' }))
    expect(screen.getByRole('tooltip')).toHaveTextContent(/highest-R² market driver/i)

    // Switch to Pro mode
    fireEvent.click(screen.getByRole('button', { name: 'Pro' }))

    // Selecting Park in USDT reveals the Crash Drawdown Trigger slider
    fireEvent.change(screen.getByLabelText('Crash Stop'), { target: { value: 'park_usdt' } })
    expect(screen.getByLabelText(/Crash Drawdown Trigger/i)).toBeVisible()

    // Selecting Anchor Lead-Lag auto-switches interval to 1m
    fireEvent.click(screen.getByRole('button', { name: /Anchor Lead-Lag/ }))
    await waitFor(() => {
      expect(within(screen.getByRole('group', { name: 'Interval' })).getByRole('button', { name: '1m' })).toHaveAttribute('aria-pressed', 'true')
    })

    // Switching away from 1m while Anchor Lead-Lag is active disables Test Strategy and offers Switch to 1m
    fireEvent.click(within(screen.getByRole('group', { name: 'Interval' })).getByRole('button', { name: '1h' }))
    expect(screen.getByText(/Anchor Lead-Lag requires 1m candles/i)).toBeVisible()
    expect(screen.getByRole('button', { name: 'Test Strategy ($10,000)' })).toBeDisabled()
    fireEvent.click(screen.getByRole('button', { name: 'Switch to 1m' }))
    await waitFor(() => {
      expect(within(screen.getByRole('group', { name: 'Interval' })).getByRole('button', { name: '1m' })).toHaveAttribute('aria-pressed', 'true')
    })
  })

  it('shows explicit benchmark guidance when no auto-detected anchor covers the window', async () => {
    vi.stubGlobal('fetch', vi.fn(async (input: string | URL | Request) => {
      const url = new URL(String(input), 'http://localhost')
      if (url.pathname.endsWith('/coins')) return json({ directory_status: 'observed', coins })
      if (url.pathname.endsWith('/advisor')) return json(advisorPayload)
      if (url.pathname.endsWith('/studies')) return json({ studies: [], next_offset: null })
      if (url.pathname.endsWith('/paper-sessions')) return json({ sessions: [], next_offset: null })
      return json({ ...makeAnalysis(), anchor: null, anchor_ranking: [] })
    }))

    render(<LabDashboard />)
    expect(await screen.findByText('Kalman Z-Score Mean Reversion')).toBeVisible()
    fireEvent.click(screen.getByRole('button', { name: 'Pro' }))
    fireEvent.change(screen.getByLabelText('Crash Stop'), { target: { value: 'park_anchor' } })
    expect(screen.getAllByText(/No auto-detected benchmark covers this full window/i)).toHaveLength(1)
    fireEvent.click(screen.getByRole('button', { name: /Anchor Lead-Lag/ }))
    await waitFor(() => {
      expect(screen.getByText(/Select a Benchmark in the top bar for Anchor Lead-Lag/i)).toBeVisible()
    })
  })

  it('expands the chart history window when Load 1Y is clicked', async () => {
    const requestedDays: string[] = []
    vi.stubGlobal('fetch', vi.fn(async (input: string | URL | Request) => {
      const url = new URL(String(input), 'http://localhost')
      if (url.pathname.endsWith('/coins')) return json({ directory_status: 'observed', coins })
      if (url.pathname.endsWith('/analysis')) requestedDays.push(url.searchParams.get('days') ?? '')
      if (url.pathname.endsWith('/advisor')) return json(advisorPayload)
      if (url.pathname.endsWith('/studies')) return json({ studies: [], next_offset: null })
      if (url.pathname.endsWith('/paper-sessions')) return json({ sessions: [], next_offset: null })
      return json(makeAnalysis())
    }))

    render(<LabDashboard />)
    const loadOlder = await screen.findByRole('button', { name: 'Load 1Y' })
    fireEvent.click(loadOlder)
    await waitFor(() => {
      expect(requestedDays).toContain('365')
    })
  })
})
