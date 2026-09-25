import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { ResearchStageStrip } from './ResearchStageStrip'

describe('research progress', () => {
  it('does not imply a relationship was measured when data preparation is blocked', () => {
    render(<ResearchStageStrip mode="relationship" stage="blocked" hasRelationship={false} />)
    expect(screen.getByText(/^Data/)).toHaveAttribute('aria-current', 'step')
    expect(screen.getByText('Ready')).not.toHaveAttribute('aria-current')
  })
})
