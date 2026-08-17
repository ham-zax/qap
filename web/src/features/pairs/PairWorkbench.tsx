import { useCallback, useState } from 'react'

import type {
  AnchorLensDto,
  PairEvidenceDto,
  PairSeriesDto,
} from '../../api/types'
import type { ChartVisibleRange } from '../../components/charts/chartData'
import { humanizeIdentifier } from '../experiments/presentation'
import { AnchorLensPanel } from './AnchorLensPanel'
import { PairRatioChart } from './PairRatioChart'
import { RebalanceMarkerOverlay } from './RebalanceMarkerOverlay'
import { RelationshipEvidencePanel } from './RelationshipEvidencePanel'
import {
  toggleOrientation,
  type PairSearch,
  type PairView,
} from './pairSearch'

interface PairWorkbenchProps {
  data: PairSeriesDto
  evidenceData: PairEvidenceDto
  anchorData: AnchorLensDto | null
  search: PairSearch
  onSearchChange: (search: PairSearch) => void
}

const VIEW_OPTIONS: Array<{ value: PairView; label: string }> = [
  { value: 'ratio', label: 'Ratio' },
  { value: 'log', label: 'Log ratio' },
  { value: 'normalized', label: 'Normalized paths' },
  { value: 'anchor', label: 'Anchor lens' },
]

function orientationLabel(value: string): string {
  return value.replace('/', ' / ')
}

