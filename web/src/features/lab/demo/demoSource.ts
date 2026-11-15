/**
 * Browser-generated sample data for design review (dev builds only).
 *
 * Deterministic per pair and bar size, with planted structure (a shared market
 * factor, a BNB-style ecosystem factor, a mean-reverting ratio) so every chart,
 * measurement and state has something believable to show. Always labelled
 * "Sample data" in the UI; it is never market data.
 */
import {
  DEFAULT_ANCHORS,
  BAR_MINUTES,
  type LabAnalysis,
  type LabAnchorFit,
  type LabAnchorLink,
  type LabBar,
  type LabCoin,
  type LabCoinMatch,
  type LabRequest,
} from '../labContract'
import {
  createRandom,
  hashSeed,
  halfLifeBars,
  hurstExponent,
  logReturns,
  mean,
  olsSlope,
  peakLag,
  pearson,
  percentileOfLast,
  rSquared,
  rollingMeanStd,
  spearman,
} from './demoStats'

const COINS: Array<[string, string, LabCoin['identity_state']]> = [
  ['BTC', 'Bitcoin', 'resolved'],
  ['ETH', 'Ethereum', 'resolved'],
  ['BNB', 'BNB', 'resolved'],
  ['SOL', 'Solana', 'resolved'],
  ['ARB', 'Arbitrum', 'resolved'],
  ['OP', 'Optimism', 'resolved'],
  ['CAKE', 'PancakeSwap', 'resolved'],
  ['XVS', 'Venus', 'resolved'],
  ['LINK', 'Chainlink', 'resolved'],
  ['AVAX', 'Avalanche', 'resolved'],
  ['W', 'Wormhole', 'unresolved'],
  ['PIXEL', 'Pixels', 'unresolved'],
]

export const DEMO_COINS: LabCoin[] = COINS.map(([code, name, identity_state]) => ({
  id: `binance:${code}`,
  code,
  name,
  identity_state,
}))

export const DEMO_DEFAULT_PAIR = { a: 'binance:ARB', b: 'binance:OP' } as const
export const DEMO_SUGGESTED_PAIRS: Array<[string, string]> = [
  ['binance:ARB', 'binance:OP'],
  ['binance:CAKE', 'binance:XVS'],
  ['binance:LINK', 'binance:AVAX'],
  ['binance:W', 'binance:PIXEL'],
]

function coinById(id: string): LabCoin {
  return DEMO_COINS.find((coin) => coin.id === id) ?? { id, code: id.split(':')[1] ?? id, name: id, identity_state: 'unresolved' }
}

export function demoSearch(query: string, limit = 8): LabCoinMatch[] {
  const needle = query.trim().toLowerCase().replace(/[/_-]?usdt$/, '').replace(/[/_-]/g, '')
  return DEMO_COINS.filter(
    (coin) => !needle || coin.code.toLowerCase().includes(needle) || coin.name.toLowerCase().includes(needle),
  )
    .slice(0, limit)
    .map((coin) => ({ ...coin, source: 'Sample data', call_available: coin.identity_state === 'resolved' }))
}

interface Universe {
  time: number[]
  closes: Map<string, number[]>
}

const cache = new Map<string, Universe>()
const YEAR_DAYS = 365

