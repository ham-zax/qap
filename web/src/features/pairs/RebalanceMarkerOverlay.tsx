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
  return (
    <section aria-labelledby="rebalance-markers-heading">
      <h2 id="rebalance-markers-heading">Persisted rebalance markers</h2>
      {data.rebalance_markers.length === 0 ? (
        <p>No strategy rebalance markers were persisted for this run.</p>
      ) : (
        <ol>
          {data.rebalance_markers.map((marker) => (
            <li key={marker.decision_id}>
              <strong>
                {marker.decision_id} -{' '}
                {marker.executed
                  ? 'executed'
                  : marker.selected
                    ? 'selected'
                    : 'not selected'}
              </strong>
              <span> at {marker.timestamp}</span>
              {marker.fill_id ? <span>; fill {marker.fill_id}</span> : null}
            </li>
          ))}
        </ol>
      )}
    </section>
  )
}
