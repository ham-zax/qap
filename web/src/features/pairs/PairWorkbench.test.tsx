import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import type { PairSeriesDto } from '../../api/types'
import { PairWorkbench } from './PairWorkbench'

const pair = {
  schema_version: 'qap.api.pair_series.v1',
  run_id: 'run-pair',
  canonical_pair: ['BTC', 'ETH'],
  requested_orientation: 'ETH/BTC',
  available_anchors: ['BTC', 'ETH', 'USDT'],
  identity_coordinate_assets: ['USDT'],
  interval: '1h',
  base_source_fingerprint: 'eth-fingerprint',
  quote_source_fingerprint: 'btc-fingerprint',
  fit_reciprocity: 'exact_transform',
  evidence_reciprocity: 'exact_transform',
  ratio: [
    { timestamp: '2025-01-01T00:00:00Z', value: 0.05 },
    { timestamp: '2025-01-01T01:00:00Z', value: 0.051 },
  ],
  log_ratio: [
    { timestamp: '2025-01-01T00:00:00Z', value: -2.9957 },
    { timestamp: '2025-01-01T01:00:00Z', value: -2.9759 },
  ],
  normalized_base: [
    { timestamp: '2025-01-01T00:00:00Z', value: 1 },
    { timestamp: '2025-01-01T01:00:00Z', value: 1.02 },
  ],
  normalized_quote: [
    { timestamp: '2025-01-01T00:00:00Z', value: 1 },
    { timestamp: '2025-01-01T01:00:00Z', value: 1.01 },
  ],
  rebalance_markers: [
    {
      timestamp: '2025-01-01T01:00:00Z',
      decision_id: 'decision-1',
      selected: true,
      executed: true,
      fill_id: 'fill-1',
    },
  ],
  descriptive_only: true,
} satisfies PairSeriesDto

describe('PairWorkbench', () => {
  it('updates URL-owned orientation and anchor state without changing pair identity', async () => {
    const user = userEvent.setup()
    const onSearchChange = vi.fn()

    render(
      <PairWorkbench
        data={pair}
        anchorData={null}
        search={{ orientation: 'ETH/BTC', anchor: 'none', view: 'ratio' }}
        onSearchChange={onSearchChange}
      />,
    )

    expect(
      screen.getByRole('heading', { name: 'Pair workbench' }),
    ).toBeInTheDocument()
    expect(screen.getByText('Canonical pair: BTC / ETH')).toBeInTheDocument()
    expect(screen.getByText('Displayed orientation: ETH/BTC')).toBeInTheDocument()
    expect(
      screen.getByText(
        'Descriptive evidence only; this chart does not establish tradable alpha.',
      ),
    ).toBeInTheDocument()
    expect(
      screen.getByRole('heading', { name: 'ETH/BTC ratio' }),
    ).toBeInTheDocument()
    expect(
      screen.getByText('Requested quote units per one requested base unit.'),
    ).toBeInTheDocument()
    expect(screen.getByText('decision-1 - executed')).toBeInTheDocument()
    expect(screen.getByText('Identity coordinates: USDT')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Show BTC/ETH' }))
    expect(onSearchChange).toHaveBeenLastCalledWith({
      orientation: 'BTC/ETH',
      anchor: 'none',
      view: 'ratio',
    })

    await user.selectOptions(screen.getByRole('combobox', { name: 'Anchor lens' }), 'USDT')
    expect(onSearchChange).toHaveBeenLastCalledWith({
      orientation: 'ETH/BTC',
      anchor: 'USDT',
      view: 'anchor',
    })
  })
})
