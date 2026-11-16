import { useCallback, useMemo, useState } from 'react'
import { TimeSeriesChart } from '../../components/charts/TimeSeriesChart'
import type { ChartMarker, ChartVisibleRange, TimeSeriesDefinition } from '../../components/charts/chartData'
import { LabReadout } from './LabReadout'
import { LabSignalChart } from './LabSignalChart'
import { WealthChart } from './LabWealth'
import { ratioReadout } from './labReadout'
import type { LabAnalysis, LabProgress, LabViewMode } from './labContract'
import type { LabStudy } from './labStudyApi'

export interface LabHeroChartsProps {
  analysis: LabAnalysis | null
  study: LabStudy | null
  progress: LabProgress | null
  error: string | null
  viewMode: LabViewMode
  onRetry: () => void
}

type ChartTab = 'ratio' | 'wealth'

function signedPct(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return '—'
  return `${value.toLocaleString('en-US', {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
    signDisplay: 'exceptZero',
  })}%`
}

export function LabHeroCharts({ analysis, study, progress, error, viewMode, onRetry }: LabHeroChartsProps) {
  const [activeTab, setActiveTab] = useState<ChartTab>('ratio')
  const [bands, setBands] = useState(true)
  const [anchor, setAnchor] = useState(true)
  const [showSignalTriggers, setShowSignalTriggers] = useState(true)
  const [showHolds, setShowHolds] = useState(false)
  const [hover, setHover] = useState<string | null>(null)
  const [sharedCursor, setSharedCursor] = useState<string | null>(null)
  const [viewport, setViewport] = useState<{ series: TimeSeriesDefinition[]; range: ChartVisibleRange | null } | null>(null)

  const series = useMemo<TimeSeriesDefinition[]>(() => {
    if (!analysis) return []
    const data = analysis.series
    const points = (values: (number | null)[]) => data.time.flatMap((time, index) => {
      const value = values[index]
      return value == null ? [] : [{ timestamp: new Date(time * 1000).toISOString(), value }]
    })
    const definitions: TimeSeriesDefinition[] = [
      { name: `${analysis.coin_a.code} per ${analysis.coin_b.code}`, unit: 'ratio', points: points(data.ratio) },
    ]
    if (bands) {
      definitions.push({ name: 'Moving average', unit: 'ratio', points: points(data.mean), dashed: true, colorToken: '--qap-muted' })
      for (const multiplier of [-2, 2]) {
        definitions.push({
          name: multiplier > 0 ? '+2σ band' : '-2σ band',
          unit: 'ratio',
          dashed: true,
          colorToken: '--qap-border-strong',
          points: points(data.mean.map((value, index) => (
            value == null || data.std[index] == null ? null : value + multiplier * data.std[index]!
          ))),
        })
      }
    }
    if (anchor && data.anchor_close && analysis.anchor) {
      definitions.push({ name: analysis.anchor.code, unit: 'USDT', points: points(data.anchor_close), priceScaleId: 'left', colorToken: '--qap-muted' })
    }
    return definitions
  }, [analysis, bands, anchor])

  const markers = useMemo<ChartMarker[]>(() => {
    if (!analysis) return []
    return (study?.result.trades ?? []).map((trade) => {
      if (trade.direction === 'into_a') {
        return { timestamp: trade.time, label: `Buy ${analysis.coin_a.code}`, selected: true, executed: true, colorToken: '--chart-coin-a', shape: 'arrowUp', position: 'belowBar' }
      }
      if (trade.direction === 'into_b') {
        return { timestamp: trade.time, label: `Buy ${analysis.coin_b.code}`, selected: true, executed: true, colorToken: '--chart-coin-b', shape: 'arrowDown', position: 'aboveBar' }
      }
      return {
        timestamp: trade.time,
        label: trade.direction === 'into_anchor' ? 'Park Anchor' : 'Park USDT',
        selected: true,
        executed: true,
        colorToken: '--qap-warning',
        shape: 'circle',
        position: 'aboveBar',
      }
    })
  }, [analysis, study])

  const options = useMemo(() => ({ bands, anchor: anchor && Boolean(analysis?.anchor) }), [bands, anchor, analysis?.anchor])
  const latest = useMemo(() => (analysis ? ratioReadout(analysis, null, options) : null), [analysis, options])
  const current = hover === null || !analysis ? latest : ratioReadout(analysis, hover, options)
  const onVisibleRangeChange = useCallback((range: ChartVisibleRange | null) => setViewport({ series, range }), [series])
  const visibleRange = viewport?.series === series ? viewport.range : null

  const signal = study?.result.signal ?? null
  const showSignal = viewMode === 'advanced' && Boolean(signal)
  const wealth = study?.result.wealth ?? null
  const vsHodl = study?.result.proof.vs_hodl_pct ?? null
  const ratioTitle = analysis ? `${analysis.coin_a.code} per ${analysis.coin_b.code}` : 'Ratio'

  return <section className="bt-hero-charts" aria-label="Market and backtest charts">
    <div className="bt-chart-header">
      <div className="bt-chart-tabs" role="tablist" aria-label="Chart view">
        <button type="button" role="tab" id="ratio" aria-selected={activeTab === 'ratio'} aria-controls="ratio-panel"
          className="bt-chart-tab" onClick={() => setActiveTab('ratio')}>
          Ratio Chart
        </button>
        <button type="button" role="tab" id="wealth" aria-selected={activeTab === 'wealth'} aria-controls="wealth-panel"
          className="bt-chart-tab" onClick={() => setActiveTab('wealth')}>
          Wealth Curve ($10,000)
          {vsHodl != null && <span className={`bt-badge ${vsHodl >= 0 ? 'bt-badge-pos' : 'bt-badge-neg'}`}>{signedPct(vsHodl)}</span>}
        </button>
      </div>
      {analysis && (
        <div className="bt-chart-toggles">
          {activeTab === 'ratio' && (
            <>
              <label title="Draw the trailing moving average with its ±2σ band">
                <input type="checkbox" checked={bands} onChange={(event) => setBands(event.target.checked)} />
                ±2σ Band
              </label>
              <label title={analysis.anchor ? 'Overlay the benchmark price on the left axis' : 'Select a Benchmark in the top bar to overlay it'}>
                <input type="checkbox" checked={anchor && Boolean(analysis.anchor)} disabled={!analysis.anchor}
                  onChange={(event) => setAnchor(event.target.checked)} />
                Benchmark ({analysis.anchor?.code ?? 'None'})
              </label>
              {showSignal && (
                <label title="Show dashed upper and lower entry trigger lines on the active signal chart">
                  <input type="checkbox" checked={showSignalTriggers} onChange={(event) => setShowSignalTriggers(event.target.checked)} />
                  Show Signal Trigger Lines
                </label>
              )}
            </>
          )}
          {activeTab === 'wealth' && wealth && Boolean(wealth.value.hold_a || wealth.value.hold_b) && (
            <label title="Overlay 100% Hold Coin A and Hold Coin B curves">
              <input type="checkbox" checked={showHolds} onChange={(event) => setShowHolds(event.target.checked)} />
              Show Hold {analysis.coin_a.code} / {analysis.coin_b.code}
            </label>
          )}
        </div>
      )}
    </div>

    <div className="bt-chart-body">
      {error ? (
        <div className="bt-chart-state" role="alert">
          <p>{error}</p>
          <button type="button" className="bt-btn-secondary" onClick={onRetry}>Retry</button>
        </div>
      ) : !analysis ? (
        <div className="bt-chart-state" role="status">
          <p>{progress ? `${progress.stage} (${progress.completed}/${progress.total})` : 'Loading market candles…'}</p>
          <progress max={Math.max(1, progress?.total ?? 1)} value={progress?.completed ?? 0} aria-label="Market data progress" />
        </div>
      ) : activeTab === 'ratio' ? (
        <div className="bt-ratio-pane" role="tabpanel" id="ratio-panel" aria-labelledby="ratio">
          <TimeSeriesChart
            title={ratioTitle}
            description="Coin A divided by Coin B. The band is the trailing moving average with its ±2σ range. Benchmark prices use the left axis."
            series={series}
            markers={markers.length > 0 ? markers : undefined}
            height={360}
            sharedCursorTime={showSignal ? sharedCursor : undefined}
            onCursorTimeChange={showSignal ? setSharedCursor : undefined}
            sharedVisibleRange={showSignal ? visibleRange : undefined}
            onVisibleRangeChange={onVisibleRangeChange}
            onHoverTimeChange={setHover}
            readout={<LabReadout title={ratioTitle} current={current} latest={latest} />}
          />
          {showSignal && signal && (
            <LabSignalChart
              signal={signal}
              showTriggers={showSignalTriggers}
              sharedCursorTime={sharedCursor}
              onCursorTimeChange={setSharedCursor}
              sharedVisibleRange={visibleRange}
              onVisibleRangeChange={onVisibleRangeChange}
            />
          )}
        </div>
      ) : (
        <div className="bt-wealth-pane" role="tabpanel" id="wealth-panel" aria-labelledby="wealth">
          {wealth ? (
            <WealthChart wealth={wealth} coinACode={analysis.coin_a.code} coinBCode={analysis.coin_b.code} showHolds={showHolds} />
          ) : (
            <p className="bt-chart-prompt">
              Run a strategy test on the right to simulate $10,000 across {analysis.coin_a.code} and {analysis.coin_b.code} after Binance fees.
            </p>
          )}
        </div>
      )}
    </div>
  </section>
}
