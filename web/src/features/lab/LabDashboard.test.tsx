import { act, renderHook, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { useLab } from './useLab'
import { LabDashboard } from './LabDashboard'
import type { LabAnalysis } from './labContract'

vi.mock('../../components/charts/TimeSeriesChart', () => ({
  TimeSeriesChart: ({ title }: { title: string }) => <div role="img" aria-label={title} />,
}))

const coins = [
  { listing_id: 'binance:BTC', venue: 'binance', trading: true, venue_asset_code: 'BTC', name: 'Bitcoin', identity_state: 'unresolved', source: 'venue', call_available: false },
  { listing_id: 'binance:W', venue: 'binance', trading: true, venue_asset_code: 'W', name: 'Wormhole', identity_state: 'unresolved', source: 'venue', call_available: false },
  { listing_id: 'binance:SOL', venue: 'binance', trading: true, venue_asset_code: 'SOL', name: 'Solana', identity_state: 'resolved', source: 'venue', call_available: true },
]

function analysis(): LabAnalysis {
  return {
    schema_version: 'qap.api.pair-rotation-analysis.v1',
    coin_a: { id: 'binance:BTC', code: 'BTC', name: 'Bitcoin', identity_state: 'unresolved' },
    coin_b: { id: 'binance:W', code: 'W', name: 'Wormhole', identity_state: 'unresolved' },
    bar: '1h', window_days: 180, band_lookback: 168, data_through: '2026-10-02T00:00:00Z', bars_used: 4320,
    identity_confirmed: false, anchor: null, anchor_ranking: [],
    series: { time: [1790897400, 1790901000], close_a: [10, 11], close_b: [2, 2], ratio: [5, 5.5], mean: [5.0, 5.0], std: [0.25, 0.25], anchor_close: null },
    measurements: { correlation: null, cointegration: null, hedge_ratio: null, half_life: null, hurst: null, ratio_percentile: 100, regime: null, anchor_a: null, anchor_b: null, kalman: null, granger: null, copula: null, rolling_dependence: null },
    datasets: [{ dataset_id: 'exact-btc', interval: '1h', venue_symbol: 'BTCUSDT', semantic_fingerprint: 'a'.repeat(64), coverage_start: '2026-04-01T00:00:00Z', cutoff: '2026-10-02T00:00:00Z' }],
  }
}

const response = (value: unknown, status = 200) =>
  new Response(JSON.stringify(value), { status, headers: { 'Content-Type': 'application/json' } })

const studyResponse = {
  study_id: 'study-1',
  created_at: '2026-10-24T00:00:00Z',
  pinned: false,
  result: {
    schema_version: 'qap.lab.study.v1',
    requested_settings: { method: 'zscore', hedge_method: 'ratio', lookback: 96, entry: 2.0, exit: 0.5, rotation_size: '0.5', crash_defense_mode: 'coins_only' },
    applied_settings: { method: 'zscore', hedge_method: 'ratio', lookback: 96, entry: 2.0, exit: 0.5, rotation_size: '0.5', crash_defense_mode: 'coins_only' },
    call: { status: 'into_a', headline: 'Rotate into BTC', reason: 'The ratio is stretched.', target_weight_a: '0.75', rotation_fraction: '0.25' },
    proof: {
      passes: true, data_role: 'validation', final_oos_used: false, validation_reused: false, settings_tried: 6,
      control: 'weekly', raw_p_value: 0.02, corrected_p_value: 0.03, significance: 0.05, folds_passing: 4,
      folds_total: 5, minimum_passing_folds: 4, validation_trades: 42, minimum_trades: 30, vs_hodl_pct: 2.5,
      vs_control_pct: 1.5, cost_paid_pct: 1.2, gross_vs_hodl_pct: 3.7, tuning_start: '2025-01-01T00:00:00Z',
      tuning_end: '2025-03-31T00:00:00Z', proof_start: '2025-04-01T00:00:00Z', proof_end: '2025-06-30T00:00:00Z',
      correction: 'Benjamini-Hochberg.', limitations: [],
    },
    signal: { time: [1790897400, 1790901000], values: [-1.2, -2.1], upper: 2.0, lower: -2.0, unit: 'sigma' },
    wealth: {
      time: [1790897400, 1790901000],
      value: { strategy: [10000, 10250], hodl: [10000, 10100], daily: [10000, 10050] },
      coins_a: { strategy: [0.1, 0.1025], hodl: [0.1, 0.101], daily: [0.1, 0.1005] },
      coins_b: { strategy: [5, 5.1], hodl: [5, 5.05], daily: [5, 5.02] },
      terminal_values: { strategy: '10250', hodl: '10100', daily: '10050' },
      window_kind: 'validation',
    },
    trades: [],
    folds: [],
    statistics: {},
    code_fingerprint: 'deadbeef1234',
    execution_route: 'two legs via USDT',
    execution_metadata: [],
    analysis: analysis(),
  },
}

beforeEach(() => localStorage.clear())
afterEach(() => { vi.unstubAllGlobals(); vi.restoreAllMocks() })

describe('Pair Rotation Lab — Binance Terminal', () => {
  it('loads cached analysis immediately without calling /open when history is already on disk', async () => {
    const fetcher = vi.fn(async (input: string | URL | Request) => {
      const path = String(input)
      if (path.includes('/coins?')) return response({ directory_status: 'observed', coins })
      if (path.includes('/studies') || path.includes('/paper-sessions')) return response({ studies: [], sessions: [], next_offset: null })
      return response(analysis())
    })
    vi.stubGlobal('fetch', fetcher)
    render(<LabDashboard />)

    expect(await screen.findByRole('img', { name: 'BTC per W' })).toBeVisible()
    expect(screen.getByText('5.5')).toBeVisible()
    expect(screen.getByText(/\+10\.0% · \+2\.0σ/)).toBeVisible()
    expect(screen.getByText(/Listing identity is unconfirmed/)).toBeVisible()
    expect(fetcher.mock.calls.filter(([path]) => String(path).endsWith('/open'))).toHaveLength(0)

    //Inspect dataset provenance in Pro Diagnostics tab
    fireEvent.click(screen.getByRole('tab', { name: 'Pro Diagnostics' }))
    expect(screen.getByText('a'.repeat(64))).toBeVisible()

    // Change interval via pill strip
    const intervalGroup = screen.getByRole('group', { name: 'Interval' })
    fireEvent.click(within(intervalGroup).getByRole('button', { name: '4h' }))
    await waitFor(() => expect(fetcher.mock.calls.some(([path]) => String(path).includes('bar=4h'))).toBe(true))
    expect(JSON.parse(localStorage.getItem('qap.lab.settings.v1') ?? '{}').bar).toBe('4h')
  })

  it('falls back to /open automatically when /analysis reports unprepared pair data', async () => {
    let prepared = false
    const opens: unknown[] = []
    vi.stubGlobal('fetch', vi.fn(async (input: string | URL | Request, init?: RequestInit) => {
      const path = String(input)
      if (path.includes('/coins?')) return response({ directory_status: 'observed', coins })
      if (path.includes('/analysis?')) {
        if (!prepared) return response({ error: { message: 'Not prepared yet' } }, 409)
        return response(analysis())
      }
      if (path.endsWith('/open')) {
        opens.push(JSON.parse(String(init?.body)))
        prepared = true
        return response({ operation_id: 'op-1' }, 202)
      }
      if (path.includes('/operations/')) return response({ status: 'completed' })
      return response({ studies: [], sessions: [], next_offset: null })
    }))

    render(<LabDashboard />)
    expect(await screen.findByRole('img', { name: 'BTC per W' })).toBeVisible()
    expect(opens).toHaveLength(1)
    expect(opens[0]).toMatchObject({ coin_a: 'binance:BTC', coin_b: 'binance:W', include_execution: true })
  })

  it('runs a $10,000 strategy test, switches to Wealth Curve tab, and restores/clears saved runs', async () => {
    const posts: Array<{ body: unknown }> = []
    vi.stubGlobal('fetch', vi.fn(async (input: string | URL | Request, init?: RequestInit) => {
      const path = String(input)
      if (path.includes('/coins?')) return response({ directory_status: 'observed', coins })
      if (path.endsWith('/studies') && init?.method === 'POST') {
        posts.push({ body: JSON.parse(String(init.body)) })
        return response(studyResponse)
      }
      if (path.includes('/studies') || path.includes('/paper-sessions')) return response({ studies: [], sessions: [], next_offset: null })
      return response(analysis())
    }))

    render(<LabDashboard />)
    expect(await screen.findByRole('img', { name: 'BTC per W' })).toBeVisible()

    fireEvent.click(screen.getByRole('button', { name: 'Test Strategy ($10,000)' }))
    expect(await screen.findByText('Validated Edge (4/5 Folds)')).toBeVisible()
    expect(screen.getByText('$10,000 → $10,250')).toBeVisible()
    expect(screen.getByText(/Signal: Swap toward BTC/)).toBeVisible()
    expect(posts).toHaveLength(1)
    expect(posts[0]!.body).toMatchObject({ coin_a: 'binance:BTC', coin_b: 'binance:W', bar: '1h', days: 180, band_lookback: 168 })

    // Switch above-the-fold chart tab to Wealth Curve ($10,000)
    fireEvent.click(screen.getByRole('tab', { name: /Wealth Curve/ }))
    expect(screen.getByRole('img', { name: 'Money over time, after fees' })).toBeVisible()
  })

  it('tests the clicked fallback preset when the advisor is unavailable', async () => {
    const posts: Array<{ settings: { method: string } }> = []
    vi.stubGlobal('fetch', vi.fn(async (input: string | URL | Request, init?: RequestInit) => {
      const path = String(input)
      if (path.includes('/coins?')) return response({ directory_status: 'observed', coins })
      if (path.includes('/advisor?')) return response({ error: { message: 'Advisor unavailable' } }, 503)
      if (path.endsWith('/studies') && init?.method === 'POST') {
        posts.push(JSON.parse(String(init.body)))
        return response(studyResponse)
      }
      if (path.includes('/studies') || path.includes('/paper-sessions')) return response({ studies: [], sessions: [] })
      return response(analysis())
    }))
    render(<LabDashboard />)
    await screen.findByRole('img', { name: 'BTC per W' })
    const card = screen.getByText('Tail Mispricing · Spread Copula').closest('article')!
    fireEvent.click(within(card).getByRole('button', { name: 'Test' }))
    await waitFor(() => expect(posts[0]?.settings.method).toBe('copula'))
  })

  it('restores the saved snapshot and all controls, then clears it on a history change', async () => {
    const snapshot = { ...analysis(), bar: '4h', window_days: 90, band_lookback: 42,
      anchor: { id: 'binance:SOL', code: 'SOL', name: 'Solana', identity_state: 'resolved' } }
    const fetcher = vi.fn(async (input: string | URL | Request) => {
      const path = String(input)
      if (path.includes('/coins?')) return response({ directory_status: 'observed', coins })
      if (path.endsWith('/studies/study-1')) return response({ ...studyResponse, result: { ...studyResponse.result, analysis: snapshot } })
      if (path.includes('/studies?')) return response({ studies: [{ study_id: 'study-1', coin_a: snapshot.coin_a,
        coin_b: snapshot.coin_b, method: 'zscore', headline: 'Saved result', pinned: false }], next_offset: null })
      if (path.includes('/paper-sessions')) return response({ sessions: [] })
      return response(analysis())
    })
    vi.stubGlobal('fetch', fetcher)
    render(<LabDashboard />)
    await screen.findByRole('img', { name: 'BTC per W' })
    fireEvent.click(screen.getByRole('tab', { name: /Saved Runs/ }))
    fireEvent.click(await screen.findByRole('button', { name: /BTC\/W · zscore/ }))
    expect(await screen.findByText(/Viewing Saved Run: BTC\/W · 4h/)).toBeVisible()
    expect(within(screen.getByRole('group', { name: 'Interval' })).getByRole('button', { name: '4h' })).toHaveAttribute('aria-pressed', 'true')
    expect(within(screen.getByRole('group', { name: 'History window' })).getByRole('button', { name: '90D' })).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByRole('combobox', { name: 'Benchmark' })).toHaveValue('binance:SOL')
    expect(fetcher.mock.calls.filter(([path]) => String(path).includes('/analysis?'))).toHaveLength(1)
    fireEvent.click(screen.getByRole('button', { name: 'Clear' }))
    expect(screen.queryByText(/Viewing Saved Run/)).not.toBeInTheDocument()
    fireEvent.click(within(screen.getByRole('group', { name: 'History window' })).getByRole('button', { name: '30D' }))
    await waitFor(() => expect(fetcher.mock.calls.some(([path]) => String(path).includes('days=30'))).toBe(true))
    expect(screen.queryByText(/Validated Edge/)).not.toBeInTheDocument()
  })

  it('allows another comparison after the user changes an in-flight comparison window', async () => {
    vi.stubGlobal('fetch', vi.fn(async (input: string | URL | Request) => {
      const path = String(input)
      if (path.includes('/coins?')) return response({ directory_status: 'observed', coins })
      if (path.endsWith('/studies/compare')) return new Promise<Response>(() => {})
      if (path.includes('/studies') || path.includes('/paper-sessions')) return response({ studies: [], sessions: [] })
      return response(analysis())
    }))
    render(<LabDashboard />)
    await screen.findByRole('img', { name: 'BTC per W' })
    fireEvent.click(screen.getByRole('button', { name: 'Compare All Presets' }))
    expect(screen.getByRole('button', { name: 'Comparing…' })).toBeDisabled()
    fireEvent.click(within(screen.getByRole('group', { name: 'History window' })).getByRole('button', { name: '30D' }))
    await waitFor(() => expect(screen.getByRole('button', { name: 'Compare All Presets' })).toBeEnabled())
  })

  it('shows preparation failure and retries cleanly', async () => {
    let failed = true
    vi.stubGlobal('fetch', vi.fn(async (input: string | URL | Request) => {
      const path = String(input)
      if (path.includes('/coins?')) return response({ directory_status: 'observed', coins })
      if (path.includes('/analysis?')) {
        if (failed) return response({ error: { message: 'Missing history' } }, 409)
        return response(analysis())
      }
      if (path.endsWith('/open')) return response({ operation_id: 'op-err' }, 202)
      if (path.includes('/operations/')) return response(failed ? { status: 'failed', failure: { message: 'Venue unavailable' } } : { status: 'completed' })
      return response({ studies: [], sessions: [], next_offset: null })
    }))

    render(<LabDashboard />)
    expect(await screen.findByRole('alert')).toHaveTextContent('Venue unavailable')
    failed = false
    fireEvent.click(screen.getByRole('button', { name: 'Retry' }))
    expect(await screen.findByRole('img', { name: 'BTC per W' })).toBeVisible()
  })
})


