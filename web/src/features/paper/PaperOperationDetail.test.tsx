import { render, screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type { PaperOperationDetailDto } from '../../api/types'
import { PaperOperationDetail } from './PaperOperationDetail'

const detail = {
  schema_version: 'qap.api.paper_operation.v1',
  operation_id: 'forward-paper-no-fill',
  data_role: 'forward_paper',
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
  total_fee_quote: '0',
  total_slippage_quote: '0',
  reconciliation_matches: true,
  research_boundary: {
    eligible_for_parameter_selection: false,
    eligible_for_model_promotion: false,
    eligible_for_deployment_evidence: false,
    rule: 'Forward-paper observations cannot be reused as deployment evidence.',
  },
} satisfies PaperOperationDetailDto

describe('PaperOperationDetail', () => {
  it('keeps no-fill constraints and the research boundary explicit', () => {
    render(<PaperOperationDetail data={detail} />)

    expect(screen.getByRole('heading', { name: 'forward-paper-no-fill' })).toBeVisible()
    expect(screen.getByText('No fill: below_minimum_notional')).toBeVisible()
    expect(screen.getByText('Forward-paper observations cannot be reused as deployment evidence.')).toBeVisible()
    expect(screen.getByText('No fills were realized.')).toBeVisible()

    const boundary = screen.getByRole('heading', { name: 'Research boundary' }).parentElement
    expect(boundary).not.toBeNull()
    expect(within(boundary as HTMLElement).getAllByText('Not eligible')).toHaveLength(3)
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })
})
