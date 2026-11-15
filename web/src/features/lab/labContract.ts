import type { components } from '../../api/schema'

export type LabBar = '1m' | '15m' | '1h' | '4h' | '1d'
export type LabDays = 30 | 90 | 180 | 365
export type LabViewMode = 'simple' | 'advanced'
export type LabSignalMethod = 'zscore' | 'copula' | 'trend' | 'lead_lag'
export type LabHedgeMethod = 'ratio' | 'ols' | 'tls' | 'kalman'
export type LabCrashDefenseMode = 'coins_only' | 'park_anchor' | 'park_usdt'
export type LabRotationPct = 25 | 50 | 75 | 100

export const LAB_BARS: readonly LabBar[] = ['1m', '15m', '1h', '4h', '1d']
export const LAB_DAYS: readonly LabDays[] = [30, 90, 180, 365]
export const LAB_ROTATION_PCTS: readonly LabRotationPct[] = [25, 50, 75, 100]

export interface LabCoin {
  id: string
  code: string
  name: string
  identity_state: 'resolved' | 'review' | 'unresolved'
}

export interface LabSeries {
  time: number[]
  close_a: number[]
  close_b: number[]
  ratio: number[]
  mean: (number | null)[]
  std: (number | null)[]
  anchor_close: number[] | null
}

export interface LabCorrelation {
  pearson: number
  spearman: number
  kendall: number
  observations: number
}

export interface LabLeadLag {
  lag_bars: number
  correlation: number
  stable: boolean
}

export interface LabAnchorLink {
  beta: number
  r_squared: number
  lead_lag: LabLeadLag | null
}

export interface LabGrangerDirection {
  lag_bars: number
  p_value: number
  passes: boolean
}

export interface LabMeasurements {
  correlation: LabCorrelation | null
  cointegration: { statistic: number; p_value: number; level: number; passes: boolean } | null
  hedge_ratio: { ols: number; tls: number; first_half_ols: number; second_half_ols: number; stable: boolean } | null
  half_life: { bars: number | null; reverting: boolean } | null
  hurst: { exponent: number; reading: 'reverting' | 'random' | 'trending' } | null
  ratio_percentile: number | null
  regime: {
    volatility: 'calm' | 'normal' | 'stressed'
    volatility_percentile: number
    trend: 'trending' | 'ranging'
    efficiency: number
  } | null
  anchor_a: LabAnchorLink | null
  anchor_b: LabAnchorLink | null
  kalman: { beta: number; standard_error: number; beta_change: number } | null
  granger: {
    a_to_b: LabGrangerDirection
    b_to_a: LabGrangerDirection
    max_lag: number
    observations: number
  } | null
  copula: { family: string; lower_tail: number; upper_tail: number; observations: number } | null
  rolling_dependence: { window_bars: number; latest: number; low: number; high: number } | null
}

export interface LabAnchorFit {
  anchor: LabCoin
  beta_a: number
  beta_b: number
  joint_explained: number
}

export interface LabDataset {
  dataset_id: string
  interval: string
  venue_symbol: string
  semantic_fingerprint: string
  coverage_start: string | null
  cutoff: string | null
}

export interface LabAnalysis {
  schema_version: 'qap.api.pair-rotation-analysis.v1'
  coin_a: LabCoin
  coin_b: LabCoin
  bar: LabBar
  window_days: number
  band_lookback: number
  data_through: string
  bars_used: number
  identity_confirmed: boolean
  series: LabSeries
  anchor: LabCoin | null
  anchor_ranking: LabAnchorFit[]
  measurements: LabMeasurements
  datasets: LabDataset[]
  demo?: true
}

export interface LabRequest {
  coin_a: string
  coin_b: string
  anchor: string | null
  bar: LabBar
  days: LabDays
  band_lookback: number
}

export interface LabProgress {
  stage: string
  completed: number
  total: number
}

export interface LabCoinMatch extends LabCoin {
  source: string
  call_available: boolean
}

export interface LabStrategyFormSettings {
  method: LabSignalMethod
  hedge_method: LabHedgeMethod
  lookback: number
  entry: number
  exit: number
  copula_probability: number
  copula_exit_band: number
  fast_window: number
  slow_window: number
  trend_deadband: number
  anchor_threshold: number
  rotation_pct: LabRotationPct
  crash_defense_mode: LabCrashDefenseMode
  auto_tune: boolean
  minimum_hold: number
  cooldown: number
  fee_bps: number
  slippage_bps: number
}

