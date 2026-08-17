import { describe, expect, it } from 'vitest'

import {
  canonicalPairSearch,
  parsePairSearch,
  toggleOrientation,
} from './pairSearch'

describe('pair URL state', () => {
  it('defaults to the path orientation, no anchor, and ratio view', () => {
    const parsed = parsePairSearch({})
    const canonical = canonicalPairSearch(
      { assetX: 'eth', assetY: 'btc' },
      parsed,
    )

    expect(canonical).toEqual({
      changed: true,
      search: {
        orientation: 'ETH/BTC',
        anchor: 'none',
        view: 'ratio',
      },
    })
  })

  it('preserves the reciprocal orientation for one canonical path pair', () => {
    const canonical = canonicalPairSearch(
      { assetX: 'ETH', assetY: 'BTC' },
      parsePairSearch({
        orientation: 'btc/eth',
        anchor: 'usdt',
        view: 'anchor',
      }),
    )

    expect(canonical).toEqual({
      changed: true,
      search: {
        orientation: 'BTC/ETH',
        anchor: 'USDT',
        view: 'anchor',
      },
    })
    expect(toggleOrientation('BTC/ETH')).toBe('ETH/BTC')
  })

  it('does not allow an anchor-only view without an admitted anchor', () => {
    const canonical = canonicalPairSearch(
      { assetX: 'ETH', assetY: 'BTC' },
      parsePairSearch({ orientation: 'ETH/BTC', anchor: 'none', view: 'anchor' }),
    )

    expect(canonical).toEqual({
      changed: true,
      search: {
        orientation: 'ETH/BTC',
        anchor: 'none',
        view: 'ratio',
      },
    })
  })

  it('canonicalizes an orientation that does not match the path assets', () => {
    const canonical = canonicalPairSearch(
      { assetX: 'ETH', assetY: 'BTC' },
      parsePairSearch({ orientation: 'ETH/USDT', view: 'unknown' }),
    )

    expect(canonical.search).toEqual({
      orientation: 'ETH/BTC',
      anchor: 'none',
      view: 'ratio',
    })
    expect(canonical.changed).toBe(true)
  })
})
