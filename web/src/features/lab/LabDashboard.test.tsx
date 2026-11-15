import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { LabDashboard } from './LabDashboard'
import type { LabAnalysis } from './labContract'

vi.mock('../../components/charts/TimeSeriesChart', () => ({
  TimeSeriesChart: ({ title }: { title: string }) => <div role="img" aria-label={title} />,
}))

const coins = [
  { listing_id: 'binance:BTC', venue: 'binance', trading: true, venue_asset_code: 'BTC', name: 'Bitcoin', identity_state: 'unresolved', source: 'venue', call_available: false },
  { listing_id: 'binance:W', venue: 'binance', trading: true, venue_asset_code: 'W', name: 'Wormhole', identity_state: 'unresolved', source: 'venue', call_available: false },
]

function analysis(): LabAnalysis {
  return {
    schema_version: 'qap.api.pair-rotation-analysis.v1',
    coin_a: { id: 'binance:BTC', code: 'BTC', name: 'Bitcoin', identity_state: 'unresolved' },
    coin_b: { id: 'binance:W', code: 'W', name: 'Wormhole', identity_state: 'unresolved' },
    bar: '15m', window_days: 180, band_lookback: 672, data_through: '2026-10-02T00:00:00Z', bars_used: 2,
    identity_confirmed: false, anchor: null, anchor_ranking: [],
    series: { time: [1790897400, 1790898300], close_a: [10, 11], close_b: [2, 2], ratio: [5, 5.5], mean: [null, null], std: [null, null], anchor_close: null },
    measurements: { correlation: null, cointegration: null, hedge_ratio: null, half_life: null, hurst: null, ratio_percentile: 100, regime: null, anchor_a: null, anchor_b: null, kalman: null, granger: null, copula: null, rolling_dependence: null },
    datasets: [{ dataset_id: 'exact-btc', interval: '15m', venue_symbol: 'BTCUSDT', semantic_fingerprint: 'a'.repeat(64), coverage_start: '2026-04-01T00:00:00Z', cutoff: '2026-10-02T00:00:00Z' }],
  }
}

const response = (value: unknown, status = 200) => new Response(JSON.stringify(value), { status, headers: { 'Content-Type': 'application/json' } })

const studyResponse = {
  study_id: 'study-1',
  created_at: '2026-10-24T00:00:00Z',
  pinned: false,
  result: {
    call: { status: 'into_a', headline: 'Rotate into BTC', reason: 'The ratio is stretched.', target_weight_a: '0.625', rotation_fraction: '0.25' },
    proof: {
      passes: true, data_role: 'validation', final_oos_used: false, validation_reused: false, settings_tried: 6,
      control: 'weekly', raw_p_value: 0.02, corrected_p_value: 0.03, significance: 0.05, folds_passing: 4,
      folds_total: 5, minimum_passing_folds: 4, validation_trades: 42, minimum_trades: 30, vs_hodl_pct: 2.5,
      vs_control_pct: 1.5, tuning_start: '2025-01-01T00:00:00Z', tuning_end: '2025-03-31T00:00:00Z',
      proof_start: '2025-04-01T00:00:00Z', proof_end: '2025-06-30T00:00:00Z', correction: 'Benjamini-Hochberg.', limitations: [],
    },
    wealth: {
      time: [1790897400, 1790898300],
      value: { strategy: [10000, 10250], hodl: [10000, 10100], daily: [10000, 10050] },
      coins_a: { strategy: [0.1, 0.1025], hodl: [0.1, 0.101], daily: [0.1, 0.1005] },
      coins_b: { strategy: [5, 5.1], hodl: [5, 5.05], daily: [5, 5.02] },
      terminal_values: { strategy: '10250', hodl: '10100', daily: '10050' },
      window_kind: 'validation',
    },
    analysis: { coin_a: { id: 'binance:BTC', code: 'BTC', name: 'Bitcoin' }, coin_b: { id: 'binance:W', code: 'W', name: 'Wormhole' } },
  },
}

beforeEach(() => localStorage.clear())
afterEach(() => { vi.unstubAllGlobals(); vi.restoreAllMocks() })

