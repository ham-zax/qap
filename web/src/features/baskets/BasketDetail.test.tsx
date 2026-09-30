import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type {
  BasketDetailDto,
  PortfolioSnapshotDto,
} from '../../api/types'
import { BasketDetail } from './BasketDetail'

const scanId = 'a'.repeat(64)
const basketId = 'b'.repeat(64)

const basket: BasketDetailDto = {
  schema_version: 'qap.api.basket_detail.v1',
  summary: {
    artifact_status: 'valid',
    basket_id: basketId,
    source_scan_id: scanId,
    source_momentum_scan_id: null,
    source_as_of: '2026-08-19T00:00:00Z',
    venue: 'binance',
    horizon: 'short',
    decision_resolution: '1h',
    economic_assets: ['AAA', 'BBB', 'CCC'],
    forensic: false,
    attempt_status: 'completed',
    economic_gate_status: 'basket_development_rejected',
    qap_run_id: 'run-basket-1',
    error: null,
  },
  selected_edges: [
    {
      candidate_id: 'c'.repeat(64),
      pair_id: 'AAA/BBB',
      asset_a: 'AAA',
      asset_b: 'BBB',
      candidate_orientation: 'AAA/BBB',
      resolution: '1h',
      model_family: 'log_ratio_mean_reversion',
      template_id: 'fast',
      automatic_neighbor_selected: true,
      manual_pinned: false,
      automatic_selected: true,
      manual_selected: false,
      deep_replay_status: 'completed',
      deep_replay_failure_reason: null,
      deep_replay_run_id: 'run-pair-1',
      economic_gate_status: 'deep_replay_survivor',
    },
  ],
  qap_experiment_run_id: 'run-basket-1',
  qap_portfolio_run_id: 'run-basket-1',
  resolver_audit_available: true,
}

const portfolio = {
  strategy_costs: {
    fill_count: 4,
    fees_value: '0.002',
    slippage_value: '0.001',
    turnover_value: '2',
  },
  concentration: { terminal_max_weight: '0.34', terminal_herfindahl: '0.3302' },
  starting: {
    holdings: [
      { asset: 'AAA', quantity: '1', value: '0.33', weight: '0.33' },
      { asset: 'BBB', quantity: '1', value: '0.33', weight: '0.33' },
      { asset: 'CCC', quantity: '1', value: '0.34', weight: '0.34' },
    ],
  },
  terminal: {
    holdings: [
      { asset: 'AAA', quantity: '1', value: '0.34', weight: '0.34' },
      { asset: 'BBB', quantity: '1', value: '0.33', weight: '0.33' },
      { asset: 'CCC', quantity: '1', value: '0.32', weight: '0.32' },
      { asset: 'USDT', quantity: '0.01', value: '0.01', weight: '0.01' },
    ],
  },
  rebalance_audit: [
    {
      evidence_ids: [
        'basket-opinions:AAA/BBB=1',
        'basket-resolver:maximum_tilt=0.10',
      ],
      target_weights: { AAA: '0.40', BBB: '0.30', CCC: '0.30' },
    },
  ],
} as unknown as PortfolioSnapshotDto

describe('BasketDetail', () => {
  it('renders authoritative resolver evidence and bridge residue from QAP artifacts', () => {
    render(<BasketDetail basket={basket} experiment={null} portfolio={portfolio} />)
    for (const details of document.querySelectorAll('details')) details.open = true

    expect(screen.getByText('basket-opinions:AAA/BBB=1')).toBeVisible()
    expect(screen.getByText('basket-resolver:maximum_tilt=0.10')).toBeVisible()
    expect(screen.getByText('0.40')).toBeVisible()
    expect(screen.getByRole('heading', { name: 'Execution-only bridge residue' })).toBeVisible()
    expect(screen.getByText('USDT')).toBeVisible()
    expect(screen.getByText(/React does not recompute them/)).toBeVisible()
  })
})
