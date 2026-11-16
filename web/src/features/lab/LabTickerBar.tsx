import { useContext } from 'react'
import { CoinPicker } from './CoinPicker'
import { InfoTip } from './InfoTip'
import { AppShellHeaderModeContext } from './labStorage'
import {
  DEFAULT_BAND_LOOKBACK,
  LAB_BARS,
  LAB_DAYS,
  type LabAnalysis,
  type LabBar,
  type LabCoinMatch,
  type LabDays,
  type LabRequest,
  type LabViewMode,
} from './labContract'

export interface LabTickerBarProps {
  request: LabRequest
  coins: LabCoinMatch[]
  analysis: LabAnalysis | null
  viewMode: LabViewMode
  syncing?: boolean
  onChangeRequest: (patch: Partial<LabRequest>) => void
  onChangeViewMode: (mode: LabViewMode) => void
  onRefreshData?: () => void
}

const INTERVAL_BARS = LAB_BARS
const BAR_TITLES: Record<LabBar, string> = {
  '1m': '1 minute',
  '15m': '15 minutes',
  '1h': '1 hour',
  '4h': '4 hours',
  '1d': '1 day',
}
const WINDOW_LABELS: Record<LabDays, string> = { 30: '30D', 90: '90D', 180: '180D', 365: '1Y' }
const BENCHMARK_CODES = ['BTC', 'ETH', 'BNB', 'SOL']

function SwapIcon() {
  return <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M7 4 3 8l4 4" /><path d="M3 8h14" /><path d="m17 20 4-4-4-4" /><path d="M21 16H7" />
  </svg>
}

function SyncIcon() {
  return <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M21 12a9 9 0 1 1-3.2-6.9" /><path d="M21 3v6h-6" />
  </svg>
}

function formatRatio(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return '—'
  return Number(value.toPrecision(4)).toString()
}

function formatSigned(value: number, digits: number, suffix: string): string {
  const text = value.toLocaleString('en-US', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
    signDisplay: 'exceptZero',
  })
  return `${text}${suffix}`
}

export function LabTickerBar({
  request,
  coins,
  analysis,
  viewMode,
  syncing = false,
  onChangeRequest,
  onChangeViewMode,
  onRefreshData,
}: LabTickerBarProps) {
  const ratio = analysis?.series.ratio.at(-1) ?? null
  const mean = analysis?.series.mean.at(-1) ?? null
  const std = analysis?.series.std.at(-1) ?? null
  const pctVsMa = ratio != null && mean != null && mean !== 0 ? ((ratio - mean) / mean) * 100 : null
  const zScore = ratio != null && mean != null && std != null && std !== 0 ? (ratio - mean) / std : null
  const headerOwnsViewMode = useContext(AppShellHeaderModeContext)
  const stretchTone = pctVsMa == null || pctVsMa === 0 ? 'bt-badge-neutral' : pctVsMa > 0 ? 'bt-badge-pos' : 'bt-badge-neg'
  const benchmarks = coins.filter((coin) => BENCHMARK_CODES.includes(coin.code))
  const autoBenchmarkCode = (analysis?.anchor ?? analysis?.anchor_ranking?.[0]?.anchor)?.code

  return <section className="bt-ticker-bar" aria-label="Pair selection">
    <div className="bt-pair-group">
      <CoinPicker label="Coin A" value={request.coin_a} coins={coins} excluded={request.coin_b} onChange={(id) => onChangeRequest({ coin_a: id })} />
      <button type="button" className="bt-swap-btn" aria-label="Swap coins" title="Swap Coin A and Coin B"
        onClick={() => onChangeRequest({ coin_a: request.coin_b, coin_b: request.coin_a })}>
        <SwapIcon />
      </button>
      <CoinPicker label="Coin B" value={request.coin_b} coins={coins} excluded={request.coin_a} onChange={(id) => onChangeRequest({ coin_b: id })} />
    </div>

    <div className="bt-ratio-stat" title="Latest ratio and its deviation from the trailing moving average">
      <span className="bt-ratio-value bt-mono">{formatRatio(ratio)}</span>
      <span className={`bt-badge ${stretchTone}`} title="Deviation from trailing moving average">
        {pctVsMa == null || zScore == null ? '—' : `${formatSigned(pctVsMa, 1, '%')} · ${formatSigned(zScore, 1, 'σ')}`}
      </span>
    </div>

    <div className="bt-pill-strip" role="group" aria-label="Interval">
      {INTERVAL_BARS.map((bar) => <button key={bar} type="button" className="bt-pill" aria-pressed={request.bar === bar}
        title={`Candle interval: ${BAR_TITLES[bar]}`}
        onClick={() => onChangeRequest({ bar, band_lookback: DEFAULT_BAND_LOOKBACK[bar] })}>
        {bar === '1d' ? '1D' : bar}
      </button>)}
    </div>

    <div className="bt-pill-strip" role="group" aria-label="History window">
      {LAB_DAYS.map((days) => <button key={days} type="button" className="bt-pill" aria-pressed={request.days === days}
        title={`${days} days of history`} onClick={() => onChangeRequest({ days })}>
        {WINDOW_LABELS[days]}
      </button>)}
    </div>

    <div className="bt-benchmark-wrap">
      <label className="bt-benchmark-select" title="Reference market driver for beta and anchor-spread models. Select None for direct two-coin analysis.">
        <span>Benchmark</span>
        <select aria-label="Benchmark" value={request.anchor ?? ''} onChange={(event) => onChangeRequest({ anchor: event.target.value || null })}>
          <option value="">Auto{autoBenchmarkCode ? ` (${autoBenchmarkCode})` : analysis ? ' (None available)' : ''}</option>
          {benchmarks.map((coin) => <option key={coin.id} value={coin.id}>{coin.code}</option>)}
          <option value="none">None</option>
        </select>
      </label>
      <InfoTip
        label="Benchmark guidance"
        align="right"
        text="Auto picks the highest-R² market driver (BTC, ETH, BNB, SOL) covering the full window to strip market-wide beta. None runs pure two-coin ratio analysis."
      />
    </div>

    <div className="bt-ticker-right">
      {onRefreshData && <button type="button" className="bt-icon-btn" aria-label="Sync latest candles" title="Sync latest candles"
        disabled={syncing} onClick={onRefreshData}>
        <SyncIcon />
      </button>}
      {!headerOwnsViewMode && (
        <div className="bt-segmented" role="group" aria-label="View mode">
          <button type="button" aria-pressed={viewMode === 'simple'} onClick={() => onChangeViewMode('simple')}>Simple</button>
          <button type="button" aria-pressed={viewMode === 'advanced'} onClick={() => onChangeViewMode('advanced')}>Pro</button>
        </div>
      )}
    </div>
  </section>
}