export const DEFAULT_STRATEGY_SETTINGS: LabStrategyFormSettings = {
  method: 'zscore',
  hedge_method: 'ratio',
  lookback: 96,
  entry: 2.0,
  exit: 0.5,
  copula_probability: 0.05,
  copula_exit_band: 0.15,
  fast_window: 12,
  slow_window: 48,
  trend_deadband: 0.002,
  anchor_threshold: 0.002,
  rotation_pct: 100,
  crash_defense_mode: 'coins_only',
  auto_tune: true,
  minimum_hold: 4,
  cooldown: 4,
  fee_bps: 10,
  slippage_bps: 5,
}

type BackendLabSettingsInput = Partial<components['schemas']['LabSettings-Input']>
type BackendLabSettingsOutput = Partial<components['schemas']['LabSettings-Output']>

export function toBackendLabSettings(form: LabStrategyFormSettings): BackendLabSettingsInput {
  const safeExit = Math.min(form.exit, Math.max(0, Number((form.entry - 0.05).toFixed(4))))
  const safeSlow = Math.max(form.slow_window, form.fast_window + 1)
  const safeCopulaExit = Math.min(
    form.copula_exit_band,
    Math.max(0.01, Number((0.49 - form.copula_probability).toFixed(4))),
  )
  return {
    method: form.method,
    hedge_method: form.hedge_method,
    lookback: form.lookback,
    entry: form.entry,
    exit: safeExit,
    copula_probability: form.copula_probability,
    copula_exit_band: safeCopulaExit,
    fast_window: form.fast_window,
    slow_window: safeSlow,
    trend_deadband: form.trend_deadband,
    anchor_threshold: form.anchor_threshold,
    rotation_size: Number((form.rotation_pct / 200).toFixed(4)),
    crash_defense_mode: form.crash_defense_mode,
    auto_tune: form.auto_tune,
    minimum_hold: form.minimum_hold,
    cooldown: form.cooldown,
    fee_bps: form.fee_bps,
    slippage_bps: form.slippage_bps,
  }
}

export function fromBackendLabSettings(raw: BackendLabSettingsOutput): LabStrategyFormSettings {
  const pctRaw = raw.rotation_size !== undefined ? Math.round(Number(raw.rotation_size) * 200) : 100
  const rotation_pct: LabRotationPct =
    pctRaw <= 37 ? 25 : pctRaw <= 62 ? 50 : pctRaw <= 87 ? 75 : 100
  return {
    method: raw.method ?? DEFAULT_STRATEGY_SETTINGS.method,
    hedge_method: raw.hedge_method ?? DEFAULT_STRATEGY_SETTINGS.hedge_method,
    lookback: raw.lookback ?? DEFAULT_STRATEGY_SETTINGS.lookback,
    entry: raw.entry ?? DEFAULT_STRATEGY_SETTINGS.entry,
    exit: raw.exit ?? DEFAULT_STRATEGY_SETTINGS.exit,
    copula_probability: raw.copula_probability ?? DEFAULT_STRATEGY_SETTINGS.copula_probability,
    copula_exit_band: raw.copula_exit_band ?? DEFAULT_STRATEGY_SETTINGS.copula_exit_band,
    fast_window: raw.fast_window ?? DEFAULT_STRATEGY_SETTINGS.fast_window,
    slow_window: raw.slow_window ?? DEFAULT_STRATEGY_SETTINGS.slow_window,
    trend_deadband: raw.trend_deadband ?? DEFAULT_STRATEGY_SETTINGS.trend_deadband,
    anchor_threshold: raw.anchor_threshold ?? DEFAULT_STRATEGY_SETTINGS.anchor_threshold,
    rotation_pct,
    crash_defense_mode: raw.crash_defense_mode ?? DEFAULT_STRATEGY_SETTINGS.crash_defense_mode,
    auto_tune: raw.auto_tune ?? DEFAULT_STRATEGY_SETTINGS.auto_tune,
    minimum_hold: raw.minimum_hold ?? DEFAULT_STRATEGY_SETTINGS.minimum_hold,
    cooldown: raw.cooldown ?? DEFAULT_STRATEGY_SETTINGS.cooldown,
    fee_bps: raw.fee_bps !== undefined ? Number(raw.fee_bps) : DEFAULT_STRATEGY_SETTINGS.fee_bps,
    slippage_bps: raw.slippage_bps !== undefined ? Number(raw.slippage_bps) : DEFAULT_STRATEGY_SETTINGS.slippage_bps,
  }
}

export const DEFAULT_ANCHORS: readonly string[] = ['binance:BTC', 'binance:ETH', 'binance:BNB', 'binance:SOL']

export const DEFAULT_BAND_LOOKBACK: Record<LabBar, number> = {
  '1m': 1440,
  '15m': 672,
  '1h': 168,
  '4h': 42,
  '1d': 30,
}

export const BAR_MINUTES: Record<LabBar, number> = { '1m': 1, '15m': 15, '1h': 60, '4h': 240, '1d': 1440 }
