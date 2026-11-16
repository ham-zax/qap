import { AlertCircle, AlertTriangle, RotateCcw } from 'lucide-react'

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Skeleton } from '@/components/ui/skeleton'
import { LabActionPanel } from './LabActionPanel'
import { LabBottomTabs } from './LabBottomTabs'
import { LabHeroCharts } from './LabHeroCharts'
import { LabTickerBar } from './LabTickerBar'
import { DEFAULT_BAND_LOOKBACK, type LabDays } from './labContract'
import { useLab } from './useLab'

function nextHistoryWindow(days: LabDays): LabDays | null {
  if (days === 30) return 90
  if (days === 90) return 180
  if (days === 180) return 365
  return null
}

export function LabDashboard() {
  const lab = useLab()
  const { request, analysis, progress, error, study, studyRestored, studyError, studyRunning, viewMode } = lab

  if (!request) {
    const pct = progress ? Math.round((progress.completed / Math.max(1, progress.total)) * 100) : 15
    return (
      <div className="lab space-y-4">
        {error ? (
          <Card className="shadow-primary p-6">
            <Alert variant="destructive">
              <AlertCircle className="size-4" aria-hidden="true" />
              <AlertTitle>Markets unavailable</AlertTitle>
              <AlertDescription className="mt-1 space-y-3">
                <p className="m-0">{error}</p>
                <Button type="button" variant="outline" size="sm" onClick={lab.retry} className="gap-1.5">
                  <RotateCcw className="size-3.5" aria-hidden="true" />
                  Retry
                </Button>
              </AlertDescription>
            </Alert>
          </Card>
        ) : (
          <Card className="shadow-primary p-6" role="status">
            <CardContent className="space-y-4 px-0">
              <p className="m-0 text-sm text-muted-foreground">
                {progress ? `${progress.stage} (${progress.completed}/${progress.total})` : 'Loading Binance markets…'}
              </p>
              <Progress value={pct} aria-label="Directory load progress" className="max-w-md" />
              <Skeleton className="h-72 w-full rounded-xl" />
            </CardContent>
          </Card>
        )}
      </div>
    )
  }

  return (
    <div className="lab space-y-4">
      <LabTickerBar
        request={request}
        coins={lab.coins}
        analysis={analysis}
        viewMode={viewMode}
        syncing={Boolean(progress)}
        onChangeRequest={lab.change}
        onChangeViewMode={lab.setViewMode}
        onRefreshData={lab.refreshPairData}
      />

      {analysis && !analysis.identity_confirmed && (
        <Alert className="border-warning/45 bg-warning/10 text-warning" role="note">
          <AlertTriangle className="size-4" aria-hidden="true" />
          <AlertDescription className="text-xs text-warning">
            Listing identity is unconfirmed in CoinGecko registry. Price ratio charts load normally; strategy verdicts stay blocked until confirmed.
          </AlertDescription>
        </Alert>
      )}

      {lab.compareError && (
        <Alert variant="destructive" role="alert">
          <AlertCircle className="size-4" aria-hidden="true" />
          <AlertDescription className="text-xs">{lab.compareError}</AlertDescription>
        </Alert>
      )}

      <div className="grid items-start gap-4 xl:grid-cols-[minmax(0,1fr)_356px]">
        <LabHeroCharts
          analysis={analysis}
          study={study}
          progress={progress}
          error={error}
          viewMode={viewMode}
          currentDays={request.days}
          onExpandWindow={() => {
            const next = nextHistoryWindow(request.days)
            if (next) lab.change({ days: next })
          }}
          onRetry={lab.retry}
        />

        <LabActionPanel
          analysis={analysis}
          settings={lab.strategySettings}
          viewMode={viewMode}
          dirty={lab.settingsDirty}
          study={study}
          studyRestored={studyRestored}
          studyRunning={studyRunning}
          studyError={studyError}
          compareRunning={lab.compareRunning}
          advisor={lab.advisor}
          advisorLoading={lab.advisorLoading}
          savedBanner={lab.loadedSavedBanner}
          bandLookback={request.band_lookback}
          bar={request.bar}
          onChangeBandLookback={(value) => lab.change({ band_lookback: value })}
          onSelectBar={(nextBar) => lab.change({ bar: nextBar, band_lookback: DEFAULT_BAND_LOOKBACK[nextBar] })}
          onDismissSavedBanner={lab.clearStudy}
          onEditSettings={() => lab.setViewMode('advanced')}
          onChangeSettings={lab.updateStrategySettings}
          onApplyPreset={lab.applyAdvisorPreset}
          onRunTest={lab.testStrategy}
          onCompareAll={lab.comparePresets}
          onClearStudy={lab.clearStudy}
        />
      </div>

      <LabBottomTabs
        analysis={analysis}
        study={study}
        viewMode={viewMode}
        compareResult={lab.compareResult}
        savedStudies={lab.savedStudies}
        activeStudyId={study?.study_id ?? null}
        savedLoading={lab.savedLoading}
        paperSession={lab.paperSession}
        paperBusy={lab.paperBusy}
        paperError={lab.paperError}
        onOpenStudy={lab.openSavedStudy}
        onTogglePinStudy={lab.togglePinStudy}
        onClearCompare={lab.clearCompare}
        onStartPaper={lab.startPaperSession}
        onStepPaper={() => lab.stepPaperSession(3.0)}
        onStopPaper={lab.stopPaperSession}
      />
    </div>
  )
}
