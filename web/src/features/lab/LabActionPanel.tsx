import {
  BAR_MINUTES,
  LAB_ROTATION_PCTS,
  fromBackendLabSettings,
  type LabAnalysis,
  type LabBar,
  type LabCrashDefenseMode,
  type LabHedgeMethod,
  type LabSignalMethod,
  type LabStrategyFormSettings,
  type LabViewMode,
} from './labContract'
import { InfoTip } from './InfoTip'
import type { LabAdvisor, LabAdvisorSuggestion, LabStudy } from './labStudyApi'

export interface LabActionPanelProps {
  analysis: LabAnalysis | null
  settings: LabStrategyFormSettings
  viewMode: LabViewMode
  dirty: boolean
  study: LabStudy | null
  studyRestored: boolean
  studyRunning: boolean
  studyError: string | null
  compareRunning: boolean
  advisor: LabAdvisor | null
  advisorLoading: boolean
  savedBanner?: { studyId: string; label: string } | null
  bandLookback: number
  bar: LabBar
  onChangeBandLookback: (value: number) => void
  onSelectBar?: (bar: LabBar) => void
  onDismissSavedBanner?: () => void
  onEditSettings?: () => void
  onChangeSettings: (patch: Partial<LabStrategyFormSettings>) => void
  onApplyPreset: (suggestion: LabAdvisorSuggestion) => void
  onRunTest: (method?: LabSignalMethod) => void
  onCompareAll: () => void
  onClearStudy: () => void
}

const METHODS: ReadonlyArray<{ id: LabSignalMethod; label: string }> = [
  { id: 'zscore', label: 'Z-Score' },
  { id: 'copula', label: 'Spread Copula' },
  { id: 'trend', label: 'Ratio Trend' },
  { id: 'lead_lag', label: 'Anchor Lead-Lag' },
]

const FALLBACK_PRESETS: ReadonlyArray<{ id: string; title: string; method: LabSignalMethod; reason: string }> = [
  { id: 'fallback-zscore', title: 'Mean Reversion · Buy Dip Coin', method: 'zscore', reason: 'Buys the coin that has fallen furthest below its usual ratio, then exits as it reverts.' },
  { id: 'fallback-copula', title: 'Tail Mispricing · Spread Copula', method: 'copula', reason: 'Trades only rare joint tail moves, where one coin is mispriced against the other.' },
  { id: 'fallback-trend', title: 'Trend Rotation · Ride Stronger Coin', method: 'trend', reason: 'Holds the coin with the stronger moving-average trend until that trend fades.' },
]

function money(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return '—'
  return `$${value.toLocaleString('en-US', { maximumFractionDigits: 0 })}`
}

function signedPct(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return '—'
  return `${value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2, signDisplay: 'exceptZero' })}%`
}

function tone(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value) || value === 0) return 'bt-badge-neutral'
  return value > 0 ? 'bt-badge-pos' : 'bt-badge-neg'
}

/** Human duration of a bar count on the active candle interval. */
function barSpan(bars: number, bar: LabBar): string {
  const minutes = bars * BAR_MINUTES[bar]
  if (!Number.isFinite(minutes) || minutes <= 0) return '0 bars'
  if (minutes < 60) return `${Math.round(minutes)} min`
  if (minutes < 1440) return `${(minutes / 60).toFixed(1)} h`
  return `${(minutes / 1440).toFixed(1)} days`
}

/** Approximate two-tailed normal probability in % for a z-score threshold. */
function approxTailPct(z: number): string {
  const t = 1 / (1 + 0.2316419 * Math.abs(z))
  const d = 0.3989423 * Math.exp((-z * z) / 2)
  const p = d * t * (0.3193815 + t * (-0.3565638 + t * (1.781478 + t * (-1.821256 + t * 1.330274))))
  const twoTail = Math.max(0.01, Math.min(99, 2 * p * 100))
  return twoTail >= 10 ? `${twoTail.toFixed(0)}%` : `${twoTail.toFixed(1)}%`
}

function RangeField({ label, valueText, badge, value, min, max, step, onChange }: {
  label: string; valueText: string; badge?: string; value: number; min: number; max: number; step: number; onChange: (value: number) => void
}) {
  return <label className="bt-field bt-range-field">
    <span className="bt-range-head">
      <span>{label}</span>
      <span className="bt-range-readout bt-mono">
        <strong>{valueText}</strong>
        {badge ? <small className="bt-range-badge">{badge}</small> : null}
      </span>
    </span>
    <input
      type="range"
      min={min}
      max={max}
      step={step}
      value={Math.min(max, Math.max(min, value))}
      onChange={(event) => {
        const parsed = Number(event.target.value)
        if (Number.isFinite(parsed)) onChange(parsed)
      }}
    />
  </label>
}

