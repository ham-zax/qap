import type { PairEvidenceDto } from '../../api/types'
import { StatusMessage } from '../../components/StatusMessage'
import type { ChartVisibleRange } from '../../components/charts/chartData'
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
      <StatusMessage title="No persisted model evidence" tone="warning">
        <p>
          This run has no relationship-model evidence artifact for the requested
          pair.
        </p>
      </StatusMessage>
    )
  }

  return (
    <section aria-labelledby="relationship-evidence-heading">
      <h2 id="relationship-evidence-heading">Persisted model evidence</h2>
      <p>
        Backend-produced observations only; the browser does not refit or
        recalculate the model.
      </p>
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
    </section>
  )
}
