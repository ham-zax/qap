import { useMemo, useState } from 'react'
import { TimeSeriesChart } from '../../components/charts/TimeSeriesChart'
import type { TimeSeriesDefinition } from '../../components/charts/chartData'
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
}

function wealthPoints(wealth: LabWealth, name: string, unitMode: WealthUnitMode) {
  const map = unitMode === 'coins_a' ? wealth.coins_a : unitMode === 'coins_b' ? wealth.coins_b : wealth.value
  return wealth.time.flatMap((time, index) => {
    const value = map[name]?.[index]
    return value == null ? [] : [{ timestamp: new Date(time * 1000).toISOString(), value }]
  })
}

export function WealthChart({ wealth, coinACode = 'Coin A', coinBCode = 'Coin B' }: WealthChartProps) {
  const [hover, setHover] = useState<string | null>(null)
  const [unitMode, setUnitMode] = useState<WealthUnitMode>('value')
  const [showHolds, setShowHolds] = useState(false)

  const names = useMemo(() => wealthNames(wealth, showHolds), [wealth, showHolds])
  const unitLabel = unitMode === 'coins_a' ? coinACode : unitMode === 'coins_b' ? coinBCode : 'USDT'
  const series = useMemo<TimeSeriesDefinition[]>(() => names.map((name) => ({
    name: name === 'hold_a' ? `Hold ${coinACode}` : name === 'hold_b' ? `Hold ${coinBCode}` : (WEALTH_LABELS[name] ?? 'Rebalance'),
    unit: unitLabel,
    points: wealthPoints(wealth, name, unitMode),
    dashed: name !== 'strategy',
    colorToken: wealthColorToken(name),
  })), [names, wealth, unitMode, unitLabel, coinACode, coinBCode])

  const latest = useMemo(
    () => wealthReadout(wealth, null, { unitMode, coinACode, coinBCode, includeHolds: showHolds }),
    [wealth, unitMode, coinACode, coinBCode, showHolds],
  )
  const current = hover === null
    ? latest
    : wealthReadout(wealth, hover, { unitMode, coinACode, coinBCode, includeHolds: showHolds })

  const validation = wealth.window_kind === 'validation'
  const hasHoldLines = Boolean(wealth.value.hold_a || wealth.value.hold_b)

  return <section className="lab-wealth" aria-label="Money over time">
    <div className="lab-wealth-header">
      <div>
        <h2>Money over time, after fees</h2>
        <p className="lab-note">
          What the starting money became, in {unitLabel}. Fees and price slippage are included.{' '}
          {validation ? 'Shows only the check period the test did not tune on.' : 'Shows context only. This test has no rotating result to draw.'}
        </p>
      </div>
      <div className="lab-wealth-controls">
        <div className="lab-segmented" role="group" aria-label="Wealth unit">
          <button type="button" aria-pressed={unitMode === 'value'} onClick={() => setUnitMode('value')}>
            USDT Value
          </button>
          <button type="button" aria-pressed={unitMode === 'coins_a'} onClick={() => setUnitMode('coins_a')}>
            {coinACode} Units
          </button>
          <button type="button" aria-pressed={unitMode === 'coins_b'} onClick={() => setUnitMode('coins_b')}>
            {coinBCode} Units
          </button>
        </div>
        {hasHoldLines && (
          <label className="lab-checkbox-row">
            <input type="checkbox" checked={showHolds} onChange={(e) => setShowHolds(e.target.checked)} />
            Show hold {coinACode} / {coinBCode}
          </label>
        )}
      </div>
    </div>
    <TimeSeriesChart title="Money over time, after fees" description="Rotating, just holding, and a simple scheduled rebalance over the same period." series={series} height={300}
      onHoverTimeChange={setHover} readout={<LabReadout title="Money over time, after fees" current={current} latest={latest} />} />
    <dl className="lab-wealth-terminal" aria-label="Final values">
      {names.map((name) => {
        const label = name === 'hold_a' ? `Hold ${coinACode}` : name === 'hold_b' ? `Hold ${coinBCode}` : (WEALTH_LABELS[name] ?? 'Rebalance')
        if (unitMode === 'coins_a' || unitMode === 'coins_b') {
          const curve = unitMode === 'coins_a' ? wealth.coins_a[name] : wealth.coins_b[name]
          const lastVal = curve?.at(-1)
          const code = unitMode === 'coins_a' ? coinACode : coinBCode
          return <div key={name}><dt>{label}, final</dt><dd>{formatCoinUnits(lastVal, code)}</dd></div>
        }
        const value = Number(wealth.terminal_values[name])
        return <div key={name}><dt>{label}, final</dt><dd>{Number.isFinite(value) ? formatUsdt(value) : 'Not available'}</dd></div>
      })}
    </dl>
  </section>
}

export function WealthPending() {
  return <section className="lab-wealth-empty" aria-label="Money over time">
    <h2>Money over time</h2>
    <div className="lab-wealth-empty-frame">
      <p>Not tested yet</p>
      <span>After a test, this chart shows your money over time for rotating, just holding, and a simple scheduled rebalance.</span>
    </div>
  </section>
}
