/**
 * Crosshair readouts for the Lab charts. Presentation only: every value is read
 * from series the analysis or study already returned. Nothing here derives a
 * trading action, a threshold crossing or a recommendation.
 */
import type { LabAnalysis } from './labContract'
import type { LabStudy } from './labStudyApi'

export type LabWealth = NonNullable<LabStudy['result']['wealth']>

export interface ReadoutRow {
  key: string
  label: string
  value: string
  /** CSS colour token of the drawn series, when the row has a line on the chart. */
  swatch?: { token: string; dashed: boolean }
}

export interface Readout {
  /** `YYYY-MM-DD HH:MM UTC` of the bar the values belong to. */
  time: string
  /** True when no bar is hovered and the readout shows the latest bar. */
  latest: boolean
  rows: ReadoutRow[]
}

export const UNAVAILABLE = 'Unavailable'

/**
 * Index of the bar at `timestamp`, or of the latest bar when `timestamp` is null.
 * Falls back to the last bar at or before the timestamp. Returns -1 for no bars.
 */
export function barIndexAt(times: readonly number[], timestamp: string | null): number {
  if (times.length === 0) return -1
  if (timestamp === null) return times.length - 1
  const target = Date.parse(timestamp) / 1000
  if (!Number.isFinite(target)) return times.length - 1
  let low = 0
  let high = times.length - 1
  if (target < times[0]!) return 0
  while (low < high) {
    const middle = Math.ceil((low + high) / 2)
    if (times[middle]! <= target) low = middle
    else high = middle - 1
  }
  return low
}

/** (ratio − mean) / std. Null when any input is missing or the deviation is zero. */
export function zScore(ratio: number | null | undefined, mean: number | null | undefined, std: number | null | undefined): number | null {
  if (ratio == null || mean == null || std == null) return null
  if (!Number.isFinite(ratio) || !Number.isFinite(mean) || !Number.isFinite(std) || std === 0) return null
  return (ratio - mean) / std
}

export function formatUtcSeconds(seconds: number): string {
  const date = new Date(seconds * 1000)
  if (Number.isNaN(date.getTime())) return UNAVAILABLE
  return `${date.toISOString().slice(0, 16).replace('T', ' ')} UTC`
}

function finite(value: number | null | undefined): value is number {
  return value != null && Number.isFinite(value)
}

/** Ratio values keep six significant digits so small ratios stay readable. */
export function formatRatio(value: number | null | undefined): string {
  return finite(value) ? value.toLocaleString('en-US', { maximumSignificantDigits: 6 }) : UNAVAILABLE
}

export function formatZ(value: number | null): string {
  return finite(value)
    ? value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2, signDisplay: 'exceptZero' })
    : UNAVAILABLE
}

/** USDT prices: two decimals from 1 upwards, six significant digits below 1. */
export function formatUsdt(value: number | null | undefined): string {
  if (!finite(value)) return UNAVAILABLE
  const text = Math.abs(value) >= 1
    ? value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    : value.toLocaleString('en-US', { maximumSignificantDigits: 6 })
  return `${text} USDT`
}

export interface RatioReadoutOptions {
  /** Bands are drawn on the chart. The values show either way. */
  bands: boolean
  /** The anchor line is drawn on the chart. */
  anchor: boolean
}

export function ratioReadout(analysis: LabAnalysis, timestamp: string | null, options: RatioReadoutOptions): Readout | null {
  const data = analysis.series
  const index = barIndexAt(data.time, timestamp)
  if (index < 0) return null
  const ratio = data.ratio[index]
  const mean = data.mean[index]
  const std = data.std[index]
  const band = (multiplier: number) => finite(mean) && finite(std) ? mean + multiplier * std : null
  const swatch = (token: string, dashed: boolean, drawn: boolean) => drawn ? { swatch: { token, dashed } } : {}
  const rows: ReadoutRow[] = [
    { key: 'ratio', label: `${analysis.coin_a.code} per ${analysis.coin_b.code}`, value: formatRatio(ratio), swatch: { token: '--chart-series-1', dashed: false } },
    { key: 'mean', label: 'Usual level', value: formatRatio(mean), ...swatch('--qap-muted', true, options.bands) },
    { key: 'upper', label: 'Normal range, top', value: formatRatio(band(2)), ...swatch('--qap-border-strong', true, options.bands) },
    { key: 'lower', label: 'Normal range, bottom', value: formatRatio(band(-2)), ...swatch('--qap-border-strong', true, options.bands) },
    { key: 'z', label: 'How unusual', value: formatZ(zScore(ratio, mean, std)) },
  ]
  if (analysis.anchor && data.anchor_close) {
    rows.push({
      key: 'anchor',
      label: analysis.anchor.code,
      value: formatUsdt(data.anchor_close[index]),
      ...swatch('--qap-muted', false, options.anchor),
    })
  }
  return { time: formatUtcSeconds(data.time[index]!), latest: timestamp === null, rows }
}

export const WEALTH_LABELS: Record<string, string> = {
  strategy: 'Rotating',
  hodl: 'Just holding',
  hold_a: 'Hold coin A',
  hold_b: 'Hold coin B',
  daily: 'Rebalance daily',
  weekly: 'Rebalance weekly',
  drift: 'Rebalance at 5% drift',
}

/** Strategy first, then HODL and the selected control. Extra holds stay out of the chart. */
export function wealthNames(wealth: LabWealth): string[] {
  const control = Object.keys(wealth.value).find((name) => !['strategy', 'hodl', 'hold_a', 'hold_b'].includes(name))
  return ['strategy', 'hodl', control].filter((name): name is string => Boolean(name && wealth.value[name]))
}

export function wealthColorToken(name: string): string {
  return name === 'strategy' ? '--qap-accent' : name === 'hodl' ? '--qap-muted' : '--qap-border-strong'
}

export function wealthReadout(wealth: LabWealth, timestamp: string | null): Readout | null {
  const index = barIndexAt(wealth.time, timestamp)
  if (index < 0) return null
  const last = index === wealth.time.length - 1
  // The final bar uses the study's recorded terminal value, not the plotted float.
  const valueAt = (name: string) => {
    const terminal = Number(wealth.terminal_values[name])
    return last && Number.isFinite(terminal) ? terminal : wealth.value[name]?.[index]
  }
  const rows = wealthNames(wealth).map((name) => ({
    key: name,
    label: WEALTH_LABELS[name] ?? 'Rebalance',
    value: formatUsdt(valueAt(name)),
    swatch: { token: wealthColorToken(name), dashed: name !== 'strategy' },
  }))
  return { time: formatUtcSeconds(wealth.time[index]!), latest: timestamp === null, rows }
}

/** One sentence for screen readers. Always describes the latest bar. */
export function readoutSentence(title: string, readout: Readout): string {
  return `${title}, latest bar ${readout.time}: ${readout.rows.map((row) => `${row.label} ${row.value}`).join(', ')}.`
}