it('groups two coin edits and ignores an obsolete in-flight result', async () => {
  let finishOld: ((value: Response) => void) | undefined
  const paths: string[] = []
  vi.stubGlobal('fetch', vi.fn(async (input: string | URL | Request) => {
    const path = String(input)
    if (path.includes('/coins?')) return response({ directory_status: 'observed', coins })
    if (path.includes('/analysis?')) {
      paths.push(path)
      if (paths.length === 1) return new Promise<Response>((resolve) => { finishOld = resolve })
      return response({ ...analysis(), coin_a: { ...analysis().coin_a, code: 'SOL' } })
    }
    return response({ studies: [], sessions: [] })
  }))
  const { result } = renderHook(() => useLab())
  await waitFor(() => expect(paths).toHaveLength(1))
  act(() => { result.current.change({ coin_a: 'binance:SOL' }); result.current.change({ coin_b: 'binance:BTC' }) })
  await waitFor(() => expect(result.current.analysis?.coin_a.code).toBe('SOL'))
  expect(paths).toHaveLength(2)
  expect(paths[1]).toContain('coin_a=binance%3ASOL&coin_b=binance%3ABTC')
  await act(async () => { finishOld!(response(analysis())) })
  expect(result.current.analysis?.coin_a.code).toBe('SOL')
})
