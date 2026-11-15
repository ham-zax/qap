import type { components } from '../../api/schema'
import { labJson } from './labApi'
import type { LabBar, LabDays } from './labContract'

export type LabStudy = components['schemas']['LabStudyDto']
export type LabSavedStudies = components['schemas']['LabSavedListDto']
export type LabSavedSummary = components['schemas']['LabSavedSummaryDto']
export type LabStudySettings = Partial<components['schemas']['LabSettings-Input']>
export type LabStudyCommand = Omit<components['schemas']['LabStudyRequestDto'], 'settings'> & { settings?: LabStudySettings }
export type LabAdvisor = components['schemas']['LabAdvisorDto']
export type LabAdvisorSuggestion = components['schemas']['LabAdvisorSuggestionDto']
export type LabCompareResult = components['schemas']['LabCompareResultDto']
export type LabCompareCommand = Omit<components['schemas']['LabCompareRequestDto'], 'candidates'> & {
  candidates?: LabStudySettings[]
}

export function computeLabStudy(command: LabStudyCommand, signal: AbortSignal): Promise<LabStudy> {
  return labJson<LabStudy>('/api/pair-rotation/studies', signal, command)
}

export function listSavedLabStudies(
  signal: AbortSignal,
  options: { limit?: number; offset?: number } = {},
): Promise<LabSavedStudies> {
  const query = new URLSearchParams({
    limit: String(options.limit ?? 25),
    offset: String(options.offset ?? 0),
  })
  return labJson<LabSavedStudies>(`/api/pair-rotation/studies?${query}`, signal)
}

export function getSavedLabStudy(studyId: string, signal: AbortSignal): Promise<LabStudy> {
  return labJson<LabStudy>(`/api/pair-rotation/studies/${encodeURIComponent(studyId)}`, signal)
}

export function pinLabStudy(studyId: string, pinned: boolean, signal: AbortSignal): Promise<LabStudy> {
  return labJson<LabStudy>(`/api/pair-rotation/studies/${encodeURIComponent(studyId)}/pin`, signal, { pinned })
}

export function fetchLabAdvisor(
  params: { coin_a: string; coin_b: string; bar: LabBar; days: LabDays; band_lookback: number; anchor: string | null },
  signal: AbortSignal,
): Promise<LabAdvisor> {
  const query = new URLSearchParams({
    coin_a: params.coin_a,
    coin_b: params.coin_b,
    bar: params.bar,
    days: String(params.days),
    band_lookback: String(params.band_lookback),
  })
  if (params.anchor) query.set('anchor', params.anchor)
  return labJson<LabAdvisor>(`/api/pair-rotation/advisor?${query}`, signal)
}

export function compareLabStudies(command: LabCompareCommand, signal: AbortSignal): Promise<LabCompareResult> {
  return labJson<LabCompareResult>('/api/pair-rotation/studies/compare', signal, command)
}
