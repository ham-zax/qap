import type { components } from '../../api/schema'
import { labJson } from './labApi'
import type { LabStudySettings } from './labStudyApi'

export type LivePaperSession = components['schemas']['LivePaperSessionDto']
export type LivePaperSessionList = components['schemas']['LivePaperSessionListDto']
export type LivePaperSessionRow = components['schemas']['LivePaperSessionRowDto']
export type LivePaperCreateRequest = Omit<components['schemas']['LivePaperCreateDto'], 'settings'> & {
  settings?: LabStudySettings
}

export function createLivePaperSession(
  body: LivePaperCreateRequest,
  signal: AbortSignal,
): Promise<LivePaperSession> {
  return labJson<LivePaperSession>('/api/pair-rotation/paper-sessions', signal, body)
}

export function listLivePaperSessions(signal: AbortSignal): Promise<LivePaperSessionList> {
  return labJson<LivePaperSessionList>('/api/pair-rotation/paper-sessions', signal)
}

export function getLivePaperSession(sessionId: string, signal: AbortSignal): Promise<LivePaperSession> {
  return labJson<LivePaperSession>(`/api/pair-rotation/paper-sessions/${encodeURIComponent(sessionId)}`, signal)
}

export function stepLivePaperSession(
  sessionId: string,
  durationSeconds: number,
  signal: AbortSignal,
): Promise<LivePaperSession> {
  return labJson<LivePaperSession>(
    `/api/pair-rotation/paper-sessions/${encodeURIComponent(sessionId)}/step`,
    signal,
    { duration_seconds: durationSeconds },
  )
}

export function stopLivePaperSession(sessionId: string, signal: AbortSignal): Promise<LivePaperSession> {
  return labJson<LivePaperSession>(
    `/api/pair-rotation/paper-sessions/${encodeURIComponent(sessionId)}/stop`,
    signal,
    {},
  )
}
