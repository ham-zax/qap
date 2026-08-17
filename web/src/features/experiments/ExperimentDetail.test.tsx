import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type { ExperimentDetailDto } from '../../api/types'
import { ExperimentDetail } from './ExperimentDetail'

const data = {
  schema_version: 'qap.api.experiment_detail.v1',
  run_id: 'run-0123456789abcdef01234567',
  family_attempt_count: 3,
  manifest: {
    schema_version: 'qap.experiment.manifest.v1',
    experiment_name: 'sealed candidate',
    description: 'Tests whether relationship evidence adds value after simple controls.',
    research_family_id: 'family-alpha',
    parent_run_id: 'run-parentparentparentparent12',
    basket: ['ETH', 'BTC', 'USDT'],
    starting_quantities: { ETH: '10', BTC: '1', USDT: '1000' },
    universe_mode: 'declared_fixed_basket',
    analysis_anchor: 'USDT',
    instruments: [],
    interval: '1h',
    data_window: {
      start: '2025-01-01T00:00:00Z',
      end: '2025-06-01T00:00:00Z',
    },
    data_sources: [
      {
        dataset_id: 'eth-usdt-final',
        instrument_id: 'eth-usdt',
        relative_path: 'final/ETHUSDT.parquet',
        expected_semantic_fingerprint: 'a'.repeat(64),
      },
    ],
    relationship: { component_id: 'ratio-band-v1', config: {} },
    policy: { component_id: 'relationship_target', config: {} },
    execution: {
      execution_instrument_id: 'eth-usdt',
      numeraire_asset: 'USDT',
      fee_bps: '10',
      slippage_bps: '5',
      minimum_rebalance_notional: '10',
      base_step: null,
      adverse_cost_scenario: null,
    },
    external_flows: [],
    benchmarks: {
      relationship_alpha_claim: true,
      primary_incremental_benchmark: 'band-5pct-half',
      controls: [],
    },
    data_role: 'final_oos',
    primary_metric: 'primary_control_relative_terminal_wealth',
    success_threshold: '0',
    random_seed: 7,
  },
  provenance: {
    schema_version: 'qap.experiment.provenance.v1',
    run_id: 'run-0123456789abcdef01234567',
    manifest_sha256: 'b'.repeat(64),
    data_fingerprints: [
      { dataset_id: 'eth-usdt-final', fingerprint: 'a'.repeat(64) },
    ],
    code_fingerprint: 'c'.repeat(64),
    git_commit: 'deadbeef',
    git_dirty: false,
    qap_version: '0.1.0.dev0',
    run_timestamp_utc: '2026-08-17T06:00:00Z',
    research_family_id: 'family-alpha',
    data_role: 'final_oos',
  },
  result: {
    schema_version: 'qap.experiment.result.v1',
    run_id: 'run-0123456789abcdef01234567',
    research_family_id: 'family-alpha',
    parent_run_id: 'run-parentparentparentparent12',
    data_role: 'final_oos',
    final_oos_consumed: true,
    start_timestamp: '2025-01-01T01:00:00Z',
    terminal_timestamp: '2025-06-01T00:00:00Z',
    primary_metric: 'primary_control_relative_terminal_wealth',
    primary_metric_value: '-0.0042',
    success_threshold: '0',
    status: 'negative',
    primary_incremental_benchmark: 'band-5pct-half',
    strategy_vs_hodl: '0.012',
    strategy_vs_matched_contribution: null,
    strategy_vs_primary_control: '-0.0042',
    strategy_unitized_vs_hodl: '0.012',
    maximum_relative_drawdown_vs_hodl: '0.031',
    incremental_log_relative_to_hodl: [],
    roles: [],
    notes: [],
  },
  final_oos_commitment: {
    schema_version: 'qap.experiment.final_oos_commitment.v1',
    run_id: 'run-0123456789abcdef01234567',
    research_family_id: 'family-alpha',
    parent_run_id: 'run-parentparentparentparent12',
    holdout_id: 'holdout-0123456789abcdef01234567',
    manifest_sha256: 'b'.repeat(64),
    code_fingerprint: 'c'.repeat(64),
    data_fingerprints: [
      { dataset_id: 'eth-usdt-final', fingerprint: 'a'.repeat(64) },
    ],
    data_window_start: '2025-01-01T00:00:00Z',
    data_window_end: '2025-06-01T00:00:00Z',
    committed_at: '2026-08-17T06:00:00Z',
    consumed: true,
    execution_status: 'completed',
    consumed_at: '2026-08-17T06:01:00Z',
  },
  available_series: [],
} as unknown as ExperimentDetailDto

describe('ExperimentDetail', () => {
  it('keeps a consumed final-OOS result negative when it beats HODL but loses to the primary control', () => {
    render(<ExperimentDetail data={data} />)

    expect(screen.getByRole('heading', { name: 'sealed candidate' })).toBeInTheDocument()
    expect(screen.getByText('Negative evidence')).toBeInTheDocument()
    expect(screen.getAllByText('Final OOS · consumed').length).toBeGreaterThan(0)
    expect(screen.getByText('Underperformed Band-5pct-half by 0.42%')).toBeInTheDocument()
    expect(screen.queryByText(/Outperformed Band-5pct-half/)).not.toBeInTheDocument()

    expect(screen.getByText('What was tested?')).toBeInTheDocument()
    expect(screen.getByText('Research boundary')).toBeInTheDocument()
    expect(screen.getByText(/This final-OOS window has been consumed/)).toBeInTheDocument()
    expect(screen.getByText('Technical provenance')).toBeInTheDocument()

    expect(screen.getAllByText('−0.42%').some((node) => node.getAttribute('data-exact') === '-0.0042')).toBe(true)
    expect(screen.getAllByText('+1.20%').some((node) => node.getAttribute('data-exact') === '0.012')).toBe(true)

    expect(screen.getByRole('link', { name: 'Portfolio economics' })).toHaveAttribute(
      'href',
      '/portfolio/run-0123456789abcdef01234567',
    )
    expect(screen.getByRole('link', { name: 'Pair evidence' })).toHaveAttribute(
      'href',
      '/pair/run-0123456789abcdef01234567/ETH/BTC?orientation=ETH%2FBTC&anchor=USDT&view=ratio',
    )
  })

  it('shows a positive arithmetic increment below the declared threshold as a threshold miss', () => {
    const thresholdMiss = {
      ...data,
      manifest: { ...data.manifest, success_threshold: '0.02' },
      result: {
        ...data.result,
        primary_metric_value: '0.01',
        success_threshold: '0.02',
        status: 'negative',
        strategy_vs_primary_control: '0.01',
      },
    } as ExperimentDetailDto

    render(<ExperimentDetail data={thresholdMiss} />)

    expect(screen.getByText('Predeclared success threshold')).toBeVisible()
    expect(screen.getByText('2.00%')).toHaveAttribute('data-exact', '0.02')
    expect(
      screen.getByText('Did not clear the research threshold against Band-5pct-half'),
    ).toBeVisible()

    const primaryBar = screen
      .getByText('Primary control · Band-5pct-half')
      .closest('[data-comparison-tone]')
    expect(primaryBar).toHaveAttribute('data-comparison-tone', 'warning')
  })
})
