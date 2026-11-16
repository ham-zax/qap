import { useMemo, useState } from 'react'

import { TimeSeriesChart } from '../../components/charts/TimeSeriesChart'
import type { TimeSeriesDefinition } from '../../components/charts/chartData'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { Label } from '@/components/ui/label'
import { cn } from '@/lib/utils'
import { LabReadout } from './LabReadout'
import {
  WEALTH_LABELS,
  formatCoinUnits,
  formatUsdt,
  wealthColorToken,
  wealthNames,
  wealthReadout,
  type LabWealth,
  type WealthUnitMode,
} from './labReadout'

interface WealthChartProps {
  wealth: LabWealth
  coinACode?: string
  coinBCode?: string
  showHolds?: boolean
}

function wealthPoints(wealth: LabWealth, name: string, unitMode: WealthUnitMode) {
  const map = unitMode === 'coins_a' ? wealth.coins_a : unitMode === 'coins_b' ? wealth.coins_b : wealth.value
  return wealth.time.flatMap((time, index) => {
    const value = map[name]?.[index]
    return value == null ? [] : [{ timestamp: new Date(time * 1000).toISOString(), value }]
  })
}

export function WealthChart({
  wealth,
  coinACode = 'Coin A',
  coinBCode = 'Coin B',
  showHolds: controlledShowHolds,
}: WealthChartProps) {
  const [hover, setHover] = useState<string | null>(null)
  const [unitMode, setUnitMode] = useState<WealthUnitMode>('value')
  const [internalShowHolds, setInternalShowHolds] = useState(false)
  const showHolds = controlledShowHolds ?? internalShowHolds

  const names = useMemo(() => wealthNames(wealth, showHolds), [wealth, showHolds])
  const unitLabel = unitMode === 'coins_a' ? coinACode : unitMode === 'coins_b' ? coinBCode : 'USDT'
  const series = useMemo<TimeSeriesDefinition[]>(
    () =>
      names.map((name) => ({
        name:
          name === 'hold_a'
            ? `Hold ${coinACode}`
            : name === 'hold_b'
              ? `Hold ${coinBCode}`
              : (WEALTH_LABELS[name] ?? 'Rebalance'),
        unit: unitLabel,
        points: wealthPoints(wealth, name, unitMode),
        dashed: name !== 'strategy',
        colorToken: wealthColorToken(name),
      })),
    [names, wealth, unitMode, unitLabel, coinACode, coinBCode],
  )

  const latest = useMemo(
    () => wealthReadout(wealth, null, { unitMode, coinACode, coinBCode, includeHolds: showHolds }),
    [wealth, unitMode, coinACode, coinBCode, showHolds],
  )
  const current =
    hover === null
      ? latest
      : wealthReadout(wealth, hover, { unitMode, coinACode, coinBCode, includeHolds: showHolds })

  const validation = wealth.window_kind === 'validation'
  const hasHoldLines = Boolean(wealth.value.hold_a || wealth.value.hold_b)

  return (
    <section className="space-y-3" aria-label="Money over time">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="space-y-1">
          <h2 className="m-0 text-sm font-semibold text-foreground">Money over time, after fees</h2>
          <p className="m-0 max-w-2xl text-xs leading-relaxed text-muted-foreground">
            What the starting money became, in {unitLabel}. Fees and price slippage are included.{' '}
            {validation
              ? 'Shows only the check period the test did not tune on.'
              : 'Shows context only. This test has no rotating result to draw.'}
          </p>
        </div>
        <div className="flex flex-col items-end gap-2">
          <div
            className="inline-flex items-center gap-0.5 rounded-lg border border-border bg-muted p-0.5"
            role="group"
            aria-label="Wealth unit"
          >
            <Button
              type="button"
              size="sm"
              variant={unitMode === 'value' ? 'secondary' : 'ghost'}
              aria-pressed={unitMode === 'value'}
              onClick={() => setUnitMode('value')}
              className={cn(
                'h-7 rounded-md px-2.5 text-xs font-medium',
                unitMode === 'value'
                  ? 'bg-background text-foreground shadow-xs'
                  : 'text-muted-foreground hover:text-foreground',
              )}
            >
              USDT Value
            </Button>
            <Button
              type="button"
              size="sm"
              variant={unitMode === 'coins_a' ? 'secondary' : 'ghost'}
              aria-pressed={unitMode === 'coins_a'}
              onClick={() => setUnitMode('coins_a')}
              className={cn(
                'h-7 rounded-md px-2.5 text-xs font-medium',
                unitMode === 'coins_a'
                  ? 'bg-background text-foreground shadow-xs'
                  : 'text-muted-foreground hover:text-foreground',
              )}
            >
              {coinACode} Units
            </Button>
            <Button
              type="button"
              size="sm"
              variant={unitMode === 'coins_b' ? 'secondary' : 'ghost'}
              aria-pressed={unitMode === 'coins_b'}
              onClick={() => setUnitMode('coins_b')}
              className={cn(
                'h-7 rounded-md px-2.5 text-xs font-medium',
                unitMode === 'coins_b'
                  ? 'bg-background text-foreground shadow-xs'
                  : 'text-muted-foreground hover:text-foreground',
              )}
            >
              {coinBCode} Units
            </Button>
          </div>
          {hasHoldLines && controlledShowHolds === undefined && (
            <Label htmlFor="wealth-show-holds" className="cursor-pointer text-xs text-muted-foreground">
              <Checkbox
                id="wealth-show-holds"
                checked={showHolds}
                onCheckedChange={(checked) => setInternalShowHolds(checked === true)}
              />
              Show hold {coinACode} / {coinBCode}
            </Label>
          )}
        </div>
      </div>

      <TimeSeriesChart
        title="Money over time, after fees"
        description="Strategy, Hold 50/50, and scheduled rebalancing over the same period."
        series={series}
        height={300}
        onHoverTimeChange={setHover}
        readout={<LabReadout title="Money over time, after fees" current={current} latest={latest} />}
      />

      <dl
        className="m-0 grid grid-cols-2 gap-2.5 border-t border-border pt-3 sm:grid-cols-3 lg:grid-cols-5"
        aria-label="Final values"
      >
        {names.map((name) => {
          const label =
            name === 'hold_a'
              ? `Hold ${coinACode}`
              : name === 'hold_b'
                ? `Hold ${coinBCode}`
                : (WEALTH_LABELS[name] ?? 'Rebalance')
          if (unitMode === 'coins_a' || unitMode === 'coins_b') {
            const curve = unitMode === 'coins_a' ? wealth.coins_a[name] : wealth.coins_b[name]
            const lastVal = curve?.at(-1)
            const code = unitMode === 'coins_a' ? coinACode : coinBCode
            return (
              <div key={name} className="rounded-lg border border-border bg-muted/40 px-3 py-2">
                <dt className="text-[11px] text-muted-foreground">{label}, final</dt>
                <dd className="m-0 mt-0.5 font-mono text-sm font-semibold text-foreground tabular-nums">
                  {formatCoinUnits(lastVal, code)}
                </dd>
              </div>
            )
          }
          const value = Number(wealth.terminal_values[name])
          return (
            <div key={name} className="rounded-lg border border-border bg-muted/40 px-3 py-2">
              <dt className="text-[11px] text-muted-foreground">{label}, final</dt>
              <dd className="m-0 mt-0.5 font-mono text-sm font-semibold text-foreground tabular-nums">
                {Number.isFinite(value) ? formatUsdt(value) : 'Not available'}
              </dd>
            </div>
          )
        })}
      </dl>
    </section>
  )
}

export function WealthPending() {
  return (
    <section
      className="rounded-xl border border-dashed border-border bg-muted/20 p-6"
      aria-label="Money over time"
    >
      <h2 className="m-0 text-sm font-semibold text-foreground">Money over time</h2>
      <div className="mt-2 space-y-1">
        <p className="m-0 text-sm font-medium text-foreground">Not tested yet</p>
        <span className="block text-xs text-muted-foreground">
          After a test, this chart shows your money over time for rotating, just holding, and a simple scheduled rebalance.
        </span>
      </div>
    </section>
  )
}
