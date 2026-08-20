import type { ResearchUniverseDto } from '../../api/types'

export interface ResearchAssetSelection {
  key: string
  symbol: string
  canonicalAssetId: string | null
  approved: boolean
  identityState: 'resolved' | 'review_required'
  venue?: 'binance' | 'gate'
  venueAssetCode?: string
  venueSymbols: string[]
}

export function researchAssetOptions(
  universe: ResearchUniverseDto,
): ResearchAssetSelection[] {
  const canonical = universe.assets.map((asset) => ({
    key: `asset:${asset.canonical_asset_id}`,
    symbol: asset.canonical_asset_id,
    canonicalAssetId: asset.canonical_asset_id,
    approved: asset.approved,
    identityState: asset.identity_state,
    venueSymbols: asset.venues.map((venue) => venue.venue_symbol),
  })) satisfies ResearchAssetSelection[]
  const unresolved = universe.identity_reviews
    .filter((review) => review.venue_asset_code !== 'USDT')
    .map((review) => ({
      key: `review:${review.venue}:${review.venue_asset_code}`,
      symbol: review.venue_asset_code,
      canonicalAssetId: null,
      approved: false,
      identityState: 'review_required' as const,
      venue: review.venue,
      venueAssetCode: review.venue_asset_code,
      venueSymbols: [...review.venue_symbols],
    }))
  return [...canonical, ...unresolved]
}

function matchRank(option: ResearchAssetSelection, query: string): number {
  const values = [option.symbol, option.canonicalAssetId ?? '', ...option.venueSymbols]
    .map((value) => value.toUpperCase())
    .filter(Boolean)
  if (values.some((value) => value === query)) return 0
  if (values.some((value) => value.startsWith(query))) return 1
  if (values.some((value) => value.includes(query))) return 2
  return 3
}

export function rankResearchAssetOptions(
  options: ResearchAssetSelection[],
  rawQuery: string,
): ResearchAssetSelection[] {
  const query = rawQuery.trim().toUpperCase()
  if (!query) return []
  return options
    .map((option) => ({ option, rank: matchRank(option, query) }))
    .filter((item) => item.rank < 3)
    .sort(
      (left, right) =>
        left.rank - right.rank ||
        Number(right.option.canonicalAssetId !== null) -
          Number(left.option.canonicalAssetId !== null) ||
        left.option.symbol.localeCompare(right.option.symbol) ||
        left.option.key.localeCompare(right.option.key),
    )
    .map((item) => item.option)
}
