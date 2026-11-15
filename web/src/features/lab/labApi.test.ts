import { afterEach, describe, expect, it, vi } from 'vitest'
import { searchLabCoins } from './labApi'

afterEach(() => vi.unstubAllGlobals())

describe('Lab venue eligibility', () => {
  it('offers only trading Binance listings from mixed search results', async () => {
    const row = { listing_id: 'binance:BTC', venue: 'binance', trading: true, venue_asset_code: 'BTC', name: 'Bitcoin', identity_state: 'unresolved', source: 'venue', call_available: false }
    vi.stubGlobal('fetch', vi.fn(async () => new Response(JSON.stringify({ directory_status: 'observed', coins: [
      row, { ...row, listing_id: 'gate:BTC', venue: 'gate' },
      { ...row, listing_id: 'binance:OLD', trading: false },
    ] }), { headers: { 'Content-Type': 'application/json' } })))
    const result = await searchLabCoins('BTC', new AbortController().signal)
    expect(result.coins.map((coin) => coin.id)).toEqual(['binance:BTC'])
  })
})
