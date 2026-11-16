import { afterEach, describe, expect, it, vi } from 'vitest'
import { loadLab, searchLabCoins } from './labApi'
import type { LabAnalysis, LabRequest } from './labContract'

afterEach(() => vi.unstubAllGlobals())

const json = (value: unknown, status = 200) =>
  new Response(JSON.stringify(value), { status, headers: { 'Content-Type': 'application/json' } })

const request: LabRequest = { coin_a: 'binance:BTC', coin_b: 'binance:ETH', anchor: null, bar: '1h', days: 180, band_lookback: 168 }

function analysis(): LabAnalysis {
  return {
    schema_version: 'qap.api.pair-rotation-analysis.v1',
    coin_a: { id: 'binance:BTC', code: 'BTC', name: 'Bitcoin', identity_state: 'unresolved' },
    coin_b: { id: 'binance:ETH', code: 'ETH', name: 'Ethereum', identity_state: 'unresolved' },
    bar: '1h', window_days: 180, band_lookback: 168, data_through: '2026-10-02T00:00:00Z', bars_used: 2,
    identity_confirmed: false, anchor: null, anchor_ranking: [],
    series: { time: [1790897400, 1790898300], close_a: [10, 11], close_b: [2, 2], ratio: [5, 5.5], mean: [null, null], std: [null, null], anchor_close: null },
    measurements: { correlation: null, cointegration: null, hedge_ratio: null, half_life: null, hurst: null, ratio_percentile: 100, regime: null, anchor_a: null, anchor_b: null, kalman: null, granger: null, copula: null, rolling_dependence: null },
    datasets: [],
  }
}

const noop = () => {}

describe('Lab venue eligibility', () => {
  it('offers only trading Binance listings from mixed search results', async () => {
    const row = { listing_id: 'binance:BTC', venue: 'binance', trading: true, venue_asset_code: 'BTC', name: 'Bitcoin', identity_state: 'unresolved', source: 'venue', call_available: false }
    vi.stubGlobal('fetch', vi.fn(async () => json({ directory_status: 'observed', coins: [
      row, { ...row, listing_id: 'gate:BTC', venue: 'gate' },
      { ...row, listing_id: 'binance:OLD', trading: false },
    ] })))
    const result = await searchLabCoins('BTC', new AbortController().signal)
    expect(result.coins.map((coin) => coin.id)).toEqual(['binance:BTC'])
  })

  it('asks the backend for the whole cached Binance directory in one request', async () => {
    const fetcher = vi.fn(async (_input: string | URL | Request) => json({ directory_status: 'observed', coins: [] }))
    vi.stubGlobal('fetch', fetcher)
    await searchLabCoins('', new AbortController().signal)
    const url = new URL(String(fetcher.mock.calls[0]![0]), 'http://localhost')
    expect(url.pathname).toBe('/api/pair-rotation/coins')
    expect(url.searchParams.get('venue')).toBe('binance')
    expect(url.searchParams.get('limit')).toBe('1000')
  })
})