/** One year of aligned closes for the pair and every anchor candidate at one bar size. */
function universe(ids: readonly string[], bar: LabBar): Universe {
  const key = `${[...ids].sort().join('|')}|${bar}`
  const hit = cache.get(key)
  if (hit) return hit
  const minutes = BAR_MINUTES[bar]
  const count = Math.floor((YEAR_DAYS * 1440) / minutes)
  const scale = Math.sqrt(minutes / 15)
  const random = createRandom(hashSeed(key))
  const m: number[] = []
  const e: number[] = []
  for (let i = 0; i < count; i += 1) {
    m.push(random.normal())
    e.push(random.normal())
  }
  const noise = () => random.normal()
  const kappa = 0.004 * (minutes / 15)
  const [idA, idB] = ids
  const returns = new Map<string, number[]>()
  const anchorSpec: Record<string, [number, number, number]> = {
    'binance:BTC': [1.0, 0, 0.35],
    'binance:ETH': [0.9, 0.2, 0.55],
    'binance:BNB': [0.6, 0.9, 0.5],
    'binance:SOL': [0.8, 0.1, 0.85],
  }
  for (const id of DEFAULT_ANCHORS) {
    const [lm, le, li] = anchorSpec[id]
    returns.set(id, m.map((value, i) => scale * 0.0022 * (lm * value + le * e[i] + li * noise())))
  }
  const closesFor = (id: string, start: number) => {
    const out = new Array<number>(count)
    let level = Math.log(start)
    for (let i = 0; i < count; i += 1) {
      level += returns.get(id)?.[i] ?? 0
      out[i] = Math.exp(level)
    }
    return out
  }
  // The pair: shared factors plus a ratio that reverts, so the picture has structure.
  const retA: number[] = []
  const retB: number[] = []
  let lr = 0
  for (let i = 0; i < count; i += 1) {
    const lagged = i >= 3 ? e[i - 3] : 0
    const pull = (kappa / 2) * lr
    const a = scale * 0.0022 * (0.6 * m[i] + 1.1 * e[i] + 1.3 * noise()) - pull
    const b = scale * 0.0022 * (0.5 * m[i] + 0.9 * lagged + 1.3 * noise()) + pull
    retA.push(a)
    retB.push(b)
    lr += a - b
  }
  returns.set(idA, retA)
  returns.set(idB, retB)
  const starts: Record<string, number> = { 'binance:BTC': 64000, 'binance:ETH': 3100, 'binance:BNB': 590, 'binance:SOL': 150 }
  const closes = new Map<string, number[]>()
  for (const id of [...DEFAULT_ANCHORS, idA, idB]) {
    closes.set(id, closesFor(id, starts[id] ?? 0.4 + (hashSeed(id) % 300) / 100))
  }
  const step = minutes * 60
  const end = Math.floor(Date.now() / 1000 / step) * step - step
  const time = Array.from({ length: count }, (_, i) => end - (count - 1 - i) * step)
  const built = { time, closes }
  cache.set(key, built)
  return built
}

function fit(r: ReturnType<typeof logReturns>, anchor: ReturnType<typeof logReturns>): LabAnchorLink {
  const half = Math.floor(r.length / 2)
  const first = peakLag(r.slice(0, half), anchor.slice(0, half), 8)
  const second = peakLag(r.slice(half), anchor.slice(half), 8)
  const overall = peakLag(r, anchor, 8)
  return {
    beta: olsSlope(anchor, r),
    r_squared: rSquared(anchor, r),
    lead_lag: {
      lag_bars: overall.lag,
      correlation: overall.correlation,
      stable: Math.abs(first.lag - second.lag) <= 1 && Math.abs(overall.lag - first.lag) <= 1,
    },
  }
}

