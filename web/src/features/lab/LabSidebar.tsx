import { LabAdvisorCard } from './LabAdvisorCard'
import { LabSavedRuns } from './LabSavedRuns'
import {
  LAB_ROTATION_PCTS,
  type LabCrashDefenseMode,
  type LabHedgeMethod,
  type LabSignalMethod,
  type LabStrategyFormSettings,
  type LabViewMode,
} from './labContract'
import type { LabAdvisor, LabAdvisorSuggestion, LabSavedSummary } from './labStudyApi'

interface LabSidebarProps {
  settings: LabStrategyFormSettings
  viewMode: LabViewMode
  dirty: boolean
  hasStudy: boolean
  studyRunning: boolean
  compareRunning: boolean
  canRun: boolean
  advisor: LabAdvisor | null
  advisorLoading: boolean
  savedStudies: readonly LabSavedSummary[]
  activeStudyId: string | null
  savedLoading: boolean
  onChange: (patch: Partial<LabStrategyFormSettings>) => void
  onRunTest: () => void
  onComparePresets: () => void
  onApplyPreset: (suggestion: LabAdvisorSuggestion) => void
  onSelectSaved: (studyId: string) => void
  onTogglePinSaved: (studyId: string, pinned: boolean) => void
}

const METHODS: ReadonlyArray<{ id: LabSignalMethod; label: string }> = [
  { id: 'zscore', label: 'Z-Score' },
  { id: 'copula', label: 'Spread Copula' },
  { id: 'trend', label: 'Ratio Trend' },
  { id: 'lead_lag', label: 'Anchor Lead-Lag' },
]

