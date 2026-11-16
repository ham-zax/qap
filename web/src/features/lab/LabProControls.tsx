import { Alert } from '@/components/ui/alert'
import { AlertDescription } from '@/components/ui/alert'
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { RangeSliderField } from '@/components/watermelon/range-slider'
import { cn } from '@/lib/utils'
import {
  BAR_MINUTES,
  LAB_ROTATION_PCTS,
  type LabAnalysis,
  type LabBar,
  type LabCrashDefenseMode,
  type LabHedgeMethod,
  type LabSignalMethod,
  type LabStrategyFormSettings,
} from './labContract'

const METHODS: ReadonlyArray<{ id: LabSignalMethod; label: string }> = [
  { id: 'zscore', label: 'Z-Score' },
  { id: 'copula', label: 'Spread Copula' },
  { id: 'trend', label: 'Ratio Trend' },
  { id: 'lead_lag', label: 'Anchor Lead-Lag' },
]

function barSpan(bars: number, bar: LabBar): string {
  const minutes = bars * BAR_MINUTES[bar]
  if (!Number.isFinite(minutes) || minutes <= 0) return '0 bars'
  if (minutes < 60) return `${Math.round(minutes)} min`
  if (minutes < 1440) return `${(minutes / 60).toFixed(1)} h`
  return `${(minutes / 1440).toFixed(1)} days`
}

function approxTailPct(z: number): string {
  const t = 1 / (1 + 0.2316419 * Math.abs(z))
  const d = 0.3989423 * Math.exp((-z * z) / 2)
  const p = d * t * (0.3193815 + t * (-0.3565638 + t * (1.781478 + t * (-1.821256 + t * 1.330274))))
  const twoTail = Math.max(0.01, Math.min(99, 2 * p * 100))
  return twoTail >= 10 ? `${twoTail.toFixed(0)}%` : `${twoTail.toFixed(1)}%`
}

function NumberField({
  label,
  hint,
  value,
  min,
  max,
  step,
  onChange,
}: {
  label: string
  hint?: string
  value: number
  min: number
  max: number
  step?: number
  onChange: (value: number) => void
}) {
  return (
    <label className="flex flex-col gap-1.5 text-xs text-muted-foreground">
      <span className="flex items-baseline justify-between gap-2">
        <span className="font-medium text-foreground/90">{label}</span>
        {hint ? <small className="font-mono text-[11px] text-muted-foreground">{hint}</small> : null}
      </span>
      <Input
        type="number"
        className="h-8 bg-background font-mono text-xs tabular-nums"
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
  )
}

