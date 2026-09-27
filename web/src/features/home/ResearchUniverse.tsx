import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'

import type { QapApiClient } from '../../api/client'
import type {
  IdentityMappingRequestDto,
  ResearchUniverseDto,
  WorkspaceStatusDto,
} from '../../api/types'
import { Badge } from '../../components/ui/Badge'
import { formatResearchTimestamp } from '../../lib/format'
import {
  ResearchAssetSelector,
  type ResearchAssetSelection,
} from '../discovery/ResearchAssetSelector'

interface ResearchUniverseProps {
  apiClient: QapApiClient
  workspace: WorkspaceStatusDto
  data: ResearchUniverseDto
}

type IdentityReview = ResearchUniverseDto['identity_reviews'][number]

function dataStateLabel(state: ResearchUniverseDto['assets'][number]['data_state']) {
  return state === 'needs_data' ? 'Needs market data' : 'Not in research scope'
}

function identityReasonLabel(
  reason: ResearchUniverseDto['assets'][number]['identity_reason'],
) {
  if (reason === 'identity_version_conflict') return 'Identity versions conflict'
  if (reason === 'mapping_unavailable') return 'Identity mapping unavailable'
  return 'Operator mapping recorded'
}

export function ResearchUniverse({
  apiClient,
  workspace,
  data,
}: ResearchUniverseProps) {
  const queryClient = useQueryClient()
  const [universe, setUniverse] = useState(data)
  const [identitySelection, setIdentitySelection] =
    useState<ResearchAssetSelection | null>(null)
  const [identityDraft, setIdentityDraft] = useState<
    (IdentityMappingRequestDto & { key: string }) | null
  >(null)

  const acceptUniverse = (next: ResearchUniverseDto) => {
    setUniverse(next)
    queryClient.setQueryData(['research-universe'], next)
  }

  const refresh = useMutation({
    mutationFn: () => apiClient.refreshResearchUniverseDirectory(),
    onSuccess: acceptUniverse,
  })
  const identity = useMutation({
    mutationFn: (command: IdentityMappingRequestDto) =>
      apiClient.setResearchUniverseIdentityMapping(command),
    onSuccess: (next) => {
      acceptUniverse(next)
      setIdentityDraft(null)
      setIdentitySelection(null)
    },
  })
  const admission = useMutation({
    mutationFn: (command: { canonical_asset_id: string; approved: boolean }) =>
      apiClient.setResearchUniverseAdmission(command),
    onSuccess: acceptUniverse,
  })

  const quoteReviews = universe.identity_reviews.filter(
    (item) => item.venue_asset_code === 'USDT',
  )
  const startIdentityReview = (item: IdentityReview) => {
    setIdentitySelection({
      key: `review:${item.venue}:${item.venue_asset_code}`,
      symbol: item.venue_asset_code,
      canonicalAssetId: null,
      approved: false,
      identityState: 'review_required',
      venue: item.venue,
      venueAssetCode: item.venue_asset_code,
      venueSymbols: [...item.venue_symbols],
    })
    setIdentityDraft({
      key: `${item.venue}:${item.venue_asset_code}`,
      venue: item.venue,
      venue_asset_code: item.venue_asset_code,
      canonical_asset_id: '',
      asset_identity_version: '',
    })
  }

  const startIdentitySelection = (selection: ResearchAssetSelection) => {
    if (!selection.venue || !selection.venueAssetCode) return
    setIdentitySelection(selection)
    setIdentityDraft({
      key: `${selection.venue}:${selection.venueAssetCode}`,
      venue: selection.venue,
      venue_asset_code: selection.venueAssetCode,
      canonical_asset_id: '',
      asset_identity_version: '',
    })
  }

  const submitIdentity = () => {
    if (
      identityDraft === null ||
      !identityDraft.canonical_asset_id.trim() ||
      !identityDraft.asset_identity_version.trim()
    ) {
      return
    }
    identity.mutate({
      venue: identityDraft.venue,
      venue_asset_code: identityDraft.venue_asset_code,
      canonical_asset_id: identityDraft.canonical_asset_id,
      asset_identity_version: identityDraft.asset_identity_version,
    })
  }

  if (workspace.workspace_mode === 'sample') {
    return (
      <section className="min-w-0">
        <header className="mb-8 max-w-4xl">
          <p className="mb-2 text-xs font-semibold uppercase tracking-[0.1em] text-accent">
            Research Universe
          </p>
          <h1 className="mb-3 text-3xl font-bold tracking-tight text-foreground md:text-4xl">
            Local Market asset setup
          </h1>
        </header>
        <div className="rounded-lg border border-info/45 bg-panel p-5">
          <Badge tone="info">Sample Workspace</Badge>
          <h2 className="mt-3 mb-2 text-xl font-semibold text-foreground">
            Asset admission is read-only here
          </h2>
          <p className="m-0 max-w-3xl text-sm leading-6 text-secondary">
            Sample Workspace keeps its deterministic evidence separate. Start the Local
            Market workspace to refresh public markets, resolve asset identity, or change
            which economic assets QAP is allowed to research.
          </p>
        </div>
      </section>
    )
  }

  return (
    <section className="min-w-0">
      <header className="mb-8 max-w-4xl">
        <p className="mb-2 text-xs font-semibold uppercase tracking-[0.1em] text-accent">
          Research Universe
        </p>
        <h1 className="mb-3 text-3xl font-bold tracking-tight text-foreground md:text-4xl">
          Choose what QAP is allowed to research
        </h1>
        <p className="m-0 text-sm leading-6 text-secondary md:text-base">
          Exchange listings are discovery input only. An economic asset enters Local
          Market research only after you explicitly approve its canonical identity.
          Matching ticker text by itself is never treated as identity evidence.
        </p>
      </header>

      <section
        className="rounded-lg border border-border bg-panel p-5"
        aria-labelledby="directory-heading"
      >
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h2 id="directory-heading" className="m-0 text-xl font-semibold text-foreground">
              Current supported markets
            </h2>
            <p className="mt-2 mb-0 text-sm leading-6 text-secondary">
              Refreshes read only public Binance and Gate Spot metadata. Refreshing the
              directory never changes your approved asset set.
            </p>
          </div>
          <button
            className="min-h-11 rounded-md bg-accent px-4 py-2 text-sm font-semibold text-canvas disabled:opacity-50"
            type="button"
            disabled={refresh.isPending}
            onClick={() => refresh.mutate()}
          >
            {refresh.isPending
              ? 'Refreshing…'
              : universe.directory_status === 'observed'
                ? 'Refresh markets'
                : 'Load current markets'}
          </button>
        </div>

        {refresh.isError ? (
          <p className="mt-3 text-sm text-negative">{refresh.error.message}</p>
        ) : null}

        {universe.directory_status === 'observed' && universe.directory_observed_at ? (
          <div className="mt-4 rounded-md border border-border bg-subtle p-4 text-sm text-secondary">
            <p className="m-0">
              Last observed {formatResearchTimestamp(universe.directory_observed_at)} ·{' '}
              {universe.sources.length} public sources
            </p>
            <details className="mt-2">
              <summary className="min-h-11 cursor-pointer py-2 font-semibold text-accent">
                Source provenance
              </summary>
              <ul className="m-0 space-y-2 pl-5 text-xs text-muted">
                {universe.sources.map((source) => (
                  <li key={source.venue}>
                    {source.venue} · {source.source_id} · observed{' '}
                    {formatResearchTimestamp(source.observed_at)} · fingerprint{' '}
                    <code>{source.source_fingerprint.slice(0, 12)}…</code>
                  </li>
                ))}
              </ul>
            </details>
          </div>
        ) : (
          <p className="mt-4 rounded-md border border-warning/40 bg-subtle p-4 text-sm text-secondary">
            No current market directory has been observed in this Local Market workspace.
          </p>
        )}
      </section>

      <section className="mt-8" aria-labelledby="approved-assets-heading">
        <div className="mb-4">
          <p className="mb-1 text-xs font-semibold uppercase tracking-[0.1em] text-accent">
            Operator-controlled scope
          </p>
          <h2 id="approved-assets-heading" className="m-0 text-xl font-semibold text-foreground">
            Canonical assets
          </h2>
        </div>

        {universe.assets.length ? (
          <div className="space-y-4">
            {universe.assets.map((asset) => (
              <article
                key={asset.canonical_asset_id}
                className="rounded-lg border border-border bg-panel p-5"
              >
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge tone={asset.approved ? 'positive' : 'neutral'}>
                        {asset.approved ? 'Approved' : 'Not approved'}
                      </Badge>
                      <Badge tone={asset.identity_state === 'resolved' ? 'info' : 'warning'}>
                        {identityReasonLabel(asset.identity_reason)}
                      </Badge>
                    </div>
                    <h3 className="mt-3 mb-1 text-lg font-semibold text-foreground">
                      {asset.canonical_asset_id}
                    </h3>
                    <p className="m-0 text-sm text-secondary">
                      {dataStateLabel(asset.data_state)}
                      {asset.asset_identity_version
                        ? ` · recorded version ${asset.asset_identity_version}`
                        : ''}
                    </p>
                  </div>
                  <button
                    className="min-h-11 rounded-md border border-border px-4 text-sm font-semibold text-foreground disabled:opacity-50"
                    type="button"
                    disabled={admission.isPending}
                    onClick={() =>
                      admission.mutate({
                        canonical_asset_id: asset.canonical_asset_id,
                        approved: !asset.approved,
                      })
                    }
                  >
                    {asset.approved ? 'Remove approval' : 'Approve asset'}
                  </button>
                </div>

                {asset.venues.some((venue) => venue.venue_asset_code && venue.venue_asset_code !== asset.canonical_asset_id) ? (
                  <p role="alert" className="mt-4 rounded-md border border-warning/45 p-3 text-sm text-warning">
                    A venue code differs from {asset.canonical_asset_id}: {asset.venues.filter((venue) => venue.venue_asset_code && venue.venue_asset_code !== asset.canonical_asset_id).map((venue) => `${venue.venue} ${venue.venue_asset_code}`).join(', ')}. This may be a valid alias or a wrong mapping. QAP has not independently verified it.
                  </p>
                ) : null}

                {asset.venues.length ? (
                  <details className="mt-4 border-t border-border pt-3">
                    <summary className="min-h-11 cursor-pointer py-2 text-sm font-semibold text-accent">
                      {asset.venues.length} current supported venue
                      {asset.venues.length === 1 ? '' : 's'}
                    </summary>
                    <ul className="m-0 space-y-2 pl-5 text-sm text-secondary">
                      {asset.venues.map((venue) => (
                        <li key={`${venue.venue}:${venue.venue_symbol}`}>
                          {venue.venue} · {venue.trading ? 'Trading' : venue.status} · code{' '}
                          <code>{venue.venue_asset_code ?? 'not reported'}</code> · market <code>{venue.venue_symbol}</code>
                        </li>
                      ))}
                    </ul>
                  </details>
                ) : (
                  <p className="mt-4 mb-0 text-sm text-muted">
                    No currently resolved USDT market is available on Binance or Gate.
                  </p>
                )}
              </article>
            ))}
          </div>
        ) : (
          <p className="rounded-lg border border-border bg-panel p-5 text-sm leading-6 text-secondary">
            No canonical research assets are resolved yet. Load current markets, then
            confirm the identity of the assets you are willing to consider.
          </p>
        )}
        {admission.isError ? (
          <p className="mt-3 text-sm text-negative">{admission.error.message}</p>
        ) : null}
      </section>

      {universe.directory_status === 'observed' ? (
        <details className="mt-8 rounded-lg border border-border bg-panel p-5">
          <summary className="min-h-11 cursor-pointer py-2 text-lg font-semibold text-accent">
            Identity review · tell QAP what each venue code means
          </summary>
          <div className="mt-3 max-w-4xl">
            <p className="text-sm leading-6 text-secondary">
              Venue codes are observed market data, not proof of economic identity. QAP records your mapping but does not independently check the asset or identity reference. Use an independent source before recording it; matching ticker text is insufficient.
            </p>

            <div className="mt-4 rounded-md border border-accent/35 bg-canvas/35 p-4">
              <p className="m-0 text-xs font-semibold uppercase tracking-[0.08em] text-muted">
                Do this in order
              </p>
              <ol className="mt-3 mb-0 space-y-2 pl-5 text-sm leading-6 text-secondary">
                <li>Resolve the venue&apos;s USDT quote identity when QAP asks for it.</li>
                <li>Search for the base-asset code you want to review.</li>
                <li>
                  Record the canonical asset and identity version only after checking an independent source.
                </li>
                <li>Approve the canonical asset separately in the list above.</li>
              </ol>
              <p className="mt-3 mb-0 text-sm leading-6 text-secondary">
                <strong className="text-foreground">Example:</strong> after independently
                confirming that Binance <code>BTC</code> is the canonical <code>BTC</code>
                identity you intend to research, map that venue code to <code>BTC</code> and
                its recorded identity version. The mapping says “the operator considers these the same
                economic identity”; the separate approval says “QAP may research this
                asset.”
              </p>
            </div>

            {quoteReviews.length ? (
              <div className="mt-5 rounded-md border border-warning/40 bg-subtle p-4">
                <h3 className="m-0 text-base font-semibold text-foreground">
                  Quote identity required
                </h3>
                <p className="mt-2 text-sm text-secondary">
                  Every asset/USDT market contains two asset identities. Resolve the
                  venue&apos;s USDT quote identity first so QAP can safely turn that market into
                  a canonical current instrument.
                </p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {quoteReviews.map((item) => (
                    <button
                      key={`${item.venue}:${item.venue_asset_code}`}
                      className="min-h-11 rounded-md border border-border px-3 text-sm font-semibold text-foreground"
                      type="button"
                      onClick={() => startIdentityReview(item)}
                    >
                      Review {item.venue} {item.venue_asset_code}
                    </button>
                  ))}
                </div>
              </div>
            ) : null}

            <div className="mt-5">
              <ResearchAssetSelector
                label="Find a venue asset code to review"
                universe={universe}
                selected={identitySelection}
                unresolvedOnly
                onSelect={startIdentitySelection}
                onClear={() => {
                  setIdentitySelection(null)
                  setIdentityDraft(null)
                }}
                placeholder="Search BTC, W, ETH…"
              />
            </div>

            {identityDraft ? (
              <div className="mt-5 rounded-md border border-border bg-subtle p-4">
                <h3 className="m-0 text-base font-semibold text-foreground">
                  Record {identityDraft.venue} {identityDraft.venue_asset_code} mapping
                </h3>
                <div className="mt-3 grid gap-3 sm:grid-cols-2">
                  <label className="text-sm font-medium text-secondary">
                    Canonical economic asset (your assessment)
                    <span className="mt-1 block text-xs font-normal leading-5 text-muted">
                      The QAP asset key this venue code belongs to, for example BTC.
                    </span>
                    <input
                      className="mt-2 min-h-11 w-full rounded-md border border-border bg-canvas px-3 text-foreground"
                      value={identityDraft.canonical_asset_id}
                      onChange={(event) =>
                        setIdentityDraft({
                          ...identityDraft,
                          canonical_asset_id: event.target.value.toUpperCase(),
                        })
                      }
                      placeholder="Confirmed QAP asset key"
                    />
                  </label>
                  <label className="text-sm font-medium text-secondary">
                    Identity version or reference (your record)
                    <span className="mt-1 block text-xs font-normal leading-5 text-muted">
                      A stable identity record you checked independently. QAP validates only that this is non-empty and does not fetch a contract address.
                    </span>
                    <input
                      className="mt-2 min-h-11 w-full rounded-md border border-border bg-canvas px-3 text-foreground"
                      value={identityDraft.asset_identity_version}
                      onChange={(event) =>
                        setIdentityDraft({
                          ...identityDraft,
                          asset_identity_version: event.target.value,
                        })
                      }
                      placeholder="Confirmed token/contract version"
                    />
                  </label>
                </div>
                <div className="mt-4 flex flex-wrap gap-2">
                  <button
                    className="min-h-11 rounded-md bg-accent px-4 text-sm font-semibold text-canvas disabled:opacity-50"
                    type="button"
                    disabled={
                      identity.isPending ||
                      !identityDraft.canonical_asset_id.trim() ||
                      !identityDraft.asset_identity_version.trim()
                    }
                    onClick={submitIdentity}
                  >
                    {identity.isPending ? 'Saving…' : 'Record identity mapping'}
                  </button>
                  <button
                    className="min-h-11 rounded-md border border-border px-4 text-sm font-semibold text-foreground"
                    type="button"
                    onClick={() => {
                      setIdentityDraft(null)
                      setIdentitySelection(null)
                    }}
                  >
                    Cancel
                  </button>
                </div>
                {identity.isError ? (
                  <p className="mt-3 text-sm text-negative">{identity.error.message}</p>
                ) : null}
              </div>
            ) : null}
          </div>
        </details>
      ) : null}
    </section>
  )
}
