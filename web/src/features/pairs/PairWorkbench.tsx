import { useCallback, useState } from 'react'

import type {
  AnchorLensDto,
  PairEvidenceDto,
  PairSeriesDto,
} from '../../api/types'
import type { ChartVisibleRange } from '../../components/charts/chartData'
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
    <article aria-labelledby="pair-workbench-heading">
      <header>
        <h1 id="pair-workbench-heading">Pair workbench</h1>
        <p>Canonical pair: {data.canonical_pair.join(' / ')}</p>
        <p>Displayed orientation: {data.requested_orientation}</p>
        <p>
          <span>
            Identity coordinates:{' '}
            {data.identity_coordinate_assets.join(', ') || 'none'}
          </span>{' '}
          are deterministic unit paths, not market observations.
        </p>
        <p>
          Descriptive evidence only; this chart does not establish tradable alpha.
        </p>
      </header>

      <section className="pair-controls" aria-label="Pair chart controls">
        <button
          type="button"
          onClick={() =>
            onSearchChange({ ...search, orientation: reciprocal })
          }
        >
          Show {reciprocal}
        </button>

        <label>
          Anchor lens
          <select
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

        <div role="group" aria-label="Chart view">
          {VIEW_OPTIONS.map((option) => (
            <button
              key={option.value}
              type="button"
              aria-pressed={search.view === option.value}
              disabled={option.value === 'anchor' && search.anchor === 'none'}
              onClick={() => onSearchChange({ ...search, view: option.value })}
            >
              {option.label}
            </button>
          ))}
        </div>
      </section>

      <section
        className="synchronized-chart-group"
        aria-labelledby="pair-evidence-heading"
      >
        <h2 id="pair-evidence-heading">Pair evidence</h2>
        <p aria-live="polite">
          Shared cursor: {cursorTime ?? 'move across either chart to synchronize time'}
        </p>
        {search.view === 'anchor' ? (
          <AnchorLensPanel anchor={search.anchor} data={anchorData} />
        ) : (
          <PairRatioChart
            data={data}
            view={search.view}
            sharedCursorTime={cursorTime}
            onCursorTimeChange={handleCursorTime}
            sharedVisibleRange={visibleRange}
            onVisibleRangeChange={handleVisibleRange}
          />
        )}

        <RelationshipEvidencePanel
          data={evidenceData}
          sharedCursorTime={cursorTime}
          onCursorTimeChange={handleCursorTime}
          sharedVisibleRange={visibleRange}
          onVisibleRangeChange={handleVisibleRange}
        />
      </section>

      <RebalanceMarkerOverlay data={data} />

      <details>
        <summary>Relationship provenance</summary>
        <dl>
          <div>
            <dt>Interval</dt>
            <dd>{data.interval}</dd>
          </div>
          <div>
            <dt>Fit reciprocity</dt>
            <dd>{data.fit_reciprocity}</dd>
          </div>
          <div>
            <dt>Evidence reciprocity</dt>
            <dd>{data.evidence_reciprocity}</dd>
          </div>
          <div>
            <dt>Base source fingerprint</dt>
            <dd>{data.base_source_fingerprint}</dd>
          </div>
          <div>
            <dt>Quote source fingerprint</dt>
            <dd>{data.quote_source_fingerprint}</dd>
          </div>
        </dl>
      </details>
    </article>
  )
}
