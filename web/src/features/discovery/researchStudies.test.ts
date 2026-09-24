import { describe, expect, it } from 'vitest'

import { addAttempt, emptyStudy, readStudies, saveStudies, studyStorageKey } from './researchStudies'

function storage() {
  const data = new Map<string, string>()
  return {
    getItem: (key: string) => data.get(key) ?? null,
    setItem: (key: string, value: string) => { data.set(key, value) },
  }
}

describe('saved research studies', () => {
  it('starts new work as a relationship question', () => {
    expect(emptyStudy('new').mode).toBe('relationship')
  })

  it('migrates old comparisons without deleting their saved attempts', () => {
    const store = storage()
    const old = addAttempt(emptyStudy('old'), 'operation-1', '2026-09-24T10:00:00Z')
    const legacy = `qap.research-studies.v1:/workspace/a`
    const raw = JSON.stringify({ version: 1, activeId: 'old', studies: [old] })
    store.setItem(legacy, raw)
    const resumed = readStudies(store, '/workspace/a')
    expect(resumed.library?.studies[0]?.mode).toBe('backtest_comparison')
    expect(resumed.library?.studies[0]?.attempts[0]?.operationId).toBe('operation-1')
    expect(saveStudies(store, '/workspace/a', resumed.library!)).toBeNull()
    expect(store.getItem(legacy)).toBe(raw)
    expect(JSON.parse(store.getItem(studyStorageKey('/workspace/a'))!).version).toBe(2)
  })

  it('resumes intent and all attempts only in the matching workspace', () => {
    const store = storage()
    const initial = { ...emptyStudy('study-1'), name: 'W and PIXEL', horizon: 'medium' as const }
    const first = addAttempt(initial, 'operation-1', '2026-09-24T10:00:00Z')
    const second = addAttempt(first, 'operation-2', '2026-09-24T11:00:00Z')
    expect(saveStudies(store, '/workspace/a', { activeId: second.id, studies: [second] })).toBeNull()
    const resumed = readStudies(store, '/workspace/a')
    expect(resumed.warning).toBeNull()
    expect(resumed.library?.studies[0]?.attempts.map((item) => item.operationId))
      .toEqual(['operation-1', 'operation-2'])
    expect(resumed.library?.studies[0]?.horizon).toBe('medium')
    expect(readStudies(store, '/workspace/b').library).toBeNull()
  })

  it('does not duplicate a retried operation reference', () => {
    const study = addAttempt(emptyStudy('study-1'), 'operation-1', '2026-09-24T10:00:00Z')
    expect(addAttempt(study, 'operation-1', '2026-09-24T10:01:00Z').attempts).toHaveLength(1)
  })

  it('preserves malformed and future-version storage instead of replacing it', () => {
    const store = storage()
    const key = studyStorageKey('/workspace/a')
    for (const raw of ['{broken', '{"version":2,"studies":[]}', '{"version":1,"activeId":"x","studies":[{}]}']) {
      store.setItem(key, raw)
      expect(readStudies(store, '/workspace/a').warning).toBeTruthy()
      expect(saveStudies(store, '/workspace/a', { activeId: 'new', studies: [emptyStudy('new')] })).toBeTruthy()
      expect(store.getItem(key)).toBe(raw)
    }
  })

  it('reports unavailable storage without preventing in-memory research', () => {
    const store = { getItem: () => { throw new Error('blocked') }, setItem: () => { throw new Error('full') } }
    expect(readStudies(store, '/workspace/a').warning).toBeTruthy()
    expect(saveStudies(store, '/workspace/a', { activeId: 'new', studies: [emptyStudy('new')] })).toBeTruthy()
  })

  it('rejects unvalidated asset records and dangling active study IDs', () => {
    const store = storage()
    store.setItem(studyStorageKey('a'), JSON.stringify({ version: 1, activeId: 'missing', studies: [emptyStudy('x')] }))
    expect(readStudies(store, 'a').warning).toBeTruthy()
    store.setItem(studyStorageKey('a'), JSON.stringify({ version: 1, activeId: 'x', studies: [{ ...emptyStudy('x'), assetA: { symbol: 'W' } }] }))
    expect(readStudies(store, 'a').warning).toBeTruthy()
  })
})
