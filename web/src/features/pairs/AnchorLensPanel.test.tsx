import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type { AnchorLensDto } from '../../api/types'
import { AnchorLensPanel } from './AnchorLensPanel'

const reducedLens = {
  schema_version: 'qap.api.anchor_lens.v1',
  run_id: 'run-anchor',
  canonical_pair: ['BTC', 'ETH'],
  requested_orientation: 'ETH/BTC',
  anchor: 'ETH',
  identity_coordinate_assets: ['USDT'],
  interval: '1h',
  base_source_fingerprint: 'eth',
  quote_source_fingerprint: 'btc',
  anchor_source_fingerprint: 'eth',
  fit_reciprocity: 'exact_transform',
  evidence_reciprocity: 'exact_transform',
  reduction: 'anchor_is_base',
  pair_ratio: [
    { timestamp: '2025-01-01T00:00:00Z', value: 0.05 },
    { timestamp: '2025-01-01T01:00:00Z', value: 0.051 },
  ],
  pair_log_ratio: [
    { timestamp: '2025-01-01T00:00:00Z', value: -2.9957 },
    { timestamp: '2025-01-01T01:00:00Z', value: -2.9759 },
  ],
  base_to_anchor: [
    { timestamp: '2025-01-01T00:00:00Z', value: 1 },
    { timestamp: '2025-01-01T01:00:00Z', value: 1 },
  ],
  quote_to_anchor: [
    { timestamp: '2025-01-01T00:00:00Z', value: 20 },
    { timestamp: '2025-01-01T01:00:00Z', value: 19.6078 },
  ],
  base_to_anchor_log: [
    { timestamp: '2025-01-01T00:00:00Z', value: 0 },
    { timestamp: '2025-01-01T01:00:00Z', value: 0 },
  ],
  quote_to_anchor_log: [
    { timestamp: '2025-01-01T00:00:00Z', value: 2.9957 },
    { timestamp: '2025-01-01T01:00:00Z', value: 2.9759 },
  ],
  max_ratio_decomposition_error: 0,
  max_log_decomposition_error: 0,
  descriptive_only: true,
} satisfies AnchorLensDto

describe('AnchorLensPanel', () => {
  it('communicates a reduced identity instead of a fake three-way decomposition', () => {
    render(<AnchorLensPanel anchor="ETH" data={reducedLens} />)

    expect(
      screen.getByText(
        'Anchor is context/decomposition, not portfolio target authority.',
      ),
    ).toBeInTheDocument()
    expect(
      screen.getByText('ETH/ETH is the identity path at 1 and is not plotted.'),
    ).toBeInTheDocument()
    expect(
      screen.getByRole('heading', { name: 'BTC/ETH reduced anchor path' }),
    ).toBeInTheDocument()
    expect(
      screen.queryByText('ETH/ETH (anchor ratio) - latest 1'),
    ).not.toBeInTheDocument()
  })

  it('renders an explicit unavailable state instead of an empty chart', () => {
    render(<AnchorLensPanel anchor="SOL" data={null} />)

    expect(
      screen.getByRole('heading', { name: 'Anchor evidence unavailable' }),
    ).toBeInTheDocument()
    expect(
      screen.getByText('The requested anchor lens was not returned by the API.'),
    ).toBeInTheDocument()
  })
})
