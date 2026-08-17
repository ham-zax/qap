import { useMemo } from 'react'

import type { PairEvidenceDto } from '../../api/types'
import { TimeSeriesChart } from '../../components/charts/TimeSeriesChart'
import type { ChartVisibleRange } from '../../components/charts/chartData'
import { humanizeIdentifier } from '../experiments/presentation'

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
    <article className="model-evidence-series min-w-0 rounded-md border border-border bg-canvas/30 p-4">
      <div className="mb-4 flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted">
        <span>Model {item.model_id} v{item.model_version}</span>
        <span>{humanizeIdentifier(item.evidence_field)}</span>
        <span>Persisted orientation: {item.persisted_orientation}</span>
        {unavailableCount > 0 ? (
          <span>{unavailableCount} observations unavailable by model validity rules.</span>
        ) : null}
      </div>
      {validPoints.length === 0 ? (
        <div className="rounded-md border border-warning/45 bg-panel p-4">
          <h3 className="mb-2 text-base font-semibold text-foreground">
            No valid model observations
          </h3>
          <p className="m-0 text-sm leading-6 text-secondary">
            Persisted observations exist, but none passed the model validity rules
            in this run window.
          </p>
        </div>
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
      <details className="mt-4 rounded-md border border-border bg-panel/60 p-3">
        <summary className="cursor-pointer text-sm font-semibold text-foreground">
          Model evidence provenance
        </summary>
        <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
          <div>
            <dt className="text-xs text-muted">Persisted orientation</dt>
            <dd className="mt-1 mb-0 text-secondary">{item.persisted_orientation}</dd>
          </div>
          <div>
            <dt className="text-xs text-muted">Requested orientation</dt>
            <dd className="mt-1 mb-0 text-secondary">{requestedOrientation}</dd>
          </div>
          <div>
            <dt className="text-xs text-muted">Fit reciprocity</dt>
            <dd className="mt-1 mb-0 text-secondary">{humanizeIdentifier(item.fit_reciprocity)}</dd>
          </div>
          <div>
            <dt className="text-xs text-muted">Evidence reciprocity</dt>
            <dd className="mt-1 mb-0 text-secondary">{humanizeIdentifier(item.evidence_reciprocity)}</dd>
          </div>
          <div className="min-w-0 sm:col-span-2">
            <dt className="text-xs text-muted">Base source fingerprint</dt>
            <dd
              className="mt-1 mb-0 overflow-x-auto rounded-md bg-canvas px-2 py-1 font-mono text-xs text-secondary"
              tabIndex={0}
            >
              {item.base_source_fingerprint}
            </dd>
          </div>
          <div className="min-w-0 sm:col-span-2">
            <dt className="text-xs text-muted">Quote source fingerprint</dt>
            <dd
              className="mt-1 mb-0 overflow-x-auto rounded-md bg-canvas px-2 py-1 font-mono text-xs text-secondary"
              tabIndex={0}
            >
              {item.quote_source_fingerprint}
            </dd>
          </div>
        </dl>
      </details>
    </article>
  )
}
