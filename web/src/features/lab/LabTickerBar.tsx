import { ArrowLeftRight, RefreshCw } from 'lucide-react'
import { useContext } from 'react'

import { Button } from '@/components/ui/button'
import { DetailTag } from '@/components/watermelon/dashboard-card'
import { cn } from '@/lib/utils'
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
  const stretchTone = pctVsMa == null || pctVsMa === 0 ? 'neutral' : pctVsMa > 0 ? 'positive' : 'negative'
  const benchmarks = coins.filter((coin) => BENCHMARK_CODES.includes(coin.code))
  const autoBenchmarkCode = (analysis?.anchor ?? analysis?.anchor_ranking?.[0]?.anchor)?.code

  return (
    <section
      className="shadow-primary flex flex-wrap items-center gap-x-3 gap-y-2 rounded-xl border border-border bg-card px-3 py-2 text-card-foreground xl:flex-nowrap"
      aria-label="Pair selection"
    >
      <div className="flex items-center gap-1.5">
        <CoinPicker
          label="Coin A"
          value={request.coin_a}
          coins={coins}
          excluded={request.coin_b}
          onChange={(id) => onChangeRequest({ coin_a: id })}
        />
        <Button
          type="button"
          variant="outline"
          size="icon-sm"
          aria-label="Swap coins"
          title="Swap Coin A and Coin B"
          onClick={() => onChangeRequest({ coin_a: request.coin_b, coin_b: request.coin_a })}
          className="size-8 rounded-md border-border-strong bg-background text-muted-foreground hover:text-foreground"
        >
          <ArrowLeftRight className="size-3.5" aria-hidden="true" />
        </Button>
        <CoinPicker
          label="Coin B"
          value={request.coin_b}
          coins={coins}
          excluded={request.coin_a}
          onChange={(id) => onChangeRequest({ coin_b: id })}
        />
      </div>

      <div
        className="flex items-center gap-2 font-mono tabular-nums"
        title="Latest ratio and its deviation from the trailing moving average"
      >
        <span className="text-base font-semibold tracking-tight text-foreground">
          {formatRatio(ratio)}
        </span>
        <DetailTag tone={stretchTone} title-hint="Deviation from trailing moving average">
          {pctVsMa == null || zScore == null
            ? '—'
            : `${formatSigned(pctVsMa, 1, '%')} · ${formatSigned(zScore, 1, 'σ')}`}
        </DetailTag>
      </div>

      <div
        className="inline-flex items-center gap-0.5 rounded-lg border border-border bg-muted p-0.5"
        role="group"
        aria-label="Interval"
      >
        {INTERVAL_BARS.map((bar) => {
          const active = request.bar === bar
          return (
            <Button
              key={bar}
              type="button"
              size="sm"
              variant={active ? 'secondary' : 'ghost'}
              aria-pressed={active}
              title={`Candle interval: ${BAR_TITLES[bar]}`}
              onClick={() => onChangeRequest({ bar, band_lookback: DEFAULT_BAND_LOOKBACK[bar] })}
              className={cn(
                'h-7 rounded-md px-2 font-mono text-xs tabular-nums',
                active
                  ? 'bg-background text-foreground shadow-xs ring-1 ring-border-strong'
                  : 'text-muted-foreground hover:text-foreground',
              )}
            >
              {bar === '1d' ? '1D' : bar}
            </Button>
          )
        })}
      </div>

      <div
        className="inline-flex items-center gap-0.5 rounded-lg border border-border bg-muted p-0.5"
        role="group"
        aria-label="History window"
      >
        {LAB_DAYS.map((days) => {
          const active = request.days === days
          return (
            <Button
              key={days}
              type="button"
              size="sm"
              variant={active ? 'secondary' : 'ghost'}
              aria-pressed={active}
              title={`${days} days of history`}
              onClick={() => onChangeRequest({ days })}
              className={cn(
                'h-7 rounded-md px-2 font-mono text-xs tabular-nums',
                active
                  ? 'bg-background text-foreground shadow-xs ring-1 ring-border-strong'
                  : 'text-muted-foreground hover:text-foreground',
              )}
            >
              {WINDOW_LABELS[days]}
            </Button>
          )
        })}
      </div>

      <div className="flex items-center gap-1.5">
        <label
          className="inline-flex items-center gap-1.5 text-xs text-muted-foreground"
          title="Reference market driver for beta and anchor-spread models. Select None for direct two-coin analysis."
        >
          <span className="hidden sm:inline xl:hidden">Benchmark</span>
          <select
            aria-label="Benchmark"
            value={request.anchor ?? ''}
            onChange={(event) => onChangeRequest({ anchor: event.target.value || null })}
            className="h-8 rounded-md border border-border-strong bg-background px-2 text-xs font-medium text-foreground shadow-xs outline-none focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/40"
          >
            <option value="">
              Auto{autoBenchmarkCode ? ` (${autoBenchmarkCode})` : analysis ? ' (None available)' : ''}
            </option>
            {benchmarks.map((coin) => (
              <option key={coin.id} value={coin.id}>
                {coin.code}
              </option>
            ))}
            <option value="none">None</option>
          </select>
        </label>
        <InfoTip
          label="Benchmark guidance"
          align="right"
          text="Auto picks the highest-R² market driver (BTC, ETH, BNB, SOL) covering the full window to strip market-wide beta. None runs pure two-coin ratio analysis."
        />
      </div>

      <div className="ml-auto flex items-center gap-2">
        {onRefreshData && (
          <Button
            type="button"
            variant="outline"
            size="icon-sm"
            aria-label="Sync latest candles"
            title="Sync latest candles"
            disabled={syncing}
            onClick={onRefreshData}
            className="size-8 rounded-md border-border-strong bg-background text-muted-foreground hover:text-foreground"
          >
            <RefreshCw className={cn('size-3.5', syncing && 'animate-spin')} aria-hidden="true" />
          </Button>
        )}
        {!headerOwnsViewMode && (
          <div
            className="inline-flex items-center gap-0.5 rounded-lg border border-border bg-muted p-0.5"
            role="group"
            aria-label="View mode"
          >
            <Button
              type="button"
              size="sm"
              variant={viewMode === 'simple' ? 'secondary' : 'ghost'}
              aria-pressed={viewMode === 'simple'}
              onClick={() => onChangeViewMode('simple')}
              className={cn(
                'h-7 rounded-md px-2.5 text-xs font-medium',
                viewMode === 'simple'
                  ? 'bg-background text-foreground shadow-xs'
                  : 'text-muted-foreground hover:text-foreground',
              )}
            >
              Simple
            </Button>
            <Button
              type="button"
              size="sm"
              variant={viewMode === 'advanced' ? 'secondary' : 'ghost'}
              aria-pressed={viewMode === 'advanced'}
              onClick={() => onChangeViewMode('advanced')}
              className={cn(
                'h-7 rounded-md px-2.5 text-xs font-medium',
                viewMode === 'advanced'
                  ? 'bg-background text-foreground shadow-xs'
                  : 'text-muted-foreground hover:text-foreground',
              )}
            >
              Pro
            </Button>
          </div>
        )}
      </div>
    </section>
  )
}
