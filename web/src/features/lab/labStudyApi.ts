import type { components } from '../../api/schema'
import { labJson } from './labApi'

export type LabStudy = components['schemas']['LabStudyDto']
export type LabSavedStudies = components['schemas']['LabSavedListDto']
export type LabStudySettings = Partial<components['schemas']['LabSettings-Input']>
export type LabStudyCommand = Omit<components['schemas']['LabStudyRequestDto'], 'settings'> & { settings?: LabStudySettings }

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
