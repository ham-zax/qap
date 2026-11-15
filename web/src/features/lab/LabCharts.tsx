import { useCallback, useMemo, useState } from 'react'
import { TimeSeriesChart } from '../../components/charts/TimeSeriesChart'
import type { ChartVisibleRange, TimeSeriesDefinition } from '../../components/charts/chartData'
import type { LabAnalysis } from './labContract'
import { LabReadout } from './LabReadout'
import { ratioReadout, type LabWealth } from './labReadout'
import { WealthChart } from './LabWealth'
import './LabCharts.css'

const VISIBLE_DATE = new Intl.DateTimeFormat('en-GB', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' })

export function LabCharts({ analysis, wealth = null }: { analysis: LabAnalysis; wealth?: LabWealth | null }) {
  const [bands, setBands] = useState(true)
  const [anchor, setAnchor] = useState(true)
  const [hover, setHover] = useState<string | null>(null)
  const [viewport, setViewport] = useState<{ series: TimeSeriesDefinition[]; range: ChartVisibleRange | null } | null>(null)
  const series = useMemo(() => {
    const data = analysis.series
    const points = (values: (number | null)[]) => data.time.flatMap((time, index) => {
      const value = values[index]
      return value == null ? [] : [{ timestamp: new Date(time * 1000).toISOString(), value }]
    })
    const definitions: TimeSeriesDefinition[] = [{ name: `${analysis.coin_a.code} per ${analysis.coin_b.code}`, unit: 'ratio', points: points(data.ratio) }]
    if (bands) {
      definitions.push({ name: 'Usual level', unit: 'ratio', points: points(data.mean), dashed: true, colorToken: '--qap-muted' })
      for (const multiplier of [-2, 2]) definitions.push({ name: multiplier > 0 ? 'Normal range, top' : 'Normal range, bottom', unit: 'ratio', dashed: true,
        colorToken: '--qap-border-strong', points: points(data.mean.map((mean, index) => mean == null || data.std[index] == null ? null : mean + multiplier * data.std[index]!)) })
    }
    if (anchor && data.anchor_close && analysis.anchor) definitions.push({ name: analysis.anchor.code, unit: 'USDT', points: points(data.anchor_close), priceScaleId: 'left', colorToken: '--qap-muted' })
    return definitions
  }, [analysis, bands, anchor])
  const options = useMemo(() => ({ bands, anchor: anchor && Boolean(analysis.anchor) }), [bands, anchor, analysis.anchor])
  const latest = useMemo(() => ratioReadout(analysis, null, options), [analysis, options])
  const current = hover === null ? latest : ratioReadout(analysis, hover, options)
  const onVisibleRangeChange = useCallback((range: ChartVisibleRange | null) => setViewport({ series, range }), [series])
  const visibleRange = viewport?.series === series ? viewport.range : null
  const ratioTitle = `${analysis.coin_a.code} per ${analysis.coin_b.code}`
  return <section className="lab-chart-area">
    <div className="lab-chart-controls"><h2>The relationship</h2><div>
      <label><input type="checkbox" checked={bands} onChange={(event) => setBands(event.target.checked)} />Usual level and normal range</label>
      <label><input type="checkbox" checked={anchor} onChange={(event) => setAnchor(event.target.checked)} disabled={!analysis.anchor} />Anchor</label>
    </div></div>
    <TimeSeriesChart title={ratioTitle} description="Coin A divided by coin B. Anchor prices use the left axis. Bands describe this window, not a rotation rule." series={series} height={380}
      onVisibleRangeChange={onVisibleRangeChange} onHoverTimeChange={setHover} readout={<LabReadout title={ratioTitle} current={current} latest={latest} />} />
    <div className="lab-chart-notes">
      {visibleRange && <p className="lab-note">
        Showing {VISIBLE_DATE.format(new Date(visibleRange.from))}–{VISIBLE_DATE.format(new Date(visibleRange.to))} (UTC).
        {Date.parse(visibleRange.from) > analysis.series.time[0]! * 1000 && ' Scroll or drag for earlier data.'}
      </p>}
      {!analysis.anchor && <p className="lab-note">No prepared anchor covers this window. Choose an anchor to load its history.</p>}
      {analysis.anchor_ranking.length > 0 && <p className="lab-note">Best available anchor: {analysis.anchor_ranking[0]!.anchor.code}. Mean R² across the two coin fits: {(analysis.anchor_ranking[0]!.joint_explained * 100).toFixed(1)}%.</p>}
    </div>
    {wealth ? <WealthChart wealth={wealth} /> : <section className="lab-wealth-empty" aria-label="Wealth over time">
      <h2>Not tested yet</h2>
      <div className="lab-wealth-empty-frame">
        <p>Wealth over time</p>
        <span>After a test, this chart shows your money over time for rotating, just holding, and a simple scheduled rebalance.</span>
      </div>
    </section>}
  </section>
}
