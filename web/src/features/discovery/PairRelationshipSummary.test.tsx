import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import type { ProductPairStudySeriesDto } from '../../api/types'
import { pairContext } from './researchStudy.test-fixtures'
import { PairRelationshipSummary } from './PairRelationshipSummary'

vi.mock('../../components/charts/TimeSeriesChart', () => ({
  TimeSeriesChart: ({ title }: { title: string }) => <div role="img" aria-label={title} />,
}))

describe('human relationship summary', () => {
  it('shows descriptive evidence without implying a profitable strategy', () => {
    render(<PairRelationshipSummary context={pairContext} series={null} />)
    expect(screen.getByRole('heading', { name: 'What the relationship shows' })).toBeInTheDocument()
    expect(screen.getAllByText(/recent reference level/i).length).toBeGreaterThan(0)
    expect(screen.getByText(/does not tell us whether trading it would improve wealth/i)).toBeInTheDocument()
    expect(screen.getByText(/180 bars/i)).toBeInTheDocument()
    expect(screen.getAllByText('What does this measure?')).toHaveLength(2)
    expect(screen.getAllByText(/^Away from usual level/)).toHaveLength(2)
    expect(screen.getAllByText(/^Away from usual level/)[0]).toHaveAttribute('data-tone', 'info')
  })
  it('does not duplicate the main chart inside the interpretation', () => {
    const series: ProductPairStudySeriesDto = {
      schema_version: 'qap.api.product_pair_study_series.v1', question: pairContext.question,
      asset_a_path: pairContext.data.asset_a_path!, asset_b_path: pairContext.data.asset_b_path!,
      base_source_fingerprint: pairContext.data.asset_a_path!.semantic_fingerprint,
      quote_source_fingerprint: pairContext.data.asset_b_path!.semantic_fingerprint,
      ratio: [], log_ratio: [], normalized_base: [], normalized_quote: [], analysis_reference: null,
    }
    render(<PairRelationshipSummary context={pairContext} series={series} />)
    expect(screen.queryByRole('img', { name: /normalized paths/ })).not.toBeInTheDocument()
  })
})
