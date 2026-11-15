import {
  DEFAULT_STRATEGY_SETTINGS,
  LAB_BARS,
  LAB_DAYS,
  toBackendLabSettings,
  type LabBar,
  type LabRequest,
  type LabStrategyFormSettings,
  type LabViewMode,
} from './labContract'
import type { LabStudyCommand } from './labStudyApi'

export const DRAFT_KEY = 'qap.lab.settings.v1'
export const STRATEGY_KEY = 'qap.lab.strategy.v1'
export const STUDY_KEY = 'qap.lab.study.v1'
export const VIEW_MODE_KEY = 'qap.lab.viewMode.v1'

export function buildStudyCommand(request: LabRequest, settings: LabStrategyFormSettings): LabStudyCommand {
  return {
    coin_a: request.coin_a,
    coin_b: request.coin_b,
    anchor: request.anchor,
    bar: request.bar,
    days: request.days,
    band_lookback: request.band_lookback,
    settings: toBackendLabSettings(settings),
  }
}

export function buildStudyKey(
  command: Pick<LabStudyCommand, 'coin_a' | 'coin_b' | 'anchor' | 'bar' | 'days' | 'band_lookback'>,
): string {
  return JSON.stringify([command.coin_a, command.coin_b, command.anchor, command.bar, command.days, command.band_lookback])
}

export function readStoredStudy(): { studyId: string; command: LabStudyCommand } | null {
  try {
    const raw = JSON.parse(localStorage.getItem(STUDY_KEY) ?? 'null') as { study_id?: unknown; request?: unknown } | null
    if (!raw || typeof raw.study_id !== 'string' || !raw.study_id) return null
    const request = raw.request as LabStudyCommand
    if (!request || typeof request.coin_a !== 'string' || typeof request.coin_b !== 'string' || request.coin_a === request.coin_b) return null
    if (!LAB_BARS.includes(request.bar as LabBar) || !LAB_DAYS.includes(request.days as 30 | 90 | 180 | 365)) return null
    if (!Number.isInteger(request.band_lookback) || request.band_lookback < 2 || request.band_lookback > 10000) return null
    if (request.anchor !== null && typeof request.anchor !== 'string') return null
    return { studyId: raw.study_id, command: request }
  } catch {
    return null
  }
}

export function writeStoredStudy(studyId: string, command: LabStudyCommand): void {
  try {
    localStorage.setItem(STUDY_KEY, JSON.stringify({ study_id: studyId, request: command }))
  } catch {
    /* Storage optional. */
  }
}

export function readSavedRequest(): LabRequest | null {
  try {
    const draft = JSON.parse(localStorage.getItem(DRAFT_KEY) ?? 'null') as LabRequest | null
    if (!draft || !LAB_BARS.includes(draft.bar) || !LAB_DAYS.includes(draft.days)) return null
    if (!Number.isInteger(draft.band_lookback) || draft.band_lookback < 2 || draft.band_lookback > 10000) return null
    if (typeof draft.coin_a !== 'string' || typeof draft.coin_b !== 'string' || draft.coin_a === draft.coin_b) return null
    if (draft.anchor !== null && typeof draft.anchor !== 'string') return null
    return draft
  } catch {
    return null
  }
}

export function readSavedStrategySettings(): LabStrategyFormSettings {
  try {
    const raw = JSON.parse(localStorage.getItem(STRATEGY_KEY) ?? 'null') as Partial<LabStrategyFormSettings> | null
    if (!raw || typeof raw !== 'object') return DEFAULT_STRATEGY_SETTINGS
    return { ...DEFAULT_STRATEGY_SETTINGS, ...raw }
  } catch {
    return DEFAULT_STRATEGY_SETTINGS
  }
}

export function readSavedViewMode(): LabViewMode {
  try {
    return localStorage.getItem(VIEW_MODE_KEY) === 'advanced' ? 'advanced' : 'simple'
  } catch {
    return 'simple'
  }
}