function NumberField({ label, hint, value, min, max, step, onChange }: {
  label: string; hint?: string; value: number; min: number; max: number; step?: number; onChange: (value: number) => void
}) {
  return <label className="bt-field">
    <span>{label}{hint ? <small>{hint}</small> : null}</span>
    <input
      type="number"
      className="bt-mono"
      min={min}
      max={max}
      step={step}
      value={value}
      onChange={(event) => {
        const parsed = Number(event.target.value)
        if (Number.isFinite(parsed) && parsed >= min && parsed <= max) onChange(parsed)
      }}
    />
  </label>
}

export function LabActionPanel({
  analysis,
  settings,
  viewMode,
  dirty,
  study,
  studyRestored,
  studyRunning,
  studyError,
  compareRunning,
  advisor,
  advisorLoading,
  savedBanner,
  bandLookback,
  bar,
  onChangeBandLookback,
  onSelectBar,
  onDismissSavedBanner,
  onEditSettings,
  onChangeSettings,
  onApplyPreset,
  onRunTest,
  onCompareAll,
  onClearStudy,
}: LabActionPanelProps) {
  const proof = study?.result.proof ?? null
  const call = study?.result.call ?? null
  const wealth = study?.result.wealth ?? null
  const rotating = wealth ? Number(wealth.terminal_values.strategy) : null
  const holding = wealth ? Number(wealth.terminal_values.hodl) : null
  const targetWeightA = call?.target_weight_a == null ? null : Number(call.target_weight_a)
  const targetPct = call == null || targetWeightA == null || !Number.isFinite(targetWeightA)
    ? null
    : Math.round((call.status === 'into_a' ? targetWeightA : 1 - targetWeightA) * 100)
  const coinCode = call?.status === 'into_b' ? analysis?.coin_b.code ?? 'Coin B' : analysis?.coin_a.code ?? 'Coin A'
  const activePreset = advisor?.suggestions.find((item) => JSON.stringify(fromBackendLabSettings(item.settings)) === JSON.stringify(settings))?.preset_id ?? null
  const dismissSaved = onDismissSavedBanner ?? onClearStudy
  const leadLagNeeds1m = settings.method === 'lead_lag' && bar !== '1m'
  const exitMax = Math.max(0, Math.min(2.5, Number((settings.entry - 0.1).toFixed(1))))
  const copulaExitMax = Math.max(0.05, Math.min(0.35, Number((0.49 - settings.copula_probability).toFixed(2))))
  const copulaEntryPct = Math.round(settings.copula_probability * 100)
  const copulaBandPct = Math.round(settings.copula_exit_band * 100)
  const proofGateSummary = proof
    ? `3-Gate Check — Cost Gate (gross >= 2× fees): ${proof.cost_gate_passed ? 'PASS' : 'FAIL'} · Walk-Forward (${proof.folds_passing}/${proof.folds_total} folds, need >= ${proof.minimum_passing_folds}): ${proof.folds_passing >= proof.minimum_passing_folds ? 'PASS' : 'FAIL'} · SPA corrected p=${proof.corrected_p_value != null ? proof.corrected_p_value.toFixed(3) : '—'} (need <= ${proof.significance}): ${proof.corrected_p_value != null && proof.corrected_p_value <= proof.significance ? 'PASS' : 'FAIL'}.`
    : ''

  return <aside className="bt-action-panel" aria-label="Strategy workbench">
    {(savedBanner || studyRestored) && (
      <div className="bt-saved-banner" role="status">
        <span>Viewing Saved Run: {savedBanner?.label ?? 'Restored'}</span>
        {onEditSettings && <button type="button" className="bt-banner-clear" onClick={onEditSettings}>Edit Settings</button>}
        <button type="button" className="bt-banner-clear" onClick={dismissSaved}>Clear</button>
      </div>
    )}

    <section className="bt-verdict-box" aria-label="Backtest verdict">
      <div className="bt-verdict-head">
        <h2>Verdict</h2>
        <span className="bt-verdict-base bt-mono">$10,000 base</span>
      </div>

      {studyRunning ? (
        <div className="bt-verdict-running">
          <p>Simulating $10,000 across walk-forward folds…</p>
          <progress aria-label="Strategy test progress" />
        </div>
      ) : studyError ? (
        <p className="bt-verdict-error" role="alert">{studyError}</p>
      ) : study && proof && call ? (
        <>
          <div className="bt-verdict-status-row">
            <span className={`bt-status-badge ${proof.passes ? 'bt-badge-pos' : 'bt-badge-neutral'}`}>
              {proof.passes ? `Validated Edge (${proof.folds_passing}/${proof.folds_total} Folds)` : call.headline}
            </span>
            <InfoTip label="Validation gate criteria" text={proofGateSummary} />
          </div>
          <dl className="bt-verdict-numbers">
            <div>
              <dt>Strategy</dt>
              <dd className="bt-mono">$10,000 → {money(rotating)}</dd>
            </div>
            <div>
              <dt>Hold 50/50</dt>
              <dd className="bt-mono">{money(holding)}</dd>
            </div>
          </dl>
          <p className="bt-verdict-deltas bt-mono">
            <span className={tone(proof.vs_hodl_pct)}>{signedPct(proof.vs_hodl_pct)} vs Hold</span>
            <span className={tone(proof.vs_control_pct)}>{signedPct(proof.vs_control_pct)} vs Rebalance</span>
          </p>
          <p className="bt-verdict-fees bt-mono">
            {proof.validation_trades} swaps · {proof.cost_paid_pct?.toFixed(2) ?? '0.00'}% total fees &amp; slippage
          </p>
          {(call.status === 'into_a' || call.status === 'into_b') && (
            <p className="bt-action-chip">
              Signal: Swap toward {coinCode}{targetPct == null ? '' : ` (${targetPct}%)`}
            </p>
          )}
        </>
      ) : (
        <p className="bt-verdict-ready">
          {analysis
            ? `${analysis.coin_a.code}/${analysis.coin_b.code} ready (${analysis.bars_used} candles). Select a strategy below to backtest $10,000 after ${(settings.fee_bps / 100).toFixed(2)}% spot fees.`
            : `Choose two coins to load market candles, then backtest $10,000 after ${(settings.fee_bps / 100).toFixed(2)}% spot fees.`}
        </p>
      )}
    </section>

    <section className="bt-strategy" aria-label="Strategy selection">
      <div className="bt-strategy-head">
        <h2>{viewMode === 'simple' ? 'Choose Strategy' : 'Strategy Controls'}</h2>
        {dirty && <span className="bt-dirty-pill">Unsaved changes</span>}
      </div>

      {viewMode === 'simple' ? (
        <>
          {bar === '15m' && advisor?.bar_warning && <p className="bt-warning" role="note">{advisor.bar_warning}</p>}
          <div className="bt-preset-grid">
            {advisor ? advisor.suggestions.map((suggestion) => (
              <article key={suggestion.preset_id} className={`bt-preset-card${activePreset === suggestion.preset_id ? ' is-active' : ''}`}>
                <button type="button" className="bt-preset-select" aria-pressed={activePreset === suggestion.preset_id}
                  onClick={() => {
                    onChangeSettings(fromBackendLabSettings(suggestion.settings))
                  }}>
                  <strong>{suggestion.title}</strong>
                  <span>{suggestion.simple_reason}</span>
                </button>
                <button type="button" className="bt-preset-test" disabled={!analysis || studyRunning} onClick={() => onApplyPreset(suggestion)}>Test</button>
              </article>
            )) : FALLBACK_PRESETS.map((preset) => (
              <article key={preset.id} className={`bt-preset-card${settings.method === preset.method ? ' is-active' : ''}`}>
                <button type="button" className="bt-preset-select" aria-pressed={settings.method === preset.method}
                  onClick={() => onChangeSettings({ method: preset.method })}>
                  <strong>{preset.title}</strong>
                  <span>{preset.reason}</span>
                </button>
                <button type="button" className="bt-preset-test" disabled={!analysis || studyRunning} onClick={() => onRunTest(preset.method)}>Test</button>
              </article>
            ))}
          </div>
          {advisorLoading && !advisor && <p className="bt-note">Matching presets to this pair…</p>}
          {leadLagNeeds1m && (
            <div className="bt-inline-alert" role="note">
              <span>Anchor Lead-Lag requires 1m candles.</span>
              {onSelectBar && (
                <button type="button" className="bt-banner-clear" onClick={() => onSelectBar('1m')}>Switch to 1m</button>
              )}
            </div>
          )}
        </>
      ) : (
        <>
          <div className="bt-method-grid" role="group" aria-label="Strategy method">
            {METHODS.map((method) => (
              <button key={method.id} type="button" className="bt-method-pill" aria-pressed={settings.method === method.id}
                onClick={() => {
                  onChangeSettings({ method: method.id })
                  if (method.id === 'lead_lag' && bar !== '1m' && onSelectBar) onSelectBar('1m')
                }}>
                <span>{method.label}</span>
                {method.id === 'lead_lag' && <small className="bt-method-badge">Requires 1m</small>}
              </button>
            ))}
          </div>

          {leadLagNeeds1m && (
            <div className="bt-inline-alert" role="note">
              <span>Anchor Lead-Lag requires 1m candles.</span>
              {onSelectBar && (
                <button type="button" className="bt-banner-clear" onClick={() => onSelectBar('1m')}>Switch to 1m</button>
              )}
            </div>
          )}

          <div className="bt-field-stack">
            {settings.method === 'zscore' && (
              <>
                <label className="bt-field">
                  <span>Regression</span>
                  <select value={settings.hedge_method} onChange={(event) => onChangeSettings({ hedge_method: event.target.value as LabHedgeMethod })}>
                    <option value="ratio">Direct Ratio</option>
                    <option value="ols">OLS Regression</option>
                    <option value="tls">Total Least Squares</option>
                    <option value="kalman">Kalman Filter</option>
                  </select>
                </label>
                <RangeField label="Lookback (bars)" valueText={`${settings.lookback}`} badge={barSpan(settings.lookback, bar)}
                  value={settings.lookback} min={24} max={720} step={12}
                  onChange={(lookback) => onChangeSettings({ lookback })} />
                <RangeField label="Entry (σ)" valueText={`${settings.entry.toFixed(1)}σ`} badge={`~${approxTailPct(settings.entry)} tail`}
                  value={settings.entry} min={0.5} max={4.5} step={0.1}
                  onChange={(entry) => onChangeSettings({
                    entry,
                    exit: settings.exit >= entry ? Math.max(0, Number((entry - 0.1).toFixed(1))) : settings.exit,
                  })} />
                <RangeField label="Exit (σ)" valueText={`${settings.exit.toFixed(1)}σ`} badge={`< ${settings.entry.toFixed(1)}σ`}
                  value={Math.min(settings.exit, exitMax)} min={0} max={exitMax} step={0.1}
                  onChange={(exit) => onChangeSettings({ exit })} />
              </>
            )}

            {settings.method === 'copula' && (
              <>
                <RangeField label="Lookback (bars)" valueText={`${settings.lookback}`} badge={barSpan(settings.lookback, bar)}
                  value={settings.lookback} min={24} max={720} step={12}
                  onChange={(lookback) => onChangeSettings({ lookback })} />
                <RangeField label="Tail Entry Prob" valueText={`${copulaEntryPct}%`}
                  value={settings.copula_probability} min={0.01} max={0.25} step={0.01}
                  onChange={(copula_probability) => onChangeSettings({
                    copula_probability,
                    copula_exit_band: Math.min(settings.copula_exit_band, Math.max(0.05, Number((0.49 - copula_probability).toFixed(2)))),
                  })} />
                <RangeField label="Neutral Exit Band" valueText={`${copulaBandPct}%`}
                  value={Math.min(settings.copula_exit_band, copulaExitMax)} min={0.05} max={copulaExitMax} step={0.01}
                  onChange={(copula_exit_band) => onChangeSettings({ copula_exit_band })} />
                <p className="bt-note">
                  Enter below {copulaEntryPct}% / above {100 - copulaEntryPct}%, exit between {50 - copulaBandPct}%–{50 + copulaBandPct}%.
                </p>
              </>
            )}

            {settings.method === 'trend' && (
              <>
                <div className="bt-field-row">
                  <NumberField label="Fast MA (bars)" hint={barSpan(settings.fast_window, bar)} value={settings.fast_window}
                    min={2} max={1000} onChange={(fast_window) => onChangeSettings({ fast_window })} />
                  <NumberField label="Slow MA (bars)" hint={barSpan(settings.slow_window, bar)} value={settings.slow_window}
                    min={3} max={10000} onChange={(slow_window) => onChangeSettings({ slow_window })} />
                </div>
                <NumberField label="Deadband" value={settings.trend_deadband} min={0} max={0.5} step={0.0005}
                  onChange={(trend_deadband) => onChangeSettings({ trend_deadband })} />
              </>
            )}

            {settings.method === 'lead_lag' && (
              <>
                <RangeField label="Lookback (bars)" valueText={`${settings.lookback}`} badge={barSpan(settings.lookback, bar)}
                  value={settings.lookback} min={24} max={720} step={12}
                  onChange={(lookback) => onChangeSettings({ lookback })} />
                <NumberField label="Benchmark Jump Threshold" value={settings.anchor_threshold} min={0.0001} max={0.5} step={0.0005}
                  onChange={(anchor_threshold) => onChangeSettings({ anchor_threshold })} />
                {analysis && !analysis.anchor && (
                  <p className="bt-warning" role="note">
                    No auto-detected benchmark covers this full window. Select a Benchmark in the top bar for Anchor Lead-Lag.
                  </p>
                )}
              </>
            )}

            <div className="bt-field">
              <span>Swap Size</span>
              <div className="bt-pill-row" role="group" aria-label="Swap size">
                {LAB_ROTATION_PCTS.map((pct) => (
                  <button key={pct} type="button" className="bt-pill" aria-pressed={settings.rotation_pct === pct}
                    onClick={() => onChangeSettings({ rotation_pct: pct })}>{pct}%</button>
                ))}
              </div>
            </div>

            <label className="bt-field">
              <span>Crash Stop</span>
              <select value={settings.crash_defense_mode} onChange={(event) => onChangeSettings({ crash_defense_mode: event.target.value as LabCrashDefenseMode })}>
                <option value="coins_only">Hold Pair</option>
                <option value="park_anchor">Park in Benchmark</option>
                <option value="park_usdt">Park in USDT</option>
              </select>
            </label>

            {settings.crash_defense_mode === 'park_anchor' && analysis && !analysis.anchor && (
              <p className="bt-warning" role="note">
                No auto-detected benchmark covers this full window. Select a Benchmark in the top bar or switch Crash Stop to Park in USDT.
              </p>
            )}

            {settings.crash_defense_mode !== 'coins_only' && (
              <RangeField label="Crash Drawdown Trigger" valueText={`${Math.round(settings.regime_break_drawdown * 100)}%`}
                value={settings.regime_break_drawdown} min={0.05} max={0.40} step={0.01}
                onChange={(regime_break_drawdown) => onChangeSettings({ regime_break_drawdown })} />
            )}

            <RangeField label="Minimum Hold (bars)" valueText={`${settings.minimum_hold}`} badge={barSpan(settings.minimum_hold, bar)}
              value={settings.minimum_hold} min={0} max={48} step={1}
              onChange={(minimum_hold) => onChangeSettings({ minimum_hold })} />
            <RangeField label="Cooldown (bars)" valueText={`${settings.cooldown}`} badge={barSpan(settings.cooldown, bar)}
              value={settings.cooldown} min={0} max={48} step={1}
              onChange={(cooldown) => onChangeSettings({ cooldown })} />

            <NumberField label="MA Band Period" hint={barSpan(bandLookback, bar)} value={bandLookback}
              min={2} max={10000} onChange={onChangeBandLookback} />

            <label className="bt-checkbox-row">
              <input type="checkbox" checked={settings.auto_tune} onChange={(event) => onChangeSettings({ auto_tune: event.target.checked })} />
              <span>Auto-tune on training folds</span>
              <small className="bt-inline-badge">Tests 0.8× / 1.0× / 1.2× on train split only</small>
            </label>

            <details className="bt-execution">
              <summary>Execution &amp; Fees</summary>
              <div className="bt-field-row">
                <NumberField label="Fee (bps)" value={settings.fee_bps} min={0.1} max={100} step={0.5}
                  onChange={(fee_bps) => onChangeSettings({ fee_bps })} />
                <NumberField label="Slippage (bps)" value={settings.slippage_bps} min={0.1} max={1000} step={0.5}
                  onChange={(slippage_bps) => onChangeSettings({ slippage_bps })} />
              </div>
            </details>
          </div>
        </>
      )}
    </section>

    <div className="bt-action-buttons">
      <button type="button" className="bt-btn-primary" disabled={!analysis || studyRunning || leadLagNeeds1m} onClick={() => onRunTest()}>
        {studyRunning ? 'Running Backtest…' : 'Test Strategy ($10,000)'}
      </button>
      <button type="button" className="bt-btn-secondary" disabled={!analysis || compareRunning} onClick={onCompareAll}>
        {compareRunning ? 'Comparing…' : 'Compare All Presets'}
      </button>
    </div>
  </aside>
}
