import { useState } from 'react'
import { CoinPicker } from './CoinPicker'
import { LabAnswer } from './LabAnswer'
import { LabCharts } from './LabCharts'
import { LabCompareTable } from './LabCompareTable'
import { LabEvidence } from './LabEvidence'
import { LabLivePaperPanel } from './LabLivePaperPanel'
import { LabScorecard } from './LabScorecard'
import { LabSidebar } from './LabSidebar'
import { LabTradeDrawer } from './LabTradeDrawer'
import { DEFAULT_BAND_LOOKBACK, LAB_BARS, LAB_DAYS, type LabBar, type LabDays } from './labContract'
import { useLab } from './useLab'
import './lab.css'
import './LabPanels.css'

function SwapIcon() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M7 4 3 8l4 4" /><path d="M3 8h14" /><path d="m17 20 4-4-4-4" /><path d="M21 16H7" />
  </svg>
}

export function LabDashboard() {
  const lab = useLab()
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false)
  const { request, analysis, progress, error, study, studyRestored, studyError, studyRunning, viewMode } = lab

  return <div className="lab">
    <header className="lab-heading">
      <div>
        <h1>Pair Rotation Lab</h1>
        <p>Would swapping between two coins have earned more than just holding both? Check it on past prices, after fees.</p>
      </div>
      <div className="lab-heading-controls">
        <button
          type="button"
          className="lab-drawer-toggle"
          aria-expanded={mobileSidebarOpen}
          onClick={() => setMobileSidebarOpen((open) => !open)}
        >
          {mobileSidebarOpen ? 'Hide strategy' : 'Strategy workbench'}
        </button>
        <div className="lab-segmented" role="group" aria-label="View mode">
          <button type="button" aria-pressed={viewMode === 'simple'} onClick={() => lab.setViewMode('simple')}>
            Simple
          </button>
          <button type="button" aria-pressed={viewMode === 'advanced'} onClick={() => lab.setViewMode('advanced')}>
            Advanced
          </button>
        </div>
        <span className="lab-status">{study ? 'Tested on past prices' : 'Not tested yet'}</span>
      </div>
    </header>

    {request && <section className="lab-toolbar" aria-label="Pair selection">
      <CoinPicker label="Coin A" value={request.coin_a} coins={lab.coins} excluded={request.coin_b} onChange={(id) => lab.change({ coin_a: id })} />
      <button type="button" className="lab-swap" aria-label="Swap coins" onClick={() => lab.change({ coin_a: request.coin_b, coin_b: request.coin_a })}><SwapIcon /></button>
      <CoinPicker label="Coin B" value={request.coin_b} coins={lab.coins} excluded={request.coin_a} onChange={(id) => lab.change({ coin_b: id })} />
      <label>Compare with<select value={request.anchor ?? ''} onChange={(event) => lab.change({ anchor: event.target.value || null })}>
        <option value="">Pick for me</option>
        {[...new Set([...lab.coins.filter((coin) => ['BTC', 'ETH', 'BNB', 'SOL'].includes(coin.code)).map((coin) => coin.id), ...(request.anchor ? [request.anchor] : [])])].map((id) => <option key={id} value={id}>{id.replace('binance:', '')}</option>)}
      </select></label>
      <label>Candle size<select value={request.bar} onChange={(event) => { const bar = event.target.value as LabBar; lab.change({ bar, band_lookback: DEFAULT_BAND_LOOKBACK[bar] }) }}>
        {LAB_BARS.map((bar) => <option key={bar}>{bar}</option>)}
      </select></label>
      <label>History<select value={request.days} onChange={(event) => lab.change({ days: Number(event.target.value) as LabDays })}>
        {LAB_DAYS.map((days) => <option key={days} value={days}>{days} days</option>)}
      </select></label>
      <label className="lab-lookback">Usual level over<input type="number" min={2} max={10000} value={request.band_lookback} aria-describedby="lab-lookback-hint" onChange={(event) => {
        const value = Number(event.target.value); if (Number.isInteger(value) && value >= 2 && value <= 10000) lab.change({ band_lookback: value })
      }} /></label>
      <p className="lab-venue"><span>Binance spot holdings only. No leverage or live orders.</span><span id="lab-lookback-hint">Usual level is the average ratio over this many candles. Settings save on this browser.</span></p>
    </section>}

    {request && <div className="lab-cockpit">
      <div className={mobileSidebarOpen ? undefined : 'lab-sidebar-collapsed'}>
        <LabSidebar
          settings={lab.strategySettings}
          viewMode={viewMode}
          dirty={lab.settingsDirty}
          hasStudy={Boolean(study)}
          studyRunning={studyRunning}
          compareRunning={lab.compareRunning}
          canRun={Boolean(analysis)}
          advisor={lab.advisor}
          advisorLoading={lab.advisorLoading}
          savedStudies={lab.savedStudies}
          activeStudyId={study?.study_id ?? null}
          savedLoading={lab.savedLoading}
          onChange={lab.updateStrategySettings}
          onRunTest={lab.testStrategy}
          onComparePresets={lab.comparePresets}
          onApplyPreset={lab.applyAdvisorPreset}
          onSelectSaved={lab.openSavedStudy}
          onTogglePinSaved={lab.togglePinStudy}
        />
      </div>

      <div className="lab-center-col">
        <div className="lab-answer-region" aria-live="polite" aria-busy={Boolean(progress) || studyRunning}>
          {error ? <div className="lab-answer"><h2>Analysis unavailable</h2><p role="alert">{error}</p><button onClick={lab.retry}>Retry analysis</button></div>
            : progress ? <div className="lab-answer"><h2>Loading prices</h2><p>{progress.stage}, {progress.completed} of {progress.total}</p><progress max={Math.max(1, progress.total)} value={progress.completed} /></div>
            : analysis ? <>
              {analysis.demo && <p className="lab-caution">Sample data for design review. These are not market observations.</p>}
              {!analysis.identity_confirmed && <p className="lab-caution">Coin identity is unresolved. Venue-local charts remain available. Economic calls stay blocked.</p>}
              {lab.compareError && <p className="lab-warning-banner" role="alert">{lab.compareError}</p>}
              {lab.compareResult && (
                <LabCompareTable
                  compare={lab.compareResult}
                  onOpenStudy={lab.openSavedStudy}
                  onClose={lab.clearCompare}
                />
              )}
              {study ? <>
                <div className="lab-study-bar">
                  <p className="lab-note">Study from {new Date(study.created_at).toLocaleString()}</p>
                  <button type="button" onClick={lab.clearStudy}>Clear result</button>
                </div>
                <LabAnswer result={study.result} progress={null} error={null} onRetry={lab.testStrategy} saved={studyRestored} />
              </>
                : <div className="lab-answer">
                  {studyRunning ? <><h2>Testing on past prices</h2><p>Replaying every swap with fees, then checking the result on periods the test did not tune on. This can take a minute.</p><progress aria-label="Strategy test progress" /></>
                    : studyError ? <><h2>Test unavailable</h2><p role="alert">{studyError}</p><button onClick={lab.testStrategy}>Retry test</button></>
                    : <div className="lab-idle"><div><h2>Not tested yet</h2><p>The charts and readings below describe the past. Run the test to see if swapping would have beaten holding, after fees.</p></div>
                      <div className="lab-idle-action"><button className="lab-primary" onClick={lab.testStrategy}>Run the test</button>
                      <p className="lab-note">Uses past prices only. No real money moves. The result saves on this computer.</p></div></div>}
                </div>}
            </>
            : <div className="lab-answer"><h2>Choose two coins</h2><p>QAP loads their price history automatically.</p></div>}
        </div>

        {analysis ? (
          <>
            <LabCharts
              analysis={analysis}
              wealth={study?.result.wealth ?? null}
              trades={study?.result.trades ?? []}
              signal={study?.result.signal ?? null}
              viewMode={viewMode}
            />
            <LabTradeDrawer analysis={analysis} study={study} />
          </>
        ) : (
          <div className="lab-chart-skeleton" aria-hidden="true"><span /> <span /> <span /></div>
        )}
      </div>

      <div className="lab-right-rail">
        {analysis && <LabEvidence analysis={analysis} viewMode={viewMode} />}
        <LabScorecard study={study} />
        <LabLivePaperPanel
          session={lab.paperSession}
          busy={lab.paperBusy}
          error={lab.paperError}
          canStart={Boolean(analysis)}
          onStart={lab.startPaperSession}
          onStep={() => lab.stepPaperSession(3.0)}
          onStop={lab.stopPaperSession}
        />
      </div>
    </div>}
  </div>
}
