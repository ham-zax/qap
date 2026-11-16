import { LabActionPanel } from './LabActionPanel'
import { LabBottomTabs } from './LabBottomTabs'
import { LabHeroCharts } from './LabHeroCharts'
import { LabTickerBar } from './LabTickerBar'
import { DEFAULT_BAND_LOOKBACK } from './labContract'
import { useLab } from './useLab'
import './lab.css'
import './LabPanels.css'
import './LabTerminal.css'
import './LabControls.css'

export function LabDashboard() {
  const lab = useLab()
  const { request, analysis, progress, error, study, studyRestored, studyError, studyRunning, viewMode } = lab

  if (!request) {
    return (
      <div className="bt-terminal lab">
        {error ? (
          <div className="bt-chart-state" role="alert">
            <p>{error}</p>
            <button type="button" className="bt-btn-secondary" onClick={lab.retry}>Retry</button>
          </div>
        ) : (
          <div className="bt-chart-state" role="status">
            <p>{progress ? `${progress.stage} (${progress.completed}/${progress.total})` : 'Loading Binance markets…'}</p>
            <progress max={Math.max(1, progress?.total ?? 1)} value={progress?.completed ?? 0} aria-label="Directory load progress" />
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="bt-terminal lab">
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
        <p className="lab-warning-banner" role="note">
          Listing identity is unconfirmed in CoinGecko registry. Price ratio charts load normally; strategy verdicts stay blocked until confirmed.
        </p>
      )}
      {lab.compareError && <p className="lab-warning-banner" role="alert">{lab.compareError}</p>}

      <div className="bt-hero-grid">
        <LabHeroCharts
          analysis={analysis}
          study={study}
          progress={progress}
          error={error}
          viewMode={viewMode}
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
