import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type { PaperOperationDetailDto } from '../../api/types'
import { PaperOperationDetail } from './PaperOperationDetail'

const detail = {
  schema_version: 'qap.api.paper_operation.v1',
  operation_id: 'forward-paper-no-fill',
  data_role: 'forward_paper',
  evidence_class: 'operational_dry_run',
  prospective_candidate_evidence: false,
  execution_timestamp: '2026-08-17T11:11:00Z',
  input_fingerprint: 'a'.repeat(64),
  source_note: 'Recorded public Binance Spot inputs.',
  bridge: 'USDT',
  starting_holdings: { SOL: '1.3', USDT: '100' },
  target_weights: { SOL: '0.248', USDT: '0.752' },
  valuation_prices: { SOL: '75.8', USDT: '1' },
  reference_prices: { SOLUSDT: '75.8' },
  market_metadata: {
    SOLUSDT: {
      venue: 'binance',
      venue_symbol: 'SOLUSDT',
      base: 'SOL',
      quote: 'USDT',
      status: 'TRADING',
      price_tick: '0.01',
      minimum_price: '0.01',
      maximum_price: '10000',
      quantity_step: '0.001',
      minimum_quantity: '0.001',
      maximum_quantity: '90000',
      minimum_notional: '5',
      maximum_notional: '9000000',
      minimum_notional_applies_to_market: true,
      maximum_notional_applies_to_market: false,
      notional_average_price_minutes: 5,
      market_quantity_step: null,
      market_minimum_quantity: null,
      market_maximum_quantity: '2850',
    },
  },
  orders: [
    {
      phase: 'sell_to_bridge',
      asset: 'SOL',
      route_id: 'direct:SOL>USDT',
      requested_source_quantity: '0.01',
      fill_ids: [],
      leg_reason: 'below_minimum_notional',
    },
  ],
  fills: [],
  ending_holdings: { SOL: '1.3', USDT: '100' },
  bridge_target_quantity: '75.2',
  bridge_residual: '24.8',
  tracking_errors: [
    {
      asset: 'SOL',
      target_weight: '0.248',
      actual_weight: '0.496',
      weight_error: '0.248',
      unfilled_quantity: '-0.65',
      unfilled_value: '-49.27',
    },
  ],
  total_fee_quote: '0',
  total_slippage_quote: '0',
  reconciliation_matches: true,
  reconciliation: {
    matches: true,
    reported_fee_total: '0',
    recomputed_fee_total: '0',
    reported_turnover: '0',
    recomputed_turnover: '0',
    reported_slippage_total: '0',
    recomputed_slippage_total: '0',
    expected_terminal_value: '198.54',
    recomputed_terminal_value: '198.54',
    economic_differences: [],
  },
  research_boundary: {
    eligible_for_parameter_selection: false,
    eligible_for_model_promotion: false,
    eligible_for_deployment_evidence: false,
    rule: 'This artifact is an operational dry run, not prospective candidate evidence.',
  },
} satisfies PaperOperationDetailDto

describe('PaperOperationDetail', () => {
  it('keeps no-fill constraints and the research boundary explicit', () => {
    render(<PaperOperationDetail data={detail} />)

    expect(screen.getByRole('heading', { name: 'Paper rebalance' })).toBeVisible()
    expect(screen.getByText('Reconciled')).toBeVisible()
    expect(
      screen.getByText('Forward paper only — not valid for parameter selection, model promotion, or deployment evidence.'),
    ).toBeVisible()
    expect(screen.getByText('No fill · SOL · Below Minimum Notional')).toBeVisible()
    expect(
      screen.getByText('This artifact is an operational dry run, not prospective candidate evidence.'),
    ).toBeVisible()
    expect(screen.getByRole('heading', { name: 'Target tracking' })).toBeVisible()
    expect(screen.getByText('−49.27')).toBeVisible()
    expect(screen.getByRole('heading', { name: 'Independent reconciliation' })).toBeVisible()
    expect(screen.getAllByText('198.54')).toHaveLength(2)
    expect(screen.getByText('No fills were realized.')).toBeVisible()

    expect(screen.getByText('Technical execution details')).toBeVisible()
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })
})
