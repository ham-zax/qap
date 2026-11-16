import { Activity, Compass, Gauge, GitCompare, Timer } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { DashboardCard } from '@/components/watermelon/dashboard-card'
import { StatCard } from '@/components/watermelon/stat-card'
import { InfoTip } from './InfoTip'
import { LabCompareTable } from './LabCompareTable'
import { LabDiagnosticsTab } from './LabDiagnosticsTab'
import { LabLivePaperPanel } from './LabLivePaperPanel'
import { LabSavedRuns } from './LabSavedRuns'
import { BAR_MINUTES, type LabAnalysis, type LabViewMode } from './labContract'
import type { LivePaperSession } from './labPaperApi'
import type { LabCompareResult, LabSavedSummary, LabStudy } from './labStudyApi'

export type BottomTabId = 'overview' | 'compare' | 'swaps' | 'saved' | 'paper' | 'diagnostics'

export interface LabBottomTabsProps {
  analysis: LabAnalysis | null
  study: LabStudy | null
  viewMode: LabViewMode
  compareResult: LabCompareResult | null
  savedStudies: readonly LabSavedSummary[]
  activeStudyId: string | null
  savedLoading: boolean
  paperSession: LivePaperSession | null
  paperBusy: boolean
  paperError: string | null
  onOpenStudy: (studyId: string) => void
  onTogglePinStudy: (studyId: string, pinned: boolean) => void
  onClearCompare: () => void
  onStartPaper: () => void
  onStepPaper: () => void
  onStopPaper: () => void
}

const HURST_READING = { reverting: 'Mean-Reverting', random: 'Random Walk', trending: 'Trending' } as const
const DASH = '—'

function fixed(raw: unknown, digits = 2): string {
  return typeof raw === 'number' && Number.isFinite(raw) ? raw.toFixed(digits) : DASH
}

