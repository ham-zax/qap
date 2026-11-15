import { afterEach, describe, expect, it, vi } from 'vitest'
import type { LabStudyCommand } from './labStudyApi'
import { computeLabStudy, getSavedLabStudy, listSavedLabStudies, pinLabStudy } from './labStudyApi'

const signal = new AbortController().signal

const command: LabStudyCommand = {
  coin_a: 'binance:BTC',
  coin_b: 'binance:ETH',
  bar: '15m',
  days: 180,
  band_lookback: 672,
  settings: { method: 'zscore', entry: 2.5 },
}

const blockedStudy = {
  study_id: 'study/blocked 1',
  created_at: '2026-10-24T00:00:00Z',
  pinned: false,
  result: {
    schema_version: 'qap.lab.study.v1',
    analysis: { data_through: '2026-10-23T23:00:00Z' },
    call: {
      status: 'execution_data_missing',
      headline: 'Blocked: execution evidence is missing',
      reason: 'Execution evidence is missing.',
      target_weight_a: null,
      rotation_fraction: null,
    },
    proof: {
      passes: false,
      data_role: 'validation',
      final_oos_used: false,
      validation_reused: false,
      limitations: ['Execution evidence is missing.'],
    },
  },
}

const savedPage = {
  studies: [
    {
      study_id: 'saved/one',
      created_at: '2026-10-24T01:00:00Z',
      pinned: true,
      coin_a: { id: 'binance:BTC', code: 'BTC', name: 'Bitcoin', identity_state: 'resolved' },
      coin_b: { id: 'binance:ETH', code: 'ETH', name: 'Ether', identity_state: 'resolved' },
      method: 'zscore',
      data_through: '2026-10-23T23:00:00Z',
      headline: 'Hold',
    },
  ],
  next_offset: 6,
}

function jsonResponse(value: unknown, status = 200): Response {
  return new Response(JSON.stringify(value), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

afterEach(() => {
  vi.unstubAllGlobals()
  vi.unstubAllEnvs()
})

describe('Lab study transport', () => {
  it('posts the unchanged command to the configured API prefix', async () => {
    vi.stubEnv('VITE_QAP_API_BASE_URL', 'https://api.example.test')
    const fetch = vi.fn(async () => jsonResponse(blockedStudy))
    vi.stubGlobal('fetch', fetch)

    const study = await computeLabStudy(command, signal)

    expect(fetch).toHaveBeenCalledWith('https://api.example.test/api/pair-rotation/studies', {
      signal,
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(command),
    })
    expect(study).toEqual(blockedStudy)
    expect(study.result.call.status).toBe('execution_data_missing')
    expect(study.result.proof.passes).toBe(false)
  })

  it('lists saved studies with default pagination and no request body', async () => {
    const fetch = vi.fn(async () => jsonResponse(savedPage))
    vi.stubGlobal('fetch', fetch)

    const page = await listSavedLabStudies(signal)

    expect(fetch).toHaveBeenCalledWith('/api/pair-rotation/studies?limit=25&offset=0', { signal })
    expect(page).toEqual(savedPage)
    expect(page.studies[0]?.study_id).toBe('saved/one')
    expect(page.studies[0]?.data_through).toBe('2026-10-23T23:00:00Z')
  })

  it('passes explicit pagination limits through the query string', async () => {
    const fetch = vi.fn(async () => jsonResponse(savedPage))
    vi.stubGlobal('fetch', fetch)

    await listSavedLabStudies(signal, { limit: 5, offset: 10 })

    expect(fetch).toHaveBeenCalledWith('/api/pair-rotation/studies?limit=5&offset=10', { signal })
  })

  it('reopens a saved study by an encoded identifier', async () => {
    const studyId = 'study/blocked 1?copy=1'
    const fetch = vi.fn(async () => jsonResponse(blockedStudy))
    vi.stubGlobal('fetch', fetch)

    const study = await getSavedLabStudy(studyId, signal)

    expect(fetch).toHaveBeenCalledWith(`/api/pair-rotation/studies/${encodeURIComponent(studyId)}`, { signal })
    expect(study).toEqual(blockedStudy)
    expect(study.study_id).toBe('study/blocked 1')
  })

  it('sends only the pin flag to the encoded pin route', async () => {
    const studyId = 'study/blocked 1'
    const fetch = vi.fn()
      .mockResolvedValueOnce(jsonResponse({ ...blockedStudy, pinned: true }))
      .mockResolvedValueOnce(jsonResponse({ ...blockedStudy, pinned: false }))
    vi.stubGlobal('fetch', fetch)

    const pinned = await pinLabStudy(studyId, true, signal)
    const unpinned = await pinLabStudy(studyId, false, signal)

    expect(fetch).toHaveBeenNthCalledWith(1, `/api/pair-rotation/studies/${encodeURIComponent(studyId)}/pin`, {
      signal,
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pinned: true }),
    })
    expect(fetch).toHaveBeenNthCalledWith(2, `/api/pair-rotation/studies/${encodeURIComponent(studyId)}/pin`, {
      signal,
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pinned: false }),
    })
    expect(pinned.pinned).toBe(true)
    expect(unpinned.pinned).toBe(false)
  })

  it('rejects a backend error envelope without inventing a fallback', async () => {
    const fetch = vi.fn(async () => jsonResponse({
      error: { code: 'lab_study_unavailable', message: 'Market data is not configured.' },
    }, 409))
    vi.stubGlobal('fetch', fetch)

    await expect(computeLabStudy(command, signal)).rejects.toThrow('Market data is not configured.')
  })

  it('propagates request failures without retrying', async () => {
    const failure = new TypeError('Failed to fetch')
    const fetch = vi.fn(async () => { throw failure })
    vi.stubGlobal('fetch', fetch)

    await expect(getSavedLabStudy('study-1', signal)).rejects.toBe(failure)
    expect(fetch).toHaveBeenCalledTimes(1)
  })

  it('propagates an aborted request signal', async () => {
    const controller = new AbortController()
    controller.abort()
    const fetch = vi.fn(async (_url: RequestInfo | URL, init?: RequestInit) => {
      if (init?.signal?.aborted) throw new DOMException('Aborted', 'AbortError')
      return jsonResponse(blockedStudy)
    })
    vi.stubGlobal('fetch', fetch)

    await expect(computeLabStudy(command, controller.signal)).rejects.toMatchObject({ name: 'AbortError' })
    expect(fetch).toHaveBeenCalledWith('/api/pair-rotation/studies', expect.objectContaining({ signal: controller.signal }))
  })
})
