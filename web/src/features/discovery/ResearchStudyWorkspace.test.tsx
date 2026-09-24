import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { QapApiClient } from '../../api/client'
import { createQapQueries } from '../../api/queries'
import type { ResearchUniverseDto, WorkspaceStatusDto } from '../../api/types'
import { ResearchStudyWorkspace } from './ResearchStudyWorkspace'
import { researchAssetOptions } from './researchAssetSearch'
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
  it('starts with relationship evidence and does not prepare an economic recipe', async () => {
    const user = userEvent.setup()
    const recipe = vi.fn()
    mount({ getProductPairStudyContext: vi.fn().mockResolvedValue(pairContext),
      getProductPairStudySeries: vi.fn().mockResolvedValue(null), getResearchRecipeProductContext: recipe })
    await selectPair(user)
    await user.click(screen.getByRole('button', { name: 'Start research' }))
    expect(await screen.findByRole('heading', { name: 'What the relationship shows' })).toBeInTheDocument()
    expect(recipe).not.toHaveBeenCalled()
    expect(screen.getByRole('button', { name: 'Backtest this pair' })).toBeEnabled()
  })

  it('starts a backtest in one click when that mode is chosen', async () => {
    const user = userEvent.setup()
    const run = vi.fn().mockResolvedValue({ operation_id: 'op-new' })
    mount({ getProductPairStudyContext: vi.fn().mockResolvedValue(pairContext),
      getProductPairStudySeries: vi.fn().mockResolvedValue(null),
      getResearchRecipeProductContext: vi.fn().mockResolvedValue({ default_draft: pairDraft, capabilities: [] }),
      checkResearchRecipeSupport: vi.fn().mockResolvedValue({ support: runnableSupport, recipe: pairDraft }),
      runResearchRecipe: run,
      getOperation: vi.fn().mockResolvedValue({ operation_id: 'op-new', status: 'running', result: null }),
    })
    await selectPair(user)
    await user.click(screen.getByRole('radio', { name: /Backtest comparison/ }))
    expect(run).not.toHaveBeenCalled()
    await user.click(screen.getByRole('button', { name: 'Start research' }))
    await waitFor(() => expect(run).toHaveBeenCalledTimes(1))
    expect(await screen.findByRole('heading', { name: 'Backtest in progress' })).toBeInTheDocument()
  })
  it('restores the named question and period after leaving the page', async () => {
    const user = userEvent.setup()
    const first = mount()
    await selectPair(user)
    await user.click(screen.getByText(/Saved studies ·/))
    await user.type(screen.getByRole('textbox', { name: /Optional study name/ }), 'My relationship question')
    await user.click(screen.getByRole('radio', { name: /180 days/ }))
    first.unmount()
    mount()
    expect(await screen.findByRole('button', { name: 'Start research' })).toBeEnabled()
    await user.click(screen.getByText(/Saved studies ·/))
    expect(screen.getByRole('textbox', { name: /Optional study name/ })).toHaveValue('My relationship question')
    expect(screen.getByRole('radio', { name: /180 days/ })).toBeChecked()
  })

  it('keeps separate studies and their questions selectable', async () => {
    const user = userEvent.setup()
    mount()
    await selectPair(user)
    await user.click(screen.getByText(/Saved studies ·/))
    await user.click(screen.getByRole('button', { name: 'New study' }))
    expect(screen.getByRole('textbox', { name: 'First asset' })).toHaveValue('')
    await user.click(screen.getByRole('button', { name: /W \/ PIXEL/ }))
    expect(screen.getByRole('button', { name: 'Start research' })).toBeEnabled()
  })

  it('does not replace an active question or overwrite edits from another tab', async () => {
    const user = userEvent.setup()
    mount()
    await selectPair(user)
    const key = studyStorageKey('local_market:/study-test')
    const other = { ...emptyStudy('other-tab'), name: 'Other tab question' }
    const raw = JSON.stringify({ version: 2, activeId: other.id, studies: [other] })
    window.localStorage.setItem(key, raw)
    act(() => { window.dispatchEvent(new StorageEvent('storage', { key })) })
    expect(screen.getByRole('alert')).toHaveTextContent('changed in another tab')
    expect(screen.getByRole('button', { name: 'Start research' })).toBeEnabled()
    await user.click(screen.getByText(/Saved studies ·/))
    await user.type(screen.getByRole('textbox', { name: /Optional study name/ }), 'Current question')
    expect(window.localStorage.getItem(key)).toBe(raw)
  })

  it('reloads an attempt from the backend without requiring another pair study', async () => {
    const saved = { ...emptyStudy('saved'), mode: 'backtest_comparison' as const, name: 'Prior study', attempts: [{ operationId: 'op-old', createdAt: '2026-09-24T00:00:00Z', question: 'W / PIXEL · 90 days' }] }
    saveStudies(window.localStorage, 'local_market:/study-test', { activeId: saved.id, studies: [saved] })
    const getOperation = vi.fn().mockResolvedValue({ operation_id: 'op-old', status: 'running', result: null })
    mount({ getOperation })
    expect(await screen.findByRole('heading', { name: 'Backtest in progress' })).toBeInTheDocument()
    expect(getOperation).toHaveBeenCalledWith('op-old')
  })

  it('recovers next-run settings for a reopened completed result without launching another run', async () => {
    const [assetA, assetB] = researchAssetOptions(universe)
    const saved = { ...emptyStudy('completed'), mode: 'backtest_comparison' as const,
      assetA, assetB, attempts: [{ operationId: 'op-done', createdAt: '2026-09-24T00:00:00Z',
        question: 'W / PIXEL · 90 days · Backtest comparison' }] }
    saveStudies(window.localStorage, 'local_market:/study-test', { activeId: saved.id, studies: [saved] })
    const settings = vi.fn().mockRejectedValueOnce(new Error('Temporary settings failure'))
      .mockResolvedValue({ default_draft: pairDraft, capabilities: [] })
    const run = vi.fn()
    mount({ getOperation: vi.fn().mockResolvedValue({ operation_id: 'op-done', status: 'completed',
      result: { run_ids: ['run-a'], compilation_sha256: 'comp-a' } }),
    getExperiment: vi.fn().mockRejectedValue(new Error('Result read unavailable')),
    getResearchRecipeProductContext: settings, runResearchRecipe: run })
    expect(await screen.findByRole('heading', { name: 'Backtest complete' })).toBeInTheDocument()
    expect(await screen.findByText(/Next-run settings unavailable/)).toBeInTheDocument()
    await userEvent.setup().click(screen.getByRole('button', { name: 'Retry loading settings' }))
    const link = await screen.findByRole('link', { name: 'Change settings' })
    expect(link).toHaveAttribute('href', '#comparison-settings')
    await userEvent.setup().click(link)
    expect(document.getElementById('comparison-settings')).toHaveAttribute('open')
    expect(run).not.toHaveBeenCalled()
  })

  it('does not trust saved asset approval when the backend has revoked it', async () => {
    const user = userEvent.setup()
    const initial = mount()
    await selectPair(user)
    initial.unmount()
    mount({ getResearchUniverse: vi.fn().mockResolvedValue({ ...universe, assets: universe.assets.map((asset) => ({ ...asset, approved: false })) }) })
    expect(await screen.findByRole('button', { name: 'Allow W in research' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Start research' })).not.toBeInTheDocument()
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
    await user.click(screen.getByText(/Saved studies ·/))
    await waitFor(() => expect(screen.getByRole('button', { name: 'New study' })).toBeDisabled())
    expect(screen.getByRole('textbox', { name: 'Verified identity reference' })).toBeDisabled()
    resolve(universe)
    await waitFor(() => expect(screen.getByRole('button', { name: 'Start research' })).toBeEnabled())
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
    await user.click(screen.getByRole('button', { name: 'Start research' }))
    expect(screen.getByRole('radio', { name: /90 days/ })).toBeDisabled()
    await user.click(screen.getByText(/Saved studies ·/))
    expect(screen.getByRole('button', { name: 'New study' })).toBeDisabled()
    reject(new Error('Price source unavailable'))
    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('Price source unavailable'))
    expect(screen.getByRole('button', { name: 'Start research' })).toBeEnabled()
  })

  it('retains relationship evidence when downstream backtest preparation fails', async () => {
    const user = userEvent.setup()
    mount({
      getProductPairStudyContext: vi.fn().mockResolvedValue(pairContext),
      getProductPairStudySeries: vi.fn().mockResolvedValue(null),
      getResearchRecipeProductContext: vi.fn().mockRejectedValue(new Error('Economic data unavailable')),
    })
    await selectPair(user)
    await user.click(screen.getByRole('radio', { name: /Backtest comparison/ }))
    await user.click(screen.getByRole('button', { name: 'Start research' }))
    expect(await screen.findByText(/Economic data unavailable/)).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'What the relationship shows' })).toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: 'Backtest in progress' })).not.toBeInTheDocument()
  })

  it('does not launch a recipe declared against a newer data snapshot than the displayed relationship', async () => {
    const user = userEvent.setup()
    const run = vi.fn().mockResolvedValue({ operation_id: 'wrong-snapshot' })
    const changedRecipe = { ...pairDraft, data: { ...pairDraft.data,
      evaluation_window: { ...pairDraft.data.evaluation_window!, end: '2026-09-02T00:00:00Z' } } }
    mount({ getProductPairStudyContext: vi.fn().mockResolvedValue(pairContext),
      getProductPairStudySeries: vi.fn().mockRejectedValue(new Error('Chart unavailable')),
      getResearchRecipeProductContext: vi.fn().mockResolvedValue({ default_draft: changedRecipe, capabilities: [] }),
      checkResearchRecipeSupport: vi.fn().mockResolvedValue({ support: runnableSupport, recipe: changedRecipe }),
      runResearchRecipe: run })
    await selectPair(user)
    await user.click(screen.getByRole('radio', { name: /Backtest comparison/ }))
    await user.click(screen.getByRole('button', { name: 'Start research' }))
    expect(await screen.findByText(/Comparison data changed while preparing this study/)).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'What the relationship shows' })).toBeInTheDocument()
    expect(run).not.toHaveBeenCalled()
  })

  it('explains workspace-wide USDT replay authority before any grant', async () => {
    const user = userEvent.setup()
    const grant = vi.fn().mockResolvedValue({ scope: 'research_replay_only' })
    const needsAuthority = { ...pairContext, economic_expression: { ...pairContext.economic_expression,
      bridge_status: 'needs_transient_authority' as const, default_recipe_declarable: false } }
    mount({ getProductPairStudyContext: vi.fn().mockResolvedValue(needsAuthority),
      getProductPairStudySeries: vi.fn().mockRejectedValue(new Error('Chart unavailable')),
      grantProductPairStudyTransientUsdtAuthority: grant })
    await selectPair(user)
    await user.click(screen.getByRole('radio', { name: /Backtest comparison/ }))
    await user.click(screen.getByRole('button', { name: 'Start research' }))
    expect(await screen.findByText(/permission applies to the current Local Market workspace and verified USDT identity, not just this study/i)).toBeInTheDocument()
    expect(grant).not.toHaveBeenCalled()
    expect(screen.getByRole('button', { name: /Allow workspace bridge replay and continue/ })).toBeEnabled()
  })

  it('distinguishes a changed backtest lookback from the descriptive relationship window', async () => {
    const [assetA, assetB] = researchAssetOptions(universe)
    const saved = { ...emptyStudy('different-windows'), mode: 'backtest_comparison' as const,
      assetA, assetB, parameters: { window_bars: '60', min_observations: '55' } }
    saveStudies(window.localStorage, 'local_market:/study-test', { activeId: saved.id, studies: [saved] })
    mount({ getProductPairStudyContext: vi.fn().mockResolvedValue(pairContext),
      getProductPairStudySeries: vi.fn().mockRejectedValue(new Error('Chart unavailable')),
      getResearchRecipeProductContext: vi.fn().mockResolvedValue({ default_draft: pairDraft, capabilities: [] }),
      checkResearchRecipeSupport: vi.fn().mockImplementation(async ({ recipe }) => ({ support: runnableSupport, recipe })),
      runResearchRecipe: vi.fn().mockResolvedValue({ operation_id: 'different-windows-op' }),
      getOperation: vi.fn().mockResolvedValue({ operation_id: 'different-windows-op', status: 'running', result: null }),
    })
    await userEvent.setup().click(await screen.findByRole('button', { name: 'Start research' }))
    expect(await screen.findByText(/Descriptive view: 180-bar window, 180 observations required/)).toBeInTheDocument()
    expect(screen.getByText(/Next backtest settings: 60-bar window, 55 observations required/)).toBeInTheDocument()
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
      getOperation: vi.fn().mockResolvedValue({ operation_id: 'op-new', status: 'completed', result: null }),
    }
    const view = mount(api)
    await selectPair(user)
    await user.click(screen.getByRole('radio', { name: /Backtest comparison/ }))
    await user.click(screen.getByRole('button', { name: 'Start research' }))
    await waitFor(() => expect(run).toHaveBeenCalledTimes(1))
    await user.click(screen.getByText('Advanced settings and assumptions'))
    const entry = screen.getByRole('spinbutton', { name: /Entry threshold/ })
    await user.clear(entry)
    await user.type(entry, '2')
    await user.click(screen.getByRole('button', { name: 'Start research' }))
    await waitFor(() => expect(check).toHaveBeenCalledTimes(2))
    expect(check.mock.lastCall?.[0].recipe.variants.every((variant: typeof pairDraft.variants[number]) => variant.decision_rule.config.enter_threshold === '2')).toBe(true)
    expect(run).toHaveBeenCalledWith({ schema_version: 'qap.api.research-recipe-run-request.v1', recipe: checkedRecipe })
    expect(await screen.findByRole('heading', { name: 'Backtest complete' })).toBeInTheDocument()
    view.unmount()
    mount(api)
    expect(await screen.findByRole('heading', { name: 'Backtest complete' })).toBeInTheDocument()
    expect(await screen.findByRole('heading', { name: 'Next run settings' })).toBeInTheDocument()
    expect(run).toHaveBeenCalledTimes(2)
    await user.click(screen.getByText(/Earlier runs/))
    expect(screen.getByRole('button', { name: /Run 1 · W \/ PIXEL · 90 days/ })).toBeInTheDocument()
    expect(check).toHaveBeenCalledTimes(2)
    await user.click(screen.getByRole('button', { name: 'Start research' }))
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
    await user.click(screen.getByRole('radio', { name: /Backtest comparison/ }))
    await user.click(screen.getByRole('button', { name: 'Start research' }))
    await waitFor(() => expect(first.client.runResearchRecipe).toHaveBeenCalled())
    first.unmount()
    const returned = mount()
    await user.click(screen.getByText(/Saved studies ·/))
    await user.click(screen.getByRole('button', { name: 'New study' }))
    await user.type(screen.getByRole('textbox', { name: /Optional study name/ }), 'Next question')
    resolve({ operation_id: 'op-delayed' })
    const key = studyStorageKey('local_market:/study-test')
    await waitFor(() => expect(window.localStorage.getItem(key)).toContain('op-delayed'))
    await user.type(screen.getByRole('textbox', { name: /Optional study name/ }), ' v2')
    returned.unmount()
    mount()
    await user.click(screen.getByText(/Saved studies ·/))
    expect(screen.getByRole('textbox', { name: /Optional study name/ })).toHaveValue('Next question v2')
    const saved = JSON.parse(window.localStorage.getItem(key)!)
    expect(saved.studies[0].attempts).toEqual([expect.objectContaining({ operationId: 'op-delayed', question: 'W / PIXEL · 90 days · Backtest comparison' })])
  })
})