function money(raw: unknown): string {
  const value = typeof raw === 'string' || typeof raw === 'number' ? Number(raw) : Number.NaN
  if (!Number.isFinite(value)) return DASH
  return value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function signedPct(raw: unknown): string {
  if (typeof raw !== 'number' || !Number.isFinite(raw)) return DASH
  return `${raw >= 0 ? '+' : ''}${raw.toFixed(2)}%`
}

function correlationWord(pearson: number | null): string {
  if (pearson == null || !Number.isFinite(pearson)) return 'Not enough overlap'
  const strength = Math.abs(pearson)
  if (strength >= 0.7) return 'Strong co-movement'
  return strength >= 0.4 ? 'Moderate co-movement' : 'Weak co-movement'
}

function halfLifeReading(analysis: LabAnalysis): { value: string; sub: string } {
  const halfLife = analysis.measurements.half_life
  if (!halfLife?.reverting || halfLife.bars == null) return { value: 'Non-reverting', sub: 'No measured decay' }
  const minutes = halfLife.bars * BAR_MINUTES[analysis.bar]
  const value =
    minutes >= 1440
      ? `${(minutes / 1440).toFixed(1)} days`
      : minutes >= 60
        ? `${(minutes / 60).toFixed(1)} h`
        : `${Math.round(minutes)} min`
  return { value, sub: `${halfLife.bars.toFixed(0)} bars at ${analysis.bar}` }
}

function benchmarkReading(analysis: LabAnalysis): { value: string; sub: string } {
  const best = analysis.anchor_ranking[0]
  if (!best) return { value: 'No benchmark', sub: 'Pick a reference asset' }
  const next = analysis.anchor_ranking[1]
  return {
    value: `${best.anchor.code} (${(best.joint_explained * 100).toFixed(0)}% R²)`,
    sub: next ? `Next: ${next.anchor.code} ${(next.joint_explained * 100).toFixed(0)}%` : 'Single benchmark tested',
  }
}

function actionLabel(direction: string, analysis: LabAnalysis | null): string {
  if (direction === 'into_a') return `Swap → ${analysis?.coin_a.code ?? 'Coin A'}`
  if (direction === 'into_b') return `Swap → ${analysis?.coin_b.code ?? 'Coin B'}`
  if (direction === 'into_anchor') return 'Park → Benchmark'
  if (direction === 'into_usdt') return 'Park → USDT'
  return direction
}

function utcStamp(raw: string): string {
  const stamp = new Date(raw)
  return Number.isNaN(stamp.getTime()) ? raw : stamp.toISOString().slice(0, 16).replace('T', ' ')
}

export function LabBottomTabs({
  analysis,
  study,
  viewMode,
  compareResult,
  savedStudies,
  activeStudyId,
  savedLoading,
  paperSession,
  paperBusy,
  paperError,
  onOpenStudy,
  onTogglePinStudy,
  onClearCompare,
  onStartPaper,
  onStepPaper,
  onStopPaper,
}: LabBottomTabsProps) {
  const [activeTab, setActiveTab] = useState<BottomTabId>('overview')
  const seenCompare = useRef<LabCompareResult | null>(compareResult)

  useEffect(() => {
    if (compareResult && compareResult !== seenCompare.current) setActiveTab('compare')
    seenCompare.current = compareResult
  }, [compareResult])

  const measurements = analysis?.measurements ?? null
  const trades = study?.result.trades ?? []
  const strategyStats = study?.result.statistics?.strategy as Record<string, unknown> | undefined
  const holdings = (strategyStats?.terminal_holdings ?? {}) as Record<string, string>
  const holdingText =
    Object.entries(holdings)
      .map(([asset, qty]) => `${asset.replace('binance:', '')} ${Number(qty).toLocaleString('en-US', { maximumSignificantDigits: 5 })}`)
      .join(' · ') || DASH

  const tabs: ReadonlyArray<{ id: BottomTabId; label: string; live?: boolean }> = [
    { id: 'overview', label: 'Overview' },
    { id: 'compare', label: compareResult ? `Compare Strategies (${compareResult.studies.length})` : 'Compare Strategies' },
    { id: 'swaps', label: `Simulated Swaps (${trades.length})` },
    { id: 'saved', label: `Saved Runs (${savedStudies.length})` },
    { id: 'paper', label: 'Live Paper', live: paperSession?.status === 'active' },
    { id: 'diagnostics', label: 'Pro Diagnostics' },
  ]

  const kpis = analysis
    ? [
        {
          label: 'Return Correlation',
          value: fixed(measurements?.correlation?.pearson),
          sub: correlationWord(measurements?.correlation?.pearson ?? null),
          icon: GitCompare,
          tone: 'info' as const,
          hint: 'Simultaneous log-return Pearson correlation. Above 0.70 indicates strong co-movement; below 0.40 indicates weak coupling.',
        },
        {
          label: 'Mean-Reversion Half-Life',
          ...halfLifeReading(analysis),
          icon: Timer,
          tone: 'positive' as const,
          hint: 'Estimated bars for a ratio dislocation to decay halfway back to its mean. Half-life < 48 bars signals fast snap-back.',
        },
        {
          label: 'Market Regime',
          value: measurements?.hurst ? HURST_READING[measurements.hurst.reading] : DASH,
          sub: measurements?.hurst ? `H = ${measurements.hurst.exponent.toFixed(2)}` : 'Not enough bars',
          icon: Gauge,
          tone: 'warning' as const,
          hint: 'Hurst exponent: H < 0.45 = mean-reverting, 0.45–0.55 = random walk, H > 0.55 = trending.',
        },
        {
          label: 'Benchmark Fit',
          ...benchmarkReading(analysis),
          icon: Compass,
          tone: 'neutral' as const,
          hint: 'Joint R² share of pair return variance explained by the top reference asset (BTC, ETH, BNB, SOL).',
        },
      ]
    : []

  const summary = strategyStats
    ? [
        ['Max Drawdown', signedPct(strategyStats.maximum_drawdown_pct)],
        ['Total Swaps', typeof strategyStats.rotations === 'number' ? strategyStats.rotations.toLocaleString('en-US') : DASH],
        ['Total Fees (USDT)', money(strategyStats.fees_usdt)],
        ['Total Slippage (USDT)', money(strategyStats.slippage_usdt)],
        ['Ending Holdings', holdingText],
      ]
    : []

  return (
    <DashboardCard className="p-0" aria-label="Research and execution tabs">
      <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as BottomTabId)} className="gap-0">
        <div className="overflow-x-auto border-b border-border px-3 py-2">
          <TabsList aria-label="Workspace panels" className="h-8 bg-muted p-0.5">
            {tabs.map((tab) => (
              <TabsTrigger
                key={tab.id}
                id={`bt-tab-${tab.id}`}
                value={tab.id}
                aria-controls={`bt-panel-${tab.id}`}
                onClick={() => setActiveTab(tab.id)}
                title={tab.live ? 'Paper session running' : undefined}
                className="h-7 gap-1.5 px-3 text-xs font-medium"
              >
                {tab.id === 'paper' && tab.live ? (
                  <Activity className="size-3.5 text-positive" aria-hidden="true" />
                ) : null}
                {tab.label}
                {tab.live && <span className="size-1.5 rounded-full bg-positive animate-pulse" aria-hidden="true" />}
              </TabsTrigger>
            ))}
          </TabsList>
        </div>

        <div className="p-4">
          <TabsContent value="overview" id="bt-panel-overview" aria-labelledby="bt-tab-overview" className="mt-0 space-y-4">
            {analysis ? (
              <>
                <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                  {kpis.map((kpi) => (
                    <StatCard
                      key={kpi.label}
                      label={kpi.label}
                      value={kpi.value}
                      sub={kpi.sub}
                      icon={kpi.icon}
                      tone={kpi.tone}
                      tip={<InfoTip label={`${kpi.label} guidance`} text={kpi.hint} />}
                    />
                  ))}
                </div>
                {summary.length > 0 && (
                  <dl
                    className="m-0 grid grid-cols-2 gap-3 border-t border-border pt-3 sm:grid-cols-3 lg:grid-cols-5"
                    aria-label="Backtest summary"
                  >
                    {summary.map(([label, value]) => (
                      <div key={label} className="rounded-lg border border-border bg-muted/35 px-3 py-2">
                        <dt className="text-[11px] text-muted-foreground">{label}</dt>
                        <dd className="m-0 mt-0.5 font-mono text-xs font-semibold text-foreground tabular-nums">
                          {value}
                        </dd>
                      </div>
                    ))}
                  </dl>
                )}
              </>
            ) : (
              <p className="m-0 py-4 text-xs text-muted-foreground">
                Choose two coins to load correlation, half-life, regime, and benchmark fit.
              </p>
            )}
          </TabsContent>

          <TabsContent value="compare" id="bt-panel-compare" aria-labelledby="bt-tab-compare" className="mt-0">
            {compareResult ? (
              <LabCompareTable compare={compareResult} onOpenStudy={onOpenStudy} onClose={onClearCompare} />
            ) : (
              <p className="m-0 py-4 text-xs text-muted-foreground">
                Click Compare All Presets in the Strategy panel to benchmark Z-Score, Copula, and Trend side-by-side.
              </p>
            )}
          </TabsContent>

          <TabsContent value="swaps" id="bt-panel-swaps" aria-labelledby="bt-tab-swaps" className="mt-0">
            {trades.length === 0 ? (
              <p className="m-0 py-4 text-xs text-muted-foreground">
                No simulated swaps yet. Run a strategy test to fill this log.
              </p>
            ) : (
              <div className="max-h-96 overflow-auto rounded-lg border border-border">
                <Table>
                  <caption className="sr-only">Simulated validation swaps</caption>
                  <TableHeader className="bg-muted/60">
                    <TableRow>
                      <TableHead className="h-9 text-xs">Time (UTC)</TableHead>
                      <TableHead className="h-9 text-xs">Action</TableHead>
                      <TableHead className="h-9 text-xs">Route</TableHead>
                      <TableHead className="h-9 text-right text-xs">Fees (USDT)</TableHead>
                      <TableHead className="h-9 text-right text-xs">Slippage (USDT)</TableHead>
                      <TableHead className="h-9 text-right text-xs">Legs</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {trades.map((trade, index) => (
                      <TableRow key={`${trade.fill_index}-${index}`}>
                        <TableCell className="font-mono text-xs tabular-nums">{utcStamp(trade.time)}</TableCell>
                        <TableCell className="text-xs font-medium">{actionLabel(trade.direction, analysis)}</TableCell>
                        <TableCell className="text-xs text-muted-foreground">{trade.route}</TableCell>
                        <TableCell className="text-right font-mono text-xs tabular-nums">
                          {Number(trade.fees_usdt).toFixed(4)}
                        </TableCell>
                        <TableCell className="text-right font-mono text-xs tabular-nums">
                          {Number(trade.slippage_usdt).toFixed(4)}
                        </TableCell>
                        <TableCell className="text-right font-mono text-xs tabular-nums">
                          {trade.fills.length}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </TabsContent>

          <TabsContent value="saved" id="bt-panel-saved" aria-labelledby="bt-tab-saved" className="mt-0">
            <LabSavedRuns
              studies={savedStudies}
              activeStudyId={activeStudyId}
              loading={savedLoading}
              onSelect={onOpenStudy}
              onTogglePin={onTogglePinStudy}
            />
          </TabsContent>

          <TabsContent value="paper" id="bt-panel-paper" aria-labelledby="bt-tab-paper" className="mt-0">
            <LabLivePaperPanel
              session={paperSession}
              busy={paperBusy}
              error={paperError}
              canStart={Boolean(analysis)}
              onStart={onStartPaper}
              onStep={onStepPaper}
              onStop={onStopPaper}
            />
          </TabsContent>

          <TabsContent value="diagnostics" id="bt-panel-diagnostics" aria-labelledby="bt-tab-diagnostics" className="mt-0">
            <LabDiagnosticsTab analysis={analysis} study={study} viewMode={viewMode} />
          </TabsContent>
        </div>
      </Tabs>
    </DashboardCard>
  )
}