export function LabSidebar(props: LabSidebarProps) {
  const {
    settings,
    viewMode,
    dirty,
    studyRunning,
    compareRunning,
    canRun,
    onChange,
    onRunTest,
    onComparePresets,
  } = props

  const num = (raw: string, min: number, max: number, integer = false): number | null => {
    const parsed = Number(raw)
    if (!Number.isFinite(parsed) || parsed < min || parsed > max) return null
    if (integer && !Number.isInteger(parsed)) return null
    return parsed
  }

  return (
    <aside className="lab-sidebar" aria-label="Strategy workbench">
      <LabAdvisorCard
        advisor={props.advisor}
        loading={props.advisorLoading}
        viewMode={viewMode}
        disabled={!canRun || studyRunning}
        onApplyPreset={props.onApplyPreset}
      />

      <section className="lab-card" aria-label="Strategy rules">
        <div className="lab-card-header">
          <h2>Strategy</h2>
          {dirty && <span className="lab-dirty-badge">Settings changed</span>}
        </div>

        <div className="lab-pill-grid" role="group" aria-label="Strategy method">
          {METHODS.map((method) => (
            <button
              key={method.id}
              type="button"
              className="lab-pill"
              aria-pressed={settings.method === method.id}
              onClick={() => onChange({ method: method.id })}
            >
              {method.label}
            </button>
          ))}
        </div>

        <div className="lab-field-stack">
          {settings.method === 'zscore' && (
            <>
              <label>
                Hedge method
                <select
                  value={settings.hedge_method}
                  onChange={(e) => onChange({ hedge_method: e.target.value as LabHedgeMethod })}
                >
                  <option value="ratio">Direct Ratio</option>
                  <option value="ols">OLS Regression</option>
                  <option value="tls">Total Least Squares</option>
                  <option value="kalman">Kalman Filter</option>
                </select>
              </label>
              <label>
                Lookback bars
                <input
                  type="number"
                  min={20}
                  max={10000}
                  value={settings.lookback}
                  onChange={(e) => {
                    const v = num(e.target.value, 20, 10000, true)
                    if (v !== null) onChange({ lookback: v })
                  }}
                />
              </label>
              <div className="lab-field-row">
                <label>
                  Entry threshold
                  <input
                    type="number"
                    min={0.1}
                    max={10}
                    step={0.1}
                    value={settings.entry}
                    onChange={(e) => {
                      const v = num(e.target.value, 0.1, 10)
                      if (v !== null) onChange({ entry: v })
                    }}
                  />
                </label>
                <label>
                  Exit threshold
                  <input
                    type="number"
                    min={0}
                    max={5}
                    step={0.1}
                    value={settings.exit}
                    onChange={(e) => {
                      const v = num(e.target.value, 0, 5)
                      if (v !== null) onChange({ exit: v })
                    }}
                  />
                </label>
              </div>
            </>
          )}

          {settings.method === 'copula' && (
            <>
              <label>
                Lookback bars
                <input
                  type="number"
                  min={20}
                  max={10000}
                  value={settings.lookback}
                  onChange={(e) => {
                    const v = num(e.target.value, 20, 10000, true)
                    if (v !== null) onChange({ lookback: v })
                  }}
                />
              </label>
              <div className="lab-field-row">
                <label>
                  Tail probability
                  <input
                    type="number"
                    min={0.01}
                    max={0.45}
                    step={0.01}
                    value={settings.copula_probability}
                    onChange={(e) => {
                      const v = num(e.target.value, 0.01, 0.45)
                      if (v !== null) onChange({ copula_probability: v })
                    }}
                  />
                </label>
                <label>
                  Exit neutral band
                  <input
                    type="number"
                    min={0.01}
                    max={0.44}
                    step={0.01}
                    value={settings.copula_exit_band}
                    onChange={(e) => {
                      const v = num(e.target.value, 0.01, 0.44)
                      if (v !== null) onChange({ copula_exit_band: v })
                    }}
                  />
                </label>
              </div>
            </>
          )}

          {settings.method === 'trend' && (
            <>
              <div className="lab-field-row">
                <label>
                  Fast window
                  <input
                    type="number"
                    min={2}
                    max={1000}
                    value={settings.fast_window}
                    onChange={(e) => {
                      const v = num(e.target.value, 2, 1000, true)
                      if (v !== null) onChange({ fast_window: v })
                    }}
                  />
                </label>
                <label>
                  Slow window
                  <input
                    type="number"
                    min={3}
                    max={10000}
                    value={settings.slow_window}
                    onChange={(e) => {
                      const v = num(e.target.value, 3, 10000, true)
                      if (v !== null) onChange({ slow_window: v })
                    }}
                  />
                </label>
              </div>
              <label>
                Trend deadband
                <input
                  type="number"
                  min={0}
                  max={0.5}
                  step={0.0005}
                  value={settings.trend_deadband}
                  onChange={(e) => {
                    const v = num(e.target.value, 0, 0.5)
                    if (v !== null) onChange({ trend_deadband: v })
                  }}
                />
              </label>
            </>
          )}

          {settings.method === 'lead_lag' && (
            <>
              <label>
                Lookback bars
                <input
                  type="number"
                  min={20}
                  max={10000}
                  value={settings.lookback}
                  onChange={(e) => {
                    const v = num(e.target.value, 20, 10000, true)
                    if (v !== null) onChange({ lookback: v })
                  }}
                />
              </label>
              <label>
                Anchor threshold
                <input
                  type="number"
                  min={0.0001}
                  max={0.5}
                  step={0.0005}
                  value={settings.anchor_threshold}
                  onChange={(e) => {
                    const v = num(e.target.value, 0.0001, 0.5)
                    if (v !== null) onChange({ anchor_threshold: v })
                  }}
                />
              </label>
            </>
          )}

          <div>
            <span className="lab-field-label">Rotation size</span>
            <div className="lab-pill-row" role="group" aria-label="Rotation size">
              {LAB_ROTATION_PCTS.map((pct) => (
                <button
                  key={pct}
                  type="button"
                  className="lab-pill"
                  aria-pressed={settings.rotation_pct === pct}
                  onClick={() => onChange({ rotation_pct: pct })}
                >
                  {pct}%
                </button>
              ))}
            </div>
          </div>

          <label>
            Crash defense
            <select
              value={settings.crash_defense_mode}
              onChange={(e) => onChange({ crash_defense_mode: e.target.value as LabCrashDefenseMode })}
            >
              <option value="coins_only">Stay in coins</option>
              <option value="park_anchor">Park in Anchor</option>
              <option value="park_usdt">Park in USDT</option>
            </select>
          </label>

          <label className="lab-checkbox-row">
            <input
              type="checkbox"
              checked={settings.auto_tune}
              onChange={(e) => onChange({ auto_tune: e.target.checked })}
            />
            Auto-tune thresholds on training folds
          </label>

          <details className="lab-advanced-exec" open={viewMode === 'advanced'}>
            <summary>Advanced execution</summary>
            <div className="lab-field-row">
              <label>
                Minimum hold
                <input
                  type="number"
                  min={0}
                  max={10000}
                  value={settings.minimum_hold}
                  onChange={(e) => {
                    const v = num(e.target.value, 0, 10000, true)
                    if (v !== null) onChange({ minimum_hold: v })
                  }}
                />
              </label>
              <label>
                Cooldown
                <input
                  type="number"
                  min={0}
                  max={10000}
                  value={settings.cooldown}
                  onChange={(e) => {
                    const v = num(e.target.value, 0, 10000, true)
                    if (v !== null) onChange({ cooldown: v })
                  }}
                />
              </label>
            </div>
            <div className="lab-field-row">
              <label>
                Fee (bps)
                <input
                  type="number"
                  min={0.1}
                  max={100}
                  step={0.5}
                  value={settings.fee_bps}
                  onChange={(e) => {
                    const v = num(e.target.value, 0.1, 100)
                    if (v !== null) onChange({ fee_bps: v })
                  }}
                />
              </label>
              <label>
                Slippage (bps)
                <input
                  type="number"
                  min={0.1}
                  max={1000}
                  step={0.5}
                  value={settings.slippage_bps}
                  onChange={(e) => {
                    const v = num(e.target.value, 0.1, 1000)
                    if (v !== null) onChange({ slippage_bps: v })
                  }}
                />
              </label>
            </div>
          </details>
        </div>

        <div className="lab-sidebar-actions">
          <button
            type="button"
            className="lab-primary"
            disabled={!canRun || studyRunning}
            onClick={onRunTest}
          >
            {studyRunning ? 'Testing…' : 'Apply & Run Test'}
          </button>
          <button
            type="button"
            disabled={!canRun || compareRunning}
            onClick={onComparePresets}
          >
            {compareRunning ? 'Comparing presets…' : 'Compare All Presets'}
          </button>
        </div>
        <p className="lab-note">Spot inventory only. No leverage or live-capital orders.</p>
      </section>

      <LabSavedRuns
        studies={props.savedStudies}
        activeStudyId={props.activeStudyId}
        loading={props.savedLoading}
        onSelect={props.onSelectSaved}
        onTogglePin={props.onTogglePinSaved}
      />
    </aside>
  )
}