export function PairWorkbench({
  data,
  evidenceData,
  anchorData,
  search,
  onSearchChange,
}: PairWorkbenchProps) {
  const reciprocal = toggleOrientation(search.orientation)
  const [cursorTime, setCursorTime] = useState<string | null>(null)
  const [visibleRange, setVisibleRange] = useState<ChartVisibleRange | null>(null)
  const handleCursorTime = useCallback((timestamp: string | null) => {
    setCursorTime(timestamp)
  }, [])
  const handleVisibleRange = useCallback((range: ChartVisibleRange | null) => {
    setVisibleRange((current) => {
      if (current?.from === range?.from && current?.to === range?.to) return current
      return range
    })
  }, [])

  return (
    <article className="min-w-0" aria-labelledby="pair-workbench-heading">
      <header className="rounded-lg border border-border bg-panel p-5 md:p-6">
        <p className="mb-2 text-xs font-semibold uppercase tracking-[0.1em] text-accent">
          Pair workbench
        </p>
        <h1
          id="pair-workbench-heading"
          className="mb-3 text-3xl font-bold tracking-tight text-foreground md:text-4xl"
        >
          {orientationLabel(data.requested_orientation)}
        </h1>
        <div className="flex flex-wrap gap-x-5 gap-y-2 text-sm text-secondary">
          <p className="m-0">
            <span className="text-muted">Displayed orientation</span>{' '}
            <strong className="font-semibold text-foreground">
              {orientationLabel(data.requested_orientation)}
            </strong>
          </p>
          <p className="m-0">
            <span className="text-muted">Interval</span>{' '}
            <strong className="font-semibold text-foreground">{data.interval}</strong>
          </p>
        </div>
        <p className="mt-4 mb-0 max-w-3xl rounded-md border border-border bg-canvas/45 p-3 text-sm leading-6 text-secondary">
          Descriptive evidence only; this chart does not establish tradable alpha.
        </p>
      </header>

      <section
        className="mt-5 rounded-lg border border-border bg-panel p-4 md:p-5"
        aria-label="Pair chart controls"
      >
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
            <button
              className="min-h-11 rounded-md border border-border-strong bg-subtle px-4 py-2 text-sm font-semibold text-foreground hover:border-accent"
              type="button"
              onClick={() => onSearchChange({ ...search, orientation: reciprocal })}
            >
              Show {orientationLabel(reciprocal)}
            </button>

            <label className="flex min-w-40 flex-col gap-1 text-xs font-medium text-muted">
              Anchor lens
              <select
                className="min-h-11 rounded-md border border-border-strong bg-subtle px-3 text-sm font-semibold text-foreground"
                value={search.anchor}
                onChange={(event) => {
                  const anchor = event.currentTarget.value
                  onSearchChange({
                    ...search,
                    anchor,
                    view:
                      anchor === 'none' && search.view === 'anchor'
                        ? 'ratio'
                        : anchor === 'none'
                          ? search.view
                          : 'anchor',
                  })
                }}
              >
                <option value="none">None</option>
                {data.available_anchors.map((anchor) => (
                  <option key={anchor} value={anchor}>
                    {anchor}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <div
            className="grid grid-cols-2 gap-2 sm:flex sm:flex-wrap"
            role="group"
            aria-label="Chart view"
          >
            {VIEW_OPTIONS.map((option) => {
              const active = search.view === option.value
              return (
                <button
                  key={option.value}
                  className={`min-h-11 rounded-md border px-3 py-2 text-sm font-semibold ${active ? 'border-accent bg-accent text-canvas' : 'border-border bg-canvas/30 text-secondary hover:border-border-strong hover:text-foreground'}`}
                  type="button"
                  aria-pressed={active}
                  disabled={option.value === 'anchor' && search.anchor === 'none'}
                  onClick={() => onSearchChange({ ...search, view: option.value })}
                >
                  {option.label}
                </button>
              )
            })}
          </div>
        </div>
      </section>

      <div className="mt-6 space-y-6">
        {search.view === 'anchor' ? (
          <AnchorLensPanel anchor={search.anchor} data={anchorData} />
        ) : (
          <section
            className="rounded-lg border border-border bg-panel p-5 md:p-6"
            aria-labelledby="pair-evidence-heading"
          >
            <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
              <div>
                <h2 id="pair-evidence-heading" className="mb-1 text-lg font-semibold text-foreground">
                  Pair evidence
                </h2>
                <p className="m-0 text-sm text-secondary">
                  {humanizeIdentifier(search.view)} view of the persisted requested orientation.
                </p>
              </div>
              <p className="m-0 text-xs text-muted" aria-live="polite">
                Shared cursor: {cursorTime ?? 'move across a chart to synchronize time'}
              </p>
            </div>
            <PairRatioChart
              data={data}
              view={search.view}
              sharedCursorTime={cursorTime}
              onCursorTimeChange={handleCursorTime}
              sharedVisibleRange={visibleRange}
              onVisibleRangeChange={handleVisibleRange}
            />
          </section>
        )}

        <RelationshipEvidencePanel
          data={evidenceData}
          sharedCursorTime={cursorTime}
          onCursorTimeChange={handleCursorTime}
          sharedVisibleRange={visibleRange}
          onVisibleRangeChange={handleVisibleRange}
        />

        <RebalanceMarkerOverlay data={data} />

        <details className="rounded-lg border border-border bg-panel p-5 md:p-6">
          <summary className="cursor-pointer font-semibold text-foreground">
            How this evidence is constructed
          </summary>
          <div className="mt-5 space-y-5 text-sm text-secondary">
            <dl className="grid gap-4 sm:grid-cols-2">
              <div>
                <dt className="text-xs text-muted">Canonical pair identity</dt>
                <dd className="mt-1 mb-0 text-foreground">
                  {data.canonical_pair.join(' / ')}
                </dd>
              </div>
              <div>
                <dt className="text-xs text-muted">Displayed orientation</dt>
                <dd className="mt-1 mb-0 text-foreground">
                  {orientationLabel(data.requested_orientation)}
                </dd>
              </div>
              <div>
                <dt className="text-xs text-muted">Fit reciprocity</dt>
                <dd className="mt-1 mb-0">{humanizeIdentifier(data.fit_reciprocity)}</dd>
              </div>
              <div>
                <dt className="text-xs text-muted">Evidence reciprocity</dt>
                <dd className="mt-1 mb-0">{humanizeIdentifier(data.evidence_reciprocity)}</dd>
              </div>
            </dl>

            <div className="rounded-md border border-border bg-canvas/35 p-4">
              <h3 className="mb-2 text-sm font-semibold text-foreground">
                Identity coordinates
              </h3>
              <p className="m-0 leading-6">
                {data.identity_coordinate_assets.length > 0
                  ? `${data.identity_coordinate_assets.join(', ')} ${data.identity_coordinate_assets.length === 1 ? 'is' : 'are'} a deterministic unit path used for relationship coordinates, not a market observation.`
                  : 'No deterministic identity coordinate is used for this pair view.'}
              </p>
            </div>

            <div className="grid min-w-0 gap-4 sm:grid-cols-2">
              <div className="min-w-0">
                <p className="m-0 text-xs text-muted">Base source fingerprint</p>
                <code
                  className="mt-1 block max-w-full overflow-x-auto rounded-md bg-canvas px-2 py-1 font-mono text-xs text-secondary"
                  tabIndex={0}
                >
                  {data.base_source_fingerprint}
                </code>
              </div>
              <div className="min-w-0">
                <p className="m-0 text-xs text-muted">Quote source fingerprint</p>
                <code
                  className="mt-1 block max-w-full overflow-x-auto rounded-md bg-canvas px-2 py-1 font-mono text-xs text-secondary"
                  tabIndex={0}
                >
                  {data.quote_source_fingerprint}
                </code>
              </div>
            </div>
          </div>
        </details>
      </div>
    </article>
  )
}
