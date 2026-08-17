import type { AnchorLensDto, PairSeriesDto } from '../../api/types'
import { AnchorLensPanel } from './AnchorLensPanel'
import { PairRatioChart } from './PairRatioChart'
import { RebalanceMarkerOverlay } from './RebalanceMarkerOverlay'
import {
  toggleOrientation,
  type PairSearch,
  type PairView,
} from './pairSearch'

interface PairWorkbenchProps {
  data: PairSeriesDto
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
  anchorData,
  search,
  onSearchChange,
}: PairWorkbenchProps) {
  const reciprocal = toggleOrientation(search.orientation)

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

      {search.view === 'anchor' ? (
        <AnchorLensPanel anchor={search.anchor} data={anchorData} />
      ) : (
        <PairRatioChart data={data} view={search.view} />
      )}

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
