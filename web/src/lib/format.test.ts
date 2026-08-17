import { describe, expect, it } from 'vitest'

import { formatRelativePercent } from './format'

describe('formatRelativePercent', () => {
  it('preserves sign and exact source while formatting a relative decimal as percent', () => {
    expect(formatRelativePercent('-0.0179')).toEqual({
      display: '−1.79%',
      exact: '-0.0179',
    })
    expect(formatRelativePercent('0.0179')).toEqual({
      display: '+1.79%',
      exact: '0.0179',
    })
  })

  it('does not turn a tiny nonzero relative value into visible zero', () => {
    expect(formatRelativePercent('-0.0000005')).toEqual({
      display: '−<0.01%',
      exact: '-0.0000005',
    })
    expect(formatRelativePercent('0.0000005')).toEqual({
      display: '+<0.01%',
      exact: '0.0000005',
    })
  })
})
