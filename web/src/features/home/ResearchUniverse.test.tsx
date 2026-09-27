import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type { QapApiClient } from '../../api/client'
import type { ResearchUniverseDto, WorkspaceStatusDto } from '../../api/types'
import { ResearchUniverse } from './ResearchUniverse'

const workspace: WorkspaceStatusDto = {
  schema_version: 'qap.api.workspace_status.v1', workspace_mode: 'local_market',
  workspace_root: '/test', market_data_status: 'catalog_detected',
  market_data_catalog_updated_at: null, product_maintenance_status: 'idle',
  current_evidence_collector_status: 'not_running',
}

const universe: ResearchUniverseDto = {
  schema_version: 'qap.api.research_universe.v1', directory_status: 'observed',
  directory_id: 'directory', directory_observed_at: '2026-09-25T00:00:00Z',
  sources: [], identity_reviews: [],
  assets: [{ canonical_asset_id: 'BTC', approved: true, identity_state: 'resolved',
    identity_reason: 'resolved', asset_identity_version: 'operator-record-1',
    data_state: 'needs_data', venues: [{ venue: 'binance', venue_symbol: 'WUSDT',
      venue_asset_code: 'W', status: 'TRADING', trading: true }] }],
}

describe('Research Universe mapping visibility', () => {
  it('shows the observed code and warns when it differs from the recorded asset', () => {
    render(<QueryClientProvider client={new QueryClient()}>
      <ResearchUniverse apiClient={{} as QapApiClient} workspace={workspace} data={universe} />
    </QueryClientProvider>)

    expect(screen.getByText('Operator mapping recorded')).toBeInTheDocument()
    expect(screen.getByRole('alert')).toHaveTextContent('A venue code differs from BTC: binance W')
    expect(screen.getByRole('alert')).toHaveTextContent('QAP has not independently verified it')
    expect(screen.getByText('W')).toBeInTheDocument()
    expect(screen.getByText('WUSDT')).toBeInTheDocument()
  })
})
