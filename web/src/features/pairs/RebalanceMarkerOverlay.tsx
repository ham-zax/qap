import type { PairSeriesDto } from '../../api/types'
import type { ChartMarker } from '../../components/charts/chartData'

export function pairChartMarkers(data: PairSeriesDto): ChartMarker[] {
  return data.rebalance_markers.map((marker) => ({
    timestamp: marker.timestamp,
    label: marker.decision_id,
    selected: marker.selected,
    executed: marker.executed,
  }))
}

interface RebalanceMarkerOverlayProps {
  data: PairSeriesDto
}

export function RebalanceMarkerOverlay({ data }: RebalanceMarkerOverlayProps) {
  const executed = data.rebalance_markers.filter((marker) => marker.executed).length
  const selected = data.rebalance_markers.filter(
    (marker) => marker.selected && !marker.executed,
  ).length

  return (
    <details className="rounded-lg border border-border bg-panel p-5 md:p-6">
      <summary className="cursor-pointer font-semibold text-foreground">
        Strategy actions on this pair
      </summary>
      <div className="mt-4">
        {data.rebalance_markers.length === 0 ? (
          <p className="m-0 text-sm text-secondary">
            No strategy rebalance markers were persisted for this run.
          </p>
        ) : (
          <>
            <p className="mt-0 mb-4 text-sm text-secondary">
              {data.rebalance_markers.length} persisted decisions · {executed} executed
              {selected > 0 ? ` · ${selected} selected without execution` : ''}.
            </p>
            <ol className="m-0 space-y-3 pl-5 text-sm text-secondary">
              {data.rebalance_markers.map((marker) => (
                <li key={marker.decision_id}>
                  <span className="font-medium text-foreground">
                    {marker.executed
                      ? 'Executed'
                      : marker.selected
                        ? 'Selected'
                        : 'No action'}
                  </span>{' '}
                  at {marker.timestamp}
                  <details className="mt-1 border-0 bg-transparent p-0">
                    <summary className="w-fit cursor-pointer text-xs text-muted">
                      Technical identity
                    </summary>
                    <p className="mt-2 mb-0 break-all font-mono text-xs text-muted">
                      Decision {marker.decision_id}
                      {marker.fill_id ? ` · Fill ${marker.fill_id}` : ''}
                    </p>
                  </details>
                </li>
              ))}
            </ol>
          </>
        )}
      </div>
    </details>
  )
}
