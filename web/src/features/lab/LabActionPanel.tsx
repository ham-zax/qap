import { Play, Sparkles, X } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { DashboardCard } from '@/components/watermelon/dashboard-card'
import { LabStrategyControls } from './LabStrategyControls'
import { LabVerdictSection } from './LabVerdictSection'
import type {
  LabAnalysis,
  LabBar,
  LabSignalMethod,
  LabStrategyFormSettings,
  LabViewMode,
} from './labContract'
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
  const dismissSaved = onDismissSavedBanner ?? onClearStudy
  const leadLagNeeds1m = settings.method === 'lead_lag' && bar !== '1m'

  return (
    <aside className="xl:sticky xl:top-3" aria-label="Strategy workbench">
      <DashboardCard className="flex flex-col gap-3.5 p-3.5">
        {(savedBanner || studyRestored) && (
          <div
            className="flex items-start justify-between gap-2 rounded-lg border border-border-strong bg-muted/60 p-2.5 text-xs"
            role="status"
          >
            <span className="min-w-0 flex-1 text-foreground">
              Viewing Saved Run: {savedBanner?.label ?? 'Restored'}
            </span>
            <div className="flex shrink-0 items-center gap-1">
              {onEditSettings && (
                <Button type="button" variant="outline" size="sm" onClick={onEditSettings} className="h-6 px-2 text-[11px]">
                  Edit Settings
                </Button>
              )}
              <Button type="button" variant="ghost" size="sm" onClick={dismissSaved} className="h-6 px-2 text-[11px]">
                <X className="size-3" aria-hidden="true" />
                Clear
              </Button>
            </div>
          </div>
        )}

        <LabVerdictSection
          analysis={analysis}
          settings={settings}
          study={study}
          studyRunning={studyRunning}
          studyError={studyError}
        />

        <Separator />

        <LabStrategyControls
          analysis={analysis}
          settings={settings}
          viewMode={viewMode}
          dirty={dirty}
          studyRunning={studyRunning}
          advisor={advisor}
          advisorLoading={advisorLoading}
          bandLookback={bandLookback}
          bar={bar}
          leadLagNeeds1m={leadLagNeeds1m}
          onChangeBandLookback={onChangeBandLookback}
          onSelectBar={onSelectBar}
          onChangeSettings={onChangeSettings}
          onApplyPreset={onApplyPreset}
          onRunTest={onRunTest}
        />

        <div className="grid gap-2 pt-1">
          <Button
            type="button"
            disabled={!analysis || studyRunning || leadLagNeeds1m}
            onClick={() => onRunTest()}
            className="h-10 w-full font-semibold"
          >
            <Play className="size-3.5" aria-hidden="true" />
            {studyRunning ? 'Running Backtest…' : 'Test Strategy ($10,000)'}
          </Button>
          <Button
            type="button"
            variant="outline"
            disabled={!analysis || compareRunning}
            onClick={onCompareAll}
            className="h-9 w-full font-medium"
          >
            <Sparkles className="size-3.5" aria-hidden="true" />
            {compareRunning ? 'Comparing…' : 'Compare All Presets'}
          </Button>
        </div>
      </DashboardCard>
    </aside>
  )
}
