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
  return (
    <details className="mt-6 rounded-md border border-border bg-canvas/35 p-4">
      <summary className="cursor-pointer text-sm font-semibold text-secondary">
        Advanced source scope
      </summary>
      <p className="text-xs leading-5 text-muted">
        QAP constrains these choices to scopes already present in the selected discovery
        evidence. Changing scope clears the portfolio draft.
      </p>
      <div className="grid gap-3 sm:grid-cols-2">
        <label className="text-xs font-semibold text-secondary">
          Research snapshot
          <select
            className="mt-1 min-h-11 w-full rounded-md border border-border bg-canvas px-3 text-sm text-foreground"
            value={scanId}
            onChange={(event) => onScanChange(event.target.value)}
          >
            {scans.map((scan) => (
              <option key={scan.scan_id} value={scan.scan_id}>
                {scan.as_of
                  ? `Research as of ${formatResearchTimestamp(scan.as_of)}`
                  : `Research ${scan.scan_id.slice(0, 8)}`}
              </option>
            ))}
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
