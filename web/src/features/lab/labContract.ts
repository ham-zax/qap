/**
 * Pair Rotation Lab — analysis contract (M3).
 *
 * This is the boundary between the dashboard and the backend analysis API. The UI
 * is built against exactly these shapes; the backend agent implements
 * `GET /api/pair-rotation/analysis` produces them. The typed backend owner is
 * src/qap/api/pair_rotation_analysis_schemas.py; OpenAPI exports the same shape.
 *
 * Conventions follow the other DTOs: snake_case keys, ISO-8601 UTC strings for
 * instants, and columnar arrays for series so a 6-month 15m window (~17,500 bars)
 * stays small on the wire. Every measurement is `null` when its history is too thin;
 * the UI shows "not enough history", never a guess.
 *
 * Nothing here is a call or a proof. Those arrive in M4 as separate fields.
 */

export type LabBar = '15m' | '1h' | '4h' | '1d'
export type LabDays = 30 | 90 | 180 | 365

export const LAB_BARS: readonly LabBar[] = ['15m', '1h', '4h', '1d']
export const LAB_DAYS: readonly LabDays[] = [30, 90, 180, 365]

/** A listing the user can research. `id` is the API listing id, e.g. `binance:W`. */
export interface LabCoin {
  id: string
  code: string
  name: string
  /** Identity resolved by the registry. Unresolved coins are viewable but cannot make a call. */
  identity_state: 'resolved' | 'review' | 'unresolved'
}

/** Aligned closes on one exact shared UTC candle-open index. All arrays share `time`'s length. */
export interface LabSeries {
  /** Candle-open instants, seconds since epoch, strictly increasing. */
  time: number[]
  close_a: number[]
  close_b: number[]
  /** close_a / close_b. */
  ratio: number[]
  /** Trailing mean / sample deviation of `ratio` over `band_lookback` bars; null during warm-up. */
  mean: (number | null)[]
  std: (number | null)[]
  /** Anchor close on the same index, or null when no anchor data is prepared. */
  anchor_close: number[] | null
}

export interface LabCorrelation {
  pearson: number
  spearman: number
  kendall: number
  observations: number
}

export interface LabLeadLag {
  /** Bars the coin trails the anchor; negative means it leads. */
  lag_bars: number
  correlation: number
  stable: boolean
}

export interface LabAnchorLink {
  beta: number
  r_squared: number
  lead_lag: LabLeadLag | null
}

export interface LabMeasurements {
  correlation: LabCorrelation | null
  cointegration: { statistic: number; p_value: number; level: number; passes: boolean } | null
  hedge_ratio: { ols: number; tls: number; first_half_ols: number; second_half_ols: number; stable: boolean } | null
  half_life: { bars: number | null; reverting: boolean } | null
  hurst: { exponent: number; reading: 'reverting' | 'random' | 'trending' } | null
  /** Share of the window at or below the latest ratio, 0–100. */
  ratio_percentile: number | null
  regime: {
    volatility: 'calm' | 'normal' | 'stressed'
    volatility_percentile: number
    trend: 'trending' | 'ranging'
    efficiency: number
  } | null
  /** Sensitivity of each coin to the selected anchor; null without an anchor. */
  anchor_a: LabAnchorLink | null
  anchor_b: LabAnchorLink | null
  /** Latest sequential hedge slope; change is measured over the settled half. */
  kalman: { beta: number; standard_error: number; beta_change: number } | null
  /** Best-lag F-test per direction; p-values are corrected for the lags tested. */
  granger: {
    a_to_b: LabGrangerDirection
    b_to_a: LabGrangerDirection
    max_lag: number
    observations: number
  } | null
  /** Joint extreme moves of the fitted copula, 0–1 per tail. */
  copula: { family: string; lower_tail: number; upper_tail: number; observations: number } | null
  /** Trailing return correlation over the band lookback. */
  rolling_dependence: { window_bars: number; latest: number; low: number; high: number } | null
}

export interface LabGrangerDirection {
  lag_bars: number
  p_value: number
  passes: boolean
}

/** One candidate anchor's explanatory power, ranked best first. */
export interface LabAnchorFit {
  anchor: LabCoin
  beta_a: number
  beta_b: number
  /** Mean R² of both coins' log returns on the anchor's, 0–1. */
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
  /** Close time of the latest completed bar used. */
  data_through: string
  bars_used: number
  /** False when either coin's economic identity is unresolved: viewable, no call. */
  identity_confirmed: boolean
  series: LabSeries
  /** Selected anchor, or null when none is prepared yet. */
  anchor: LabCoin | null
  /** Candidates ranked by explanatory power; may be empty while anchors download. */
  anchor_ranking: LabAnchorFit[]
  measurements: LabMeasurements
  datasets: LabDataset[]
  /** Sample data produced in the browser for design review; real responses omit it. */
  demo?: true
}

/** Request for one analysis. */
export interface LabRequest {
  coin_a: string
  coin_b: string
  anchor: string | null
  bar: LabBar
  days: LabDays
  band_lookback: number
}

/** Data preparation progress, mirrored from the operation record. */
export interface LabProgress {
  stage: string
  completed: number
  total: number
}

/** A coin match from search; same shape the coin-search endpoint already returns. */
export interface LabCoinMatch extends LabCoin {
  source: string
  call_available: boolean
}

/** Default anchor candidates, per the MVP design §4.3. */
export const DEFAULT_ANCHORS: readonly string[] = ['binance:BTC', 'binance:ETH', 'binance:BNB', 'binance:SOL']

/** Band lookback default per bar size: about one week of bars (one month on 1d). */
export const DEFAULT_BAND_LOOKBACK: Record<LabBar, number> = {
  '15m': 672,
  '1h': 168,
  '4h': 42,
  '1d': 30,
}

export const BAR_MINUTES: Record<LabBar, number> = { '15m': 15, '1h': 60, '4h': 240, '1d': 1440 }
