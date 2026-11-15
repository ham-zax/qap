/**
 * Plain-TypeScript statistics for the browser demo data only.
 *
 * Real measurements come from the backend (statsmodels and scipy). These are just
 * enough to make sample data internally consistent for design review.
 */

export function mean(values: readonly number[]): number {
  let sum = 0
  for (const value of values) sum += value
  return sum / values.length
}

export function logReturns(close: readonly number[]): number[] {
  const out: number[] = new Array(close.length - 1)
  for (let i = 1; i < close.length; i += 1) out[i - 1] = Math.log(close[i] / close[i - 1])
  return out
}

export function pearson(x: readonly number[], y: readonly number[]): number {
  const mx = mean(x)
  const my = mean(y)
  let sxy = 0
  let sxx = 0
  let syy = 0
  for (let i = 0; i < x.length; i += 1) {
    const dx = x[i] - mx
    const dy = y[i] - my
    sxy += dx * dy
    sxx += dx * dx
    syy += dy * dy
  }
  return sxy / Math.sqrt(sxx * syy)
}

function ranks(values: readonly number[]): number[] {
  const order = values.map((_, index) => index).sort((a, b) => values[a] - values[b])
  const out: number[] = new Array(values.length)
  order.forEach((index, rank) => {
    out[index] = rank
  })
  return out
}

export function spearman(x: readonly number[], y: readonly number[]): number {
  return pearson(ranks(x), ranks(y))
}

export function olsSlope(x: readonly number[], y: readonly number[]): number {
  const mx = mean(x)
  const my = mean(y)
  let sxy = 0
  let sxx = 0
  for (let i = 0; i < x.length; i += 1) {
    sxy += (x[i] - mx) * (y[i] - my)
    sxx += (x[i] - mx) ** 2
  }
  return sxy / sxx
}

export function rSquared(x: readonly number[], y: readonly number[]): number {
  return pearson(x, y) ** 2
}

export function halfLifeBars(logRatio: readonly number[]): number | null {
  const lagged = logRatio.slice(0, -1)
  const delta = logRatio.slice(1).map((value, index) => value - logRatio[index])
  const phi = 1 + olsSlope(lagged, delta)
  return phi > 0 && phi < 1 ? -Math.LN2 / Math.log(phi) : null
}

export function hurstExponent(logRatio: readonly number[]): number {
  const lags = [2, 4, 8, 16, 32, 64]
  const x: number[] = []
  const y: number[] = []
  for (const lag of lags) {
    const diffs: number[] = []
    for (let i = lag; i < logRatio.length; i += 1) diffs.push(logRatio[i] - logRatio[i - lag])
    const m = mean(diffs)
    const sd = Math.sqrt(mean(diffs.map((d) => (d - m) ** 2)))
    x.push(Math.log(lag))
    y.push(Math.log(sd))
  }
  return olsSlope(x, y)
}

/** Lag (bars) at which the coin's returns correlate most with the anchor's earlier returns. */
export function peakLag(coin: readonly number[], anchor: readonly number[], maxLag: number) {
  let best = { lag: 0, correlation: 0 }
  for (let lag = -maxLag; lag <= maxLag; lag += 1) {
    const left = lag >= 0 ? coin.slice(lag) : coin.slice(0, coin.length + lag)
    const right = lag >= 0 ? anchor.slice(0, anchor.length - lag) : anchor.slice(-lag)
    const c = pearson(left, right)
    if (Math.abs(c) > Math.abs(best.correlation)) best = { lag, correlation: c }
  }
  return best
}

/** Trailing mean and sample deviation, null until a full window exists. */
export function rollingMeanStd(values: readonly number[], lookback: number) {
  const meanOut: (number | null)[] = new Array(values.length).fill(null)
  const stdOut: (number | null)[] = new Array(values.length).fill(null)
  let sum = 0
  let squares = 0
  for (let i = 0; i < values.length; i += 1) {
    sum += values[i]
    squares += values[i] * values[i]
    if (i >= lookback) {
      sum -= values[i - lookback]
      squares -= values[i - lookback] * values[i - lookback]
    }
    if (i >= lookback - 1) {
      const m = sum / lookback
      meanOut[i] = m
      stdOut[i] = Math.sqrt(Math.max((squares - lookback * m * m) / (lookback - 1), 0))
    }
  }
  return { mean: meanOut, std: stdOut }
}

export function percentileOfLast(values: readonly number[]): number {
  const last = values[values.length - 1]
  let atOrBelow = 0
  for (const value of values) if (value <= last) atOrBelow += 1
  return (atOrBelow / values.length) * 100
}

/** Deterministic PRNG (mulberry32) with Box–Muller normals. */
export function createRandom(seed: number) {
  let state = seed >>> 0
  const uniform = () => {
    state = (state + 0x6d2b79f5) >>> 0
    let t = state
    t = Math.imul(t ^ (t >>> 15), t | 1)
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61)
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
  let spare: number | null = null
  const normal = () => {
    if (spare !== null) {
      const value = spare
      spare = null
      return value
    }
    const u = Math.max(uniform(), 1e-12)
    const v = uniform()
    const radius = Math.sqrt(-2 * Math.log(u))
    spare = radius * Math.sin(2 * Math.PI * v)
    return radius * Math.cos(2 * Math.PI * v)
  }
  return { uniform, normal }
}

export function hashSeed(text: string): number {
  let hash = 2166136261
  for (let i = 0; i < text.length; i += 1) {
    hash ^= text.charCodeAt(i)
    hash = Math.imul(hash, 16777619)
  }
  return hash >>> 0
}
