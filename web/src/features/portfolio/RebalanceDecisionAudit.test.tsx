import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import type { RebalanceDecisionAuditDto } from '../../api/types'
import { RebalanceDecisionAudit } from './RebalanceDecisionAudit'

const base = {
  decision_time: '2025-03-01T00:00:00Z',
  evidence_ids: [],
  current_weights: { BTC: '0.8', USDT: '0.2' },
  baseline_target_weights: { BTC: '0.75', USDT: '0.25' },
  target_weights: { BTC: '0.7', USDT: '0.3' },
  modeled_fee_bps: '10',
  modeled_slippage_bps: '5',
  requested_quantity_deltas: null,
  selected: true,
  fills: [],
  post_fill_holdings: [],
}

const decisions = [
  { ...base, decision_id: 'decision-1', reason: 'first reason' },
  { ...base, decision_id: 'decision-2', reason: 'second reason' },
] as unknown as RebalanceDecisionAuditDto[]

describe('RebalanceDecisionAudit', () => {
  it('renders detail for the selected decision identity rather than another timeline row', () => {
    render(
      <RebalanceDecisionAudit
        decisions={decisions}
        selectedDecisionId="decision-2"
        onSelectDecision={vi.fn()}
      />,
    )

    expect(screen.getByRole('heading', { name: 'Rebalance 2 of 2' })).toBeInTheDocument()
    expect(screen.getByText('Second reason')).toBeInTheDocument()
    expect(screen.queryByText('First reason')).not.toBeInTheDocument()
  })
})
