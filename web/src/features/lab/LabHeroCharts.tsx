import { AlertCircle, RotateCcw } from 'lucide-react'
import { useCallback, useMemo, useState } from 'react'

import { TimeSeriesChart } from '../../components/charts/TimeSeriesChart'
import type { ChartMarker, ChartVisibleRange, TimeSeriesDefinition } from '../../components/charts/chartData'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { Label } from '@/components/ui/label'
import { Progress } from '@/components/ui/progress'
import { Skeleton } from '@/components/ui/skeleton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { DashboardCard, DetailTag } from '@/components/watermelon/dashboard-card'
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
    const points = (values: (number | null)[]) =>
      data.time.flatMap((time, index) => {
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
          points: points(
            data.mean.map((value, index) =>
              value == null || data.std[index] == null ? null : value + multiplier * data.std[index]!,
            ),
          ),
        })
      }
    }
    if (anchor && data.anchor_close && analysis.anchor) {
      definitions.push({
        name: analysis.anchor.code,
        unit: 'USDT',
        points: points(data.anchor_close),
        priceScaleId: 'left',
        colorToken: '--qap-muted',
      })
    }
    return definitions
  }, [analysis, bands, anchor])

  const markers = useMemo<ChartMarker[]>(() => {
    if (!analysis) return []
    return (study?.result.trades ?? []).map((trade) => {
      if (trade.direction === 'into_a') {
        return {
          timestamp: trade.time,
          label: `Buy ${analysis.coin_a.code}`,
          selected: true,
          executed: true,
          colorToken: '--chart-coin-a',
          shape: 'arrowUp',
          position: 'belowBar',
        }
      }
      if (trade.direction === 'into_b') {
        return {
          timestamp: trade.time,
          label: `Buy ${analysis.coin_b.code}`,
          selected: true,
          executed: true,
          colorToken: '--chart-coin-b',
          shape: 'arrowDown',
          position: 'aboveBar',
        }
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

  const options = useMemo(
    () => ({ bands, anchor: anchor && Boolean(analysis?.anchor) }),
    [bands, anchor, analysis?.anchor],
  )
  const latest = useMemo(() => (analysis ? ratioReadout(analysis, null, options) : null), [analysis, options])
  const current = hover === null || !analysis ? latest : ratioReadout(analysis, hover, options)
  const onVisibleRangeChange = useCallback(
    (range: ChartVisibleRange | null) => setViewport({ series, range }),
    [series],
  )
  const visibleRange = viewport?.series === series ? viewport.range : null

  const signal = study?.result.signal ?? null
  const showSignal = viewMode === 'advanced' && Boolean(signal)
  const wealth = study?.result.wealth ?? null
  const vsHodl = study?.result.proof.vs_hodl_pct ?? null
  const ratioTitle = analysis ? `${analysis.coin_a.code} per ${analysis.coin_b.code}` : 'Ratio'
  const progressPct = progress ? Math.round((progress.completed / Math.max(1, progress.total)) * 100) : 20

  return (
    <DashboardCard className="bt-hero-charts flex flex-col gap-3 p-3.5" aria-label="Market and backtest charts">
      <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as ChartTab)} className="w-full gap-3">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border pb-2.5">
          <TabsList aria-label="Chart view" className="h-8 bg-muted p-0.5">
            <TabsTrigger
              id="ratio"
              value="ratio"
              aria-controls="ratio-panel"
              onClick={() => setActiveTab('ratio')}
              className="h-7 px-3 text-xs font-medium"
            >
              Ratio Chart
            </TabsTrigger>
            <TabsTrigger
              id="wealth"
              value="wealth"
              aria-controls="wealth-panel"
              onClick={() => setActiveTab('wealth')}
              className="h-7 gap-1.5 px-3 text-xs font-medium"
            >
              Wealth Curve ($10,000)
              {vsHodl != null && (
                <DetailTag tone={vsHodl >= 0 ? 'positive' : 'negative'} className="px-1.5 py-0 text-[11px]">
                  {signedPct(vsHodl)}
                </DetailTag>
              )}
            </TabsTrigger>
          </TabsList>

          {analysis && (
            <div className="flex flex-wrap items-center gap-3">
              {activeTab === 'ratio' && (
                <>
                  <Label
                    htmlFor="chart-toggle-bands"
                    className="cursor-pointer text-xs font-normal text-muted-foreground hover:text-foreground"
                    title="Draw the trailing moving average with its ±2σ band"
                  >
                    <Checkbox
                      id="chart-toggle-bands"
                      checked={bands}
                      onCheckedChange={(checked) => setBands(checked === true)}
                    />
                    ±2σ Band
                  </Label>
                  <Label
                    htmlFor="chart-toggle-anchor"
                    className="cursor-pointer text-xs font-normal text-muted-foreground hover:text-foreground"
                    title={
                      analysis.anchor
                        ? 'Overlay the benchmark price on the left axis'
                        : 'Select a Benchmark in the top bar to overlay it'
                    }
                  >
                    <Checkbox
                      id="chart-toggle-anchor"
                      checked={anchor && Boolean(analysis.anchor)}
                      disabled={!analysis.anchor}
                      onCheckedChange={(checked) => setAnchor(checked === true)}
                    />
                    Benchmark ({analysis.anchor?.code ?? 'None'})
                  </Label>
                  {showSignal && (
                    <Label
                      htmlFor="chart-toggle-signal-lines"
                      className="cursor-pointer text-xs font-normal text-muted-foreground hover:text-foreground"
                      title="Show dashed upper and lower entry trigger lines on the active signal chart"
                    >
                      <Checkbox
                        id="chart-toggle-signal-lines"
                        checked={showSignalTriggers}
                        onCheckedChange={(checked) => setShowSignalTriggers(checked === true)}
                      />
                      Show Signal Trigger Lines
                    </Label>
                  )}
                </>
              )}
              {activeTab === 'wealth' && wealth && Boolean(wealth.value.hold_a || wealth.value.hold_b) && (
                <Label
                  htmlFor="chart-toggle-holds"
                  className="cursor-pointer text-xs font-normal text-muted-foreground hover:text-foreground"
                  title="Overlay 100% Hold Coin A and Hold Coin B curves"
                >
                  <Checkbox
                    id="chart-toggle-holds"
                    checked={showHolds}
                    onCheckedChange={(checked) => setShowHolds(checked === true)}
                  />
                  Show Hold {analysis.coin_a.code} / {analysis.coin_b.code}
                </Label>
              )}
            </div>
          )}
        </div>

        <div className="min-w-0">
          {error ? (
            <div className="flex min-h-80 items-center justify-center p-4">
              <Alert variant="destructive" className="max-w-lg">
                <AlertCircle className="size-4" aria-hidden="true" />
                <AlertTitle>Market data unavailable</AlertTitle>
                <AlertDescription className="mt-1 space-y-3">
                  <p className="m-0">{error}</p>
                  <Button type="button" variant="outline" size="sm" onClick={onRetry}>
                    <RotateCcw className="size-3.5" aria-hidden="true" />
                    Retry
                  </Button>
                </AlertDescription>
              </Alert>
            </div>
          ) : !analysis ? (
            <div className="flex min-h-80 flex-col justify-center gap-4 p-4" role="status">
              <div className="space-y-2">
                <p className="m-0 text-sm text-muted-foreground">
                  {progress
                    ? `${progress.stage} (${progress.completed}/${progress.total})`
                    : 'Loading market candles…'}
                </p>
                <Progress
                  value={progressPct}
                  aria-label="Market data progress"
                  className="max-w-md"
                />
              </div>
              <Skeleton className="h-56 w-full rounded-lg" />
            </div>
          ) : (
            <>
              <TabsContent value="ratio" id="ratio-panel" aria-labelledby="ratio" className="mt-0">
                <div className="bt-ratio-pane">
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
              </TabsContent>

              <TabsContent value="wealth" id="wealth-panel" aria-labelledby="wealth" className="mt-0">
                {wealth ? (
                  <WealthChart
                    wealth={wealth}
                    coinACode={analysis.coin_a.code}
                    coinBCode={analysis.coin_b.code}
                    showHolds={showHolds}
                  />
                ) : (
                  <div className="flex min-h-64 items-center justify-center rounded-lg border border-dashed border-border bg-muted/20 p-6 text-center">
                    <p className="m-0 max-w-md text-sm text-muted-foreground">
                      Run a strategy test on the right to simulate $10,000 across {analysis.coin_a.code} and{' '}
                      {analysis.coin_b.code} after Binance fees.
                    </p>
                  </div>
                )}
              </TabsContent>
            </>
          )}
        </div>
      </Tabs>
    </DashboardCard>
  )
}
