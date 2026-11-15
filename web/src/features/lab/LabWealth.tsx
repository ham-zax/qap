import { useMemo, useState } from 'react'
import { TimeSeriesChart } from '../../components/charts/TimeSeriesChart'
import type { TimeSeriesDefinition } from '../../components/charts/chartData'
import { LabReadout } from './LabReadout'
import { WEALTH_LABELS, wealthColorToken, wealthNames, wealthReadout, type LabWealth } from './labReadout'

function wealthPoints(wealth: LabWealth, name: string) {
  return wealth.time.flatMap((time, index) => {
    const value = wealth.value[name]?.[index]
    return value == null ? [] : [{ timestamp: new Date(time * 1000).toISOString(), value }]
  })
}

export function WealthChart({ wealth }: { wealth: LabWealth }) {
  const [hover, setHover] = useState<string | null>(null)
  const names = useMemo(() => wealthNames(wealth), [wealth])
  const series = useMemo<TimeSeriesDefinition[]>(() => names.map((name) => ({
    name: WEALTH_LABELS[name] ?? 'Rebalance',
    unit: 'USDT',
    points: wealthPoints(wealth, name),
    dashed: name !== 'strategy',
    colorToken: wealthColorToken(name),
  })), [names, wealth])
  const latest = useMemo(() => wealthReadout(wealth, null), [wealth])
  const current = hover === null ? latest : wealthReadout(wealth, hover)
  const validation = wealth.window_kind === 'validation'
  return <section className="lab-wealth" aria-label="Money over time">
    <h2>Money over time, after fees</h2>
    <p className="lab-note">
      What the starting money became, in USDT. Fees and price slippage are included.{' '}
      {validation ? 'Shows only the check period the test did not tune on.' : 'Shows context only. This test has no rotating result to draw.'}
    </p>
    <TimeSeriesChart title="Money over time, after fees" description="Rotating, just holding, and a simple scheduled rebalance over the same period." series={series} height={300}
      onHoverTimeChange={setHover} readout={<LabReadout title="Money over time, after fees" current={current} latest={latest} />} />
    <dl className="lab-wealth-terminal" aria-label="Final values">
      {names.map((name) => {
        const value = Number(wealth.terminal_values[name])
        return <div key={name}><dt>{WEALTH_LABELS[name] ?? 'Rebalance'}, final</dt><dd>{Number.isFinite(value) ? `${value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} USDT` : 'Not available'}</dd></div>
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
