import { useMutation, useQuery } from '@tanstack/react-query'
import { useMemo, useState } from 'react'

import type { QapApiClient } from '../../api/client'
import type { BasketListDto, OperationRefDto, ScanListDto } from '../../api/types'
import { Badge } from '../../components/ui/Badge'
import { BasketGraph } from './BasketGraph'

interface BasketHomeProps {
  apiClient: QapApiClient
  baskets: BasketListDto
  scans: ScanListDto
}

type Venue = 'binance' | 'gate'
type Horizon = 'short' | 'medium' | 'swing'

export function BasketHome({ apiClient, baskets, scans }: BasketHomeProps) {
  const validScans = scans.items.filter((item) => item.artifact_status === 'valid')
  const [scanId, setScanId] = useState(validScans[0]?.scan_id ?? '')
  const [venue, setVenue] = useState<Venue>('binance')
  const [horizon, setHorizon] = useState<Horizon>('short')
  const [resolution, setResolution] = useState('1h')
  const [assets, setAssets] = useState<string[]>([])
  const [selectedEdges, setSelectedEdges] = useState<Record<string, string>>({})
  const [operation, setOperation] = useState<OperationRefDto | null>(null)

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

  const scopeAssets = useMemo(
    () =>
      (scanQuery.data?.universe ?? [])
        .filter(
          (item) =>
            item.venue === venue &&
            item.horizon === horizon &&
            (item.automatic_eligible || item.forensic_research_allowed),
        )
        .map((item) => item.asset_id),
    [horizon, scanQuery.data?.universe, venue],
  )

  const candidates = useMemo(
    () =>
      (candidateQuery.data?.items ?? []).filter(
        (item) =>
          item.venue === venue &&
          item.horizon === horizon &&
          item.resolution === resolution &&
          item.trial_status === 'valid' &&
          item.deep_replay_status !== 'replay_failed' &&
          (item.deep_replay_status !== 'setup_failed' ||
            item.replay_failure_reason === 'unsupported_direct_market') &&
          assets.includes(item.pair_id.split('/')[0] ?? '') &&
          assets.includes(item.pair_id.split('/')[1] ?? ''),
      ),
    [assets, candidateQuery.data?.items, horizon, resolution, venue],
  )

  const pairs = useMemo(
    () => [...new Set(candidates.map((item) => item.pair_id))].sort(),
    [candidates],
  )
  const graphEdges = pairs
    .filter((pair) => selectedEdges[pair])
    .map((pair) => ({ pair, label: selectedEdges[pair] }))
  const momentum = scanQuery.data?.momentum_generations.find(
    (item) => item.venue === venue && item.horizon === horizon,
  )

  const mutation = useMutation({
    mutationFn: () =>
      apiClient.runBasket({
        scan_id: scanId,
        venue,
        horizon,
        decision_resolution: resolution,
        economic_assets: assets,
        candidate_ids: Object.values(selectedEdges).filter(Boolean),
        momentum_scan_id: momentum?.momentum_scan_id ?? null,
      }),
    onSuccess: setOperation,
  })

  const toggleAsset = (asset: string) => {
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

  const canRun = assets.length >= 3 && assets.length <= 6 && graphEdges.length > 0

  return (
    <section className="min-w-0">
      <header className="mb-8 max-w-4xl">
        <p className="mb-2 text-xs font-semibold uppercase tracking-[0.1em] text-accent">Slice 3 portfolio research</p>
        <h1 className="mb-3 text-3xl font-bold tracking-tight text-foreground md:text-4xl">Baskets</h1>
        <p className="m-0 text-sm leading-6 text-secondary md:text-base">
          Draft 3–6 asset baskets locally, select admitted candidate edges, and submit one authoritative QAP basket run. No target is previewed before replay.
        </p>
      </header>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.15fr)_minmax(20rem,0.85fr)]">
        <section className="rounded-lg border border-border bg-panel p-5">
          <h2 className="mt-0 text-lg font-semibold text-foreground">Local basket draft</h2>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <select className="min-h-11 rounded-md border border-border bg-canvas px-3 text-sm text-foreground" value={scanId} onChange={(event) => { setScanId(event.target.value); setAssets([]); setSelectedEdges({}) }} aria-label="Source scan">
              <option value="">Select scan</option>
              {validScans.map((scan) => <option key={scan.scan_id} value={scan.scan_id}>{scan.horizons.join('/')} · {scan.scan_id.slice(0, 8)}</option>)}
            </select>
            <select className="min-h-11 rounded-md border border-border bg-canvas px-3 text-sm text-foreground" value={venue} onChange={(event) => { setVenue(event.target.value as Venue); setAssets([]); setSelectedEdges({}) }} aria-label="Venue">
              <option value="binance">binance</option><option value="gate">gate</option>
            </select>
            <select className="min-h-11 rounded-md border border-border bg-canvas px-3 text-sm text-foreground" value={horizon} onChange={(event) => { setHorizon(event.target.value as Horizon); setAssets([]); setSelectedEdges({}) }} aria-label="Horizon">
              <option value="short">short</option><option value="medium">medium</option><option value="swing">swing</option>
            </select>
            <input className="min-h-11 rounded-md border border-border bg-canvas px-3 text-foreground" value={resolution} onChange={(event) => { setResolution(event.target.value); setSelectedEdges({}) }} aria-label="Decision resolution" placeholder="1h" />
          </div>

          <h3 className="mt-6 text-sm font-semibold text-foreground">Economic assets</h3>
          <div className="flex flex-wrap gap-2">
            {scopeAssets.map((asset) => (
              <label key={asset} className="flex min-h-11 items-center gap-2 rounded-md border border-border px-3 text-sm">
                <input type="checkbox" checked={assets.includes(asset)} onChange={() => toggleAsset(asset)} />{asset}
              </label>
            ))}
          </div>
          <p className="mt-2 text-xs text-muted">{assets.length}/6 selected; minimum 3.</p>

          <h3 className="mt-6 text-sm font-semibold text-foreground">One admitted rule per relationship</h3>
          {pairs.length === 0 ? <p className="text-sm text-secondary">Select assets with admitted candidate evidence at this scope/resolution.</p> : (
            <div className="space-y-3">
              {pairs.map((pair) => {
                const options = candidates.filter((item) => item.pair_id === pair)
                return (
                  <label key={pair} className="grid gap-2 rounded-md border border-border p-3 text-sm sm:grid-cols-[8rem_1fr] sm:items-center">
                    <span className="font-semibold text-foreground">{pair}</span>
                    <select className="min-h-11 rounded-md border border-border bg-canvas px-3 text-sm text-foreground" value={selectedEdges[pair] ?? ''} onChange={(event) => setSelectedEdges((current) => ({ ...current, [pair]: event.target.value }))}>
                      <option value="">No edge selected</option>
                      {options.map((candidate) => (
                        <option key={candidate.candidate_id} value={candidate.candidate_id}>
                          {candidate.model_family} · {candidate.template_id} · {candidate.orientation}{candidate.manual_pinned ? ' · manual' : ''}{candidate.deep_replay_status === 'setup_failed' && candidate.replay_failure_reason === 'unsupported_direct_market' ? ' · indirect' : ''}
                        </option>
                      ))}
                    </select>
                  </label>
                )
              })}
            </div>
          )}

          <button type="button" className="mt-6 min-h-11 rounded-md bg-accent px-5 font-semibold text-canvas disabled:opacity-50" disabled={!canRun || mutation.isPending} onClick={() => mutation.mutate()}>
            {mutation.isPending ? 'Starting…' : 'Run basket through QAP'}
          </button>
          {mutation.isError ? <p className="mt-3 text-sm text-negative">{mutation.error.message}</p> : null}
          {operation ? <p className="mt-3 text-sm text-secondary">Operation started. <a className="font-semibold text-accent" href={`/operations/${operation.operation_id}`}>Track operation</a></p> : null}
        </section>

        <aside className="rounded-lg border border-border bg-panel p-5">
          <div className="flex flex-wrap gap-2"><Badge tone="info">Pre-run topology only</Badge>{momentum ? <Badge tone="positive">Momentum available</Badge> : <Badge tone="warning">No momentum artifact</Badge>}</div>
          <h2 className="mt-4 text-lg font-semibold text-foreground">Selected topology</h2>
          <BasketGraph assets={assets} edges={graphEdges} />
          <p className="text-sm leading-6 text-secondary">
            This preview shows only selected assets and candidate relationships. Current edge opinions, resolver pressure, and final target weights do not exist authoritatively until ordinary QAP replay.
          </p>
          {momentum ? (
            <div className="mt-4 border-t border-border pt-4">
              <p className="m-0 text-xs font-semibold uppercase tracking-[0.08em] text-muted">Pair-blind context</p>
              <ul className="mt-2 space-y-1 pl-5 text-sm text-secondary">
                {momentum.observations.filter((item) => assets.includes(item.asset_id) && item.status === 'valid').sort((a, b) => (a.rank ?? 9999) - (b.rank ?? 9999)).map((item) => <li key={item.asset_id}>{item.asset_id}: rank {item.rank ?? '—'} · {item.relative_momentum?.toFixed(5) ?? '—'}</li>)}
              </ul>
            </div>
          ) : null}
        </aside>
      </div>

      <section className="mt-8" aria-labelledby="completed-baskets-heading">
        <h2 id="completed-baskets-heading" className="text-xl font-semibold text-foreground">Completed baskets</h2>
        {baskets.items.length === 0 ? (
          <p className="text-sm text-secondary">No terminal basket evidence yet.</p>
        ) : (
          <div className="mt-4 grid gap-4 lg:grid-cols-2">
            {baskets.items.map((basket) => (
              <article key={basket.basket_id} className="rounded-lg border border-border bg-panel p-5">
                <div className="flex flex-wrap gap-2">
                  <Badge tone={basket.artifact_status === 'valid' ? 'positive' : 'negative'}>{basket.artifact_status}</Badge>
                  {basket.economic_gate_status ? <Badge tone={basket.economic_gate_status.includes('survivor') ? 'positive' : 'warning'}>{basket.economic_gate_status}</Badge> : null}
                </div>
                <h3 className="mt-4 mb-2 text-base font-semibold text-foreground">{basket.economic_assets.join(' · ') || basket.basket_id.slice(0, 12)}</h3>
                <p className="m-0 text-sm text-secondary">{basket.venue ?? '—'} / {basket.horizon ?? '—'} · {basket.decision_resolution ?? '—'}</p>
                {basket.error ? <p className="mt-2 text-sm text-negative">{basket.error.message}</p> : null}
                <a className="mt-4 inline-flex min-h-11 items-center font-semibold text-accent" href={`/baskets/${basket.basket_id}`}>Inspect basket</a>
              </article>
            ))}
          </div>
        )}
      </section>
    </section>
  )
}