describe('Pair Rotation Lab', () => {
  it('restores saved coins and supported anchors beyond the discovery page', async () => {
    localStorage.setItem('qap.lab.settings.v1', JSON.stringify({ coin_a: 'binance:X', coin_b: 'binance:Y', anchor: null, bar: '15m', days: 180, band_lookback: 672 }))
    const initial = Array.from({ length: 100 }, (_, index) => ({ ...coins[0], listing_id: `binance:A${index}`, venue_asset_code: `A${index}` }))
    const fetcher = vi.fn(async (input: string | URL | Request) => {
      const url = new URL(String(input), 'http://localhost')
      if (url.pathname.endsWith('/coins')) {
        const query = url.searchParams.get('q')
        const selected = query && ['X', 'Y', 'SOL'].includes(query) ? [{ ...coins[0], listing_id: `binance:${query}`, venue_asset_code: query }] : []
        return response({ directory_status: 'observed', coins: query ? selected : initial })
      }
      if (url.pathname.endsWith('/open')) return response({ operation_id: 'test-operation' }, 202)
      if (url.pathname.includes('/operations/')) return response({ status: 'completed' })
      return response(analysis())
    })
    vi.stubGlobal('fetch', fetcher)
    render(<LabDashboard />)
    await screen.findByText('Not tested yet', { selector: '.lab-idle h2' })
    expect(screen.getByLabelText('Coin A: X')).toBeVisible()
    expect(screen.getByLabelText('Coin B: Y')).toBeVisible()
    expect(screen.getByRole('option', { name: 'SOL' })).toBeInTheDocument()
    expect(fetcher.mock.calls.some(([path]) => String(path).includes('coin_a=binance%3AX') && String(path).includes('coin_b=binance%3AY'))).toBe(true)
  })

  it('prepares data automatically and labels unresolved descriptive evidence honestly', async () => {
    const fetcher = vi.fn(async (input: string | URL | Request) => {
      const path = String(input)
      if (path.includes('/coins?')) return response({ directory_status: 'observed', coins })
      if (path.endsWith('/open')) return response({ operation_id: 'test-operation' }, 202)
      if (path.includes('/operations/')) return response({ status: 'completed', progress: { stage: 'data ready', completed: 8, total: 8 } })
      return response(analysis())
    })
    vi.stubGlobal('fetch', fetcher)
    render(<LabDashboard />)
    expect(await screen.findByText('Not tested yet', { selector: '.lab-idle h2' })).toBeVisible()
    expect(screen.getByText(/Coin identity is unresolved/)).toBeVisible()
    expect(screen.queryByText('No reliable edge')).not.toBeInTheDocument()
    expect(screen.getByRole('img', { name: 'BTC per W' })).toBeVisible()
    fireEvent.click(screen.getByText(/Where the data comes from/))
    expect(screen.getByText('a'.repeat(64))).toBeVisible()
    fireEvent.change(screen.getByRole('combobox', { name: 'Candle size' }), { target: { value: '1h' } })
    await waitFor(() => expect(fetcher.mock.calls.some(([path]) => String(path).includes('bar=1h'))).toBe(true))
    expect(fetcher.mock.calls.filter(([path]) => String(path).endsWith('/open'))).toHaveLength(1)
    expect(JSON.parse(localStorage.getItem('qap.lab.settings.v1') ?? '{}').bar).toBe('1h')
  })

  it('runs one saved study and clears its call when settings change', async () => {
    const posts: Array<{ url: string; body: unknown }> = []
    const opens: unknown[] = []
    vi.stubGlobal('fetch', vi.fn(async (input: string | URL | Request, init?: RequestInit) => {
      const path = String(input)
      if (path.includes('/coins?')) return response({ directory_status: 'observed', coins })
      if (path.endsWith('/open')) {
        opens.push(JSON.parse(String(init?.body)))
        return response({ operation_id: 'test-operation' }, 202)
      }
      if (path.includes('/operations/')) return response({ status: 'completed' })
      if (path.endsWith('/studies')) {
        posts.push({ url: path, body: JSON.parse(String(init?.body)) })
        return response(studyResponse)
      }
      return response(analysis())
    }))
    render(<LabDashboard />)
    expect(await screen.findByText('Not tested yet', { selector: '.lab-idle h2' })).toBeVisible()
    fireEvent.click(screen.getByRole('button', { name: 'Run the test' }))
    expect(await screen.findByRole('heading', { name: 'Rotate into BTC' })).toBeVisible()
    expect(screen.getByText('Validation passes.')).toBeVisible()
    expect(screen.getByRole('img', { name: 'Money over time, after fees' })).toBeVisible()
    expect(screen.getByText('10,250.00 USDT')).toBeVisible()
    expect(screen.queryByText('Not tested yet')).not.toBeInTheDocument()
    expect(posts).toHaveLength(1)
    expect(posts[0]!.body).toMatchObject({ coin_a: 'binance:BTC', coin_b: 'binance:W', anchor: null, bar: '15m', days: 180, band_lookback: 672 })
    expect(opens[0]).toMatchObject({ coin_a: 'binance:BTC', coin_b: 'binance:W', include_execution: true })
    expect(JSON.parse(localStorage.getItem('qap.lab.study.v1') ?? '{}').study_id).toBe('study-1')
    fireEvent.change(screen.getByRole('combobox', { name: 'Candle size' }), { target: { value: '1h' } })
    expect(await screen.findByText('Not tested yet', { selector: '.lab-idle h2' })).toBeVisible()
    expect(screen.queryByRole('heading', { name: 'Rotate into BTC' })).not.toBeInTheDocument()
  })

  it('restores the last saved study after a reload and clears it on request', async () => {
    localStorage.setItem('qap.lab.settings.v1', JSON.stringify({ coin_a: 'binance:BTC', coin_b: 'binance:W', anchor: null, bar: '15m', days: 180, band_lookback: 672 }))
    localStorage.setItem('qap.lab.study.v1', JSON.stringify({
      study_id: 'study-1',
      request: { coin_a: 'binance:BTC', coin_b: 'binance:W', anchor: null, bar: '15m', days: 180, band_lookback: 672 },
    }))
    const fetcher = vi.fn(async (input: string | URL | Request) => {
      const path = String(input)
      if (path.includes('/coins?')) return response({ directory_status: 'observed', coins })
      if (path.endsWith('/open')) return response({ operation_id: 'test-operation' }, 202)
      if (path.includes('/operations/')) return response({ status: 'completed' })
      if (path.endsWith('/studies/study-1')) return response(studyResponse)
      return response(analysis())
    })
    vi.stubGlobal('fetch', fetcher)
    render(<LabDashboard />)
    expect(await screen.findByRole('heading', { name: 'Rotate into BTC' })).toBeVisible()
    expect(screen.getByText('Saved result')).toBeVisible()
    expect(screen.getByText(/^Study from /)).toBeVisible()
    expect(fetcher.mock.calls.some(([path]) => String(path).endsWith('/studies/study-1'))).toBe(true)
    fireEvent.click(screen.getByRole('button', { name: 'Clear result' }))
    expect(screen.getByText('Not tested yet', { selector: '.lab-idle h2' })).toBeVisible()
    expect(screen.queryByText('Saved result')).not.toBeInTheDocument()
    expect(localStorage.getItem('qap.lab.study.v1')).toBeNull()
  })

  it('does not restore a saved study that belongs to other settings', async () => {
    localStorage.setItem('qap.lab.settings.v1', JSON.stringify({ coin_a: 'binance:BTC', coin_b: 'binance:W', anchor: null, bar: '15m', days: 180, band_lookback: 672 }))
    localStorage.setItem('qap.lab.study.v1', JSON.stringify({
      study_id: 'study-1',
      request: { coin_a: 'binance:BTC', coin_b: 'binance:W', anchor: null, bar: '1h', days: 180, band_lookback: 672 },
    }))
    const fetcher = vi.fn(async (input: string | URL | Request) => {
      const path = String(input)
      if (path.includes('/coins?')) return response({ directory_status: 'observed', coins })
      if (path.endsWith('/open')) return response({ operation_id: 'test-operation' }, 202)
      if (path.includes('/operations/')) return response({ status: 'completed' })
      return response(analysis())
    })
    vi.stubGlobal('fetch', fetcher)
    render(<LabDashboard />)
    expect(await screen.findByText('Not tested yet', { selector: '.lab-idle h2' })).toBeVisible()
    await waitFor(() => expect(fetcher.mock.calls.some(([path]) => String(path).includes('bar=15m'))).toBe(true))
    expect(fetcher.mock.calls.some(([path]) => String(path).includes('/studies/'))).toBe(false)
  })

  it('shows a typed preparation failure and retries the same pair', async () => {
    let failed = true
    vi.stubGlobal('fetch', vi.fn(async (input: string | URL | Request) => {
      const path = String(input)
      if (path.includes('/coins?')) return response({ directory_status: 'observed', coins })
      if (path.endsWith('/open')) return response({ operation_id: 'test-operation' }, 202)
      if (path.includes('/operations/')) return response(failed ? { status: 'failed', failure: { message: 'Venue unavailable' } } : { status: 'completed' })
      return response(analysis())
    }))
    render(<LabDashboard />)
    expect(await screen.findByRole('alert')).toHaveTextContent('Venue unavailable')
    expect(screen.queryByRole('img', { name: 'BTC per W' })).not.toBeInTheDocument()
    failed = false
    fireEvent.click(screen.getByRole('button', { name: 'Retry analysis' }))
    expect(await screen.findByText('Not tested yet', { selector: '.lab-idle h2' })).toBeVisible()
  })

  it('discards a late result after the user changes the interval', async () => {
    let finishOld: ((value: Response) => void) | undefined
    vi.stubGlobal('fetch', vi.fn(async (input: string | URL | Request) => {
      const path = String(input)
      if (path.includes('/coins?')) return response({ directory_status: 'observed', coins })
      if (path.endsWith('/open')) return response({ operation_id: 'test-operation' }, 202)
      if (path.includes('/operations/')) return response({ status: 'completed' })
      if (path.includes('bar=15m')) return new Promise<Response>((resolve) => { finishOld = resolve })
      return response({ ...analysis(), coin_a: { ...analysis().coin_a, code: 'NEW' } })
    }))
    render(<LabDashboard />)
    await waitFor(() => expect(finishOld).toBeDefined())
    fireEvent.change(screen.getByRole('combobox', { name: 'Candle size' }), { target: { value: '1h' } })
    expect(await screen.findByRole('img', { name: 'NEW per W' })).toBeVisible()
    finishOld!(response({ ...analysis(), coin_a: { ...analysis().coin_a, code: 'OLD' } }))
    await waitFor(() => expect(screen.queryByRole('img', { name: 'OLD per W' })).not.toBeInTheDocument())
  })
})
