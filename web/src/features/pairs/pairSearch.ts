export type PairView = 'ratio' | 'log' | 'normalized' | 'anchor'

export interface PairSearchInput {
  orientation: string | null
  anchor: string
  view: PairView
}

export interface PairSearch {
  orientation: string
  anchor: string
  view: PairView
}

const PAIR_VIEWS = new Set<PairView>(['ratio', 'log', 'normalized', 'anchor'])

function stringValue(value: unknown): string | null {
  if (typeof value !== 'string') return null
  const trimmed = value.trim()
  return trimmed.length > 0 ? trimmed : null
}

export function parsePairSearch(raw: Record<string, unknown>): PairSearchInput {
  const orientation = stringValue(raw.orientation)
  const anchor = stringValue(raw.anchor) ?? 'none'
  const requestedView = stringValue(raw.view)
  const view =
    requestedView && PAIR_VIEWS.has(requestedView as PairView)
      ? (requestedView as PairView)
      : 'ratio'
  return { orientation, anchor, view }
}

export function canonicalPairSearch(
  params: { assetX: string; assetY: string },
  input: PairSearchInput,
): { search: PairSearch; changed: boolean } {
  const assetX = params.assetX.trim().toUpperCase()
  const assetY = params.assetY.trim().toUpperCase()
  const forward = `${assetX}/${assetY}`
  const reverse = `${assetY}/${assetX}`
  const requestedOrientation = input.orientation?.trim().toUpperCase() ?? forward
  const orientation =
    requestedOrientation === forward || requestedOrientation === reverse
      ? requestedOrientation
      : forward
  const anchor =
    input.anchor.trim().toLowerCase() === 'none'
      ? 'none'
      : input.anchor.trim().toUpperCase()
  const view = anchor === 'none' && input.view === 'anchor' ? 'ratio' : input.view
  const search = { orientation, anchor, view }
  const changed =
    input.orientation !== orientation ||
    input.anchor !== anchor ||
    input.view !== search.view
  return { search, changed }
}

export function toggleOrientation(orientation: string): string {
  const [base, quote, ...extra] = orientation.split('/')
  if (!base || !quote || extra.length > 0) {
    throw new Error(`invalid pair orientation: ${orientation}`)
  }
  return `${quote}/${base}`
}
