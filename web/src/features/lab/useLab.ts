import { useCallback, useEffect, useRef, useState } from 'react'
import { bootstrapLab, loadLab, searchLabCoins } from './labApi'
import {
  DEFAULT_ANCHORS,
  DEFAULT_BAND_LOOKBACK,
  LAB_BARS,
  fromBackendLabSettings,
  type LabAnalysis,
  type LabBar,
  type LabCoinMatch,
  type LabProgress,
  type LabRequest,
  type LabStrategyFormSettings,
} from './labContract'
import {
  DRAFT_KEY,
  STRATEGY_KEY,
  STUDY_KEY,
  buildStudyCommand,
  buildStudyKey,
  readSavedRequest,
  readSavedStrategySettings,
  readStoredStudy,
  useLabViewMode,
  writeStoredStudy,
} from './labStorage'
import { useLabPaper } from './useLabPaper'
import {
  compareLabStudies,
  computeLabStudy,
  fetchLabAdvisor,
  getSavedLabStudy,
  listSavedLabStudies,
  pinLabStudy,
  type LabAdvisor,
  type LabAdvisorSuggestion,
  type LabCompareResult,
  type LabSavedSummary,
  type LabStudy,
  type LabStudySettings,
} from './labStudyApi'

export function useLab() {
  const [request, setRequest] = useState<LabRequest | null>(null)
  const [strategySettings, setStrategySettings] = useState<LabStrategyFormSettings>(readSavedStrategySettings)
  const [settingsDirty, setSettingsDirty] = useState(false)
  const [viewMode, setViewMode] = useLabViewMode()
  const [coins, setCoins] = useState<LabCoinMatch[]>([])
  const [analysis, setAnalysis] = useState<LabAnalysis | null>(null)
  const [progress, setProgress] = useState<LabProgress | null>({ stage: 'Reading available coins', completed: 0, total: 1 })
  const [error, setError] = useState<string | null>(null)
  const [attempt, setAttempt] = useState(0)

  const [advisor, setAdvisor] = useState<LabAdvisor | null>(null)
  const [advisorLoading, setAdvisorLoading] = useState(false)

  const [study, setStudy] = useState<LabStudy | null>(null)
  const [studyRestored, setStudyRestored] = useState(false)
  const [studyError, setStudyError] = useState<string | null>(null)
  const [studyRunning, setStudyRunning] = useState(false)
  const [loadedSavedBanner, setLoadedSavedBanner] = useState<{ studyId: string; label: string } | null>(null)

  const [compareResult, setCompareResult] = useState<LabCompareResult | null>(null)
  const [compareRunning, setCompareRunning] = useState(false)
  const [compareError, setCompareError] = useState<string | null>(null)

  const [savedStudies, setSavedStudies] = useState<LabSavedSummary[]>([])
  const [savedLoading, setSavedLoading] = useState(false)

  const {
    paperSession,
    paperBusy,
    paperError,
    resetPaperSession,
    syncActivePaperSession,
    startPaperSession,
    stepPaperSession,
    stopPaperSession,
  } = useLabPaper(request, strategySettings)

  const forcePrepare = useRef(false)
  const pendingLoadedStudy = useRef<LabStudy | null>(null)
  const studyController = useRef<AbortController | null>(null)
  const restoreController = useRef<AbortController | null>(null)
  const compareController = useRef<AbortController | null>(null)
  const pendingAutoTest = useRef<LabStrategyFormSettings | null>(null)

  const updateStrategySettings = useCallback((patch: Partial<LabStrategyFormSettings>) => {
    setStrategySettings((current) => {
      const next = { ...current, ...patch }
      try { localStorage.setItem(STRATEGY_KEY, JSON.stringify(next)) } catch { /* Storage optional. */ }
      return next
    })
    setSettingsDirty((prev) => prev || Boolean(study))
  }, [study])

  const refreshSaved = useCallback((signal?: AbortSignal) => {
    const ctrl = signal ? null : new AbortController()
    const activeSignal = signal ?? ctrl!.signal
    setSavedLoading(true)
    void listSavedLabStudies(activeSignal, { limit: 20, offset: 0 })
      .then((page) => {
        if (!activeSignal.aborted && page && Array.isArray(page.studies)) {
          setSavedStudies(page.studies)
        }
      })
      .catch(() => { /* Saved list is non-blocking. */ })
      .finally(() => { if (!activeSignal.aborted) setSavedLoading(false) })
  }, [])

  useEffect(() => {
    const controller = new AbortController()
    async function discover() {
      try {
        setError(null)
        let found = await searchLabCoins('', controller.signal)
        if (!found.ready) {
          await bootstrapLab(controller.signal, setProgress)
          found = await searchLabCoins('', controller.signal)
        }
        const saved = readSavedRequest()
        const wanted = [...new Set([...DEFAULT_ANCHORS, ...(saved ? [saved.coin_a, saved.coin_b, ...(saved.anchor && saved.anchor !== 'none' ? [saved.anchor] : [])] : [])])]
        const missing = wanted.filter((id) => !found.coins.some((coin) => coin.id === id))
        const extra = missing.length ? (await Promise.all(missing.map(async (id) =>
          (await searchLabCoins(id.replace('binance:', ''), controller.signal)).coins.filter((coin) => coin.id === id)))).flat() : []
        if (controller.signal.aborted) return
        const allCoins = [...new Map([...found.coins, ...extra].map((coin) => [coin.id, coin])).values()]
        setCoins(allCoins)
        if (allCoins.length < 2) throw new Error('Two eligible Binance coins are needed. Retry when the directory is available.')
        const available = (key: string) => allCoins.some((coin) => coin.id === key)
        const defaults = ['binance:BTC', 'binance:ETH'].filter(available)
        const choices = [...new Set([...defaults, ...allCoins.map((coin) => coin.id)])]
        setRequest((current) => current ?? (saved ?? {
          coin_a: choices[0]!, coin_b: choices[1]!, anchor: null, bar: '1h', days: 180, band_lookback: DEFAULT_BAND_LOOKBACK['1h'],
        }))
      } catch (cause) {
        if (!controller.signal.aborted) { setError(cause instanceof Error ? cause.message : 'Coin search failed.'); setProgress(null) }
      }
    }
    void discover()
    return () => controller.abort()
  }, [attempt])

  const executeStudy = useCallback((req: LabRequest, formSettings: LabStrategyFormSettings) => {
    restoreController.current?.abort()
    studyController.current?.abort()
    const controller = new AbortController()
    const command = buildStudyCommand(req, formSettings)
    studyController.current = controller
    setStudy(null)
    setStudyRestored(false)
    setStudyError(null)
    setStudyRunning(true)
    setSettingsDirty(false)
    setCompareResult(null)
    setLoadedSavedBanner(null)
    void computeLabStudy(command, controller.signal)
      .then((result) => {
        if (controller.signal.aborted) return
        setStudy(result)
        setStudyRestored(false)
        setStudyRunning(false)
        writeStoredStudy(result.study_id, command)
        refreshSaved()
      })
      .catch((cause: unknown) => {
        if (!controller.signal.aborted) {
          setStudyError(cause instanceof Error ? cause.message : 'Strategy test failed.')
          setStudyRunning(false)
        }
      })
  }, [refreshSaved])

  useEffect(() => {
    if (!request) return
    const controller = new AbortController()
    const prepare = forcePrepare.current
    forcePrepare.current = false
    const carriedStudy = pendingLoadedStudy.current
    pendingLoadedStudy.current = null
    studyController.current?.abort()
    compareController.current?.abort()
    resetPaperSession()
    setStudy(carriedStudy)
    if (!carriedStudy) setLoadedSavedBanner(null)
    setStudyRestored(Boolean(carriedStudy))
    setStudyError(null)
    setStudyRunning(false)
    setSettingsDirty(false)
    setCompareResult(null)
    setCompareRunning(false)
    setCompareError(null)
    setAnalysis(carriedStudy?.result.analysis ?? null)
    setAdvisor(null)
    setError(null)
    setProgress({ stage: 'Preparing pair history', completed: 0, total: 8 })
    try { localStorage.setItem(DRAFT_KEY, JSON.stringify(request)) } catch { /* Storage optional. */ }

    setAdvisorLoading(true)
    // Group rapid selector edits. Cleanup cancels the delay and all stale responses.
    const settled = new Promise<void>((resolve) => {
      const timer = setTimeout(resolve, 250)
      controller.signal.addEventListener('abort', () => clearTimeout(timer), { once: true })
    })
    const analysisResult = carriedStudy ? Promise.resolve(carriedStudy.result.analysis)
      : settled.then(() => loadLab(request, controller.signal, (next) => { if (!controller.signal.aborted) setProgress(next) }, prepare))
    void analysisResult
      .then((result) => {
        if (controller.signal.aborted) return
        setAnalysis(result)
        setProgress(null)
        const queued = pendingAutoTest.current
        if (queued) {
          pendingAutoTest.current = null
          executeStudy(request, queued)
        }
        return fetchLabAdvisor(request, controller.signal)
          .then((res) => {
            if (!controller.signal.aborted && res && Array.isArray(res.suggestions)) setAdvisor(res)
          })
          .catch(() => { /* Advisor is optional. */ })
      })
      .catch((cause: unknown) => {
        if (!controller.signal.aborted) { setError(cause instanceof Error ? cause.message : 'Analysis failed.'); setProgress(null) }
      })
      .finally(() => { if (!controller.signal.aborted) setAdvisorLoading(false) })

    refreshSaved(controller.signal)
    syncActivePaperSession(request, controller.signal)

    return () => controller.abort()
  }, [request, attempt, executeStudy, refreshSaved, resetPaperSession, syncActivePaperSession])

  useEffect(() => {
    if (!analysis || !request || study || studyRunning || studyError) return
    const saved = readStoredStudy()
    if (!saved || buildStudyKey(saved.command) !== buildStudyKey(buildStudyCommand(request, strategySettings))) return
    restoreController.current?.abort()
    const controller = new AbortController()
    restoreController.current = controller
    void getSavedLabStudy(saved.studyId, controller.signal)
      .then((result) => {
        if (controller.signal.aborted) return
        setStudy(result)
        setStudyRestored(true)
        setAnalysis(result.result.analysis)
      })
      .catch(() => { /* Stored study may have been pruned; user can run a fresh test. */ })
    return () => controller.abort()
  }, [analysis, request, study, studyRunning, studyError, strategySettings])

  const change = useCallback((next: Partial<LabRequest>) => {
    restoreController.current?.abort()
    pendingAutoTest.current = null
    setRequest((current) => current ? { ...current, ...next } : current)
  }, [])

  useEffect(() => () => {
    studyController.current?.abort()
    restoreController.current?.abort()
    compareController.current?.abort()
  }, [])

  const testStrategy = useCallback((method?: LabStrategyFormSettings['method']) => {
    if (!request || studyRunning) return
    const settings = method ? { ...strategySettings, method } : strategySettings
    if (method) updateStrategySettings({ method })
    executeStudy(request, settings)
  }, [request, studyRunning, strategySettings, executeStudy, updateStrategySettings])

  const applyAdvisorPreset = useCallback((suggestion: LabAdvisorSuggestion) => {
    if (!request) return
    const nextStrategy = fromBackendLabSettings(suggestion.settings)
    setStrategySettings(nextStrategy)
    try { localStorage.setItem(STRATEGY_KEY, JSON.stringify(nextStrategy)) } catch { /* Storage optional. */ }
    const nextBar = (LAB_BARS.includes(suggestion.recommended_bar as LabBar) ? suggestion.recommended_bar : request.bar) as LabBar
    const nextAnchor = request.anchor === 'none' ? 'none' : (suggestion.recommended_anchor ?? request.anchor)
    if (nextBar !== request.bar || nextAnchor !== request.anchor) {
      pendingAutoTest.current = nextStrategy
      setRequest({
        ...request,
        bar: nextBar,
        anchor: nextAnchor,
        band_lookback: nextBar !== request.bar ? DEFAULT_BAND_LOOKBACK[nextBar] : request.band_lookback,
      })
    } else {
      executeStudy(request, nextStrategy)
    }
  }, [request, executeStudy])

  const comparePresets = useCallback(() => {
    if (!request || compareRunning) return
    compareController.current?.abort()
    const controller = new AbortController()
    compareController.current = controller
    setCompareRunning(true)
    setCompareError(null)
    const fallbacks: LabStudySettings[] = [
      { method: 'zscore', hedge_method: 'kalman', lookback: 96, entry: 2.0, exit: 0.4 },
      { method: 'copula', lookback: 120, copula_probability: 0.05 },
      { method: 'trend', fast_window: 12, slow_window: 48 },
    ]
    const candidates = advisor?.suggestions.length ? advisor.suggestions.map((s) => s.settings) : fallbacks
    void compareLabStudies({
      coin_a: request.coin_a,
      coin_b: request.coin_b,
      anchor: request.anchor,
      bar: request.bar,
      days: request.days,
      band_lookback: request.band_lookback,
      candidates,
    }, controller.signal)
      .then((res) => {
        if (controller.signal.aborted) return
        setCompareResult(res)
        setCompareRunning(false)
        refreshSaved()
      })
      .catch((cause: unknown) => {
        if (!controller.signal.aborted) {
          setCompareError(cause instanceof Error ? cause.message : 'Preset comparison failed.')
          setCompareRunning(false)
        }
      })
  }, [request, compareRunning, strategySettings, advisor, refreshSaved])

  const openSavedStudy = useCallback((studyId: string) => {
    studyController.current?.abort()
    compareController.current?.abort()
    pendingAutoTest.current = null
    restoreController.current?.abort()
    const controller = new AbortController()
    restoreController.current = controller
    setStudyError(null)
    setCompareResult(null)
    void getSavedLabStudy(studyId, controller.signal)
      .then((loaded) => {
        if (controller.signal.aborted) return
        pendingLoadedStudy.current = loaded
        setStudy(loaded)
        setStudyRestored(true)
        setSettingsDirty(false)
        if (loaded.result.applied_settings) {
          const synced = fromBackendLabSettings(loaded.result.applied_settings)
          setStrategySettings(synced)
          try { localStorage.setItem(STRATEGY_KEY, JSON.stringify(synced)) } catch { /* Storage optional. */ }
        }
        const snapshot = loaded.result.analysis
        const method = loaded.result.applied_settings?.method ?? 'zscore'
        setLoadedSavedBanner({ studyId, label: `${snapshot.coin_a.code}/${snapshot.coin_b.code} · ${snapshot.bar} · ${loaded.created_at} · ${method.toUpperCase()}` })
        const restoredAnchor = snapshot.anchor?.id ?? (snapshot.anchor_ranking.length > 0 ? 'none' : null)
        setRequest({ coin_a: snapshot.coin_a.id, coin_b: snapshot.coin_b.id, anchor: restoredAnchor,
          bar: snapshot.bar, days: snapshot.window_days as LabRequest['days'], band_lookback: snapshot.band_lookback })
      })
      .catch((cause: unknown) => {
        if (!controller.signal.aborted) setStudyError(cause instanceof Error ? cause.message : 'Could not open saved study.')
      })
  }, [])

  const refreshPairData = useCallback(() => {
    if (!request) return
    forcePrepare.current = true
    setAttempt((value) => value + 1)
  }, [request])

  const togglePinStudy = useCallback((studyId: string, pinned: boolean) => {
    const controller = new AbortController()
    void pinLabStudy(studyId, pinned, controller.signal)
      .then(() => refreshSaved())
      .catch(() => { /* Non-blocking. */ })
  }, [refreshSaved])

  const clearStudy = useCallback(() => {
    pendingLoadedStudy.current = null
    pendingAutoTest.current = null
    studyController.current?.abort()
    restoreController.current?.abort()
    setStudy(null)
    setStudyRestored(false)
    setStudyError(null)
    setStudyRunning(false)
    setSettingsDirty(false)
    setLoadedSavedBanner(null)
    try { localStorage.removeItem(STUDY_KEY) } catch { /* Storage optional. */ }
  }, [])

  return {
    request, coins, analysis, progress, error, change,
    viewMode, setViewMode,
    strategySettings, updateStrategySettings, settingsDirty,
    advisor, advisorLoading, applyAdvisorPreset,
    study, studyRestored, studyError, studyRunning, testStrategy, clearStudy,
    loadedSavedBanner, refreshPairData,
    compareResult, compareRunning, compareError, comparePresets, clearCompare: () => setCompareResult(null),
    savedStudies, savedLoading, openSavedStudy, togglePinStudy,
    paperSession, paperBusy, paperError, startPaperSession, stepPaperSession, stopPaperSession,
    retry: () => setAttempt((value) => value + 1),
  }
}
