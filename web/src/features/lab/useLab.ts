import { useEffect, useRef, useState } from 'react'
import { bootstrapLab, loadLab, searchLabCoins } from './labApi'
import { computeLabStudy, getSavedLabStudy, type LabStudy, type LabStudyCommand } from './labStudyApi'
import { DEFAULT_ANCHORS, DEFAULT_BAND_LOOKBACK, type LabAnalysis, type LabCoinMatch, type LabProgress, type LabRequest } from './labContract'

const DRAFT_KEY = 'qap.lab.settings.v1'
const STUDY_KEY = 'qap.lab.study.v1'

/** The study command a request produces, so a stored result never pairs with other settings. */
function studyCommand(request: LabRequest): LabStudyCommand {
  return {
    coin_a: request.coin_a,
    coin_b: request.coin_b,
    anchor: request.anchor,
    bar: request.bar,
    days: request.days,
    band_lookback: request.band_lookback,
  }
}

function studyKey(command: LabStudyCommand): string {
  return JSON.stringify([command.coin_a, command.coin_b, command.anchor, command.bar, command.days, command.band_lookback])
}

/** Reads the last study saved on this browser. Stored data is untrusted, so every field is checked. */
function storedStudy(): { studyId: string; command: LabStudyCommand } | null {
  try {
    const raw = JSON.parse(localStorage.getItem(STUDY_KEY) ?? 'null') as { study_id?: unknown; request?: unknown } | null
    if (!raw || typeof raw.study_id !== 'string' || !raw.study_id) return null
    const request = raw.request as LabStudyCommand
    if (!request || typeof request.coin_a !== 'string' || typeof request.coin_b !== 'string' || request.coin_a === request.coin_b) return null
    if (!['15m', '1h', '4h', '1d'].includes(request.bar) || ![30, 90, 180, 365].includes(request.days)) return null
    if (!Number.isInteger(request.band_lookback) || request.band_lookback < 2 || request.band_lookback > 10000) return null
    if (request.anchor !== null && typeof request.anchor !== 'string') return null
    return { studyId: raw.study_id, command: request }
  } catch { return null }
}

function rememberStudy(studyId: string, command: LabStudyCommand) {
  try { localStorage.setItem(STUDY_KEY, JSON.stringify({ study_id: studyId, request: command })) } catch { /* Private browsing can disable storage. */ }
}

function savedSettings(): LabRequest | null {
  try {
    const draft = JSON.parse(localStorage.getItem(DRAFT_KEY) ?? 'null') as LabRequest | null
    if (!draft || !['15m', '1h', '4h', '1d'].includes(draft.bar) || ![30, 90, 180, 365].includes(draft.days)) return null
    if (!Number.isInteger(draft.band_lookback) || draft.band_lookback < 2 || draft.band_lookback > 10000) return null
    if (typeof draft.coin_a !== 'string' || typeof draft.coin_b !== 'string' || draft.coin_a === draft.coin_b) return null
    if (draft.anchor !== null && typeof draft.anchor !== 'string') return null
    return draft
  } catch { return null }
}

export function useLab() {
  const [request, setRequest] = useState<LabRequest | null>(null)
  const [coins, setCoins] = useState<LabCoinMatch[]>([])
  const [analysis, setAnalysis] = useState<LabAnalysis | null>(null)
  const [progress, setProgress] = useState<LabProgress | null>({ stage: 'Reading available coins', completed: 0, total: 1 })
  const [error, setError] = useState<string | null>(null)
  const [attempt, setAttempt] = useState(0)
  const [study, setStudy] = useState<LabStudy | null>(null)
  const [studyRestored, setStudyRestored] = useState(false)
  const [studyError, setStudyError] = useState<string | null>(null)
  const [studyRunning, setStudyRunning] = useState(false)
  const preparedKey = useRef<string | null>(null)
  const studyController = useRef<AbortController | null>(null)
  const restoreController = useRef<AbortController | null>(null)

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
        const saved = savedSettings()
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

  useEffect(() => {
    if (!request) return
    const controller = new AbortController()
    const key = [...new Set([request.coin_a, request.coin_b, ...(request.anchor ? [request.anchor] : [])])].sort().join('|')
    studyController.current?.abort()
    setStudy(null)
    setStudyRestored(false)
    setStudyError(null)
    setStudyRunning(false)
    setAnalysis(null)
    setError(null)
    setProgress({ stage: 'Preparing pair history', completed: 0, total: 8 })
    try { localStorage.setItem(DRAFT_KEY, JSON.stringify(request)) } catch { /* Private browsing can disable storage. */ }
    void loadLab(request, controller.signal, (next) => { if (!controller.signal.aborted) setProgress(next) }, preparedKey.current !== key)
      .then((result) => { if (!controller.signal.aborted) { preparedKey.current = key; setAnalysis(result); setProgress(null) } })
      .catch((cause: unknown) => {
        if (!controller.signal.aborted) { setError(cause instanceof Error ? cause.message : 'Analysis failed.'); setProgress(null) }
      })
    return () => controller.abort()
  }, [request, attempt])

  // Restore the last study saved on this browser, but only when the current
  // settings still produce the same command. A restored result is labelled.
  useEffect(() => {
    if (!request) return
    const stored = storedStudy()
    if (!stored || studyKey(stored.command) !== studyKey(studyCommand(request))) return
    const controller = new AbortController()
    restoreController.current?.abort()
    restoreController.current = controller
    void getSavedLabStudy(stored.studyId, controller.signal)
      .then((saved) => {
        if (controller.signal.aborted || saved.result?.analysis?.coin_a?.id !== request.coin_a || saved.result.analysis.coin_b?.id !== request.coin_b) return
        setStudy(saved)
        setStudyRestored(true)
        setStudyError(null)
      })
      .catch(() => { /* A missing or unreachable saved study keeps the untested state. */ })
    return () => controller.abort()
  }, [request, attempt])

  const change = (next: Partial<LabRequest>) => setRequest((current) => current ? { ...current, ...next } : current)

  useEffect(() => () => { studyController.current?.abort(); restoreController.current?.abort() }, [])

  const testStrategy = () => {
    if (!request || studyRunning) return
    restoreController.current?.abort()
    const controller = new AbortController()
    const command = studyCommand(request)
    studyController.current = controller
    setStudy(null)
    setStudyRestored(false)
    setStudyError(null)
    setStudyRunning(true)
    void computeLabStudy(command, controller.signal)
      .then((result) => {
        if (controller.signal.aborted) return
        setStudy(result)
        setStudyRestored(false)
        setStudyRunning(false)
        rememberStudy(result.study_id, command)
      })
      .catch((cause: unknown) => {
        if (!controller.signal.aborted) {
          setStudyError(cause instanceof Error ? cause.message : 'Strategy test failed.')
          setStudyRunning(false)
        }
      })
  }

  const clearStudy = () => {
    studyController.current?.abort()
    restoreController.current?.abort()
    setStudy(null)
    setStudyRestored(false)
    setStudyError(null)
    setStudyRunning(false)
    try { localStorage.removeItem(STUDY_KEY) } catch { /* Private browsing can disable storage. */ }
  }

  return {
    request, coins, analysis, progress, error, change,
    study, studyRestored, studyError, studyRunning, testStrategy, clearStudy,
    retry: () => { preparedKey.current = null; setAttempt((value) => value + 1) },
  }
}
