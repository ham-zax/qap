import { useMutation, useQuery } from '@tanstack/react-query'
import { useMemo, useState } from 'react'

import type { QapApiClient } from '../../api/client'
import type {
  BasketListDto,
  BasketRunRequestDto,
  OperationRefDto,
  ScanListDto,
} from '../../api/types'
import { Badge } from '../../components/ui/Badge'
import { formatResearchTimestamp } from '../../lib/format'
import { BasketGraph } from './BasketGraph'
import { BasketResults } from './BasketResults'
import { BasketScopeControls } from './BasketScopeControls'

interface BasketHomeProps {
  apiClient: QapApiClient
  baskets: BasketListDto
  scans: ScanListDto
}

type Venue = 'binance' | 'gate'
type Horizon = 'short' | 'medium' | 'swing'

function isVenue(value: string): value is Venue {
  return value === 'binance' || value === 'gate'
}

function isHorizon(value: string): value is Horizon {
  return value === 'short' || value === 'medium' || value === 'swing'
}

function scopeLabel(horizon: Horizon | undefined) {
  if (horizon === 'short') return 'Short horizon'
  if (horizon === 'medium') return 'Medium horizon'
  if (horizon === 'swing') return 'Swing horizon'
  return 'Scope unavailable'
}

function relationshipLabel(candidate: {
  automatic_neighbor_selected: boolean
  manual_pinned: boolean
  deep_replay_status?: string | null
  replay_failure_reason?: string | null
}) {
  if (candidate.manual_pinned) return 'Manual research relationship'
  if (
    candidate.deep_replay_status === 'setup_failed' &&
    candidate.replay_failure_reason === 'unsupported_direct_market'
  ) {
    return 'Indirect research relationship'
  }
  if (candidate.automatic_neighbor_selected) return 'Scanner-neighbor relationship'
  return 'Admitted relationship'
}

function isProductSource(scan: ScanListDto['items'][number]) {
  return scan.claim?.kind === 'current_approved_retrospective'
}

function sourceBoundary(scan: ScanListDto['items'][number] | undefined) {
  if (!scan) return 'Research boundary unavailable'
  if (isProductSource(scan)) {
    return scan.eligible_information_end
      ? `Data through ${formatResearchTimestamp(scan.eligible_information_end)}`
      : 'Data boundary unavailable'
  }
  if (scan.claim?.kind === 'historical_pit') {
    return scan.as_of
      ? `Historical universe as of ${formatResearchTimestamp(scan.as_of)}`
      : 'Historical boundary unavailable'
  }
  const boundary = scan.eligible_information_end ?? scan.as_of
  return boundary
    ? `Research data boundary ${formatResearchTimestamp(boundary)}`
    : 'Research boundary unavailable'
}

