import { useCallback, useEffect, useRef, useState } from 'react'

import { toBackendLabSettings, type LabRequest, type LabStrategyFormSettings } from './labContract'
import {
  createLivePaperSession,
  getLivePaperSession,
  listLivePaperSessions,
  stepLivePaperSession,
  stopLivePaperSession,
  type LivePaperSession,
} from './labPaperApi'

export function useLabPaper(request: LabRequest | null, strategySettings: LabStrategyFormSettings) {
  const [paperSession, setPaperSession] = useState<LivePaperSession | null>(null)
  const [paperBusy, setPaperBusy] = useState(false)
  const [paperError, setPaperError] = useState<string | null>(null)
  const paperController = useRef<AbortController | null>(null)

  const resetPaperSession = useCallback(() => {
    paperController.current?.abort()
    setPaperSession(null)
    setPaperBusy(false)
    setPaperError(null)
  }, [])

  const syncActivePaperSession = useCallback((nextRequest: LabRequest, signal: AbortSignal) => {
    void listLivePaperSessions(signal)
      .then((list) => {
        if (signal.aborted || !list || !Array.isArray(list.sessions)) return
        const active = list.sessions.find(
          (row) => row.status === 'active' && row.coin_a === nextRequest.coin_a && row.coin_b === nextRequest.coin_b,
        )
        if (active) {
          return getLivePaperSession(active.session_id, signal).then((detail) => {
            if (!signal.aborted && detail && detail.session_id) setPaperSession(detail)
          })
        }
        return undefined
      })
      .catch(() => { /* Paper session list is optional. */ })
  }, [])

  useEffect(() => () => {
    paperController.current?.abort()
  }, [])

  const startPaperSession = useCallback(() => {
    if (!request || paperBusy) return
    paperController.current?.abort()
    const controller = new AbortController()
    paperController.current = controller
    setPaperBusy(true)
    setPaperError(null)
    void createLivePaperSession(
      {
        coin_a: request.coin_a,
        coin_b: request.coin_b,
        anchor: request.anchor === 'none' ? null : request.anchor,
        bar: request.bar,
        order_rtt_ms: 75,
        max_staleness_ms: 500,
        settings: toBackendLabSettings(strategySettings),
      },
      controller.signal,
    )
      .then((session) => {
        if (!controller.signal.aborted) {
          setPaperSession(session)
          setPaperBusy(false)
        }
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
        if (!controller.signal.aborted) {
          setPaperSession(session)
          setPaperBusy(false)
        }
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
        if (!controller.signal.aborted) {
          setPaperSession(session)
          setPaperBusy(false)
        }
      })
      .catch((cause: unknown) => {
        if (!controller.signal.aborted) {
          setPaperError(cause instanceof Error ? cause.message : 'Could not stop paper session.')
          setPaperBusy(false)
        }
      })
  }, [paperSession, paperBusy])

  return {
    paperSession,
    paperBusy,
    paperError,
    resetPaperSession,
    syncActivePaperSession,
    startPaperSession,
    stepPaperSession,
    stopPaperSession,
  }
}
