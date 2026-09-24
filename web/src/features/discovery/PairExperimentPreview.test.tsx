import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { PairExperimentPreview } from './PairExperimentPreview'
import { pairDraft } from './researchStudy.test-fixtures'

describe('descriptive and backtest settings boundary', () => {
  it('names both windows when the backtest settings differ from the descriptive relationship', () => {
    const recipe = { ...pairDraft, variants: pairDraft.variants.map((variant) => ({ ...variant,
      relationship: { ...variant.relationship, config: { ...variant.relationship.config,
        window_bars: 60, min_observations: 55 } } })) }
    render(<PairExperimentPreview recipe={recipe} busy={false} onParameters={vi.fn()}
      descriptiveWindowBars={180} descriptiveMinimumObservations={171} />)
    expect(screen.getByText(/Descriptive view: 180-bar window, 171 observations required/)).toBeInTheDocument()
    expect(screen.getByText(/Backtest settings: 60-bar window, 55 observations required/)).toBeInTheDocument()
  })
})
