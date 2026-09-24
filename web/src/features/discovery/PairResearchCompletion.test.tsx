import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import type { QapApiClient } from '../../api/client'
import { createQapQueries } from '../../api/queries'
import { PairResearchCompletion } from './PairResearchCompletion'

// Only fields consumed by this presentation are needed at the mocked API boundary.
const experiment = {
  run_id: 'run-a',
  manifest: {
    basket: ['W', 'PIXEL'], data_window: { start: '2026-06-01T00:00:00Z', end: '2026-09-01T00:00:00Z' },
    starting_quantities: { W: '100', PIXEL: '100' },
    relationship: { component_id: 'rolling_log_ratio_zscore', config: { window_bars: 180 } },
    policy: { component_id: 'relationship_target', config: {} },
    execution: { mode: 'multi_asset_bridge', bridge_asset: 'USDT', numeraire_asset: 'USDT', fee_bps: '10', slippage_bps: '5' },
  },
  result: {
    status: 'negative', data_role: 'development', final_oos_consumed: false,
    strategy_vs_hodl: '0.012', strategy_vs_primary_control: '-0.0042',
    primary_incremental_benchmark: 'band-control', success_threshold: '0',
    maximum_relative_drawdown_vs_hodl: '0.031',
    roles: [
      { role: 'strategy', terminal_value: '1012', fill_count: 3, fees_value: '2', slippage_value: '1' },
      { role: 'hodl', terminal_value: '1000', fill_count: 0 },
      { role: 'control:band-control', terminal_value: '1016.2683', fill_count: 2 },
    ],
  },
  provenance: { manifest_sha256: 'b'.repeat(64), data_fingerprints: [] },
}

function mount(overrides: Partial<QapApiClient> = {}) {
  const client = {
    getExperiment: vi.fn().mockResolvedValue(experiment),
    getPortfolioPerformance: vi.fn().mockRejectedValue(new Error('Chart unavailable')),
    getResearchRecipeRunLineage: vi.fn().mockResolvedValue({ matches: [] }),
    ...overrides,
  } as unknown as QapApiClient
  const cache = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(<QueryClientProvider client={cache}><PairResearchCompletion queries={createQapQueries(client)}
    runIds={['run-a']} operationId="op-a" compilationSha256="compilation-a" /></QueryClientProvider>)
  return client
}

describe('pair research conclusions', () => {
  it('retains negative control evidence despite a positive HODL comparison and a chart failure', async () => {
    mount()
    const conclusion = await screen.findByRole('region', { name: 'Research conclusion' })
    expect(conclusion).toHaveTextContent('Underperformed Simple rebalancing by 0.42%')
    expect(conclusion).toHaveTextContent('test completed successfully, but the strategy did not meet')
    expect(screen.getByText('+1.20%')).toHaveAttribute('data-exact', '0.012')
    expect(screen.getByText('−0.42%')).toHaveAttribute('data-exact', '-0.0042')
    const table = screen.getByRole('table', { name: /Ending wealth after modeled costs/ })
    expect(within(table).getByText('1,012')).toHaveAttribute('data-exact', '1012')
    expect(await screen.findByText(/Comparison chart unavailable/)).toBeInTheDocument()
    expect(screen.queryByText('Positive evidence')).not.toBeInTheDocument()
  })

  it('keeps hashes behind disclosure and requests additional lineage only on demand', async () => {
    const client = mount()
    const hash = await screen.findByText('b'.repeat(64))
    expect(hash.closest('details')).not.toHaveAttribute('open')
    expect(client.getResearchRecipeRunLineage).not.toHaveBeenCalled()
    await userEvent.setup().click(screen.getByText('Reproducibility details'))
    expect(hash.closest('details')).toHaveAttribute('open')
    expect(client.getResearchRecipeRunLineage).toHaveBeenCalledWith('run-a')
  })

  it('shows a consumed holdout explicitly without presenting it as untouched', async () => {
    mount({ getExperiment: vi.fn().mockResolvedValue({ ...experiment,
      result: { ...experiment.result, data_role: 'final_oos', final_oos_consumed: true },
    }) })
    expect(await screen.findByText(/that holdout is now consumed/)).toBeInTheDocument()
    expect(screen.getByText(/Final OOS · consumed/)).toBeInTheDocument()
  })

  it('keeps a failed result read recoverable', async () => {
    const getExperiment = vi.fn().mockRejectedValueOnce(new Error('Temporary read failure')).mockResolvedValue(experiment)
    mount({ getExperiment })
    await userEvent.setup().click(await screen.findByRole('button', { name: 'Retry loading result' }))
    expect(await screen.findByRole('region', { name: 'Research conclusion' })).toBeInTheDocument()
    expect(getExperiment).toHaveBeenCalledTimes(2)
  })
})
