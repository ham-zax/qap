import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import type { ResearchUniverseDto } from '../../api/types'
import { ResearchAssetSelector } from './ResearchAssetSelector'

function universe(code: string): ResearchUniverseDto {
  return {
    schema_version: 'qap.api.research_universe.v1',
    directory_status: 'observed', directory_id: 'directory',
    directory_observed_at: '2026-09-25T00:00:00Z', sources: [], identity_reviews: [], directory_refreshes: [],
    assets: [{
      canonical_asset_id: 'BTC', approved: true, identity_state: 'resolved',
      identity_reason: 'resolved', asset_identity_version: 'operator-record-1',
      data_state: 'needs_data',
      venues: [{ venue: 'binance', venue_symbol: `${code}USDT`, venue_asset_code: code,
        status: 'TRADING', trading: true }],
    }],
  }
}

describe('research asset selection identity visibility', () => {
  it('shows the observed market before selection and warns about a divergent recorded code', async () => {
    const data = universe('W')
    const onSelect = vi.fn()
    const props = { label: 'First asset', universe: data, onSelect, onClear: vi.fn() }
    const view = render(<ResearchAssetSelector {...props} selected={null} />)
    const user = userEvent.setup()
    await user.type(screen.getByRole('textbox', { name: 'First asset' }), 'BTC')
    await user.click(screen.getByRole('button', { name: /BTC.*WUSDT.*mapping recorded/i }))
    view.rerender(<ResearchAssetSelector {...props} selected={onSelect.mock.calls[0][0]} />)

    expect(screen.getByText(/Observed markets: binance WUSDT \(code W\)/)).toBeInTheDocument()
    expect(screen.getByText(/Operator-entered identity reference: operator-record-1/)).toBeInTheDocument()
    expect(screen.getByRole('alert')).toHaveTextContent('A recorded venue code differs from BTC: binance W')
    expect(screen.getByRole('alert')).toHaveTextContent('QAP has not independently verified it')
  })

  it('does not label a matching recorded code as a mismatch', () => {
    const data = universe('BTC')
    render(<ResearchAssetSelector label="First asset" universe={data}
      selected={{ key: 'asset:BTC', symbol: 'BTC', canonicalAssetId: 'BTC', approved: true,
        identityState: 'resolved', venueSymbols: ['BTCUSDT'] }}
      onSelect={vi.fn()} onClear={vi.fn()} />)

    expect(screen.getByText(/Observed markets: binance BTCUSDT \(code BTC\)/)).toBeInTheDocument()
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })

  it('keeps the market visible while an older API has not reported the venue code', () => {
    const data = universe('W')
    delete (data.assets[0].venues[0] as Partial<typeof data.assets[number]['venues'][number]>).venue_asset_code
    render(<ResearchAssetSelector label="First asset" universe={data}
      selected={{ key: 'asset:BTC', symbol: 'BTC', canonicalAssetId: 'BTC', approved: true,
        identityState: 'resolved', venueSymbols: ['WUSDT'] }}
      onSelect={vi.fn()} onClear={vi.fn()} />)

    expect(screen.getByText('Observed markets: binance WUSDT')).toBeInTheDocument()
    expect(screen.queryByText(/undefined/)).not.toBeInTheDocument()
  })

  it('keeps an unresolved venue market visible after selection', () => {
    render(<ResearchAssetSelector label="First asset" universe={universe('BTC')}
      selected={{ key: 'venue:gate:ETH', symbol: 'ETH', canonicalAssetId: null,
        approved: false, identityState: 'review_required', venue: 'gate', venueSymbols: ['ETH_USDT'] }}
      onSelect={vi.fn()} onClear={vi.fn()} />)

    expect(screen.getByText('Observed markets: gate ETH_USDT')).toBeInTheDocument()
  })
})
