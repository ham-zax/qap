import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type {
  ExperimentDetailDto,
  PortfolioPerformanceDto,
  PortfolioSnapshotDto,
} from '../../api/types'
import { PortfolioOverview } from './PortfolioOverview'

const experiment = {
  schema_version: 'qap.api.experiment_detail.v1',
  run_id: 'run-portfolio-boundary',
  family_attempt_count: 4,
  manifest: {
    experiment_name: 'relationship candidate',
    description: 'A candidate that beats HODL but loses to stronger controls.',
    research_family_id: 'family-alpha',
    parent_run_id: null,
    basket: ['BTC', 'USDT'],
    universe_mode: 'declared_fixed_basket',
    analysis_anchor: 'USDT',
    relationship: { component_id: 'ratio-band-v1', config: {} },
    policy: { component_id: 'relationship-target-v1', config: {} },
    benchmarks: {
      relationship_alpha_claim: true,
      primary_incremental_benchmark: 'periodic-2',
      controls: [],
    },
    data_window: {
      start: '2025-01-01T00:00:00Z',
      end: '2025-06-01T00:00:00Z',
    },
    execution: {
      numeraire_asset: 'USDT',
    },
    external_flows: [
      {
        flow_id: 'deposit-1',
        effective_time: '2025-02-01T00:00:00Z',
        asset: 'USDT',
        quantity_delta: '1000',
      },
    ],
  },
  result: {
    run_id: 'run-portfolio-boundary',
    research_family_id: 'family-alpha',
    data_role: 'final_oos',
    final_oos_consumed: true,
    status: 'negative',
    primary_metric: 'primary_control_relative_terminal_wealth',
    primary_metric_value: '-0.012',
    primary_incremental_benchmark: 'periodic-2',
    strategy_vs_hodl: '0.018',
    strategy_vs_matched_contribution: '-0.006',
    strategy_vs_primary_control: '-0.012',
    maximum_relative_drawdown_vs_hodl: '0.031',
    roles: [
      {
        role: 'strategy',
        policy_id: 'relationship-target-v1',
        terminal_value: '62500',
        unitized_terminal_value: '1.08',
        terminal_quantities: { BTC: '0.75', USDT: '17500' },
        fill_count: 6,
        fees_value: '124.50',
        slippage_value: '63.25',
        turnover_value: '124500',
        external_flow_ids: ['deposit-1'],
      },
      {
        role: 'hodl',
        policy_id: 'hodl',
        terminal_value: '61400',
        unitized_terminal_value: '1.07',
        terminal_quantities: { BTC: '1', USDT: '8000' },
        fill_count: 0,
        fees_value: '0',
        slippage_value: '0',
        turnover_value: '0',
        external_flow_ids: ['deposit-1'],
      },
      {
        role: 'control:periodic-2',
        policy_id: 'periodic-2',
        terminal_value: '63260',
        unitized_terminal_value: '1.09',
        terminal_quantities: { BTC: '0.8', USDT: '15000' },
        fill_count: 3,
        fees_value: '70',
        slippage_value: '35',
        turnover_value: '70000',
        external_flow_ids: ['deposit-1'],
      },
      {
        role: 'matched_contribution',
        policy_id: 'matched-contribution-hodl',
        terminal_value: '62877',
        unitized_terminal_value: '1.085',
        terminal_quantities: { BTC: '0.85', USDT: '12500' },
        fill_count: 1,
        fees_value: '0',
        slippage_value: '0',
        turnover_value: '1000',
        external_flow_ids: ['deposit-1'],
      },
    ],
  },
  provenance: {},
  final_oos_commitment: {},
  available_series: [],
} as unknown as ExperimentDetailDto

const snapshot = {
  schema_version: 'qap.api.portfolio_snapshot.v1',
  run_id: 'run-portfolio-boundary',
  starting: {
    timestamp: '2025-01-01T00:00:00Z',
    role: 'strategy',
    holdings: [
      { asset: 'BTC', quantity: '1', value: '42000', weight: '0.84' },
      { asset: 'USDT', quantity: '8000', value: '8000', weight: '0.16' },
    ],
  },
  terminal: {
    timestamp: '2025-06-01T00:00:00Z',
    role: 'strategy',
    holdings: [
      { asset: 'BTC', quantity: '0.75', value: '45000', weight: '0.72' },
      { asset: 'USDT', quantity: '17500', value: '17500', weight: '0.28' },
    ],
  },
  hodl_terminal: {
    timestamp: '2025-06-01T00:00:00Z',
    role: 'hodl',
    holdings: [],
  },
  role_terminals: [],
  allocation_history: [],
  concentration: {
    start_max_weight: '0.84',
    terminal_max_weight: '0.72',
    start_herfindahl: '0.7312',
    terminal_herfindahl: '0.5968',
  },
  strategy_vs_hodl_terminal_deltas: [
    { asset: 'BTC', quantity_delta: '-0.25', value_delta: '-15000' },
    { asset: 'USDT', quantity_delta: '10500', value_delta: '10500' },
  ],
  strategy_vs_matched_contribution_terminal_deltas: [
    { asset: 'BTC', quantity_delta: '-0.10', value_delta: '-6000' },
    { asset: 'USDT', quantity_delta: '5000', value_delta: '5000' },
  ],
  strategy_costs: {
    fill_count: 6,
    fees_value: '124.50',
    slippage_value: '63.25',
    turnover_value: '124500',
  },
  rebalance_audit: [
    {
      decision_id: 'decision-1',
      decision_time: '2025-03-01T00:00:00Z',
      reason: 'relationship band crossed',
      evidence_ids: ['relationship-evidence-1'],
      current_weights: { BTC: '0.8', USDT: '0.2' },
      baseline_target_weights: { BTC: '0.75', USDT: '0.25' },
      target_weights: { BTC: '0.7', USDT: '0.3' },
      modeled_fee_bps: '10',
      modeled_slippage_bps: '5',
      requested_quantity_deltas: { BTC: '-0.05', USDT: '3000' },
      selected: true,
      fills: [],
      post_fill_holdings: [
        { asset: 'BTC', quantity: '0.95', value: '57000', weight: '0.74' },
        { asset: 'USDT', quantity: '20000', value: '20000', weight: '0.26' },
      ],
    },
  ],
} satisfies PortfolioSnapshotDto

