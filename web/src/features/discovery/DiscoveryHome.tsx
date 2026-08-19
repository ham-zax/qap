import { useMutation } from '@tanstack/react-query'
import { useMemo, useState } from 'react'

import type { QapApiClient } from '../../api/client'
import type {
  OperationRefDto,
  RunScanRequestDto,
  ScanListDto,
  ScannerProtocolDto,
} from '../../api/types'
import { Badge } from '../../components/ui/Badge'
import { formatResearchTimestamp } from '../../lib/format'

type Horizon = RunScanRequestDto['horizons'][number]
type Pin = RunScanRequestDto['pins'][number]

interface DiscoveryHomeProps {
  apiClient: QapApiClient
  protocol: ScannerProtocolDto
  scans: ScanListDto
}

const HORIZONS: Horizon[] = ['short', 'medium', 'swing']

export function DiscoveryHome({ apiClient, protocol, scans }: DiscoveryHomeProps) {
  const [asOf, setAsOf] = useState('')
  const [horizons, setHorizons] = useState<Horizon[]>(['short'])
  const [pins, setPins] = useState<Pin[]>([])
  const [pinDraft, setPinDraft] = useState<Pin>({
    venue: 'binance',
    asset_a: '',
    asset_b: '',
    horizons: ['short'],
    forensic: false,
  })
  const [manualReplayIds, setManualReplayIds] = useState('')
  const [operation, setOperation] = useState<OperationRefDto | null>(null)

  const mutation = useMutation({
    mutationFn: (command: RunScanRequestDto) => apiClient.runScan(command),
    onSuccess: setOperation,
  })

  const protocolByHorizon = useMemo(
    () => new Map(protocol.horizons.map((item) => [item.horizon, item])),
    [protocol.horizons],
  )

  const toggleHorizon = (horizon: Horizon) => {
    const next = horizons.includes(horizon)
      ? horizons.filter((item) => item !== horizon)
      : [...horizons, horizon]
    setHorizons(next)
    setPins((current) => current.map((pin) => ({ ...pin, horizons: next })))
    setPinDraft((current) => ({ ...current, horizons: next }))
  }

  const addPin = () => {
    if (
      horizons.length === 0 ||
      !pinDraft.asset_a.trim() ||
      !pinDraft.asset_b.trim()
    ) return
    setPins((current) => [...current, { ...pinDraft, horizons }])
    setPinDraft({ ...pinDraft, asset_a: '', asset_b: '' })
  }

  const submit = () => {
    if (!asOf || horizons.length === 0) return
    mutation.mutate({
      as_of: asOf,
      horizons,
      pins,
      manual_replay_candidate_ids: manualReplayIds
        .split(/[\s,]+/)
        .map((item) => item.trim())
        .filter(Boolean),
    })
  }

  return (
    <section className="min-w-0">
      <header className="mb-8 max-w-4xl">
        <p className="mb-2 text-xs font-semibold uppercase tracking-[0.1em] text-accent">
          Research ideas
        </p>
        <h1 className="mb-3 text-3xl font-bold tracking-tight text-foreground md:text-4xl">
          Discover
        </h1>
        <p className="m-0 text-sm leading-6 text-secondary md:text-base">
          Choose when and how far ahead to research. QAP applies the frozen market
          universe, models, costs, and historical checks.
        </p>
      </header>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.1fr)_minmax(22rem,0.9fr)]">
        <section
          className="rounded-lg border border-border bg-panel p-5"
          aria-labelledby="scan-command-heading"
        >
          <h2
            id="scan-command-heading"
            className="mt-0 text-lg font-semibold text-foreground"
          >
            Find research ideas
          </h2>
          <label className="mt-4 block text-sm font-medium text-secondary">
            Analysis date and time (UTC)
            <input
              className="mt-2 min-h-11 w-full rounded-md border border-border bg-canvas px-3 text-foreground"
              value={asOf}
              onChange={(event) => setAsOf(event.target.value)}
              placeholder="2026-08-19T00:00:00Z"
              inputMode="text"
            />
          </label>

          <fieldset className="mt-5 border-0 p-0">
            <legend className="text-sm font-medium text-secondary">
              Research timeframe
            </legend>
            <div className="mt-2 flex flex-wrap gap-3">
              {HORIZONS.map((horizon) => (
                <label
                  key={horizon}
                  className="flex min-h-11 items-center gap-2 rounded-md border border-border px-3 text-sm"
                >
                  <input
                    type="checkbox"
                    checked={horizons.includes(horizon)}
                    onChange={() => toggleHorizon(horizon)}
                  />
                  {horizon.charAt(0).toUpperCase() + horizon.slice(1)}
                </label>
              ))}
            </div>
          </fieldset>

          <details className="mt-6 border-t border-border pt-5">
            <summary className="min-h-11 cursor-pointer py-2 text-sm font-semibold text-accent">
              Advanced research controls
            </summary>
            <div className="mt-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h3 className="m-0 text-sm font-semibold text-foreground">
                Re-evaluate a manually selected pair
              </h3>
              <span className="text-xs text-muted">
                Forensic/manual lineage remains explicit
              </span>
            </div>
            <div className="mt-3 grid gap-3 sm:grid-cols-2">
              <select
                className="min-h-11 rounded-md border border-border bg-canvas px-3 text-sm text-foreground"
                value={pinDraft.venue}
                onChange={(event) =>
                  setPinDraft({
                    ...pinDraft,
                    venue: event.target.value as Pin['venue'],
                  })
                }
                aria-label="Pin venue"
              >
                {protocol.venues.map((venue) => (
                  <option key={venue} value={venue}>
                    {venue}
                  </option>
                ))}
              </select>
              <label className="flex min-h-11 items-center gap-2 rounded-md border border-border px-3 text-sm">
                <input
                  type="checkbox"
                  checked={pinDraft.forensic}
                  onChange={(event) =>
                    setPinDraft({ ...pinDraft, forensic: event.target.checked })
                  }
                />
                Forensic
              </label>
              <input
                className="min-h-11 rounded-md border border-border bg-canvas px-3 text-foreground"
                value={pinDraft.asset_a}
                onChange={(event) =>
                  setPinDraft({
                    ...pinDraft,
                    asset_a: event.target.value.toUpperCase(),
                  })
                }
                placeholder="Asset A"
                aria-label="Pin asset A"
              />
              <input
                className="min-h-11 rounded-md border border-border bg-canvas px-3 text-foreground"
                value={pinDraft.asset_b}
                onChange={(event) =>
                  setPinDraft({
                    ...pinDraft,
                    asset_b: event.target.value.toUpperCase(),
                  })
                }
                placeholder="Asset B"
                aria-label="Pin asset B"
              />
            </div>
            <button
              className="mt-3 min-h-11 rounded-md border border-border px-4 text-sm font-semibold text-foreground"
              type="button"
              onClick={addPin}
            >
              Add pin
            </button>
            {pins.length ? (
              <ul className="mt-3 space-y-2 pl-5 text-sm text-secondary">
                {pins.map((pin, index) => (
                  <li key={`${pin.venue}-${pin.asset_a}-${pin.asset_b}-${index}`}>
                    {pin.venue} · {pin.asset_a}/{pin.asset_b} ·{' '}
                    {pin.horizons.join(', ')}
                    {pin.forensic ? ' · forensic' : ''}
                  </li>
                ))}
              </ul>
            ) : null}

            <label className="mt-5 block text-sm font-medium text-secondary">
              Re-evaluate specific research idea IDs
              <input
                className="mt-2 min-h-11 w-full rounded-md border border-border bg-canvas px-3 text-foreground"
                value={manualReplayIds}
                onChange={(event) => setManualReplayIds(event.target.value)}
                placeholder="Candidate IDs, separated by spaces or commas"
                aria-label="Manual replay candidate IDs"
              />
            </label>
            </div>
          </details>

          <button
            className="mt-6 min-h-11 rounded-md bg-accent px-5 py-2 font-semibold text-canvas disabled:opacity-50"
            type="button"
            disabled={!asOf || horizons.length === 0 || mutation.isPending}
            onClick={submit}
          >
            {mutation.isPending ? 'Starting…' : 'Find research ideas'}
          </button>
          {mutation.isError ? (
            <p className="mt-3 text-sm text-negative">{mutation.error.message}</p>
          ) : null}
          {operation ? (
            <p className="mt-4 rounded-md border border-positive/40 bg-subtle p-3 text-sm text-secondary">
              Background analysis started.{' '}
              <a
                className="font-semibold text-accent"
                href={`/operations/${operation.operation_id}`}
              >
                View in Activity
              </a>
            </p>
          ) : null}
        </section>

        <details
          className="rounded-lg border border-border bg-panel p-5"
        >
          <summary className="min-h-11 cursor-pointer py-2 text-sm font-semibold text-accent">
            Scanner protocol details
          </summary>
          <div className="mt-3">
          <div className="flex flex-wrap items-center gap-2">
            <Badge tone="info">Frozen protocol</Badge>
            <span className="text-xs text-muted">{protocol.protocol_id}</span>
          </div>
          <h2
            id="protocol-heading"
            className="mt-4 text-lg font-semibold text-foreground"
          >
            Scientific controls are backend-owned
          </h2>
          <p className="text-sm leading-6 text-secondary">
            Venues: {protocol.venues.join(', ')} · quote asset {protocol.quote_asset}.
            The UI exposes intent, not scanner internals.
          </p>
          <div className="mt-4 space-y-3">
            {HORIZONS.map((horizon) => {
              const item = protocolByHorizon.get(horizon)
              if (!item) return null
              return (
                <article
                  key={horizon}
                  className="rounded-md border border-border p-3 text-sm"
                >
                  <p className="m-0 font-semibold text-foreground">{horizon}</p>
                  <p className="mt-1 mb-0 text-secondary">
                    Graph {item.graph_interval} · evaluation{' '}
                    {Math.round(item.evaluation_window_seconds / 86400)}d · models{' '}
                    {item.model_resolutions.join(' / ')}
                  </p>
                  <p className="mt-1 mb-0 text-secondary">
                    Momentum {item.momentum_resolution} /{' '}
                    {Math.round(item.momentum_formation_seconds / 86400)}d
                  </p>
                </article>
              )
            })}
          </div>
          </div>
        </details>
      </div>

      <section className="mt-8" aria-labelledby="completed-scans-heading">
        <h2
          id="completed-scans-heading"
          className="text-xl font-semibold text-foreground"
        >
          Previous discovery research
        </h2>
        {scans.items.length === 0 ? (
          <p className="text-secondary">No completed scan generations are available yet.</p>
        ) : (
          <div className="mt-4 grid gap-4 lg:grid-cols-2">
            {scans.items.map((scan) => (
              <article
                key={scan.scan_id}
                className="rounded-lg border border-border bg-panel p-4"
              >
                <div className="flex flex-wrap gap-2">
                  <Badge tone={scan.artifact_status === 'valid' ? 'info' : 'negative'}>
                    {scan.artifact_status === 'valid'
                      ? 'Evidence available'
                      : 'Evidence unavailable'}
                  </Badge>
                  {scan.survivor_count !== null ? (
                    <Badge tone="info">
                      {scan.survivor_count} ideas passed
                    </Badge>
                  ) : null}
                </div>
                <h3 className="mt-3 mb-2 text-base font-semibold text-foreground">
                  {scan.horizons.join(' / ') || 'Unknown scope'} ·{' '}
                  {scan.venues.join(' / ') || 'Unknown venue'}
                </h3>
                {scan.as_of ? (
                  <p className="m-0 text-sm text-secondary">
                    As of {formatResearchTimestamp(scan.as_of)}
                  </p>
                ) : null}
                <p className="mt-2 mb-0 text-sm text-secondary">
                  {scan.candidate_count ?? 0} evaluated rules ·{' '}
                  {scan.selected_replay_count ?? 0} selected for historical checks
                </p>
                {scan.error ? (
                  <p className="mt-2 text-sm text-negative">{scan.error.message}</p>
                ) : null}
                <a
                  className="mt-4 inline-flex min-h-11 items-center font-semibold text-accent"
                  href={`/scanner/${scan.scan_id}`}
                >
                  Review research ideas
                </a>
              </article>
            ))}
          </div>
        )}
      </section>
    </section>
  )
}
