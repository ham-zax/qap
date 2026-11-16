import type { LabAnalysis, LabCoinMatch, LabProgress, LabRequest } from './labContract'

interface CoinSearch {
  directory_status: string
  coins: Array<{ listing_id: string; venue: string; trading: boolean; venue_asset_code: string; name: string; identity_state: LabCoinMatch['identity_state']; source: string; call_available: boolean }>
}

interface Operation {
  status: string
  progress: LabProgress | null
  failure?: { message: string } | null
}

class LabRequestError extends Error {
  constructor(message: string, readonly status: number, readonly code?: string) { super(message) }
}

export async function labJson<T>(path: string, signal: AbortSignal, body?: object): Promise<T> {
  const response = await fetch(`${import.meta.env.VITE_QAP_API_BASE_URL ?? ''}${path}`, {
    signal,
    ...(body ? { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) } : {}),
  })
  const value = await response.json()
  if (!response.ok) throw new LabRequestError(value.error?.message ?? `Request failed (${response.status})`, response.status, value.error?.code)
  return value as T
}

function pause(signal: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    const abort = () => { clearTimeout(timer); reject(new DOMException('Aborted', 'AbortError')) }
    const timer = setTimeout(() => { signal.removeEventListener('abort', abort); resolve() }, 1000)
    signal.addEventListener('abort', abort, { once: true })
    if (signal.aborted) abort()
  })
}

async function operation(path: string, body: object, signal: AbortSignal, progress: (value: LabProgress) => void) {
  let started: { operation_id: string } | undefined
  for (let attempt = 0; attempt < 1200; attempt += 1) {
    signal.throwIfAborted()
    try {
      started = await labJson<{ operation_id: string }>(path, signal, body)
      break
    } catch (cause) {
      if (!(cause instanceof LabRequestError) || cause.code !== 'operation_busy' || cause.status !== 409) throw cause
      progress({ stage: 'Waiting for previous data preparation', completed: 0, total: 1 })
      await pause(signal)
    }
  }
  if (!started) throw new Error('Data preparation is still busy. Retry to continue.')
  for (let attempt = 0; attempt < 1200; attempt += 1) {
    const current = await labJson<Operation>(`/api/operations/${encodeURIComponent(started.operation_id)}`, signal)
    if (current.progress) progress(current.progress)
    if (current.status === 'completed') return
    if (['failed', 'interrupted', 'cancelled'].includes(current.status)) {
      throw new Error(current.failure?.message ?? 'Data preparation stopped. Retry to continue.')
    }
    await pause(signal)
  }
  throw new Error('Data preparation took too long. Retry to resume.')
}

/**
 * One request returns every eligible Binance Spot USDT listing: the backend filters
 * `venue=binance` and serves the cached 396-coin directory in ~2.4 ms warm.
 */
export async function searchLabCoins(query: string, signal: AbortSignal): Promise<{ ready: boolean; coins: LabCoinMatch[] }> {
  const found = await labJson<CoinSearch>(`/api/pair-rotation/coins?q=${encodeURIComponent(query)}&venue=binance&limit=1000`, signal)
  return {
    ready: found.directory_status !== 'not_refreshed',
    coins: found.coins.filter((coin) => coin.venue === 'binance' && coin.trading).map((coin) => ({ id: coin.listing_id, code: coin.venue_asset_code, name: coin.name,
      identity_state: coin.identity_state, source: coin.source, call_available: coin.call_available })),
  }
}

export const bootstrapLab = (signal: AbortSignal, progress: (value: LabProgress) => void) =>
  operation('/api/pair-rotation/bootstrap', {}, signal, progress)

function analysisPath(request: LabRequest): string {
  const query = new URLSearchParams({ coin_a: request.coin_a, coin_b: request.coin_b, bar: request.bar,
    days: String(request.days), band_lookback: String(request.band_lookback) })
  if (request.anchor) query.set('anchor', request.anchor)
  return `/api/pair-rotation/analysis?${query}`
}

async function preparePair(request: LabRequest, signal: AbortSignal, progress: (value: LabProgress) => void) {
  const openBody = request.bar === '1m'
    ? { coin_a: request.coin_a, coin_b: request.coin_b, base_interval: '1m' as const, lookback_days: request.days, include_execution: true }
    : { coin_a: request.coin_a, coin_b: request.coin_b, include_execution: true }
  await operation('/api/pair-rotation/open', openBody, signal, progress)
  if (request.anchor && request.anchor !== 'none' && ![request.coin_a, request.coin_b].includes(request.anchor)) {
    progress({ stage: 'Loading anchor history', completed: 0, total: 1 })
    const anchorBody = request.bar === '1m'
      ? { coin_a: request.coin_a, coin_b: request.anchor, base_interval: '1m' as const, lookback_days: request.days }
      : { coin_a: request.coin_a, coin_b: request.anchor }
    await operation('/api/pair-rotation/open', anchorBody, signal, progress)
  }
}

/**
 * Cache-first: a prepared pair renders straight from `/analysis` in under two seconds.
 * `/open` only runs when the cached history is missing or the user asks for a fresh sync.
 */
export async function loadLab(request: LabRequest, signal: AbortSignal, progress: (value: LabProgress) => void, prepare = false): Promise<LabAnalysis> {
  const path = analysisPath(request)
  if (!prepare) {
    try {
      return await labJson<LabAnalysis>(path, signal)
    } catch (cause) {
      if (signal.aborted || !(cause instanceof LabRequestError) || cause.status !== 409) throw cause
      // No cached history for this pair yet: prepare it once, then read the analysis.
    }
  }
  await preparePair(request, signal, progress)
  progress({ stage: 'Measuring the relationship', completed: 0, total: 1 })
  return labJson<LabAnalysis>(path, signal)
}
