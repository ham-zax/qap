import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useEffect, useState } from 'react'

import type { QapApiClient } from '../../api/client'
import type { ResearchUniverseDto } from '../../api/types'
import { ResearchAssetSelector, type ResearchAssetSelection } from './ResearchAssetSelector'
import { STUDY_PERIODS, type ResearchStudy } from './researchStudies'

type Intent = Partial<Omit<ResearchStudy, 'id' | 'attempts'>>

function IdentityConfirmation({ selection, apiClient, onResolved, onBusyChange }: {
  selection: ResearchAssetSelection; apiClient: QapApiClient
  onResolved: (next: ResearchUniverseDto, canonicalId: string) => void
  onBusyChange: (busy: boolean) => void
}) {
  const [assetId, setAssetId] = useState('')
  const [reference, setReference] = useState('')
  const identity = useMutation({
    mutationFn: () => {
      if (!selection.venue || !selection.venueAssetCode) throw new Error('Review this identity in asset setup.')
      return apiClient.setResearchUniverseIdentityMapping({
        venue: selection.venue, venue_asset_code: selection.venueAssetCode,
        canonical_asset_id: assetId, asset_identity_version: reference,
      })
    },
    onSuccess: (next) => onResolved(next, assetId.trim().toUpperCase()),
  })
  useEffect(() => { onBusyChange(identity.isPending) }, [identity.isPending, onBusyChange])
  useEffect(() => () => onBusyChange(false), [onBusyChange])
  return (
    <section className="mt-4 rounded-md border border-warning/40 bg-subtle p-4">
      <h3 className="m-0 font-semibold text-foreground">Confirm which asset {selection.symbol} represents</h3>
      <p className="mt-2 text-sm leading-6 text-secondary">
        {selection.venue} uses this code for {selection.venueSymbols.slice(0, 3).join(', ')}.
        Verify the asset using the venue listing and an independent identity source. Matching names alone are insufficient.
        {selection.symbol === 'USDT' ? ' This identifies the price quote currency; it does not approve holding it or grant permission to trade.' : ''}
      </p>
      <div className="grid gap-3 md:grid-cols-2">
        <label className="text-sm text-secondary">Verified asset identifier
          <input value={assetId} onChange={(event) => setAssetId(event.target.value.toUpperCase())}
            placeholder={selection.symbol} className="mt-1 min-h-11 w-full rounded-md border border-border bg-canvas px-3" />
        </label>
        <label className="text-sm text-secondary">Verified identity reference
          <input value={reference} onChange={(event) => setReference(event.target.value)}
            placeholder="Contract address or versioned identity record"
            className="mt-1 min-h-11 w-full rounded-md border border-border bg-canvas px-3" />
        </label>
      </div>
      <p className="mt-2 text-xs leading-5 text-muted">Use the same identity reference for the same asset across venues. If you cannot verify it, leave it unresolved.</p>
      <button type="button" disabled={!assetId.trim() || !reference.trim() || identity.isPending}
        onClick={() => identity.mutate()} className="mt-3 min-h-11 rounded-md bg-accent px-4 font-semibold text-canvas disabled:opacity-50">
        {identity.isPending ? 'Saving confirmation…' : `Confirm ${selection.symbol} identity`}
      </button>
      {identity.isError ? <p role="alert" className="text-sm text-negative">{identity.error.message}</p> : null}
    </section>
  )
}

