import { render, screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type { ExperimentListDto } from '../../api/types'
import { ExperimentList } from './ExperimentList'

const data: ExperimentListDto = {
  schema_version: 'qap.api.experiment_list.v1',
  items: [
    {
      artifact_status: 'valid',
      run_id: 'run-0123456789abcdef01234567',
      experiment_name: 'relationship candidate',
      research_family_id: 'family-alpha',
      parent_run_id: null,
      universe_mode: 'declared_fixed_basket',
      basket: ['BTC', 'USDT'],
      analysis_anchor: 'USDT',
      relationship_id: 'none',
      policy_id: 'scheduled_target',
      data_role: 'development',
      final_oos_consumed: false,
      status: 'negative',
      primary_metric: 'primary_control_relative_terminal_wealth',
      primary_metric_value: '-0.0179',
      primary_incremental_benchmark: 'periodic-2',
      incremental_vs_primary_control: '-0.0179',
      incremental_vs_matched_contribution: '-0.0180',
      created_timestamp: '2026-08-17T06:00:00Z',
      git_dirty: true,
      sibling_trial_count: 2,
      error: null,
    },
  ],
}

describe('ExperimentList', () => {
  it('renders negative evidence with benchmark and research context intact', () => {
    render(<ExperimentList data={data} />)

    const card = screen.getByRole('article', {
      name: 'relationship candidate',
    })
    expect(within(card).getByText('Negative')).toBeInTheDocument()
    expect(within(card).getByText('family-alpha')).toBeInTheDocument()
    expect(within(card).getByText('Development')).toBeInTheDocument()
    expect(within(card).getByText('BTC · USDT')).toBeInTheDocument()
    expect(within(card).getByText('Anchor: USDT')).toBeInTheDocument()
    expect(within(card).getByText('Model: none')).toBeInTheDocument()
    expect(within(card).getByText('Policy: scheduled_target')).toBeInTheDocument()
    expect(
      within(card).getByText('Primary control: periodic-2'),
    ).toBeInTheDocument()
    expect(
      within(card).getByText('Increment vs primary control: -0.0179'),
    ).toBeInTheDocument()
    expect(within(card).getByText('Dirty code snapshot')).toBeInTheDocument()
    expect(
      within(card).getByRole('link', { name: 'Inspect evidence' }),
    ).toHaveAttribute(
      'href',
      '/experiments/run-0123456789abcdef01234567',
    )
  })
})
