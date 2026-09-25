import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import type { ProductPairStudySeriesDto } from '../../api/types'
import { pairContext } from './researchStudy.test-fixtures'
import { PairStudyResults } from './PairStudyResults'

vi.mock('../../components/charts/TimeSeriesChart', () => ({
  TimeSeriesChart: ({ title }: { title: string }) => <div role="img" aria-label={title} />,
}))

const series: ProductPairStudySeriesDto = {
  schema_version: 'qap.api.product_pair_study_series.v1', question: pairContext.question,
  asset_a_path: pairContext.data.asset_a_path!, asset_b_path: pairContext.data.asset_b_path!,
  base_source_fingerprint: pairContext.data.asset_a_path!.semantic_fingerprint,
  quote_source_fingerprint: pairContext.data.asset_b_path!.semantic_fingerprint,
  ratio: [], log_ratio: [], normalized_base: [], normalized_quote: [], analysis_reference: null,
}

describe('pair study canvas', () => {
  it('leads with the normalized chart and keeps model and provenance behind disclosures', async () => {
    const user = userEvent.setup()
    render(<PairStudyResults context={pairContext} series={series} capabilities={[]} />)
    expect(screen.getByRole('img', { name: 'W/PIXEL normalized paths' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Normalized paths' })).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByText('Raw ratio')).toBeInTheDocument()
    expect(screen.getByText('Model details').closest('details')).not.toHaveAttribute('open')
    expect(screen.queryByText('Economic replay is a separate question')).not.toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Ratio' }))
    expect(screen.getByRole('img', { name: 'W/PIXEL ratio' })).toBeInTheDocument()
    await user.click(screen.getByText('Model details'))
    expect(screen.getByText(/Alpha:/)).toBeVisible()
    expect(screen.getByText('Normalized W:')).toBeVisible()
    await user.click(screen.getByText('Evidence & provenance'))
    expect(screen.getByText(/W-fixture/)).toBeVisible()
  })
})