export function LabProControls({
  analysis,
  settings,
  bandLookback,
  bar,
  leadLagAlert,
  onChangeBandLookback,
  onSelectBar,
  onChangeSettings,
}: {
  analysis: LabAnalysis | null
  settings: LabStrategyFormSettings
  bandLookback: number
  bar: LabBar
  leadLagAlert: React.ReactNode
  onChangeBandLookback: (value: number) => void
  onSelectBar?: (bar: LabBar) => void
  onChangeSettings: (patch: Partial<LabStrategyFormSettings>) => void
}) {
  const exitMax = Math.max(0, Math.min(2.5, Number((settings.entry - 0.1).toFixed(1))))
  const copulaExitMax = Math.max(0.05, Math.min(0.35, Number((0.49 - settings.copula_probability).toFixed(2))))
  const copulaEntryPct = Math.round(settings.copula_probability * 100)
  const copulaBandPct = Math.round(settings.copula_exit_band * 100)

  return (
    <>
      <div className="grid grid-cols-2 gap-1.5" role="group" aria-label="Strategy method">
        {METHODS.map((method) => {
          const active = settings.method === method.id
          return (
            <Button
              key={method.id}
              type="button"
              size="sm"
              variant="ghost"
              aria-pressed={active}
              onClick={() => {
                onChangeSettings({ method: method.id })
                if (method.id === 'lead_lag' && bar !== '1m' && onSelectBar) onSelectBar('1m')
              }}
              className={cn(
                'h-8 justify-center gap-1 border px-2 text-xs',
                active
                  ? 'border-primary bg-primary/15 font-semibold text-foreground hover:bg-primary/20'
                  : 'border-border-strong bg-background text-foreground/80 hover:bg-muted/70 hover:text-foreground',
              )}
            >
              <span className="truncate">{method.label}</span>
              {method.id === 'lead_lag' && (
                <small
                  title="Requires 1m candles"
                  className="shrink-0 rounded bg-muted px-1 py-0.5 text-[9.5px] font-medium text-muted-foreground"
                >
                  1m
                </small>
              )}
            </Button>
          )
        })}
      </div>

      {leadLagAlert}

      <div className="grid gap-3">
        {settings.method === 'zscore' && (
          <>
            <label className="flex flex-col gap-1.5 text-xs text-muted-foreground">
              <span className="font-medium text-foreground/90">Regression</span>
              <select
                value={settings.hedge_method}
                onChange={(event) => onChangeSettings({ hedge_method: event.target.value as LabHedgeMethod })}
                className="h-8 rounded-md border border-border-strong bg-background px-2 text-xs text-foreground shadow-xs outline-none focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/40"
              >
                <option value="ratio">Direct Ratio</option>
                <option value="ols">OLS Regression</option>
                <option value="tls">Total Least Squares</option>
                <option value="kalman">Kalman Filter</option>
              </select>
            </label>
            <RangeSliderField
              label="Lookback (bars)"
              valueText={`${settings.lookback}`}
              badge={barSpan(settings.lookback, bar)}
              value={settings.lookback}
              min={24}
              max={720}
              step={12}
              onChange={(lookback) => onChangeSettings({ lookback })}
            />
            <RangeSliderField
              label="Entry (σ)"
              valueText={`${settings.entry.toFixed(1)}σ`}
              badge={`~${approxTailPct(settings.entry)} tail`}
              value={settings.entry}
              min={0.5}
              max={4.5}
              step={0.1}
              onChange={(entry) =>
                onChangeSettings({
                  entry,
                  exit: settings.exit >= entry ? Math.max(0, Number((entry - 0.1).toFixed(1))) : settings.exit,
                })
              }
            />
            <RangeSliderField
              label="Exit (σ)"
              valueText={`${settings.exit.toFixed(1)}σ`}
              badge={`< ${settings.entry.toFixed(1)}σ`}
              value={Math.min(settings.exit, exitMax)}
              min={0}
              max={exitMax}
              step={0.1}
              onChange={(exit) => onChangeSettings({ exit })}
            />
          </>
        )}

        {settings.method === 'copula' && (
          <>
            <RangeSliderField
              label="Lookback (bars)"
              valueText={`${settings.lookback}`}
              badge={barSpan(settings.lookback, bar)}
              value={settings.lookback}
              min={24}
              max={720}
              step={12}
              onChange={(lookback) => onChangeSettings({ lookback })}
            />
            <RangeSliderField
              label="Tail Entry Prob"
              valueText={`${copulaEntryPct}%`}
              value={settings.copula_probability}
              min={0.01}
              max={0.25}
              step={0.01}
              onChange={(copula_probability) =>
                onChangeSettings({
                  copula_probability,
                  copula_exit_band: Math.min(
                    settings.copula_exit_band,
                    Math.max(0.05, Number((0.49 - copula_probability).toFixed(2))),
                  ),
                })
              }
            />
            <RangeSliderField
              label="Neutral Exit Band"
              valueText={`${copulaBandPct}%`}
              value={Math.min(settings.copula_exit_band, copulaExitMax)}
              min={0.05}
              max={copulaExitMax}
              step={0.01}
              onChange={(copula_exit_band) => onChangeSettings({ copula_exit_band })}
            />
            <p className="m-0 text-[11px] text-muted-foreground">
              Enter below {copulaEntryPct}% / above {100 - copulaEntryPct}%, exit between {50 - copulaBandPct}%–
              {50 + copulaBandPct}%.
            </p>
          </>
        )}

        {settings.method === 'trend' && (
          <>
            <div className="grid grid-cols-2 gap-2">
              <NumberField
                label="Fast MA (bars)"
                hint={barSpan(settings.fast_window, bar)}
                value={settings.fast_window}
                min={2}
                max={1000}
                onChange={(fast_window) => onChangeSettings({ fast_window })}
              />
              <NumberField
                label="Slow MA (bars)"
                hint={barSpan(settings.slow_window, bar)}
                value={settings.slow_window}
                min={3}
                max={10000}
                onChange={(slow_window) => onChangeSettings({ slow_window })}
              />
            </div>
            <NumberField
              label="Deadband"
              value={settings.trend_deadband}
              min={0}
              max={0.5}
              step={0.0005}
              onChange={(trend_deadband) => onChangeSettings({ trend_deadband })}
            />
          </>
        )}

        {settings.method === 'lead_lag' && (
          <>
            <RangeSliderField
              label="Lookback (bars)"
              valueText={`${settings.lookback}`}
              badge={barSpan(settings.lookback, bar)}
              value={settings.lookback}
              min={24}
              max={720}
              step={12}
              onChange={(lookback) => onChangeSettings({ lookback })}
            />
            <NumberField
              label="Benchmark Jump Threshold"
              value={settings.anchor_threshold}
              min={0.0001}
              max={0.5}
              step={0.0005}
              onChange={(anchor_threshold) => onChangeSettings({ anchor_threshold })}
            />
            {analysis && !analysis.anchor && (
              <Alert className="border-warning/45 bg-warning/10 py-2 text-warning">
                <AlertDescription className="text-xs text-warning">
                  No auto-detected benchmark covers this full window. Select a Benchmark in the top bar for Anchor Lead-Lag.
                </AlertDescription>
              </Alert>
            )}
          </>
        )}

        <div className="space-y-1.5">
          <span className="block text-xs font-medium text-foreground/90">Swap Size</span>
          <div
            className="grid grid-cols-4 gap-0.5 rounded-lg border border-border bg-muted p-0.5"
            role="group"
            aria-label="Swap size"
          >
            {LAB_ROTATION_PCTS.map((pct) => {
              const active = settings.rotation_pct === pct
              return (
                <Button
                  key={pct}
                  type="button"
                  size="sm"
                  variant={active ? 'secondary' : 'ghost'}
                  aria-pressed={active}
                  onClick={() => onChangeSettings({ rotation_pct: pct })}
                  className={cn(
                    'h-7 rounded-md font-mono text-xs tabular-nums',
                    active
                      ? 'bg-background font-semibold text-foreground shadow-xs ring-1 ring-border-strong'
                      : 'text-muted-foreground hover:text-foreground',
                  )}
                >
                  {pct}%
                </Button>
              )
            })}
          </div>
        </div>

        <label className="flex flex-col gap-1.5 text-xs text-muted-foreground">
          <span className="font-medium text-foreground/90">Crash Stop</span>
          <select
            value={settings.crash_defense_mode}
            onChange={(event) =>
              onChangeSettings({ crash_defense_mode: event.target.value as LabCrashDefenseMode })
            }
            className="h-8 rounded-md border border-border-strong bg-background px-2 text-xs text-foreground shadow-xs outline-none focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/40"
          >
            <option value="coins_only">Hold Pair</option>
            <option value="park_anchor">Park in Benchmark</option>
            <option value="park_usdt">Park in USDT</option>
          </select>
        </label>

        {settings.crash_defense_mode === 'park_anchor' && analysis && !analysis.anchor && (
          <Alert className="border-warning/45 bg-warning/10 py-2 text-warning">
            <AlertDescription className="text-xs text-warning">
              No auto-detected benchmark covers this full window. Select a Benchmark in the top bar or switch Crash Stop to Park in USDT.
            </AlertDescription>
          </Alert>
        )}

        {settings.crash_defense_mode !== 'coins_only' && (
          <RangeSliderField
            label="Crash Drawdown Trigger"
            valueText={`${Math.round(settings.regime_break_drawdown * 100)}%`}
            value={settings.regime_break_drawdown}
            min={0.05}
            max={0.4}
            step={0.01}
            onChange={(regime_break_drawdown) => onChangeSettings({ regime_break_drawdown })}
          />
        )}

        <RangeSliderField
          label="Minimum Hold (bars)"
          valueText={`${settings.minimum_hold}`}
          badge={barSpan(settings.minimum_hold, bar)}
          value={settings.minimum_hold}
          min={0}
          max={48}
          step={1}
          onChange={(minimum_hold) => onChangeSettings({ minimum_hold })}
        />
        <RangeSliderField
          label="Cooldown (bars)"
          valueText={`${settings.cooldown}`}
          badge={barSpan(settings.cooldown, bar)}
          value={settings.cooldown}
          min={0}
          max={48}
          step={1}
          onChange={(cooldown) => onChangeSettings({ cooldown })}
        />

        <NumberField
          label="MA Band Period"
          hint={barSpan(bandLookback, bar)}
          value={bandLookback}
          min={2}
          max={10000}
          onChange={onChangeBandLookback}
        />

        <div className="flex items-center justify-between gap-2 rounded-lg border border-border bg-muted/30 px-2.5 py-2">
          <div className="min-w-0">
            <Label htmlFor="auto-tune-switch" className="cursor-pointer text-xs font-medium text-foreground">
              Auto-tune on training folds
            </Label>
            <p className="m-0 text-[10.5px] text-muted-foreground">
              Tests 0.8× / 1.0× / 1.2× on train split only
            </p>
          </div>
          <Switch
            id="auto-tune-switch"
            checked={settings.auto_tune}
            onCheckedChange={(checked) => onChangeSettings({ auto_tune: checked })}
          />
        </div>

        <Accordion type="single" collapsible>
          <AccordionItem value="execution-fees" className="border-b-0">
            <AccordionTrigger className="py-1.5 text-xs font-medium text-muted-foreground hover:text-foreground hover:no-underline">
              Execution &amp; Fees
            </AccordionTrigger>
            <AccordionContent className="pt-2 pb-1">
              <div className="grid grid-cols-2 gap-2">
                <NumberField
                  label="Fee (bps)"
                  value={settings.fee_bps}
                  min={0.1}
                  max={100}
                  step={0.5}
                  onChange={(fee_bps) => onChangeSettings({ fee_bps })}
                />
                <NumberField
                  label="Slippage (bps)"
                  value={settings.slippage_bps}
                  min={0.1}
                  max={1000}
                  step={0.5}
                  onChange={(slippage_bps) => onChangeSettings({ slippage_bps })}
                />
              </div>
            </AccordionContent>
          </AccordionItem>
        </Accordion>
      </div>
    </>
  )
}
