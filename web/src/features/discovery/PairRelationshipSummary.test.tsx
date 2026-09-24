import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { pairContext } from './researchStudy.test-fixtures'
import { PairRelationshipSummary } from './PairRelationshipSummary'

describe('human relationship summary', () => {
  it('shows descriptive evidence without implying a profitable strategy', () => {
    render(<PairRelationshipSummary context={pairContext} series={null} />)
    expect(screen.getByRole('heading', { name: 'What the relationship shows' })).toBeInTheDocument()
    expect(screen.getAllByText(/recent reference level/i).length).toBeGreaterThan(0)
    expect(screen.getByText(/does not tell us whether trading it would improve wealth/i)).toBeInTheDocument()
    expect(screen.getByText(/180 bars/i)).toBeInTheDocument()
  })
})