export function PairResearchSetup({ apiClient, universe, study, assetA, assetB, busy, onChange, onBusyChange }: {
  apiClient: QapApiClient; universe: ResearchUniverseDto; study: ResearchStudy
  assetA: ResearchAssetSelection | null; assetB: ResearchAssetSelection | null
  busy: boolean; onChange: (patch: Intent) => void
  onBusyChange: (busy: boolean) => void
}) {
  const client = useQueryClient()
  const [identityBusy, setIdentityBusy] = useState(false)
  const accept = async (next: ResearchUniverseDto) => {
    client.setQueryData(['research-universe'], next)
    await client.invalidateQueries({ queryKey: ['research-recipe-product-context'] })
  }
  const refresh = useMutation({ mutationFn: () => apiClient.refreshResearchUniverseDirectory(), onSuccess: accept })
  const admission = useMutation({
    mutationFn: (id: string) => apiClient.setResearchUniverseAdmission({ canonical_asset_id: id, approved: true }),
    onSuccess: accept,
  })
  const setupBusy = identityBusy || refresh.isPending || admission.isPending
  useEffect(() => { onBusyChange(setupBusy) }, [setupBusy, onBusyChange])
  useEffect(() => () => onBusyChange(false), [onBusyChange])
  const unresolved = [assetA, assetB].find((asset) => asset && !asset.canonicalAssetId)
  const approval = [assetA, assetB].find((asset) => asset?.canonicalAssetId && !asset.approved)
  const conflict = [assetA, assetB].find((asset) => asset?.canonicalAssetId && asset.identityState !== 'resolved')
  const aVenues = universe.assets.find((asset) => asset.canonical_asset_id === assetA?.canonicalAssetId)?.venues ?? []
  const bVenues = universe.assets.find((asset) => asset.canonical_asset_id === assetB?.canonicalAssetId)?.venues ?? []
  const hasCommonVenue = aVenues.some((a) => a.trading && bVenues.some((b) => b.trading && b.venue === a.venue))
  const quoteReviews = universe.identity_reviews.filter((review) => review.venue_asset_code === 'USDT')

  return (
    <fieldset disabled={busy} className="m-0 min-w-0 border-0 p-0 disabled:opacity-70">
      <legend className="text-xl font-semibold text-foreground">Your research question</legend>
      <p className="mt-2 text-sm leading-6 text-secondary">Choose two assets and what you want to learn. Nothing here places orders.</p>
      <div className="mt-4 grid gap-3 sm:grid-cols-2" role="radiogroup" aria-label="Research mode">
        <label className={`cursor-pointer rounded-md border p-4 ${study.mode === 'relationship' ? 'border-accent bg-subtle' : 'border-border'}`}>
          <input type="radio" name="research-mode" value="relationship" checked={study.mode === 'relationship'}
            onChange={() => onChange({ mode: 'relationship' })} /> <strong className="text-foreground">Relationship</strong>
          <span className="mt-1 block text-xs leading-5 text-secondary">See how their historical prices moved together. No strategy is tested.</span>
        </label>
        <label className={`cursor-pointer rounded-md border p-4 ${study.mode === 'backtest_comparison' ? 'border-accent bg-subtle' : 'border-border'}`}>
          <input type="radio" name="research-mode" value="backtest_comparison" checked={study.mode === 'backtest_comparison'}
            onChange={() => onChange({ mode: 'backtest_comparison' })} /> <strong className="text-foreground">Backtest comparison</strong>
          <span className="mt-1 block text-xs leading-5 text-secondary">Test whether rebalancing improved wealth against holding and simple rebalancing after modeled costs.</span>
        </label>
      </div>
      {universe.directory_status !== 'observed' ? (
        <div className="my-4 rounded-md border border-border bg-subtle p-4">
          <p className="mt-0 text-sm text-secondary">First, load the available spot markets. You choose which assets to include.</p>
          <button type="button" disabled={refresh.isPending} onClick={() => refresh.mutate()}
            className="min-h-11 rounded-md bg-accent px-4 font-semibold text-canvas">{refresh.isPending ? 'Loading markets…' : 'Load available assets'}</button>
        </div>
      ) : null}
      {refresh.isError ? <p role="alert" className="text-sm text-negative">{refresh.error.message}</p> : null}
      <div className="mt-4 grid gap-4 md:grid-cols-2">
        <ResearchAssetSelector label="First asset" universe={universe} selected={assetA}
          excludeCanonicalAssetIds={assetB?.canonicalAssetId ? [assetB.canonicalAssetId] : []}
          onSelect={(asset) => onChange({ assetA: asset })} onClear={() => onChange({ assetA: null })} />
        <ResearchAssetSelector label="Second asset" universe={universe} selected={assetB}
          excludeCanonicalAssetIds={assetA?.canonicalAssetId ? [assetA.canonicalAssetId] : []}
          onSelect={(asset) => onChange({ assetB: asset })} onClear={() => onChange({ assetB: null })} />
      </div>
      <div className="mt-5" role="radiogroup" aria-label="Research period">
        <p className="mb-2 text-sm font-semibold text-secondary">Period</p>
        <div className="grid gap-2 sm:grid-cols-3">
          {Object.entries(STUDY_PERIODS).map(([value, period]) => (
            <label key={value}
              className={`flex min-h-12 cursor-pointer items-center gap-3 rounded-md border px-4 py-2 ${study.horizon === value ? 'border-accent bg-subtle text-foreground' : 'border-border text-secondary'}`}>
              <input type="radio" name="pair-period" value={value} checked={study.horizon === value}
                onChange={() => onChange({ horizon: value as ResearchStudy['horizon'] })} />
              <span>
                <strong className="block text-sm">{period.label}</strong>
                <span className="block text-xs text-muted">{period.detail}</span>
              </span>
            </label>
          ))}
        </div>
      </div>
      <p className="mt-2 text-xs leading-5 text-muted">Trailing completed history. Development comparison only; this is not untouched holdout confirmation.</p>
      {unresolved ? (
        <IdentityConfirmation key={unresolved.key} selection={unresolved} apiClient={apiClient}
          onBusyChange={setIdentityBusy}
          onResolved={(next, canonicalId) => {
            void accept(next)
            const resolved = { ...unresolved, key: `asset:${canonicalId}`, canonicalAssetId: canonicalId, identityState: 'resolved' as const }
            onChange(assetA?.key === unresolved.key ? { assetA: resolved } : { assetB: resolved })
          }} />
      ) : conflict ? (
        <p role="alert" className="mt-4 text-sm text-warning">{conflict.symbol} has conflicting identity records. <a className="underline" href="/universe">Review asset identities</a>; this study will stay saved.</p>
      ) : approval?.canonicalAssetId ? (
        <div className="mt-4 rounded-md border border-warning/40 p-4">
          <p className="mt-0 text-sm text-secondary">Allow {approval.symbol} in your research? This records an asset you are willing to own; it does not place orders.</p>
          <button type="button" disabled={admission.isPending} onClick={() => admission.mutate(approval.canonicalAssetId!)}
            className="min-h-11 rounded-md bg-accent px-4 font-semibold text-canvas">{admission.isPending ? 'Saving…' : `Allow ${approval.symbol} in research`}</button>
          {admission.isError ? <p role="alert" className="text-sm text-negative">{admission.error.message}</p> : null}
        </div>
      ) : null}
      {assetA?.approved && assetB?.approved && !hasCommonVenue && quoteReviews.length > 0 ? (
        <section className="mt-5">
          <h3 className="text-base font-semibold text-foreground">Finish price-data setup</h3>
          <p className="text-sm leading-6 text-secondary">The price paths may need a quote-currency identity. Confirm it on a venue listing both assets, then continue here. Asset and venue availability are checked again before research.</p>
          {quoteReviews.map((review) => (
            <IdentityConfirmation key={`${review.venue}:${review.venue_asset_code}`}
              onBusyChange={setIdentityBusy}
              apiClient={apiClient} onResolved={(next) => { void accept(next) }}
              selection={{ key: `quote:${review.venue}`, symbol: review.venue_asset_code,
                canonicalAssetId: null, approved: false, identityState: 'review_required',
                venue: review.venue, venueAssetCode: review.venue_asset_code, venueSymbols: review.venue_symbols }} />
          ))}
        </section>
      ) : null}
      {universe.directory_status === 'observed' ? <details className="mt-4 text-xs text-muted">
        <summary className="cursor-pointer py-2">Asset availability</summary>
        <button type="button" disabled={refresh.isPending} onClick={() => refresh.mutate()} className="min-h-11 text-accent">{refresh.isPending ? 'Refreshing…' : 'Refresh available markets'}</button>
      </details> : null}
    </fieldset>
  )
}
