import type { ResearchAssetSelection } from './researchAssetSearch'
import type { ResearchRecipeDraftV1 } from '../../api/types'

export type StudyHorizon = 'short' | 'medium' | 'swing'
export type ResearchMode = 'relationship' | 'backtest_comparison'
export interface StudyAttempt {
  operationId: string
  createdAt: string
  question: string
}
export interface ResearchStudy {
  id: string
  name: string
  assetA: ResearchAssetSelection | null
  assetB: ResearchAssetSelection | null
  horizon: StudyHorizon
  mode: ResearchMode
  useBtcReference: boolean
  attempts: StudyAttempt[]
  parameters?: Record<string, string>
}
export interface StudyLibrary {
  activeId: string
  studies: ResearchStudy[]
}
export interface StudyStorage {
  getItem: (key: string) => string | null
  setItem: (key: string, value: string) => void
}

export const STUDY_PERIODS = {
  short: { label: '30 days', detail: 'Hourly bars · 7-day relationship window' },
  medium: { label: '90 days', detail: '4-hour bars · 30-day relationship window' },
  swing: { label: '180 days', detail: 'Daily bars · 90-day relationship window' },
} as const

export function emptyStudy(id: string): ResearchStudy {
  return { id, name: '', assetA: null, assetB: null, horizon: 'medium', mode: 'relationship', useBtcReference: false, attempts: [] }
}

export function studyTitle(study: ResearchStudy): string {
  return study.name.trim() || (study.assetA && study.assetB
    ? `${study.assetA.symbol} / ${study.assetB.symbol}` : 'Untitled study')
}

export function studyQuestion(study: ResearchStudy): string {
  return `${study.assetA?.symbol ?? '?'} / ${study.assetB?.symbol ?? '?'} · ${STUDY_PERIODS[study.horizon].label} · ${study.mode === 'relationship' ? 'Relationship' : 'Backtest comparison'}`
}

export function addAttempt(study: ResearchStudy, operationId: string, createdAt: string, question = studyQuestion(study)): ResearchStudy {
  if (study.attempts.some((item) => item.operationId === operationId)) return study
  return {
    ...study,
    attempts: [...study.attempts, {
      operationId, createdAt,
      question,
    }],
  }
}

export function studyStorageKey(workspace: string): string {
  return `qap.research-studies.v2:${workspace}`
}

export function legacyStudyStorageKey(workspace: string): string {
  return `qap.research-studies.v1:${workspace}`
}

function object(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}
function text(value: unknown): value is string {
  return typeof value === 'string' && value.length > 0
}
function selection(value: unknown): value is ResearchAssetSelection | null {
  return value === null || (object(value) && text(value.key) && text(value.symbol)
    && (value.canonicalAssetId === null || text(value.canonicalAssetId))
    && typeof value.approved === 'boolean'
    && (value.identityState === 'resolved' || value.identityState === 'review_required')
    && (value.venue === undefined || value.venue === 'binance' || value.venue === 'gate')
    && (value.venueAssetCode === undefined || text(value.venueAssetCode))
    && Array.isArray(value.venueSymbols) && value.venueSymbols.every(text))
}
function study(value: unknown, version: 1 | 2): value is ResearchStudy {
  return object(value) && text(value.id) && typeof value.name === 'string'
    && selection(value.assetA) && selection(value.assetB)
    && (value.horizon === 'short' || value.horizon === 'medium' || value.horizon === 'swing')
    && (version === 1 || value.mode === 'relationship' || value.mode === 'backtest_comparison')
    && typeof value.useBtcReference === 'boolean' && Array.isArray(value.attempts)
    && (value.parameters === undefined || (object(value.parameters)
      && Object.entries(value.parameters).every(([key, item]) => PARAMETER_KEYS.includes(key) && typeof item === 'string')))
    && value.attempts.every((item) => object(item) && text(item.operationId)
      && text(item.createdAt) && Number.isFinite(Date.parse(item.createdAt)) && text(item.question))
}

export const PARAMETER_KEYS = ['window_bars', 'min_observations', 'enter_threshold', 'neutral_threshold', 'maximum_tilt']

export function applyStudyParameters(recipe: ResearchRecipeDraftV1, parameters: Record<string, string>): ResearchRecipeDraftV1 {
  return { ...recipe, variants: recipe.variants.map((variant) => {
    const relationship = { ...variant.relationship.config }
    const decision = { ...variant.decision_rule.config }
    for (const key of PARAMETER_KEYS) {
      const value = parameters[key]
      if (value === undefined) continue
      if (key === 'window_bars' || key === 'min_observations') {
        // Invalid/empty input remains invalid for the backend support check.
        relationship[key] = value.trim() !== '' && Number.isFinite(Number(value)) ? Number(value) : value
      } else decision[key] = value
    }
    return { ...variant, relationship: { ...variant.relationship, config: relationship },
      decision_rule: { ...variant.decision_rule, config: decision } }
  }) }
}

export function readStudies(storage: StudyStorage, workspace: string): {
  library: StudyLibrary | null; warning: string | null
} {
  try {
    const current = storage.getItem(studyStorageKey(workspace))
    const raw = current ?? storage.getItem(legacyStudyStorageKey(workspace))
    if (raw === null) return { library: null, warning: null }
    const value: unknown = JSON.parse(raw)
    const version = current === null ? 1 : 2
    if (!object(value) || value.version !== version || !text(value.activeId)
      || !Array.isArray(value.studies) || !value.studies.every((item) => study(item, version))
      || !value.studies.some((item) => item.id === value.activeId)
      || new Set(value.studies.map((item) => item.id)).size !== value.studies.length) {
      throw new Error('Invalid saved studies')
    }
    const studies: ResearchStudy[] = version === 1
      ? value.studies.map((item: ResearchStudy) => ({ ...item, mode: 'backtest_comparison' }))
      : value.studies
    return { library: { activeId: value.activeId, studies }, warning: null }
  } catch {
    return {
      library: null,
      warning: 'Saved studies could not be read. Existing saved data has been left untouched. You can work in this session; backend results remain in History.',
    }
  }
}

export function saveStudies(storage: StudyStorage, workspace: string, library: StudyLibrary): string | null {
  const previous = readStudies(storage, workspace)
  if (previous.warning) return previous.warning
  try {
    storage.setItem(studyStorageKey(workspace), JSON.stringify({ version: 2, ...library }))
    return null
  } catch {
    return 'This browser could not save your study. Keep this page open to retain the draft. Started backtests and results remain in History.'
  }
}