const performance = {
  schema_version: 'qap.api.portfolio_performance.v1',
  run_id: 'run-portfolio-boundary',
  primary_incremental_benchmark: 'periodic-2',
  maximum_relative_drawdown_vs_hodl: '0.031',
  time_below_hodl_seconds: 36000,
  time_below_primary_control_seconds: 36000,
  series: [
    {
      name: 'relative::strategy_vs_hodl',
      points: [
        { timestamp: '2025-01-01T00:00:00Z', value: '0' },
        { timestamp: '2025-06-01T00:00:00Z', value: '0.018' },
      ],
    },
    {
      name: 'relative::strategy_vs_primary_control',
      points: [
        { timestamp: '2025-01-01T00:00:00Z', value: '0' },
        { timestamp: '2025-06-01T00:00:00Z', value: '-0.012' },
      ],
    },
    {
      name: 'log_relative::strategy_vs_hodl',
      points: [
        { timestamp: '2025-01-01T00:00:00Z', value: '0' },
        { timestamp: '2025-06-01T00:00:00Z', value: '0.017840' },
      ],
    },
    {
      name: 'log_relative::strategy_vs_primary_control',
      points: [
        { timestamp: '2025-01-01T00:00:00Z', value: '0' },
        { timestamp: '2025-06-01T00:00:00Z', value: '-0.012073' },
      ],
    },
  ],
} satisfies PortfolioPerformanceDto

describe('PortfolioOverview', () => {
  it('distinguishes positive increment from meeting the predeclared success threshold', () => {
    const thresholdExperiment = {
      ...experiment,
      result: {
        ...experiment.result,
        status: 'negative',
        primary_metric_value: '0.01',
        strategy_vs_primary_control: '0.01',
        success_threshold: '0.02',
      },
    } as unknown as ExperimentDetailDto

    render(
      <PortfolioOverview
        experiment={thresholdExperiment}
        snapshot={snapshot}
        performance={performance}
      />,
    )

    expect(screen.getByText('Negative evidence')).toBeInTheDocument()
    expect(
      screen.getByText(
        'Relationship intelligence added a 1.00% increment over Periodic-2, but this run did not meet the predeclared 2.00% success threshold.',
      ),
    ).toBeInTheDocument()
  })

  it('does not relabel HODL outperformance as relationship or accumulation alpha', () => {
    render(
      <PortfolioOverview
        experiment={experiment}
        snapshot={snapshot}
        performance={performance}
      />,
    )

    expect(
      screen.getByRole('heading', { name: 'Portfolio economics' }),
    ).toBeInTheDocument()
    expect(screen.getByText('Negative evidence')).toBeInTheDocument()
    expect(screen.getAllByText('Final OOS · consumed').length).toBeGreaterThan(0)
    expect(screen.getByText('Underperformed Periodic-2 by 1.20%')).toBeInTheDocument()
    expect(screen.getAllByText('−1.20%').some((node) => node.getAttribute('data-exact') === '-0.012')).toBe(true)
    expect(screen.getAllByText('+1.80%').some((node) => node.getAttribute('data-exact') === '0.018')).toBe(true)
    expect(
      screen.getByRole('heading', { name: 'Relative wealth through time' }),
    ).toBeInTheDocument()
    expect(
      screen.getByText(
        'QAP vs primary control (relative wealth) - latest -0.012',
      ),
    ).toBeInTheDocument()
    expect(
      screen.getByText(
        'Relationship intelligence underperformed Periodic-2 by 1.20%.',
      ),
    ).toBeInTheDocument()
    expect(
      screen.getByText(
        'Contribution timing underperformed matched-contribution static HODL by 0.60%.',
      ),
    ).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'What changed vs HODL?' })).toBeInTheDocument()
    expect(screen.getByText('−15,000')).toBeInTheDocument()
    expect(screen.getByText('+10,500')).toBeInTheDocument()
    expect(screen.getByText('Time below HODL')).toBeInTheDocument()
    expect(screen.getAllByText('10h')).toHaveLength(2)
    expect(screen.getByRole('heading', { name: 'Rebalance decisions' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Rebalance 1 of 1' })).toBeInTheDocument()
  })
})