export function demoAnalysis(request: LabRequest): LabAnalysis {
  const candidates = DEFAULT_ANCHORS.filter((id) => id !== request.coin_a && id !== request.coin_b)
  const data = universe([request.coin_a, request.coin_b], request.bar)
  const minutes = BAR_MINUTES[request.bar]
  const want = Math.min(Math.floor((request.days * 1440) / minutes), data.time.length)
  const from = data.time.length - want
  const slice = (id: string) => (data.closes.get(id) ?? []).slice(from)
  const a = slice(request.coin_a)
  const b = slice(request.coin_b)
  const ratio = a.map((value, i) => value / b[i])
  const lookback = Math.min(request.band_lookback, Math.max(2, ratio.length - 1))
  const bands = rollingMeanStd(ratio, lookback)
  const ra = logReturns(a)
  const rb = logReturns(b)
  const logRatio = ratio.map(Math.log)

  const ranking: LabAnchorFit[] = candidates
    .map((id) => {
      const rr = logReturns(slice(id))
      const ba = rSquared(rr, ra)
      const bb = rSquared(rr, rb)
      return { anchor: coinById(id), beta_a: olsSlope(rr, ra), beta_b: olsSlope(rr, rb), joint_explained: (ba + bb) / 2 }
    })
    .sort((x, y) => y.joint_explained - x.joint_explained)
  const selectedId = request.anchor && candidates.includes(request.anchor) ? request.anchor : ranking[0]?.anchor.id ?? null
  const anchorReturns = selectedId ? logReturns(slice(selectedId)) : null
  const halfLife = halfLifeBars(logRatio)
  const hurst = hurstExponent(logRatio)
  const recentVol = mean(logReturns(ratio).slice(-lookback).map((x) => x * x)) ** 0.5
  const volSeries = logReturns(ratio)
  const vols: number[] = []
  for (let i = lookback; i < volSeries.length; i += Math.max(1, Math.floor(lookback / 4))) {
    vols.push(mean(volSeries.slice(i - lookback, i).map((x) => x * x)) ** 0.5)
  }
  vols.push(recentVol)
  const volPct = percentileOfLast(vols)
  const tail = logRatio.slice(-lookback)
  const path = tail.slice(1).reduce((sum, value, i) => sum + Math.abs(value - tail[i]), 0)
  const efficiency = path === 0 ? 0 : Math.abs(tail[tail.length - 1] - tail[0]) / path
  const rho = pearson(ra, rb)
  const fingerprint = (id: string) => hashSeed(`${id}|${request.bar}`).toString(16).padStart(8, '0').repeat(8)
  const interval = request.bar
  const coverageStart = new Date(data.time[from] * 1000).toISOString()
  const cutoff = new Date((data.time[data.time.length - 1] + minutes * 60) * 1000).toISOString()

  return {
    schema_version: 'qap.api.pair-rotation-analysis.v1',
    demo: true,
    coin_a: coinById(request.coin_a),
    coin_b: coinById(request.coin_b),
    bar: request.bar,
    window_days: request.days,
    band_lookback: lookback,
    data_through: cutoff,
    bars_used: a.length,
    identity_confirmed: coinById(request.coin_a).identity_state === 'resolved' && coinById(request.coin_b).identity_state === 'resolved',
    series: {
      time: data.time.slice(from),
      close_a: a,
      close_b: b,
      ratio,
      mean: bands.mean,
      std: bands.std,
      anchor_close: selectedId ? slice(selectedId) : null,
    },
    anchor: selectedId ? coinById(selectedId) : null,
    anchor_ranking: ranking,
    measurements: {
      correlation: { pearson: rho, spearman: spearman(ra, rb), kendall: (2 / Math.PI) * Math.asin(rho), observations: ra.length },
      cointegration: { statistic: -4.31, p_value: 0.0094, level: 0.05, passes: true },
      hedge_ratio: (() => {
        const la = a.map(Math.log)
        const lb = b.map(Math.log)
        const ols = olsSlope(lb, la)
        const h = Math.floor(la.length / 2)
        const first = olsSlope(lb.slice(0, h), la.slice(0, h))
        const second = olsSlope(lb.slice(h), la.slice(h))
        return { ols, tls: ols / Math.max(0.5, Math.sqrt(rSquared(lb, la))), first_half_ols: first, second_half_ols: second, stable: Math.abs(first - second) / Math.max(Math.abs(first), Math.abs(second), 1e-9) <= 0.25 }
      })(),
      half_life: { bars: halfLife, reverting: halfLife !== null },
      hurst: { exponent: hurst, reading: hurst < 0.45 ? 'reverting' : hurst > 0.55 ? 'trending' : 'random' },
      ratio_percentile: percentileOfLast(ratio),
      regime: {
        volatility: volPct < 33 ? 'calm' : volPct > 67 ? 'stressed' : 'normal',
        volatility_percentile: volPct,
        trend: efficiency > 0.3 ? 'trending' : 'ranging',
        efficiency,
      },
      anchor_a: anchorReturns ? fit(ra, anchorReturns) : null,
      anchor_b: anchorReturns ? fit(rb, anchorReturns) : null,
      // The sample source does not imitate the dependence fits; they stay unavailable.
      kalman: null,
      granger: null,
      copula: null,
      rolling_dependence: null,
    },
    datasets: [request.coin_a, request.coin_b, ...(selectedId ? [selectedId] : [])].map((id) => ({
      dataset_id: `binance-spot:${id.split(':')[1]}USDT:1:1:${interval}`,
      interval,
      venue_symbol: `${id.split(':')[1]}USDT`,
      semantic_fingerprint: fingerprint(id),
      coverage_start: coverageStart,
      cutoff,
    })),
  }
}

/** Simulates the background download so the progress state can be reviewed. */
export function demoOpen(onProgress: (stage: string, completed: number, total: number) => void): Promise<void> {
  const stages = ['directory', 'identity', 'ARBUSDT 15m', 'OPUSDT 15m', 'ARBUSDT 1h', 'OPUSDT 1h', 'ARBUSDT 4h', 'OPUSDT 4h']
  return new Promise((resolve) => {
    let done = 0
    const tick = () => {
      onProgress(stages[Math.min(done, stages.length - 1)], done, stages.length)
      if (done >= stages.length) return resolve()
      done += 1
      setTimeout(tick, 260)
    }
    tick()
  })
}
