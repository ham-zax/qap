import { Alert, AlertDescription } from '@/components/ui/alert'
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
  LAB_ROTATION_PCTS,
  type LabAnalysis,
  type LabBar,
  type LabCrashDefenseMode,
  type LabStrategyFormSettings,
} from './labContract'
import {
  STRATEGY_METHODS,
  STRATEGY_REGISTRY,
  barSpan,
  type StrategyFieldSpec,
  type StrategyNumberField,
} from './strategyRegistry'

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

function renderNumberField(
  field: StrategyNumberField,
  settings: LabStrategyFormSettings,
  bar: LabBar,
  onChangeSettings: (patch: Partial<LabStrategyFormSettings>) => void,
) {
  return (
    <NumberField
      key={field.id}
      label={field.label}
      hint={field.hint ? field.hint(bar, settings) : undefined}
      value={field.getValue(settings)}
      min={field.min}
      max={field.max}
      step={field.step}
      onChange={(value) => onChangeSettings(field.patch(value))}
    />
  )
}

function renderStrategyField(
  field: StrategyFieldSpec,
  settings: LabStrategyFormSettings,
  bar: LabBar,
  onChangeSettings: (patch: Partial<LabStrategyFormSettings>) => void,
) {
  if (field.kind === 'select') {
    return (
      <label key={field.id} className="flex flex-col gap-1.5 text-xs text-muted-foreground">
        <span className="font-medium text-foreground/90">{field.label}</span>
        <select
          value={field.getValue(settings)}
          onChange={(event) => onChangeSettings(field.patch(event.target.value))}
          className="h-8 rounded-md border border-border-strong bg-background px-2 text-xs text-foreground shadow-xs outline-none focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/40"
        >
          {field.options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </label>
    )
  }
  if (field.kind === 'slider') {
    const max = typeof field.max === 'function' ? field.max(settings) : field.max
    return (
      <RangeSliderField
        key={field.id}
        label={field.label}
        valueText={field.valueText(settings)}
        badge={field.badge ? field.badge(settings, bar) : undefined}
        value={field.getValue(settings)}
        min={field.min}
        max={max}
        step={field.step}
        onChange={(value) => onChangeSettings(field.patch(value, settings))}
      />
    )
  }
  if (field.kind === 'number') {
    return renderNumberField(field, settings, bar, onChangeSettings)
  }
  if (field.kind === 'numberPair') {
    return (
      <div key={field.id} className="grid grid-cols-2 gap-2">
        {field.fields.map((child) => renderNumberField(child, settings, bar, onChangeSettings))}
      </div>
    )
  }
  return (
    <p key={field.id} className="m-0 text-[11px] text-muted-foreground">
      {field.text(settings)}
    </p>
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
  const activeStrategy = STRATEGY_REGISTRY[settings.method]
  const anchorWarning = activeStrategy.requiresAnchorMessage?.(analysis) ?? null

  return (
    <>
      <div className="grid grid-cols-2 gap-1.5" role="group" aria-label="Strategy method">
        {STRATEGY_METHODS.map((method) => {
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
                if (method.requires1m && bar !== '1m' && onSelectBar) onSelectBar('1m')
              }}
              className={cn(
                'h-8 justify-center gap-1 border px-2 text-xs',
                active
                  ? 'border-primary bg-primary/15 font-semibold text-foreground hover:bg-primary/20'
                  : 'border-border-strong bg-background text-foreground/80 hover:bg-muted/70 hover:text-foreground',
              )}
            >
              <span className="truncate">{method.buttonLabel}</span>
              {method.badge && (
                <small
                  title={method.badgeTitle}
                  className="shrink-0 rounded bg-muted px-1 py-0.5 text-[9.5px] font-medium text-muted-foreground"
                >
                  {method.badge}
                </small>
              )}
            </Button>
          )
        })}
      </div>

      {leadLagAlert}

      <div className="grid gap-3">
        {activeStrategy.fields.map((field) => renderStrategyField(field, settings, bar, onChangeSettings))}

        {anchorWarning && (
          <Alert className="border-warning/45 bg-warning/10 py-2 text-warning">
            <AlertDescription className="text-xs text-warning">{anchorWarning}</AlertDescription>
          </Alert>
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