export function BasketHome({ apiClient, baskets, scans }: BasketHomeProps) {
  const validScans = scans.items
    .filter((item) => item.artifact_status === 'valid')
    .sort((left, right) => Number(isProductSource(right)) - Number(isProductSource(left)))
  const [scanId, setScanId] = useState(validScans[0]?.scan_id ?? '')
  const [venueOverride, setVenueOverride] = useState<Venue | ''>('')
  const [horizonOverride, setHorizonOverride] = useState<Horizon | ''>('')
  const [resolutionOverride, setResolutionOverride] = useState('')
  const [assets, setAssets] = useState<string[]>([])
  const [selectedEdges, setSelectedEdges] = useState<Record<string, string>>({})
  const [operation, setOperation] = useState<OperationRefDto | null>(null)
  const selectedScan = validScans.find((item) => item.scan_id === scanId)
  const selectedClaim = selectedScan?.claim
  const productSource = selectedClaim?.kind === 'current_approved_retrospective'

  const scanQuery = useQuery({
    queryKey: ['basket-draft-scan', scanId],
    queryFn: () => apiClient.getScan(scanId),
    enabled: Boolean(scanId),
  })
  const candidateQuery = useQuery({
    queryKey: ['basket-draft-candidates', scanId],
    queryFn: () => apiClient.listScanCandidates(scanId),
    enabled: Boolean(scanId),
  })

  const availableVenues = useMemo(
    () =>
      [...new Set((scanQuery.data?.graph_scopes ?? []).map((item) => item.venue))]
        .filter(isVenue)
        .sort(),
    [scanQuery.data?.graph_scopes],
  )
  const effectiveVenue = availableVenues.includes(venueOverride as Venue)
    ? (venueOverride as Venue)
    : availableVenues[0]

  const availableHorizons = useMemo(
    () =>
      [
        ...new Set(
          (scanQuery.data?.graph_scopes ?? [])
            .filter((item) => item.venue === effectiveVenue)
            .map((item) => item.horizon),
        ),
      ]
        .filter(isHorizon)
        .sort(),
    [effectiveVenue, scanQuery.data?.graph_scopes],
  )
  const effectiveHorizon = availableHorizons.includes(horizonOverride as Horizon)
    ? (horizonOverride as Horizon)
    : availableHorizons[0]

  const availableResolutions = useMemo(
    () =>
      [
        ...new Set(
          (candidateQuery.data?.items ?? [])
            .filter(
              (item) =>
                item.venue === effectiveVenue &&
                item.horizon === effectiveHorizon &&
                item.trial_status === 'valid',
            )
            .map((item) => item.resolution),
        ),
      ].sort(),
    [candidateQuery.data?.items, effectiveHorizon, effectiveVenue],
  )
  const effectiveResolution = availableResolutions.includes(resolutionOverride)
    ? resolutionOverride
    : availableResolutions[0]

  const scopeAssets = useMemo(
    () =>
      [
        ...new Set(
          (scanQuery.data?.universe ?? [])
            .filter(
              (item) =>
                item.venue === effectiveVenue &&
                item.horizon === effectiveHorizon &&
                (item.automatic_eligible || item.forensic_research_allowed),
            )
            .map((item) => item.asset_id),
        ),
      ].sort(),
    [effectiveHorizon, effectiveVenue, scanQuery.data?.universe],
  )

  const candidates = useMemo(
    () =>
      (candidateQuery.data?.items ?? []).filter(
        (item) =>
          item.venue === effectiveVenue &&
          item.horizon === effectiveHorizon &&
          item.resolution === effectiveResolution &&
          item.trial_status === 'valid' &&
          item.deep_replay_status !== 'replay_failed' &&
          (item.deep_replay_status !== 'setup_failed' ||
            item.replay_failure_reason === 'unsupported_direct_market') &&
          assets.includes(item.pair_id.split('/')[0] ?? '') &&
          assets.includes(item.pair_id.split('/')[1] ?? ''),
      ),
    [
      assets,
      candidateQuery.data?.items,
      effectiveHorizon,
      effectiveResolution,
      effectiveVenue,
    ],
  )

  const pairs = useMemo(
    () => [...new Set(candidates.map((item) => item.pair_id))].sort(),
    [candidates],
  )
  const topologyEdges = pairs.map((pair) => ({
    pair,
    label: selectedEdges[pair]
      ? 'Selected relationship evidence'
      : 'Relationship evidence available',
  }))
  const selectedCandidateIds = Object.values(selectedEdges).filter(Boolean)
  const momentum = productSource
    ? undefined
    : scanQuery.data?.momentum_generations.find(
        (item) => item.venue === effectiveVenue && item.horizon === effectiveHorizon,
      )

  const mutation = useMutation({
    mutationFn: (command: BasketRunRequestDto) => apiClient.runBasket(command),
    onSuccess: setOperation,
  })

  function resetSelection() {
    setAssets([])
    setSelectedEdges({})
  }

  function toggleAsset(asset: string) {
    setAssets((current) => {
      if (current.includes(asset)) {
        const next = current.filter((item) => item !== asset)
        setSelectedEdges((edges) =>
          Object.fromEntries(
            Object.entries(edges).filter(([pair]) => {
              const [a, b] = pair.split('/')
              return next.includes(a ?? '') && next.includes(b ?? '')
            }),
          ),
        )
        return next
      }
      return current.length >= 6 ? current : [...current, asset]
    })
  }

  function analyzePortfolio() {
    if (!effectiveVenue || !effectiveHorizon || !effectiveResolution) return
    mutation.mutate({
      scan_id: scanId,
      venue: effectiveVenue,
      horizon: effectiveHorizon,
      decision_resolution: effectiveResolution,
      economic_assets: assets,
      candidate_ids: selectedCandidateIds,
      momentum_scan_id: productSource ? null : (momentum?.momentum_scan_id ?? null),
    })
  }

  const canAnalyze =
    Boolean(effectiveVenue && effectiveHorizon && effectiveResolution) &&
    assets.length >= 3 &&
    assets.length <= 6 &&
    selectedCandidateIds.length > 0

  return (
    <section className="min-w-0">
      <header className="mb-8 max-w-4xl">
        <p className="mb-2 text-xs font-semibold uppercase tracking-[0.1em] text-accent">
          Portfolios
        </p>
        <h1 className="mb-3 text-3xl font-bold tracking-tight text-foreground md:text-4xl">
          Analyze a portfolio
        </h1>
        <p className="m-0 text-sm leading-6 text-secondary md:text-base">
          Select 3–6 assets, connect only relationships backed by admitted research
          evidence, then let ordinary QAP produce the portfolio result. No target or
          resolver opinion is previewed before replay.
        </p>
      </header>

      {validScans.length === 0 ? (
        <p className="rounded-lg border border-border bg-panel p-5 text-secondary">
          No valid research is available yet. Find relationship evidence in Research
          before building a portfolio.
        </p>
      ) : (
        <>
          <section className="mb-6 rounded-lg border border-border bg-panel p-5">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div className="max-w-3xl">
                <p className="m-0 text-xs font-semibold uppercase tracking-[0.08em] text-muted">
                  Portfolio research source
                </p>
                <h2 className="mt-2 mb-2 text-lg font-semibold text-foreground">
                  {selectedClaim?.label ?? 'Versioned Research Claim'}
                </h2>
                <p className="m-0 text-sm leading-6 text-secondary">
                  {sourceBoundary(selectedScan)}.{' '}
                  {productSource
                    ? 'This is the frozen data boundary of Current Approved Market Research; it is not a historical point-in-time universe claim.'
                    : selectedClaim?.kind === 'historical_pit'
                      ? 'This Advanced source preserves the strict historical point-in-time universe claim.'
                      : 'This source keeps its backend-declared research claim unchanged.'}
                </p>
              </div>
              <Badge tone={productSource ? 'positive' : 'warning'}>
                {productSource ? 'Product source' : 'Advanced source'}
              </Badge>
            </div>
          </section>

          <div className="grid gap-6 xl:grid-cols-[minmax(0,1.15fr)_minmax(20rem,0.85fr)]">
          <section className="rounded-lg border border-border bg-panel p-5">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h2 className="mt-0 mb-1 text-lg font-semibold text-foreground">
                  Select portfolio assets
                </h2>
                <p className="m-0 text-sm text-secondary">
                  {scopeLabel(effectiveHorizon)} · {effectiveVenue ?? 'venue unavailable'} ·{' '}
                  {effectiveResolution ?? 'resolution unavailable'} evidence
                </p>
              </div>
              <Badge tone="info">3–6 assets</Badge>
            </div>

            {scanQuery.isError || candidateQuery.isError ? (
              <p className="mt-4 text-sm text-negative">
                The selected research evidence could not be loaded.
              </p>
            ) : null}

            <div className="mt-5 flex flex-wrap gap-2">
              {scopeAssets.length === 0 ? (
                <p className="text-sm text-secondary">
                  No eligible assets exist in this compatible research scope.
                </p>
              ) : (
                scopeAssets.map((asset) => (
                  <label
                    key={asset}
                    className="flex min-h-11 items-center gap-2 rounded-md border border-border px-3 text-sm"
                  >
                    <input
                      type="checkbox"
                      checked={assets.includes(asset)}
                      onChange={() => toggleAsset(asset)}
                    />
                    <span className="font-semibold text-foreground">{asset}</span>
                  </label>
                ))
              )}
            </div>
            <p className="mt-2 text-xs text-muted">
              {assets.length}/6 selected; choose at least 3.
            </p>

            <section className="mt-7" aria-labelledby="relationships-heading">
              <h2 id="relationships-heading" className="text-lg font-semibold text-foreground">
                Choose relationship evidence
              </h2>
              <p className="text-sm leading-6 text-secondary">
                Each line in the topology means QAP has admitted relationship evidence for
                that selected pair. Choose one admitted rule for any relationship you want
                QAP to use; missing lines mean no admitted relationship exists in this scope.
              </p>

              {pairs.length === 0 ? (
                <p className="text-sm text-secondary">
                  Select assets that share admitted relationship evidence.
                </p>
              ) : (
                <div className="space-y-3">
                  {pairs.map((pair) => {
                    const options = candidates.filter((item) => item.pair_id === pair)
                    const selected = options.find(
                      (item) => item.candidate_id === selectedEdges[pair],
                    )
                    return (
                      <article key={pair} className="rounded-md border border-border p-3">
                        <label className="grid gap-2 text-sm sm:grid-cols-[8rem_1fr] sm:items-center">
                          <span className="font-semibold text-foreground">{pair}</span>
                          <select
                            className="min-h-11 rounded-md border border-border bg-canvas px-3 text-sm text-foreground"
                            value={selectedEdges[pair] ?? ''}
                            onChange={(event) =>
                              setSelectedEdges((current) => ({
                                ...current,
                                [pair]: event.target.value,
                              }))
                            }
                          >
                            <option value="">Evidence available — do not use</option>
                            {options.map((candidate) => (
                              <option
                                key={candidate.candidate_id}
                                value={candidate.candidate_id}
                              >
                                {relationshipLabel(candidate)} · {candidate.model_family}
                              </option>
                            ))}
                          </select>
                        </label>
                        {selected ? (
                          <details className="mt-2 text-xs text-muted">
                            <summary className="cursor-pointer font-semibold">
                              Exact relationship rule
                            </summary>
                            <p className="mb-0 break-all font-mono">
                              {selected.model_family} · {selected.template_id} ·{' '}
                              {selected.orientation} · candidate {selected.candidate_id}
                              {selected.manual_pinned ? ' · manual pin' : ''}
                              {selected.deep_replay_status === 'setup_failed' &&
                              selected.replay_failure_reason === 'unsupported_direct_market'
                                ? ' · indirect/scout-only'
                                : ''}
                            </p>
                          </details>
                        ) : null}
                      </article>
                    )
                  })}
                </div>
              )}
            </section>

            <button
              type="button"
              className="mt-6 min-h-11 rounded-md bg-accent px-5 font-semibold text-canvas disabled:opacity-50"
              disabled={!canAnalyze || mutation.isPending}
              onClick={analyzePortfolio}
            >
              {mutation.isPending ? 'Starting…' : 'Analyze portfolio'}
            </button>
            {mutation.isError ? (
              <p className="mt-3 text-sm text-negative">{mutation.error.message}</p>
            ) : null}
            {operation ? (
              <p className="mt-3 text-sm text-secondary">
                Portfolio analysis started.{' '}
                <a
                  className="font-semibold text-accent"
                  href={`/operations/${operation.operation_id}`}
                >
                  Track it in Activity
                </a>
              </p>
            ) : null}

            <BasketScopeControls
              scans={validScans}
              scanId={scanId}
              availableVenues={availableVenues}
              venue={effectiveVenue}
              availableHorizons={availableHorizons}
              horizon={effectiveHorizon}
              availableResolutions={availableResolutions}
              resolution={effectiveResolution}
              onScanChange={(nextScanId) => {
                setScanId(nextScanId)
                setVenueOverride('')
                setHorizonOverride('')
                setResolutionOverride('')
                resetSelection()
              }}
              onVenueChange={(nextVenue) => {
                setVenueOverride(nextVenue)
                setHorizonOverride('')
                setResolutionOverride('')
                resetSelection()
              }}
              onHorizonChange={(nextHorizon) => {
                setHorizonOverride(nextHorizon)
                setResolutionOverride('')
                resetSelection()
              }}
              onResolutionChange={(nextResolution) => {
                setResolutionOverride(nextResolution)
                resetSelection()
              }}
            />
          </section>

          <aside className="rounded-lg border border-border bg-panel p-5">
            <div className="flex flex-wrap gap-2">
              <Badge tone="info">Pre-run topology only</Badge>
              {productSource ? (
                <Badge tone="neutral">Product momentum not required</Badge>
              ) : (
                <Badge tone="info">
                  {momentum ? 'Pair-blind context available' : 'No pair-blind context artifact'}
                </Badge>
              )}
            </div>
            <h2 className="mt-4 text-lg font-semibold text-foreground">
              Relationship availability
            </h2>
            <BasketGraph assets={assets} edges={topologyEdges} />
            <p className="text-sm leading-6 text-secondary">
              Lines show only admitted relationship evidence among the selected assets.
              They do not preview direction, resolver pressure, or target weights.
            </p>
            <p className="text-xs text-muted">
              {pairs.length} admitted relationship{pairs.length === 1 ? '' : 's'} available ·{' '}
              {selectedCandidateIds.length} selected for analysis.
            </p>

            {productSource ? (
              <div className="mt-4 border-t border-border pt-4">
                <p className="m-0 text-xs font-semibold uppercase tracking-[0.08em] text-muted">
                  Product source boundary
                </p>
                <p className="mt-2 mb-0 text-xs leading-5 text-muted">
                  Product portfolio creation uses the selected research scan and its frozen
                  execution generations. Product asset-momentum lineage is deliberately not
                  required or submitted for basket creation.
                </p>
              </div>
            ) : momentum ? (
              <div className="mt-4 border-t border-border pt-4">
                <p className="m-0 text-xs font-semibold uppercase tracking-[0.08em] text-muted">
                  Pair-blind market context
                </p>
                <p className="mt-2 text-xs leading-5 text-muted">
                  Context only — momentum is asset-level and is not relationship evidence.
                </p>
                <ul className="mt-2 space-y-1 pl-5 text-sm text-secondary">
                  {momentum.observations
                    .filter(
                      (item) => assets.includes(item.asset_id) && item.status === 'valid',
                    )
                    .sort((a, b) => (a.rank ?? 9999) - (b.rank ?? 9999))
                    .map((item) => (
                      <li key={item.asset_id}>
                        {item.asset_id}: rank {item.rank ?? '—'} · relative momentum{' '}
                        {item.relative_momentum?.toFixed(5) ?? '—'}
                      </li>
                    ))}
                </ul>
              </div>
            ) : null}
          </aside>
        </div>
        </>
      )}

      <BasketResults baskets={baskets} />
    </section>
  )
}
