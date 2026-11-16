import { useEffect, useRef, useState, type KeyboardEvent } from 'react'
import { BAR_MINUTES, type LabAnalysis, type LabViewMode } from './labContract'
import type { LivePaperSession } from './labPaperApi'
import type { LabCompareResult, LabSavedSummary, LabStudy } from './labStudyApi'
import { InfoTip } from './InfoTip'
import { LabCompareTable } from './LabCompareTable'
import { LabLivePaperPanel } from './LabLivePaperPanel'
import { LabSavedRuns } from './LabSavedRuns'
import './LabTerminal.css'

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

const TAB_ORDER: readonly BottomTabId[] = ['overview', 'compare', 'swaps', 'saved', 'paper', 'diagnostics']
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
    minutes >= 1440 ? `${(minutes / 1440).toFixed(1)} days` : minutes >= 60 ? `${(minutes / 60).toFixed(1)} h` : `${Math.round(minutes)} min`
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

function foldWindow(row: Record<string, unknown>): string {
  const start = row.test_start ?? row.start
  const end = row.test_end ?? row.end
  return start == null || end == null ? DASH : `${String(start).slice(0, 10)} → ${String(end).slice(0, 10)}`
}

export function LabBottomTabs({
  analysis, study, viewMode, compareResult, savedStudies, activeStudyId, savedLoading,
  paperSession, paperBusy, paperError, onOpenStudy, onTogglePinStudy, onClearCompare,
  onStartPaper, onStepPaper, onStopPaper,
}: LabBottomTabsProps) {
  const [activeTab, setActiveTab] = useState<BottomTabId>('overview')
  const seenCompare = useRef<LabCompareResult | null>(compareResult)

  useEffect(() => {
    if (compareResult && compareResult !== seenCompare.current) setActiveTab('compare')
    seenCompare.current = compareResult
  }, [compareResult])

  const measurements = analysis?.measurements ?? null
  const trades = study?.result.trades ?? []
  const folds = study?.result.folds ?? []
  const proof = study?.result.proof ?? null
  const datasets = analysis?.datasets ?? []
  const coinA = analysis?.coin_a.code ?? 'A'
  const coinB = analysis?.coin_b.code ?? 'B'
  const strategyStats = study?.result.statistics?.strategy as Record<string, unknown> | undefined
  const holdings = (strategyStats?.terminal_holdings ?? {}) as Record<string, string>
  const holdingText = Object.entries(holdings)
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

  const kpis = analysis ? [
    { label: 'Return Correlation', value: fixed(measurements?.correlation?.pearson), sub: correlationWord(measurements?.correlation?.pearson ?? null), hint: 'Simultaneous log-return Pearson correlation. Above 0.70 indicates strong co-movement; below 0.40 indicates weak coupling.' },
    { label: 'Mean-Reversion Half-Life', ...halfLifeReading(analysis), hint: 'Estimated bars for a ratio dislocation to decay halfway back to its mean. Half-life < 48 bars signals fast snap-back.' },
    { label: 'Market Regime', value: measurements?.hurst ? HURST_READING[measurements.hurst.reading] : DASH, sub: measurements?.hurst ? `H = ${measurements.hurst.exponent.toFixed(2)}` : 'Not enough bars', hint: 'Hurst exponent: H < 0.45 = mean-reverting, 0.45–0.55 = random walk, H > 0.55 = trending.' },
    { label: 'Benchmark Fit', ...benchmarkReading(analysis), hint: 'Joint R² share of pair return variance explained by the top reference asset (BTC, ETH, BNB, SOL).' },
  ] : []

  const summary = strategyStats ? [
    ['Max Drawdown', signedPct(strategyStats.maximum_drawdown_pct)],
    ['Total Swaps', typeof strategyStats.rotations === 'number' ? strategyStats.rotations.toLocaleString('en-US') : DASH],
    ['Total Fees (USDT)', money(strategyStats.fees_usdt)],
    ['Total Slippage (USDT)', money(strategyStats.slippage_usdt)],
    ['Ending Holdings', holdingText],
  ] : []

  const econometrics = [
    { test: 'Cointegration ADF', reading: measurements?.cointegration ? `stat ${measurements.cointegration.statistic.toFixed(2)}` : DASH, detail: measurements?.cointegration ? `p = ${measurements.cointegration.p_value.toFixed(4)} · ${measurements.cointegration.passes ? 'Passes' : 'Fails'}` : 'Unavailable' },
    { test: 'Hedge slopes', reading: measurements?.hedge_ratio ? `OLS ${measurements.hedge_ratio.ols.toFixed(3)} · TLS ${measurements.hedge_ratio.tls.toFixed(3)}` : DASH, detail: measurements?.kalman ? `Kalman β ${measurements.kalman.beta.toFixed(3)} ± ${measurements.kalman.standard_error.toFixed(3)}` : 'Kalman unavailable' },
    { test: 'Tail dependence', reading: measurements?.copula ? `λL ${measurements.copula.lower_tail.toFixed(2)} · λU ${measurements.copula.upper_tail.toFixed(2)}` : DASH, detail: measurements?.copula ? `${measurements.copula.family} family · ${measurements.copula.observations} returns` : 'Unavailable' },
    { test: 'Granger lead-lag', reading: measurements?.granger ? `${coinA}→${coinB} p ${measurements.granger.a_to_b.p_value.toFixed(3)}` : DASH, detail: measurements?.granger ? `${coinB}→${coinA} p ${measurements.granger.b_to_a.p_value.toFixed(3)} · lag ${measurements.granger.max_lag}` : 'Unavailable' },
  ]

  function moveTab(event: KeyboardEvent<HTMLButtonElement>, current: BottomTabId) {
    const step = event.key === 'ArrowRight' ? 1 : event.key === 'ArrowLeft' ? -1 : 0
    if (step === 0) return
    event.preventDefault()
    const next = TAB_ORDER[(TAB_ORDER.indexOf(current) + step + TAB_ORDER.length) % TAB_ORDER.length]
    setActiveTab(next)
    document.getElementById(`bt-tab-${next}`)?.focus()
  }

  return (
    <section className="bt-bottom-workspace" aria-label="Research and execution tabs">
      <div className="bt-tab-bar" role="tablist" aria-label="Workspace panels">
        {tabs.map((tab) => (
          <button
            key={tab.id} type="button" role="tab" id={`bt-tab-${tab.id}`} className="bt-tab"
            aria-selected={activeTab === tab.id} aria-controls={`bt-panel-${tab.id}`}
            tabIndex={activeTab === tab.id ? 0 : -1} title={tab.live ? 'Paper session running' : undefined}
            onClick={() => setActiveTab(tab.id)} onKeyDown={(event) => moveTab(event, tab.id)}
          >
            {tab.label}
            {tab.live && <span className="bt-live-dot" aria-hidden="true" />}
          </button>
        ))}
      </div>

      <div className="bt-panel" role="tabpanel" id={`bt-panel-${activeTab}`} aria-labelledby={`bt-tab-${activeTab}`} tabIndex={0}>
        {activeTab === 'overview' && (analysis ? (
          <>
            <div className="bt-kpi-grid">
              {kpis.map((kpi) => (
                <div key={kpi.label} className="bt-kpi-tile">
                  <span className="bt-kpi-label">
                    {kpi.label}
                    <InfoTip label={`${kpi.label} guidance`} text={kpi.hint} />
                  </span>
                  <strong className="bt-kpi-value bt-mono">{kpi.value}</strong>
                  <span className="bt-kpi-sub">{kpi.sub}</span>
                </div>
              ))}
            </div>
            {summary.length > 0 && (
              <dl className="bt-summary-strip" aria-label="Backtest summary">
                {summary.map(([label, value]) => (
                  <div key={label}><dt>{label}</dt><dd className="bt-mono">{value}</dd></div>
                ))}
              </dl>
            )}
          </>
        ) : (
          <p className="bt-empty">Choose two coins to load correlation, half-life, regime, and benchmark fit.</p>
        ))}

        {activeTab === 'compare' && (compareResult ? (
          <LabCompareTable compare={compareResult} onOpenStudy={onOpenStudy} onClose={onClearCompare} />
        ) : (
          <p className="bt-empty">Click Compare All Presets in the Strategy panel to benchmark Z-Score, Copula, and Trend side-by-side.</p>
        ))}

        {activeTab === 'swaps' && (trades.length === 0 ? (
          <p className="bt-empty">No simulated swaps yet. Run a strategy test to fill this log.</p>
        ) : (
          <div className="bt-table-scroll">
            <table className="bt-table">
              <caption className="bt-visually-hidden">Simulated validation swaps</caption>
              <thead>
                <tr><th scope="col">Time (UTC)</th><th scope="col">Action</th><th scope="col">Route</th><th scope="col" className="bt-num">Fees (USDT)</th><th scope="col" className="bt-num">Slippage (USDT)</th><th scope="col" className="bt-num">Legs</th></tr>
              </thead>
              <tbody>
                {trades.map((trade, index) => (
                  <tr key={`${trade.fill_index}-${index}`}>
                    <td className="bt-mono">{utcStamp(trade.time)}</td>
                    <td>{actionLabel(trade.direction, analysis)}</td>
                    <td className="bt-muted-cell">{trade.route}</td>
                    <td className="bt-mono bt-num">{Number(trade.fees_usdt).toFixed(4)}</td>
                    <td className="bt-mono bt-num">{Number(trade.slippage_usdt).toFixed(4)}</td>
                    <td className="bt-mono bt-num">{trade.fills.length}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ))}

        {activeTab === 'saved' && (
          <LabSavedRuns studies={savedStudies} activeStudyId={activeStudyId} loading={savedLoading} onSelect={onOpenStudy} onTogglePin={onTogglePinStudy} />
        )}

        {activeTab === 'paper' && (
          <LabLivePaperPanel session={paperSession} busy={paperBusy} error={paperError} canStart={Boolean(analysis)} onStart={onStartPaper} onStep={onStepPaper} onStop={onStopPaper} />
        )}

        {activeTab === 'diagnostics' && (
          <div className="bt-diag-grid">
            <section className="bt-diag-col" aria-label="Econometric and dependence tests">
              <h3 className="bt-diag-title">Econometric &amp; dependence tests</h3>
              {viewMode === 'simple' && (
                <p className="bt-note">Pro mode adds strategy controls and a signal chart. These tables stay available in either mode.</p>
              )}
              <div className="bt-table-scroll">
                <table className="bt-table">
                  <thead>
                    <tr><th scope="col">Test</th><th scope="col">Reading</th><th scope="col">Detail</th></tr>
                  </thead>
                  <tbody>
                    {econometrics.map((row) => (
                      <tr key={row.test}><td>{row.test}</td><td className="bt-mono">{row.reading}</td><td className="bt-muted-cell">{row.detail}</td></tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>

            <section className="bt-diag-col" aria-label="Walk-forward folds and audit provenance">
              <h3 className="bt-diag-title">Walk-forward folds &amp; audit provenance</h3>
              {folds.length === 0 ? (
                <p className="bt-empty">Run a strategy test to inspect validation folds and SPA p-values.</p>
              ) : (
                <div className="bt-table-scroll">
                  <table className="bt-table">
                    <thead>
                      <tr><th scope="col">Fold</th><th scope="col">Test window</th><th scope="col" className="bt-num">Strategy return</th><th scope="col" className="bt-num">Control return</th><th scope="col">Passed</th></tr>
                    </thead>
                    <tbody>
                      {folds.map((fold, index) => (
                        <tr key={index}>
                          <td className="bt-mono">{String(fold.fold ?? index + 1)}</td>
                          <td className="bt-mono">{foldWindow(fold)}</td>
                          <td className="bt-mono bt-num">{signedPct(fold.strategy_return_pct)}</td>
                          <td className="bt-mono bt-num">{signedPct(fold.control_return_pct)}</td>
                          <td>{fold.passes === true ? 'Yes' : fold.passes === false ? 'No' : DASH}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {proof && (
                <dl className="bt-proof-strip" aria-label="SPA significance">
                  <div><dt>SPA raw p</dt><dd className="bt-mono">{fixed(proof.raw_p_value, 4)}</dd></div>
                  <div><dt>SPA corrected p</dt><dd className="bt-mono">{fixed(proof.corrected_p_value, 4)}</dd></div>
                  <div><dt>Settings tried</dt><dd className="bt-mono">{proof.settings_tried.toLocaleString('en-US')}</dd></div>
                </dl>
              )}

              <h4 className="bt-diag-subtitle">Dataset SHA-256</h4>
              {datasets.length === 0 ? (
                <p className="bt-empty">No dataset loaded.</p>
              ) : (
                <div className="bt-table-scroll">
                  <table className="bt-table">
                    <thead>
                      <tr><th scope="col">Market</th><th scope="col">Interval</th><th scope="col">SHA-256</th></tr>
                    </thead>
                    <tbody>
                      {datasets.map((dataset) => (
                        <tr key={dataset.dataset_id}>
                          <td>{dataset.venue_symbol}</td>
                          <td className="bt-mono">{dataset.interval}</td>
                          <td className="bt-mono bt-hash">{dataset.semantic_fingerprint}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </section>
          </div>
        )}
      </div>
    </section>
  )
}
