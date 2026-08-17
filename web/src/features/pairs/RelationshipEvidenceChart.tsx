import { useMemo } from 'react'

import type { PairEvidenceDto } from '../../api/types'
import { StatusMessage } from '../../components/StatusMessage'
import { TimeSeriesChart } from '../../components/charts/TimeSeriesChart'
import type { ChartVisibleRange } from '../../components/charts/chartData'

type EvidenceSeries = PairEvidenceDto['series'][number]

interface RelationshipEvidenceChartProps {
  item: EvidenceSeries
  requestedOrientation: string
  sharedCursorTime?: string | null
  onCursorTimeChange?: (timestamp: string | null) => void
  sharedVisibleRange?: ChartVisibleRange | null
  onVisibleRangeChange?: (range: ChartVisibleRange | null) => void
}

export function RelationshipEvidenceChart({
  item,
  requestedOrientation,
  sharedCursorTime,
  onCursorTimeChange,
  sharedVisibleRange,
  onVisibleRangeChange,
}: RelationshipEvidenceChartProps) {
  const validPoints = useMemo(
    () =>
      item.points.flatMap((point) =>
        point.value === null
          ? []
          : [{ timestamp: point.timestamp, value: point.value }],
      ),
    [item.points],
  )
  const unavailableCount = item.points.length - validPoints.length
  const title = `${item.model_id} v${item.model_version} ${item.evidence_field}`
  const chartSeries = useMemo(
    () => [
      {
        name: item.model_id,
        unit: item.evidence_field,
        points: validPoints,
      },
    ],
    [item.evidence_field, item.model_id, validPoints],
  )

  return (
    <article className="model-evidence-series">
      <p>Persisted orientation: {item.persisted_orientation}</p>
      <p>Requested orientation: {requestedOrientation}</p>
      <p>{unavailableCount} observations unavailable by model validity rules.</p>
      {validPoints.length === 0 ? (
        <StatusMessage title="No valid model observations" tone="warning">
          <p>
            Persisted observations exist, but none passed the model validity rules
            in this run window.
          </p>
        </StatusMessage>
      ) : (
        <TimeSeriesChart
          title={title}
          description="Persisted model score from the admitted causal evidence window."
          series={chartSeries}
          sharedCursorTime={sharedCursorTime}
          onCursorTimeChange={onCursorTimeChange}
          sharedVisibleRange={sharedVisibleRange}
          onVisibleRangeChange={onVisibleRangeChange}
        />
      )}
      <details>
        <summary>Model evidence provenance</summary>
        <dl>
          <div>
            <dt>Fit reciprocity</dt>
            <dd>{item.fit_reciprocity}</dd>
          </div>
          <div>
            <dt>Evidence reciprocity</dt>
            <dd>{item.evidence_reciprocity}</dd>
          </div>
          <div>
            <dt>Base source fingerprint</dt>
            <dd>{item.base_source_fingerprint}</dd>
          </div>
          <div>
            <dt>Quote source fingerprint</dt>
            <dd>{item.quote_source_fingerprint}</dd>
          </div>
        </dl>
      </details>
    </article>
  )
}
