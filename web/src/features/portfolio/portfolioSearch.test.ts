import { describe, expect, it } from 'vitest'

import { canonicalPortfolioSearch, parsePortfolioSearch } from './portfolioSearch'

const decisions = [
  { decision_id: 'decision-1' },
  { decision_id: 'decision-2' },
]

describe('portfolio decision search', () => {
  it('keeps a valid selected decision and canonicalizes missing or unknown selections to the first decision', () => {
    expect(canonicalPortfolioSearch(parsePortfolioSearch({ decision: 'decision-2' }), decisions)).toEqual({
      search: { decision: 'decision-2' },
      changed: false,
    })
    expect(canonicalPortfolioSearch(parsePortfolioSearch({}), decisions)).toEqual({
      search: { decision: 'decision-1' },
      changed: true,
    })
    expect(canonicalPortfolioSearch(parsePortfolioSearch({ decision: 'missing' }), decisions)).toEqual({
      search: { decision: 'decision-1' },
      changed: true,
    })
  })
})
