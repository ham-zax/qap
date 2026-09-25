import { describe, expect, it } from 'vitest'

import { interpretRelationshipScore, relationshipSummary, researchMethodName } from './researchPresentation'

describe('descriptive relationship interpretation', () => {
  it('names the tested log-ratio method without implying an arithmetic ratio average', () => {
    expect(researchMethodName('rolling_log_ratio_zscore')).toBe('Price-ratio rebalancing')
    expect(researchMethodName('residual_mean_reversion')).toBe('Fitted-relationship rebalancing')
  })
  it.each([
    [0.99, 'near_reference', 'neutral'], [1, 'noticeable_displacement', 'info'],
    [1.99, 'noticeable_displacement', 'info'], [2, 'large_displacement', 'warning'],
  ] as const)('classifies %s for presentation only', (score, band, tone) => {
    expect(interpretRelationshipScore('ratio', 'valid', score)).toMatchObject({ band, tone, score })
  })

  it('keeps direction separate from desirability', () => {
    expect(interpretRelationshipScore('ratio', 'valid', -2).direction).toBe('below its recent reference level')
    expect(interpretRelationshipScore('residual', 'valid', 2).direction).toBe('above its fitted relationship')
    expect(interpretRelationshipScore('ratio', 'valid', -1.5).label).toBe('Away from usual level')
  })

  it('does not turn missing or invalid scores into zero', () => {
    expect(interpretRelationshipScore('ratio', 'insufficient_history', 0).band).toBe('unavailable')
    expect(interpretRelationshipScore('residual', 'valid', Number.NaN).score).toBeNull()
  })

  it('describes agreement, disagreement, and partial availability without an economic verdict', () => {
    const ratio = interpretRelationshipScore('ratio', 'valid', -2)
    expect(relationshipSummary(ratio, interpretRelationshipScore('residual', 'valid', -2))).toMatch(/same direction/)
    expect(relationshipSummary(ratio, interpretRelationshipScore('residual', 'valid', 2))).toMatch(/different directions/)
    expect(relationshipSummary(ratio, interpretRelationshipScore('residual', 'insufficient_history', undefined))).toMatch(/could not be interpreted/)
    expect(relationshipSummary(interpretRelationshipScore('ratio', 'valid', 0), interpretRelationshipScore('residual', 'valid', 0))).toMatch(/close to their/)
  })
  it('explains a below-reference ratio and near-reference fit in everyday language', () => {
    const summary = relationshipSummary(
      interpretRelationshipScore('ratio', 'valid', -1.95),
      interpretRelationshipScore('residual', 'valid', -0.46),
    )
    expect(summary).toMatch(/price ratio is below its recent reference level/i)
    expect(summary).not.toMatch(/displaced/i)
  })
})
