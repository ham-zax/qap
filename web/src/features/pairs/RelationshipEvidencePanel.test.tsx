import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type { PairEvidenceDto } from '../../api/types'
import { RelationshipEvidencePanel } from './RelationshipEvidencePanel'

const evidence = {
  schema_version: 'qap.api.pair_evidence.v1',
  run_id: 'run-evidence',
  canonical_pair: ['BTC', 'USDT'],
  requested_orientation: 'BTC/USDT',
  series: [
    {
      persisted_orientation: 'BTC/USDT',
      model_id: 'rolling_log_ratio_zscore',
      model_version: '1',
      evidence_field: 'score',
      fit_reciprocity: 'exact_transform',
      evidence_reciprocity: 'exact_transform',
      base_source_fingerprint: 'base-fingerprint',
      quote_source_fingerprint: 'quote-fingerprint',
      points: [
        {
          timestamp: '2025-01-01T01:00:00Z',
          value: null,
          status: 'insufficient_history',
          window_observations: 3,
          required_observations: 3,
          coverage_observations: 1,
          input_fingerprint: 'a'.repeat(64),
        },
        {
          timestamp: '2025-01-01T02:00:00Z',
          value: null,
          status: 'insufficient_history',
          window_observations: 3,
          required_observations: 3,
          coverage_observations: 2,
          input_fingerprint: 'b'.repeat(64),
        },
        {
          timestamp: '2025-01-01T03:00:00Z',
          value: 1.224744871,
          status: 'valid',
          window_observations: 3,
          required_observations: 3,
          coverage_observations: 3,
          input_fingerprint: 'c'.repeat(64),
        },
      ],
    },
  ],
} satisfies PairEvidenceDto

describe('RelationshipEvidencePanel', () => {
  it('plots only persisted valid values while keeping invalid coverage visible', () => {
    render(<RelationshipEvidencePanel data={evidence} />)

    expect(
      screen.getByRole('heading', { name: 'Persisted model evidence' }),
    ).toBeInTheDocument()
    expect(
      screen.getByText(
        'Backend-produced observations only; the browser does not refit or recalculate the model.',
      ),
    ).toBeInTheDocument()
    expect(
      screen.getByRole('heading', {
        name: 'rolling_log_ratio_zscore v1 score',
      }),
    ).toBeInTheDocument()
    expect(screen.getByText('Persisted orientation: BTC/USDT')).toBeInTheDocument()
    expect(
      screen.getByText('2 observations unavailable by model validity rules.'),
    ).toBeInTheDocument()
    expect(
      screen.getByText('rolling_log_ratio_zscore (score) - latest 1.2247449'),
    ).toBeInTheDocument()
    expect(evidence.series[0]?.points.at(-1)?.value).toBe(1.224744871)
  })

  it('renders an explicit model-free state instead of an empty chart', () => {
    render(
      <RelationshipEvidencePanel
        data={{ ...evidence, series: [] } satisfies PairEvidenceDto}
      />,
    )

    expect(
      screen.getByRole('heading', { name: 'No persisted model evidence' }),
    ).toBeInTheDocument()
    expect(
      screen.getByText(
        'This run has no relationship-model evidence artifact for the requested pair.',
      ),
    ).toBeInTheDocument()
  })
})
