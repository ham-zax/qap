import { useCallback, useEffect, useRef, useState } from 'react'
import { bootstrapLab, loadLab, searchLabCoins } from './labApi'
import {
  DEFAULT_ANCHORS,
  DEFAULT_BAND_LOOKBACK,
  LAB_BARS,
  fromBackendLabSettings,
  toBackendLabSettings,
  type LabAnalysis,
  type LabBar,
  type LabCoinMatch,
  type LabProgress,
  type LabRequest,
  type LabStrategyFormSettings,
  type LabViewMode,
} from './labContract'
import {
  DRAFT_KEY,
  STRATEGY_KEY,
  STUDY_KEY,
  VIEW_MODE_KEY,
  buildStudyCommand,
  buildStudyKey,
  readSavedRequest,
  readSavedStrategySettings,
  readSavedViewMode,
  readStoredStudy,
  writeStoredStudy,
} from './labStorage'
import {
  createLivePaperSession,
  getLivePaperSession,
  listLivePaperSessions,
  stepLivePaperSession,
  stopLivePaperSession,
  type LivePaperSession,
} from './labPaperApi'
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
  const [viewMode, setViewModeState] = useState<LabViewMode>(readSavedViewMode)
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

  const [compareResult, setCompareResult] = useState<LabCompareResult | null>(null)
  const [compareRunning, setCompareRunning] = useState(false)
  const [compareError, setCompareError] = useState<string | null>(null)

  const [savedStudies, setSavedStudies] = useState<LabSavedSummary[]>([])
  const [savedLoading, setSavedLoading] = useState(false)

  const [paperSession, setPaperSession] = useState<LivePaperSession | null>(null)
  const [paperBusy, setPaperBusy] = useState(false)
  const [paperError, setPaperError] = useState<string | null>(null)

  const preparedKey = useRef<string | null>(null)
  const studyController = useRef<AbortController | null>(null)
  const restoreController = useRef<AbortController | null>(null)
  const compareController = useRef<AbortController | null>(null)
  const paperController = useRef<AbortController | null>(null)
  const pendingAutoTest = useRef<LabStrategyFormSettings | null>(null)

  const setViewMode = useCallback((mode: LabViewMode) => {
    setViewModeState(mode)
    try { localStorage.setItem(VIEW_MODE_KEY, mode) } catch { /* Storage optional. */ }
  }, [])

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
        const wanted = [...new Set([...DEFAULT_ANCHORS, ...(saved ? [saved.coin_a, saved.coin_b, ...(saved.anchor ? [saved.anchor] : [])] : [])])]
        const resolved = await Promise.all(wanted.map(async (id) => {
          const result = await searchLabCoins(id.replace('binance:', ''), controller.signal)
          return result.coins.filter((coin) => coin.id === id)
        }))
        if (controller.signal.aborted) return
        const allCoins = [...new Map([...found.coins, ...resolved.flat()].map((coin) => [coin.id, coin])).values()]
        setCoins(allCoins)
        if (allCoins.length < 2) throw new Error('Two eligible Binance coins are needed. Retry when the directory is available.')
        const available = (key: string) => allCoins.some((coin) => coin.id === key)
        const defaults = ['binance:BTC', 'binance:ETH'].filter(available)
        const choices = [...new Set([...defaults, ...allCoins.map((coin) => coin.id)])]
        setRequest((current) => current ?? (saved ?? {
          coin_a: choices[0]!, coin_b: choices[1]!, anchor: null, bar: '15m', days: 180, band_lookback: DEFAULT_BAND_LOOKBACK['15m'],
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
    const key = [...new Set([request.coin_a, request.coin_b, ...(request.anchor ? [request.anchor] : [])])].sort().join('|')
    studyController.current?.abort()
    compareController.current?.abort()
    setStudy(null)
    setStudyRestored(false)
    setStudyError(null)
    setStudyRunning(false)
    setSettingsDirty(false)
    setCompareResult(null)
    setCompareError(null)
    setAnalysis(null)
    setAdvisor(null)
    setError(null)
    setProgress({ stage: 'Preparing pair history', completed: 0, total: 8 })
    try { localStorage.setItem(DRAFT_KEY, JSON.stringify(request)) } catch { /* Storage optional. */ }

    setAdvisorLoading(true)
    void loadLab(request, controller.signal, (next) => { if (!controller.signal.aborted) setProgress(next) }, preparedKey.current !== key)
      .then((result) => {
        if (controller.signal.aborted) return
        preparedKey.current = key
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

    void listLivePaperSessions(controller.signal)
      .then((list) => {
        if (controller.signal.aborted || !list || !Array.isArray(list.sessions)) return
        const active = list.sessions.find((row) => row.status === 'active' && row.coin_a === request.coin_a && row.coin_b === request.coin_b)
        if (active) {
          return getLivePaperSession(active.session_id, controller.signal).then((detail) => {
            if (!controller.signal.aborted && detail && detail.session_id) setPaperSession(detail)
          })
        }
        return undefined
      })
      .catch(() => { /* Paper session list is optional. */ })

    return () => controller.abort()
  }, [request, attempt, executeStudy, refreshSaved])

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
      })
      .catch(() => { /* Stored study may have been pruned; user can run a fresh test. */ })
    return () => controller.abort()
  }, [analysis, request, study, studyRunning, studyError, strategySettings])

  const change = useCallback((next: Partial<LabRequest>) => {
    setRequest((current) => current ? { ...current, ...next } : current)
  }, [])

  useEffect(() => () => {
    studyController.current?.abort()
    restoreController.current?.abort()
    compareController.current?.abort()
    paperController.current?.abort()
  }, [])

  const testStrategy = useCallback(() => {
    if (!request || studyRunning) return
    executeStudy(request, strategySettings)
  }, [request, studyRunning, strategySettings, executeStudy])

  const applyAdvisorPreset = useCallback((suggestion: LabAdvisorSuggestion) => {
    if (!request) return
    const nextStrategy = fromBackendLabSettings(suggestion.settings)
    setStrategySettings(nextStrategy)
    try { localStorage.setItem(STRATEGY_KEY, JSON.stringify(nextStrategy)) } catch { /* Storage optional. */ }
    const nextBar = (LAB_BARS.includes(suggestion.recommended_bar as LabBar) ? suggestion.recommended_bar : request.bar) as LabBar
    const nextAnchor = suggestion.recommended_anchor ?? request.anchor
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
    const candidates: LabStudySettings[] = [
      toBackendLabSettings(strategySettings),
      ...(advisor?.suggestions.map((s) => s.settings) ?? []),
      ...fallbacks,
    ].slice(0, 6)
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
    restoreController.current?.abort()
    const controller = new AbortController()
    restoreController.current = controller
    setStudyError(null)
    setCompareResult(null)
    void getSavedLabStudy(studyId, controller.signal)
      .then((loaded) => {
        if (controller.signal.aborted) return
        setStudy(loaded)
        setStudyRestored(true)
        setSettingsDirty(false)
        if (loaded.result.applied_settings) {
          const synced = fromBackendLabSettings(loaded.result.applied_settings)
          setStrategySettings(synced)
        }
      })
      .catch((cause: unknown) => {
        if (!controller.signal.aborted) setStudyError(cause instanceof Error ? cause.message : 'Could not open saved study.')
      })
  }, [])

  const togglePinStudy = useCallback((studyId: string, pinned: boolean) => {
    const controller = new AbortController()
    void pinLabStudy(studyId, pinned, controller.signal)
      .then(() => refreshSaved())
      .catch(() => { /* Non-blocking. */ })
  }, [refreshSaved])

  const clearStudy = useCallback(() => {
    studyController.current?.abort()
    restoreController.current?.abort()
    setStudy(null)
    setStudyRestored(false)
    setStudyError(null)
    setStudyRunning(false)
    setSettingsDirty(false)
    try { localStorage.removeItem(STUDY_KEY) } catch { /* Storage optional. */ }
  }, [])

  const startPaperSession = useCallback(() => {
    if (!request || paperBusy) return
    paperController.current?.abort()
    const controller = new AbortController()
    paperController.current = controller
    setPaperBusy(true)
    setPaperError(null)
    void createLivePaperSession({
      coin_a: request.coin_a,
      coin_b: request.coin_b,
      anchor: request.anchor,
      bar: request.bar,
      order_rtt_ms: 75,
      max_staleness_ms: 500,
      settings: toBackendLabSettings(strategySettings),
    }, controller.signal)
      .then((session) => {
        if (!controller.signal.aborted) { setPaperSession(session); setPaperBusy(false) }
      })
      .catch((cause: unknown) => {
        if (!controller.signal.aborted) {
          setPaperError(cause instanceof Error ? cause.message : 'Could not start live paper session.')
          setPaperBusy(false)
        }
      })
  }, [request, paperBusy, strategySettings])

  const stepPaperSession = useCallback((durationSeconds = 3.0) => {
    if (!paperSession || paperBusy) return
    paperController.current?.abort()
    const controller = new AbortController()
    paperController.current = controller
    setPaperBusy(true)
    setPaperError(null)
    void stepLivePaperSession(paperSession.session_id, durationSeconds, controller.signal)
      .then((session) => {
        if (!controller.signal.aborted) { setPaperSession(session); setPaperBusy(false) }
      })
      .catch((cause: unknown) => {
        if (!controller.signal.aborted) {
          setPaperError(cause instanceof Error ? cause.message : 'Paper step failed.')
          setPaperBusy(false)
        }
      })
  }, [paperSession, paperBusy])

  const stopPaperSession = useCallback(() => {
    if (!paperSession || paperBusy) return
    paperController.current?.abort()
    const controller = new AbortController()
    paperController.current = controller
    setPaperBusy(true)
    setPaperError(null)
    void stopLivePaperSession(paperSession.session_id, controller.signal)
      .then((session) => {
        if (!controller.signal.aborted) { setPaperSession(session); setPaperBusy(false) }
      })
      .catch((cause: unknown) => {
        if (!controller.signal.aborted) {
          setPaperError(cause instanceof Error ? cause.message : 'Could not stop paper session.')
          setPaperBusy(false)
        }
      })
  }, [paperSession, paperBusy])

  return {
    request, coins, analysis, progress, error, change,
    viewMode, setViewMode,
    strategySettings, updateStrategySettings, settingsDirty,
    advisor, advisorLoading, applyAdvisorPreset,
    study, studyRestored, studyError, studyRunning, testStrategy, clearStudy,
    compareResult, compareRunning, compareError, comparePresets, clearCompare: () => setCompareResult(null),
    savedStudies, savedLoading, openSavedStudy, togglePinStudy,
    paperSession, paperBusy, paperError, startPaperSession, stepPaperSession, stopPaperSession,
    retry: () => { preparedKey.current = null; setAttempt((value) => value + 1) },
  }
}
