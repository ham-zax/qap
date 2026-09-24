import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import type { QapApiClient } from '../../api/client'
import { createQapQueries } from '../../api/queries'
import type { WorkspaceStatusDto } from '../../api/types'
import { ExperimentLab } from './ExperimentLab'
import { pairDraft, runnableSupport } from './researchStudy.test-fixtures'

const workspace: WorkspaceStatusDto = {
  schema_version: 'qap.api.workspace_status.v1', workspace_mode: 'local_market', workspace_root: '/lab-test',
  market_data_status: 'not_prepared', market_data_catalog_updated_at: null,
  product_maintenance_status: 'idle', current_evidence_collector_status: 'not_running',
}
const productContext = {
  schema_version: 'qap.api.research-recipe-product-context.v1' as const,
  capability_catalog_version: 'test', default_recipe_version: 'test',
  default_draft: pairDraft, capabilities: [],
}

describe('custom experiment launch', () => {
  it('freezes editable settings while support is checked and the checked recipe starts', async () => {
    let resolve!: (value: { support: typeof runnableSupport; recipe: typeof pairDraft }) => void
    const check = vi.fn().mockReturnValue(new Promise((done) => { resolve = done }))
    const run = vi.fn().mockResolvedValue({ operation_id: 'lab-op' })
    const api = {
      getResearchUniverse: vi.fn().mockResolvedValue({ assets: [], identity_reviews: [] }),
      getResearchRecipeProductContext: vi.fn().mockResolvedValue(productContext),
      checkResearchRecipeSupport: check, runResearchRecipe: run,
      getOperation: vi.fn().mockResolvedValue({ operation_id: 'lab-op', status: 'running', result: null }),
    } as unknown as QapApiClient
    const cache = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })
    render(<QueryClientProvider client={cache}><ExperimentLab apiClient={api} queries={createQapQueries(api)} workspace={workspace} /></QueryClientProvider>)
    const user = userEvent.setup()
    await user.click(await screen.findByRole('button', { name: 'Run experiment' }))
    await waitFor(() => expect(check).toHaveBeenCalledTimes(1))
    expect(screen.getByRole('combobox', { name: 'Research object' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Add declared variant' })).toBeDisabled()
    resolve({ support: runnableSupport, recipe: pairDraft })
    await waitFor(() => expect(run).toHaveBeenCalledTimes(1))
    expect(run).toHaveBeenCalledWith({ schema_version: 'qap.api.research-recipe-run-request.v1', recipe: pairDraft })
  })

  it('does not launch a checked recipe after a background context refresh replaces its draft', async () => {
    let resolve!: (value: { support: typeof runnableSupport; recipe: typeof pairDraft }) => void
    const check = vi.fn().mockReturnValue(new Promise((done) => { resolve = done }))
    const run = vi.fn().mockResolvedValue({ operation_id: 'stale-op' })
    const api = {
      getResearchUniverse: vi.fn().mockResolvedValue({ assets: [], identity_reviews: [] }),
      getResearchRecipeProductContext: vi.fn().mockResolvedValue(productContext),
      checkResearchRecipeSupport: check, runResearchRecipe: run,
    } as unknown as QapApiClient
    const queries = createQapQueries(api)
    const cache = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })
    render(<QueryClientProvider client={cache}><ExperimentLab apiClient={api} queries={queries} workspace={workspace} /></QueryClientProvider>)
    const user = userEvent.setup()
    await user.click(await screen.findByRole('button', { name: 'Run experiment' }))
    await waitFor(() => expect(check).toHaveBeenCalledTimes(1))
    const refreshed = { ...pairDraft, research_family_id: 'new-current-recipe' }
    cache.setQueryData(queries.researchRecipeProductContext({ researchObject: 'pair', horizon: 'short' }).queryKey,
      { ...productContext, default_draft: refreshed })
    await waitFor(() => expect(screen.getByText(/new-current-recipe/)).toBeInTheDocument())
    resolve({ support: runnableSupport, recipe: pairDraft })
    await waitFor(() => expect(screen.getByText(/settings changed while support was checked/i)).toBeInTheDocument())
    expect(run).not.toHaveBeenCalled()
  })
})
