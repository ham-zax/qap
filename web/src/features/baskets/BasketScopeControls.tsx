import type { ScanListDto } from '../../api/types'
import { formatResearchTimestamp } from '../../lib/format'

type Venue = 'binance' | 'gate'
type Horizon = 'short' | 'medium' | 'swing'

interface BasketScopeControlsProps {
  scans: ScanListDto['items']
  scanId: string
  availableVenues: Venue[]
  venue?: Venue
  availableHorizons: Horizon[]
  horizon?: Horizon
  availableResolutions: string[]
  resolution?: string
  onScanChange: (scanId: string) => void
  onVenueChange: (venue: Venue) => void
  onHorizonChange: (horizon: Horizon) => void
  onResolutionChange: (resolution: string) => void
}

function horizonLabel(horizon: Horizon) {
  if (horizon === 'short') return 'Short horizon'
  if (horizon === 'medium') return 'Medium horizon'
  return 'Swing horizon'
}

function scanOptionLabel(scan: ScanListDto['items'][number]) {
  if (scan.claim?.kind === 'current_approved_retrospective') {
    return scan.eligible_information_end
      ? `${scan.claim.label} · Data through ${formatResearchTimestamp(scan.eligible_information_end)}`
      : scan.claim.label
  }
  if (scan.claim?.kind === 'historical_pit') {
    return scan.as_of
      ? `${scan.claim.label} · As of ${formatResearchTimestamp(scan.as_of)}`
      : scan.claim.label
  }
  return scan.claim?.label ?? `Research ${scan.scan_id.slice(0, 8)}`
}

export function BasketScopeControls({
  scans,
  scanId,
  availableVenues,
  venue,
  availableHorizons,
  horizon,
  availableResolutions,
  resolution,
  onScanChange,
  onVenueChange,
  onHorizonChange,
  onResolutionChange,
}: BasketScopeControlsProps) {
  const productScans = scans.filter(
    (scan) => scan.claim?.kind === 'current_approved_retrospective',
  )
  const pitScans = scans.filter((scan) => scan.claim?.kind === 'historical_pit')
  const otherScans = scans.filter(
    (scan) =>
      scan.claim?.kind !== 'current_approved_retrospective' &&
      scan.claim?.kind !== 'historical_pit',
  )

  return (
    <details className="mt-6 rounded-md border border-border bg-canvas/35 p-4">
      <summary className="cursor-pointer text-sm font-semibold text-secondary">
        Research source and advanced scope
      </summary>
      <p className="text-xs leading-5 text-muted">
        Current Approved Market Research is the normal Product source. Strict Historical
        Point-in-Time Research remains an Advanced source. QAP constrains all choices to
        scopes already present in the selected research evidence; changing scope clears the
        portfolio draft.
      </p>
      <div className="grid gap-3 sm:grid-cols-2">
        <label className="text-xs font-semibold text-secondary">
          Research source
          <select
            className="mt-1 min-h-11 w-full rounded-md border border-border bg-canvas px-3 text-sm text-foreground"
            value={scanId}
            onChange={(event) => onScanChange(event.target.value)}
          >
            {productScans.length ? (
              <optgroup label="Product · Current Approved Market Research">
                {productScans.map((scan) => (
                  <option key={scan.scan_id} value={scan.scan_id}>
                    {scanOptionLabel(scan)}
                  </option>
                ))}
              </optgroup>
            ) : null}
            {pitScans.length ? (
              <optgroup label="Advanced · Historical Point-in-Time Research">
                {pitScans.map((scan) => (
                  <option key={scan.scan_id} value={scan.scan_id}>
                    {scanOptionLabel(scan)}
                  </option>
                ))}
              </optgroup>
            ) : null}
            {otherScans.length ? (
              <optgroup label="Advanced · Other versioned research">
                {otherScans.map((scan) => (
                  <option key={scan.scan_id} value={scan.scan_id}>
                    {scanOptionLabel(scan)}
                  </option>
                ))}
              </optgroup>
            ) : null}
          </select>
        </label>
        <label className="text-xs font-semibold text-secondary">
          Venue
          <select
            className="mt-1 min-h-11 w-full rounded-md border border-border bg-canvas px-3 text-sm text-foreground"
            value={venue ?? ''}
            onChange={(event) => onVenueChange(event.target.value as Venue)}
          >
            {availableVenues.map((item) => (
              <option key={item} value={item}>
                {item === 'binance' ? 'Binance' : 'Gate'}
              </option>
            ))}
          </select>
        </label>
        <label className="text-xs font-semibold text-secondary">
          Research horizon
          <select
            className="mt-1 min-h-11 w-full rounded-md border border-border bg-canvas px-3 text-sm text-foreground"
            value={horizon ?? ''}
            onChange={(event) => onHorizonChange(event.target.value as Horizon)}
          >
            {availableHorizons.map((item) => (
              <option key={item} value={item}>
                {horizonLabel(item)}
              </option>
            ))}
          </select>
        </label>
        <label className="text-xs font-semibold text-secondary">
          Decision resolution
          <select
            className="mt-1 min-h-11 w-full rounded-md border border-border bg-canvas px-3 text-sm text-foreground"
            value={resolution ?? ''}
            onChange={(event) => onResolutionChange(event.target.value)}
          >
            {availableResolutions.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </label>
      </div>
    </details>
  )
}
