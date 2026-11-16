import { AlertTriangle } from 'lucide-react'

import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { LabProControls } from './LabProControls'
import {
  fromBackendLabSettings,
  type LabAnalysis,
  type LabBar,
  type LabSignalMethod,
  type LabStrategyFormSettings,
  type LabViewMode,
} from './labContract'
import type { LabAdvisor, LabAdvisorSuggestion } from './labStudyApi'

const FALLBACK_PRESETS: ReadonlyArray<{ id: string; title: string; method: LabSignalMethod; reason: string }> = [
  {
    id: 'fallback-zscore',
    title: 'Mean Reversion · Buy Dip Coin',
    method: 'zscore',
    reason: 'Buys the coin that has fallen furthest below its usual ratio, then exits as it reverts.',
  },
  {
    id: 'fallback-copula',
    title: 'Tail Mispricing · Spread Copula',
    method: 'copula',
    reason: 'Trades only rare joint tail moves, where one coin is mispriced against the other.',
  },
  {
    id: 'fallback-trend',
    title: 'Trend Rotation · Ride Stronger Coin',
    method: 'trend',
    reason: 'Holds the coin with the stronger moving-average trend until that trend fades.',
  },
]

export function LabStrategyControls({
  analysis,
  settings,
  viewMode,
  dirty,
  studyRunning,
  advisor,
  advisorLoading,
  bandLookback,
  bar,
  leadLagNeeds1m,
  onChangeBandLookback,
  onSelectBar,
  onChangeSettings,
  onApplyPreset,
  onRunTest,
}: {
  analysis: LabAnalysis | null
  settings: LabStrategyFormSettings
  viewMode: LabViewMode
  dirty: boolean
  studyRunning: boolean
  advisor: LabAdvisor | null
  advisorLoading: boolean
  bandLookback: number
  bar: LabBar
  leadLagNeeds1m: boolean
  onChangeBandLookback: (value: number) => void
  onSelectBar?: (bar: LabBar) => void
  onChangeSettings: (patch: Partial<LabStrategyFormSettings>) => void
  onApplyPreset: (suggestion: LabAdvisorSuggestion) => void
  onRunTest: (method?: LabSignalMethod) => void
}) {
  const activePreset =
    advisor?.suggestions.find(
      (item) => JSON.stringify(fromBackendLabSettings(item.settings)) === JSON.stringify(settings),
    )?.preset_id ?? null

  const leadLagAlert = leadLagNeeds1m ? (
    <div
      className="flex items-center justify-between gap-2 rounded-lg border border-warning/50 bg-warning/10 px-2.5 py-2 text-xs text-warning"
      role="note"
    >
      <span>Anchor Lead-Lag requires 1m candles.</span>
      {onSelectBar && (
        <Button type="button" variant="outline" size="sm" onClick={() => onSelectBar('1m')} className="h-6 px-2 text-[11px]">
          Switch to 1m
        </Button>
      )}
    </div>
  ) : null

  return (
    <section className="space-y-3" aria-label="Strategy selection">
      <div className="flex items-center justify-between gap-2">
        <h2 className="m-0 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          {viewMode === 'simple' ? 'Choose Strategy' : 'Strategy Controls'}
        </h2>
        {dirty && (
          <Badge variant="outline" className="border-warning/45 bg-warning/10 text-warning">
            Unsaved changes
          </Badge>
        )}
      </div>

      {viewMode === 'simple' ? (
        <>
          {bar === '15m' && advisor?.bar_warning && (
            <Alert className="border-warning/45 bg-warning/10 py-2 text-warning">
              <AlertTriangle className="size-3.5" aria-hidden="true" />
              <AlertDescription className="text-xs text-warning">{advisor.bar_warning}</AlertDescription>
            </Alert>
          )}
          <div className="grid gap-2">
            {advisor
              ? advisor.suggestions.map((suggestion) => {
                  const active = activePreset === suggestion.preset_id
                  return (
                    <article
                      key={suggestion.preset_id}
                      className={cn(
                        'flex items-stretch overflow-hidden rounded-lg border bg-background transition-colors',
                        active ? 'border-primary ring-1 ring-primary/30' : 'border-border hover:border-border-strong',
                      )}
                    >
                      <button
                        type="button"
                        className="grid flex-1 gap-1 bg-transparent p-2.5 text-left transition-colors hover:bg-muted/60"
                        aria-pressed={active}
                        onClick={() => onChangeSettings(fromBackendLabSettings(suggestion.settings))}
                      >
                        <strong className="text-xs font-semibold leading-snug text-foreground">
                          {suggestion.title}
                        </strong>
                        <span className="text-[11px] leading-relaxed text-muted-foreground">
                          {suggestion.simple_reason}
                        </span>
                      </button>
                      <button
                        type="button"
                        disabled={!analysis || studyRunning}
                        onClick={() => onApplyPreset(suggestion)}
                        className="border-l border-border bg-muted/60 px-3 text-xs font-semibold text-foreground transition-colors hover:bg-muted disabled:opacity-50"
                      >
                        Test
                      </button>
                    </article>
                  )
                })
              : FALLBACK_PRESETS.map((preset) => {
                  const active = settings.method === preset.method
                  return (
                    <article
                      key={preset.id}
                      className={cn(
                        'flex items-stretch overflow-hidden rounded-lg border bg-background transition-colors',
                        active ? 'border-primary ring-1 ring-primary/30' : 'border-border hover:border-border-strong',
                      )}
                    >
                      <button
                        type="button"
                        className="grid flex-1 gap-1 bg-transparent p-2.5 text-left transition-colors hover:bg-muted/60"
                        aria-pressed={active}
                        onClick={() => onChangeSettings({ method: preset.method })}
                      >
                        <strong className="text-xs font-semibold leading-snug text-foreground">
                          {preset.title}
                        </strong>
                        <span className="text-[11px] leading-relaxed text-muted-foreground">
                          {preset.reason}
                        </span>
                      </button>
                      <button
                        type="button"
                        disabled={!analysis || studyRunning}
                        onClick={() => onRunTest(preset.method)}
                        className="border-l border-border bg-muted/60 px-3 text-xs font-semibold text-foreground transition-colors hover:bg-muted disabled:opacity-50"
                      >
                        Test
                      </button>
                    </article>
                  )
                })}
          </div>
          {advisorLoading && !advisor && (
            <p className="m-0 text-xs text-muted-foreground">Matching presets to this pair…</p>
          )}
          {leadLagAlert}
        </>
      ) : (
        <LabProControls
          analysis={analysis}
          settings={settings}
          bandLookback={bandLookback}
          bar={bar}
          leadLagAlert={leadLagAlert}
          onChangeBandLookback={onChangeBandLookback}
          onSelectBar={onSelectBar}
          onChangeSettings={onChangeSettings}
        />
      )}
    </section>
  )
}