describe('Cache-first pair open', () => {
  it('renders a prepared pair from /analysis without spawning /open', async () => {
    const fetcher = vi.fn(async (input: string | URL | Request) => {
      const path = String(input)
      if (path.endsWith('/open')) return json({ operation_id: 'op-1' }, 202)
      if (path.includes('/operations/')) return json({ status: 'completed' })
      return json(analysis())
    })
    vi.stubGlobal('fetch', fetcher)
    const result = await loadLab(request, new AbortController().signal, noop)
    expect(result.coin_a.code).toBe('BTC')
    expect(fetcher.mock.calls.some(([path]) => String(path).endsWith('/open'))).toBe(false)
    expect(fetcher.mock.calls.some(([path]) => String(path).includes('/analysis?'))).toBe(true)
  })

  it('prepares the pair once when cached history is missing, then reads the analysis', async () => {
    let prepared = false
    const fetcher = vi.fn(async (input: string | URL | Request) => {
      const path = String(input)
      if (path.endsWith('/open')) { prepared = true; return json({ operation_id: 'op-1' }, 202) }
      if (path.includes('/operations/')) return json({ status: 'completed' })
      if (!prepared) return json({ error: { message: 'Pair history is not prepared.' } }, 409)
      return json(analysis())
    })
    vi.stubGlobal('fetch', fetcher)
    const result = await loadLab(request, new AbortController().signal, noop)
    expect(result.bar).toBe('1h')
    expect(fetcher.mock.calls.filter(([path]) => String(path).endsWith('/open'))).toHaveLength(1)
  })

  it('forces a fresh /open sync when the user asks for one', async () => {
    const fetcher = vi.fn(async (input: string | URL | Request) => {
      const path = String(input)
      if (path.endsWith('/open')) return json({ operation_id: 'op-1' }, 202)
      if (path.includes('/operations/')) return json({ status: 'completed' })
      return json(analysis())
    })
    vi.stubGlobal('fetch', fetcher)
    await loadLab(request, new AbortController().signal, noop, true)
    const paths = fetcher.mock.calls.map(([path]) => String(path))
    expect(paths.filter((path) => path.endsWith('/open'))).toHaveLength(1)
    expect(paths.findIndex((path) => path.endsWith('/open'))).toBeLessThan(paths.findIndex((path) => path.includes('/analysis?')))
  })

  it('rethrows an aborted analysis instead of preparing the pair', async () => {
    const controller = new AbortController()
    const fetcher = vi.fn(async (_input: string | URL | Request) => { controller.abort(); throw new DOMException('Aborted', 'AbortError') })
    vi.stubGlobal('fetch', fetcher)
    await expect(loadLab(request, controller.signal, noop)).rejects.toThrow('Aborted')
    expect(fetcher.mock.calls.some(([path]) => String(path).endsWith('/open'))).toBe(false)
  })

  it.each([422, 500])('shows a %s analysis failure without starting a history download', async (status) => {
    const fetcher = vi.fn(async () => json({ error: { message: 'Analysis rejected.' } }, status))
    vi.stubGlobal('fetch', fetcher)
    await expect(loadLab(request, new AbortController().signal, noop)).rejects.toThrow('Analysis rejected.')
    expect(fetcher).toHaveBeenCalledTimes(1)
  })
})


describe('Preparation contention', () => {
  it('waits for a busy operation and then prepares the current pair', async () => {
    vi.useFakeTimers()
    let opens = 0
    const progress = vi.fn()
    vi.stubGlobal('fetch', vi.fn(async (input: string | URL | Request) => {
      const path = String(input)
      if (path.endsWith('/open')) {
        opens += 1
        return opens === 1 ? json({ error: { code: 'operation_busy', message: 'Busy' } }, 409) : json({ operation_id: 'next' })
      }
      if (path.includes('/operations/')) return json({ status: 'completed' })
      return json(analysis())
    }))
    try {
      const result = loadLab(request, new AbortController().signal, progress, true)
      await vi.advanceTimersByTimeAsync(1000)
      expect((await result).coin_a.code).toBe('BTC')
      expect(opens).toBe(2)
      expect(progress).toHaveBeenCalledWith(expect.objectContaining({ stage: 'Waiting for previous data preparation' }))
    } finally { vi.useRealTimers() }
  })

  it('stops retrying when the user changes the pair', async () => {
    const controller = new AbortController()
    const fetcher = vi.fn(async () => json({ error: { code: 'operation_busy' } }, 409))
    vi.stubGlobal('fetch', fetcher)
    const result = loadLab(request, controller.signal, () => controller.abort(), true)
    await expect(result).rejects.toMatchObject({ name: 'AbortError' })
    expect(fetcher).toHaveBeenCalledTimes(1)
  })

  it('sends explicit no-anchor analysis without preparing an anchor', async () => {
    const fetcher = vi.fn(async () => json(analysis()))
    vi.stubGlobal('fetch', fetcher)
    await loadLab({ ...request, anchor: 'none' }, new AbortController().signal, noop)
    expect(fetcher.mock.calls).toHaveLength(1)
    expect(fetcher).toHaveBeenCalledWith(expect.stringContaining('anchor=none'), expect.anything())
  })

  it('requests 1m base_interval when preparing a 1m pair analysis', async () => {
    let prepared = false
    const openBodies: unknown[] = []
    vi.stubGlobal('fetch', vi.fn(async (input: string | URL | Request, init?: RequestInit) => {
      const path = String(input)
      if (path.endsWith('/open')) {
        prepared = true
        openBodies.push(JSON.parse(String(init?.body)))
        return json({ operation_id: 'op-1m' }, 202)
      }
      if (path.includes('/operations/')) return json({ status: 'completed' })
      if (!prepared) return json({ error: { message: 'Missing 1m history.' } }, 409)
      return json({ ...analysis(), bar: '1m' })
    }))
    const result = await loadLab({ ...request, bar: '1m', days: 30, band_lookback: 1440 }, new AbortController().signal, noop)
    expect(result.bar).toBe('1m')
    expect(openBodies).toEqual([
      { coin_a: 'binance:BTC', coin_b: 'binance:ETH', base_interval: '1m', lookback_days: 30, include_execution: true },
    ])
  })
})
