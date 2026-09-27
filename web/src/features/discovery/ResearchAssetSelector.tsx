import { useMemo, useState } from 'react'

import type { ResearchUniverseDto } from '../../api/types'
import { Badge } from '../../components/ui/Badge'
import {
  rankResearchAssetOptions,
  researchAssetOptions,
  type ResearchAssetSelection,
} from './researchAssetSearch'

export type { ResearchAssetSelection } from './researchAssetSearch'

interface ResearchAssetSelectorProps {
  label: string
  universe: ResearchUniverseDto
  selected: ResearchAssetSelection | null
  onSelect: (selection: ResearchAssetSelection) => void
  onClear: () => void
  excludeCanonicalAssetIds?: string[]
  unresolvedOnly?: boolean
  placeholder?: string
}

export function ResearchAssetSelector({
  label,
  universe,
  selected,
  onSelect,
  onClear,
  excludeCanonicalAssetIds = [],
  unresolvedOnly = false,
  placeholder = 'Search BTC, W, ETH…',
}: ResearchAssetSelectorProps) {
  const [query, setQuery] = useState('')
  const options = useMemo(
    () =>
      researchAssetOptions(universe).filter(
        (option) =>
          (!unresolvedOnly || option.canonicalAssetId === null) &&
          (option.canonicalAssetId === null ||
            !excludeCanonicalAssetIds.includes(option.canonicalAssetId)),
      ),
    [excludeCanonicalAssetIds, unresolvedOnly, universe],
  )
  const matches = useMemo(
    () => rankResearchAssetOptions(options, query).slice(0, 16),
    [options, query],
  )
  const selectedAsset = selected?.canonicalAssetId
    ? universe.assets.find((asset) => asset.canonical_asset_id === selected.canonicalAssetId)
    : null
  const differingCodes = selectedAsset?.venues.filter(
    (venue) => venue.venue_asset_code && venue.venue_asset_code !== selected?.canonicalAssetId,
  ) ?? []

  if (selected) {
    return (
      <div className="rounded-md border border-border bg-canvas/35 p-4">
        <p className="m-0 text-xs font-semibold uppercase tracking-[0.08em] text-muted">
          {label}
        </p>
        <div className="mt-2 flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="m-0 text-lg font-semibold text-foreground">{selected.symbol}</p>
            <div className="mt-2 flex flex-wrap gap-2">
              {selected.canonicalAssetId ? (
                <Badge tone={selected.approved ? 'positive' : 'warning'}>
                  {selected.approved ? 'Approved' : 'Needs approval'}
                </Badge>
              ) : (
                <Badge tone="warning">Needs identity mapping</Badge>
              )}
              {selected.venue ? <Badge tone="neutral">{selected.venue}</Badge> : null}
            </div>
          </div>
          <button
            type="button"
            className="min-h-11 rounded-md border border-border px-4 text-sm font-semibold text-foreground"
            onClick={() => {
              setQuery('')
              onClear()
            }}
          >
            Change
          </button>
        </div>
        {selectedAsset?.venues.length || selected.venueSymbols.length ? (
          <p className="mt-3 mb-0 text-xs leading-5 text-secondary">
            Observed markets: {selectedAsset?.venues.length
              ? selectedAsset.venues.map((venue) => `${venue.venue} ${venue.venue_symbol}${venue.venue_asset_code ? ` (code ${venue.venue_asset_code})` : ''}`).join(' · ')
              : selected.venueSymbols.map((symbol) => `${selected.venue ?? 'venue'} ${symbol}`).join(' · ')}
          </p>
        ) : null}
        {selectedAsset?.asset_identity_version ? (
          <p className="mt-2 mb-0 break-all text-xs leading-5 text-secondary">
            Operator-entered identity reference: {selectedAsset.asset_identity_version}
          </p>
        ) : null}
        {differingCodes.length ? <p role="alert" className="mt-3 mb-0 text-sm leading-6 text-warning">
          A recorded venue code differs from {selected.symbol}: {differingCodes.map((venue) => `${venue.venue} ${venue.venue_asset_code}`).join(', ')}.
          This may be a valid alias or an incorrect mapping. QAP has not independently verified it; review the identity record before trusting results.
        </p> : null}
      </div>
    )
  }

  return (
    <div>
      <label className="block text-sm font-medium text-secondary">
        {label}
        <input
          className="mt-2 min-h-11 w-full rounded-md border border-border bg-canvas px-3 text-foreground"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder={placeholder}
          autoComplete="off"
        />
      </label>
      {query.trim() ? (
        matches.length ? (
          <div className="mt-2 max-h-72 overflow-y-auto rounded-md border border-border bg-panel p-2">
            {matches.map((option) => (
              <button
                key={option.key}
                type="button"
                className="flex min-h-11 w-full items-center justify-between gap-3 rounded-md px-3 py-2 text-left text-sm hover:bg-subtle"
                onClick={() => {
                  onSelect(option)
                  setQuery('')
                }}
              >
                <span>
                  <strong className="text-foreground">{option.symbol}</strong>
                  {option.venue ? (
                    <span className="ml-2 text-xs text-muted">{option.venue}</span>
                  ) : null}
                  {option.venueSymbols.length ? <span className="mt-1 block text-xs text-muted">Markets: {option.venueSymbols.slice(0, 2).join(' · ')}</span> : null}
                </span>
                <span className="text-xs text-muted">
                  {option.canonicalAssetId
                    ? option.approved
                      ? 'mapping recorded'
                      : 'mapping recorded · approval needed'
                    : 'identity mapping needed'}
                </span>
              </button>
            ))}
          </div>
        ) : (
          <p className="mt-2 text-sm text-muted">No current matching asset code.</p>
        )
      ) : null}
    </div>
  )
}
