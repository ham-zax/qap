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

export async function labJson<T>(path: string, signal: AbortSignal, body?: object): Promise<T> {
  const response = await fetch(`${import.meta.env.VITE_QAP_API_BASE_URL ?? ''}${path}`, {
    signal,
    ...(body ? { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) } : {}),
  })
  const value = await response.json()
  if (!response.ok) throw new Error(value.error?.message ?? `Request failed (${response.status})`)
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
  const started = await labJson<{ operation_id: string }>(path, signal, body)
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

export async function searchLabCoins(query: string, signal: AbortSignal): Promise<{ ready: boolean; coins: LabCoinMatch[] }> {
  const found = await labJson<CoinSearch>(`/api/pair-rotation/coins?q=${encodeURIComponent(query)}&limit=100`, signal)
  return {
    ready: found.directory_status !== 'not_refreshed',
    coins: found.coins.filter((coin) => coin.venue === 'binance' && coin.trading).map((coin) => ({ id: coin.listing_id, code: coin.venue_asset_code, name: coin.name,
      identity_state: coin.identity_state, source: coin.source, call_available: coin.call_available })),
  }
}

export const bootstrapLab = (signal: AbortSignal, progress: (value: LabProgress) => void) =>
  operation('/api/pair-rotation/bootstrap', {}, signal, progress)

export async function loadLab(request: LabRequest, signal: AbortSignal, progress: (value: LabProgress) => void, prepare = true): Promise<LabAnalysis> {
  if (prepare) {
    await operation('/api/pair-rotation/open', { coin_a: request.coin_a, coin_b: request.coin_b, include_execution: true }, signal, progress)
    if (request.anchor && ![request.coin_a, request.coin_b].includes(request.anchor)) {
      progress({ stage: 'Loading anchor history', completed: 0, total: 1 })
      await operation('/api/pair-rotation/open', { coin_a: request.coin_a, coin_b: request.anchor }, signal, progress)
    }
  }
  progress({ stage: 'Measuring the relationship', completed: 0, total: 1 })
  const query = new URLSearchParams({ coin_a: request.coin_a, coin_b: request.coin_b, bar: request.bar,
    days: String(request.days), band_lookback: String(request.band_lookback) })
  if (request.anchor) query.set('anchor', request.anchor)
  return labJson<LabAnalysis>(`/api/pair-rotation/analysis?${query}`, signal)
}
