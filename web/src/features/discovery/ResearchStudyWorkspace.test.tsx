import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { QapApiClient } from '../../api/client'
import { createQapQueries } from '../../api/queries'
import type { ResearchUniverseDto, WorkspaceStatusDto } from '../../api/types'
import { ResearchStudyWorkspace } from './ResearchStudyWorkspace'
import { emptyStudy, saveStudies, studyStorageKey } from './researchStudies'
import { pairContext, pairDraft, runnableSupport } from './researchStudy.test-fixtures'

const workspace: WorkspaceStatusDto = {
  schema_version: 'qap.api.workspace_status.v1', workspace_mode: 'local_market', workspace_root: '/study-test',
  market_data_status: 'not_prepared', market_data_catalog_updated_at: null,
  product_maintenance_status: 'idle', current_evidence_collector_status: 'not_running',
}
const universe: ResearchUniverseDto = {
  schema_version: 'qap.api.research_universe.v1', directory_status: 'observed', directory_id: 'directory',
  directory_observed_at: '2026-09-24T00:00:00Z', sources: [], identity_reviews: [],
  assets: ['W', 'PIXEL'].map((asset) => ({
    canonical_asset_id: asset, approved: true, identity_state: 'resolved', identity_reason: 'resolved',
    asset_identity_version: `${asset}-verified`, data_state: 'needs_data',
    venues: [{ venue: 'gate', venue_symbol: `${asset}_USDT`, status: 'trading', trading: true }],
  })),
}

function mount(overrides: Partial<QapApiClient> = {}) {
  const client = { getResearchUniverse: vi.fn().mockResolvedValue(universe), ...overrides } as unknown as QapApiClient
  const queries = createQapQueries(client)
  const cache = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })
  const rendered = render(<QueryClientProvider client={cache}><ResearchStudyWorkspace apiClient={client} queries={queries} workspace={workspace} /></QueryClientProvider>)
  return { ...rendered, client, cache }
}

async function selectPair(user: ReturnType<typeof userEvent.setup>) {
  await user.type(await screen.findByRole('textbox', { name: 'First asset' }), 'W')
  await user.click(screen.getByRole('button', { name: /W\s*ready identity/ }))
  await user.type(screen.getByRole('textbox', { name: 'Second asset' }), 'PIXEL')
  await user.click(screen.getByRole('button', { name: /PIXEL\s*ready identity/ }))
}

beforeEach(() => { window.localStorage.clear() })

