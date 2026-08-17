import type { PairEvidenceDto } from '../../api/types'
import type { ChartVisibleRange } from '../../components/charts/chartData'
import { formatDecimal } from '../../lib/format'
import { humanizeIdentifier } from '../experiments/presentation'
import { RelationshipEvidenceChart } from './RelationshipEvidenceChart'

interface RelationshipEvidencePanelProps {
  data: PairEvidenceDto
  sharedCursorTime?: string | null
  onCursorTimeChange?: (timestamp: string | null) => void
  sharedVisibleRange?: ChartVisibleRange | null
  onVisibleRangeChange?: (range: ChartVisibleRange | null) => void
}

export function RelationshipEvidencePanel({
  data,
  sharedCursorTime,
  onCursorTimeChange,
  sharedVisibleRange,
  onVisibleRangeChange,
}: RelationshipEvidencePanelProps) {
  if (data.series.length === 0) {
    return (
      <section
        className="rounded-lg border border-warning/45 bg-panel p-5 md:p-6"
        aria-labelledby="relationship-evidence-heading"
      >
        <h2 id="relationship-evidence-heading" className="mb-2 text-lg font-semibold text-foreground">
          No persisted model evidence
        </h2>
        <p className="m-0 text-sm leading-6 text-secondary">
          This run has no relationship-model evidence artifact for the requested pair.
        </p>
        <p className="mt-2 mb-0 text-xs text-muted">
          The descriptive pair chart remains available above.
        </p>
      </section>
    )
  }

  return (
    <section
      className="rounded-lg border border-border bg-panel p-5 md:p-6"
      aria-labelledby="relationship-evidence-heading"
    >
      <h2 id="relationship-evidence-heading" className="mb-2 text-lg font-semibold text-foreground">
        Persisted model evidence
      </h2>
      <p className="mt-0 mb-5 max-w-3xl text-sm leading-6 text-secondary">
        Backend-produced observations only; the browser does not refit or recalculate the model.
      </p>

      <div className="mb-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {data.series.map((item) => {
          const latest = item.points.at(-1)
          const formatted = latest?.value == null ? null : formatDecimal(String(latest.value), 6)
          return (
            <div
              key={`${item.persisted_orientation}:${item.model_id}:${item.model_version}:${item.evidence_field}:summary`}
              className="rounded-md border border-border bg-canvas/45 p-4"
            >
              <p className="m-0 text-xs text-muted">
                {humanizeIdentifier(item.evidence_field)} · {item.model_id} v{item.model_version}
              </p>
              <p className="mt-1 mb-0 text-xl font-semibold tabular-nums text-foreground">
                {formatted?.display ?? 'Unavailable'}
              </p>
              <p className="mt-2 mb-0 text-xs text-secondary">
                Latest status: {humanizeIdentifier(latest?.status ?? 'unknown')}
                {latest ? ` · ${latest.coverage_observations}/${latest.required_observations} observations` : ''}
              </p>
            </div>
          )
        })}
      </div>

      <div className="space-y-5">
        {data.series.map((item) => {
        const key = [
          item.persisted_orientation,
          item.model_id,
          item.model_version,
          item.evidence_field,
        ].join(':')
        return (
          <RelationshipEvidenceChart
            key={key}
            item={item}
            requestedOrientation={data.requested_orientation}
            sharedCursorTime={sharedCursorTime}
            onCursorTimeChange={onCursorTimeChange}
            sharedVisibleRange={sharedVisibleRange}
            onVisibleRangeChange={onVisibleRangeChange}
          />
        )
      })}
      </div>
    </section>
  )
}