describe('research study continuity', () => {
  it('restores the named question and period after leaving the page', async () => {
    const user = userEvent.setup()
    const first = mount()
    await selectPair(user)
    await user.type(screen.getByRole('textbox', { name: 'Study name' }), 'My relationship question')
    await user.selectOptions(screen.getByRole('combobox', { name: 'Historical test period' }), 'swing')
    first.unmount()
    mount()
    expect(await screen.findByRole('button', { name: 'Study this pair' })).toBeEnabled()
    expect(screen.getByRole('textbox', { name: 'Study name' })).toHaveValue('My relationship question')
    expect(screen.getByRole('combobox', { name: 'Historical test period' })).toHaveValue('swing')
  })

  it('keeps separate studies and their questions selectable', async () => {
    const user = userEvent.setup()
    mount()
    await selectPair(user)
    await user.click(screen.getByRole('button', { name: 'New study' }))
    expect(screen.getByRole('textbox', { name: 'First asset' })).toHaveValue('')
    const sidebar = screen.getByRole('complementary', { name: 'Saved research studies' })
    await user.click(within(sidebar).getByRole('button', { name: /W \/ PIXEL/ }))
    expect(screen.getByRole('button', { name: 'Study this pair' })).toBeEnabled()
  })

  it('does not replace an active question or overwrite edits from another tab', async () => {
    const user = userEvent.setup()
    mount()
    await selectPair(user)
    const key = studyStorageKey('local_market:/study-test')
    const other = { ...emptyStudy('other-tab'), name: 'Other tab question' }
    const raw = JSON.stringify({ version: 1, activeId: other.id, studies: [other] })
    window.localStorage.setItem(key, raw)
    act(() => { window.dispatchEvent(new StorageEvent('storage', { key })) })
    expect(screen.getByRole('alert')).toHaveTextContent('changed in another tab')
    expect(screen.getByRole('button', { name: 'Study this pair' })).toBeEnabled()
    await user.type(screen.getByRole('textbox', { name: 'Study name' }), 'Current question')
    expect(window.localStorage.getItem(key)).toBe(raw)
  })

  it('reloads an attempt from the backend without requiring another pair study', async () => {
    const saved = { ...emptyStudy('saved'), name: 'Prior study', attempts: [{ operationId: 'op-old', createdAt: '2026-09-24T00:00:00Z', question: 'W / PIXEL · 90 days' }] }
    saveStudies(window.localStorage, 'local_market:/study-test', { activeId: saved.id, studies: [saved] })
    const getOperation = vi.fn().mockResolvedValue({ operation_id: 'op-old', status: 'running', result: null })
    mount({ getOperation })
    expect(await screen.findByRole('heading', { name: 'Backtest in progress' })).toBeInTheDocument()
    expect(getOperation).toHaveBeenCalledWith('op-old')
  })

  it('does not trust saved asset approval when the backend has revoked it', async () => {
    const user = userEvent.setup()
    const initial = mount()
    await selectPair(user)
    initial.unmount()
    mount({ getResearchUniverse: vi.fn().mockResolvedValue({ ...universe, assets: universe.assets.map((asset) => ({ ...asset, approved: false })) }) })
    expect(await screen.findByRole('button', { name: 'Allow W in research' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Study this pair' })).not.toBeInTheDocument()
  })

  it('offers quote identity recovery within the saved question', async () => {
    const user = userEvent.setup()
    mount({ getResearchUniverse: vi.fn().mockResolvedValue({ ...universe,
      assets: universe.assets.map((asset) => ({ ...asset, venues: [] })),
      identity_reviews: [{ venue: 'gate', venue_asset_code: 'USDT', venue_symbols: ['W_USDT', 'PIXEL_USDT'], reason: 'mapping_unavailable' }],
    }) })
    await selectPair(user)
    expect(screen.getByRole('heading', { name: 'Finish price-data setup' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Confirm USDT identity' })).toBeDisabled()
  })

  it('requires explicit quote identity evidence and locks setup while saving it', async () => {
    let resolve!: (value: ResearchUniverseDto) => void
    const pending = new Promise<ResearchUniverseDto>((done) => { resolve = done })
    const save = vi.fn().mockReturnValue(pending)
    const user = userEvent.setup()
    mount({ setResearchUniverseIdentityMapping: save,
      getResearchUniverse: vi.fn().mockResolvedValue({ ...universe,
        assets: universe.assets.map((asset) => ({ ...asset, venues: [] })),
        identity_reviews: [{ venue: 'gate', venue_asset_code: 'USDT', venue_symbols: ['W_USDT', 'PIXEL_USDT'] }],
      }) })
    await selectPair(user)
    await user.type(screen.getByRole('textbox', { name: 'Verified asset identifier' }), 'USDT')
    await user.type(screen.getByRole('textbox', { name: 'Verified identity reference' }), 'verified-record-v1')
    await user.click(screen.getByRole('button', { name: 'Confirm USDT identity' }))
    expect(save).toHaveBeenCalledWith({ venue: 'gate', venue_asset_code: 'USDT', canonical_asset_id: 'USDT', asset_identity_version: 'verified-record-v1' })
    await waitFor(() => expect(screen.getByRole('button', { name: 'New study' })).toBeDisabled())
    expect(screen.getByRole('textbox', { name: 'Verified identity reference' })).toBeDisabled()
    resolve(universe)
    await waitFor(() => expect(screen.getByRole('button', { name: 'Study this pair' })).toBeEnabled())
    expect(screen.queryByRole('heading', { name: 'Finish price-data setup' })).not.toBeInTheDocument()
  })

  it('preserves unreadable stored data and explains session-only operation', async () => {
    const key = studyStorageKey('local_market:/study-test')
    window.localStorage.setItem(key, '{broken')
    const user = userEvent.setup()
    mount()
    expect(screen.getByRole('alert')).toHaveTextContent('Existing saved data has been left untouched')
    await selectPair(user)
    expect(window.localStorage.getItem(key)).toBe('{broken')
  })

  it('locks the question during preparation and reports a recoverable error', async () => {
    let reject!: (error: Error) => void
    const pending = new Promise<never>((_, fail) => { reject = fail })
    const user = userEvent.setup()
    mount({ getProductPairStudyContext: vi.fn().mockReturnValue(pending) })
    await selectPair(user)
    await user.click(screen.getByRole('button', { name: 'Study this pair' }))
    expect(screen.getByRole('combobox', { name: 'Historical test period' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'New study' })).toBeDisabled()
    reject(new Error('Price source unavailable'))
    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('Price source unavailable'))
    expect(screen.getByRole('button', { name: 'Study this pair' })).toBeEnabled()
  })

  it('retains relationship evidence when downstream backtest preparation fails', async () => {
    const user = userEvent.setup()
    mount({
      getProductPairStudyContext: vi.fn().mockResolvedValue(pairContext),
      getProductPairStudySeries: vi.fn().mockResolvedValue(null),
      getResearchRecipeProductContext: vi.fn().mockRejectedValue(new Error('Economic data unavailable')),
    })
    await selectPair(user)
    await user.click(screen.getByRole('button', { name: 'Study this pair' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Economic data unavailable')
    expect(screen.getByRole('heading', { name: /W\/PIXEL · Medium-term/ })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Rolling log-ratio z-score' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Run backtest' })).not.toBeInTheDocument()
  })

  it('requires a new check after an edit, runs its returned recipe, and resumes the attempt', async () => {
    const user = userEvent.setup()
    const checkedRecipe = { ...pairDraft, recipe_sha256: 'backend-checked' }
    const check = vi.fn().mockResolvedValue({ support: runnableSupport, recipe: checkedRecipe })
    const run = vi.fn().mockResolvedValue({ operation_id: 'op-new' })
    const api = {
      getProductPairStudyContext: vi.fn().mockResolvedValue(pairContext),
      getProductPairStudySeries: vi.fn().mockResolvedValue(null),
      getResearchRecipeProductContext: vi.fn().mockResolvedValue({ default_draft: pairDraft, capabilities: [] }),
      checkResearchRecipeSupport: check, runResearchRecipe: run,
      getOperation: vi.fn().mockResolvedValue({ operation_id: 'op-new', status: 'running', result: null }),
    }
    const view = mount(api)
    await selectPair(user)
    await user.click(screen.getByRole('button', { name: 'Study this pair' }))
    expect(await screen.findByRole('button', { name: 'Run backtest' })).toBeEnabled()
    await user.click(screen.getByText('Adjust the experiment'))
    const entry = screen.getByRole('spinbutton', { name: /Entry threshold/ })
    await user.clear(entry)
    await user.type(entry, '2')
    expect(screen.queryByRole('button', { name: 'Run backtest' })).not.toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Check backtest settings' }))
    expect(check.mock.lastCall?.[0].recipe.variants.every((variant: typeof pairDraft.variants[number]) => variant.decision_rule.config.enter_threshold === '2')).toBe(true)
    await user.click(await screen.findByRole('button', { name: 'Run backtest' }))
    expect(run).toHaveBeenCalledWith({ schema_version: 'qap.api.research-recipe-run-request.v1', recipe: checkedRecipe })
    expect(await screen.findByRole('heading', { name: 'Backtest in progress' })).toBeInTheDocument()
    view.unmount()
    mount(api)
    expect(await screen.findByRole('heading', { name: 'Backtest in progress' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Attempt 1 · W \/ PIXEL · 90 days/ })).toBeInTheDocument()
    expect(check).toHaveBeenCalledTimes(2)
    await user.click(screen.getByRole('button', { name: 'Study this pair' }))
    await waitFor(() => expect(check).toHaveBeenCalledTimes(3))
    expect(check.mock.lastCall?.[0].recipe.variants[0].decision_rule.config.enter_threshold).toBe('2')
  })

  it('records a delayed start without losing newer edits after leaving and returning', async () => {
    let resolve!: (value: { operation_id: string }) => void
    const pending = new Promise<{ operation_id: string }>((done) => { resolve = done })
    const user = userEvent.setup()
    const first = mount({
      getProductPairStudyContext: vi.fn().mockResolvedValue(pairContext),
      getProductPairStudySeries: vi.fn().mockResolvedValue(null),
      getResearchRecipeProductContext: vi.fn().mockResolvedValue({ default_draft: pairDraft, capabilities: [] }),
      checkResearchRecipeSupport: vi.fn().mockResolvedValue({ support: runnableSupport, recipe: pairDraft }),
      runResearchRecipe: vi.fn().mockReturnValue(pending),
    })
    await selectPair(user)
    await user.click(screen.getByRole('button', { name: 'Study this pair' }))
    await user.click(await screen.findByRole('button', { name: 'Run backtest' }))
    first.unmount()
    const returned = mount()
    await user.click(screen.getByRole('button', { name: 'New study' }))
    await user.type(screen.getByRole('textbox', { name: 'Study name' }), 'Next question')
    resolve({ operation_id: 'op-delayed' })
    const key = studyStorageKey('local_market:/study-test')
    await waitFor(() => expect(window.localStorage.getItem(key)).toContain('op-delayed'))
    await user.type(screen.getByRole('textbox', { name: 'Study name' }), ' v2')
    returned.unmount()
    mount()
    expect(screen.getByRole('textbox', { name: 'Study name' })).toHaveValue('Next question v2')
    const saved = JSON.parse(window.localStorage.getItem(key)!)
    expect(saved.studies[0].attempts).toEqual([expect.objectContaining({ operationId: 'op-delayed', question: 'W / PIXEL · 90 days' })])
  })
})
