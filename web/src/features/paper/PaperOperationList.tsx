import type { PaperOperationSummaryDto } from '../../api/types'
import { ExactNumber } from '../../components/ExactNumber'

interface PaperOperationListProps {
  items: PaperOperationSummaryDto[]
}

function statusLabel(item: PaperOperationSummaryDto): string {
  return item.reconciliation_matches ? 'Reconciled' : 'Reconciliation mismatch'
}

export function PaperOperationList({ items }: PaperOperationListProps) {
  if (items.length === 0) {
    return <p>No forward-paper operations are available.</p>
  }

  return (
    <section aria-labelledby="paper-operation-list-heading">
      <h1 id="paper-operation-list-heading">Forward-paper operations</h1>
      <p>
        These are read-only operational dry-run artifacts. They are not prospective
        candidate or deployment evidence and cannot execute orders from the browser.
      </p>
      {items.map((item) => (
        <article key={item.operation_id} aria-label={item.operation_id}>
          <h2>{item.operation_id}</h2>
          <dl>
            <div>
              <dt>Status</dt>
              <dd>{statusLabel(item)}</dd>
            </div>
            <div>
              <dt>Evidence class</dt>
              <dd>Operational dry run</dd>
            </div>
            <div>
              <dt>Prospective candidate evidence</dt>
              <dd>
                {item.prospective_candidate_evidence
                  ? 'Eligible'
                  : 'Not prospective candidate evidence'}
              </dd>
            </div>
            <div>
              <dt>Execution time</dt>
              <dd>{item.execution_timestamp}</dd>
            </div>
            <div>
              <dt>Fill count</dt>
              <dd>{item.fill_count}</dd>
            </div>
            <div>
              <dt>Total fees</dt>
              <dd><ExactNumber value={item.total_fee_quote} /></dd>
            </div>
            <div>
              <dt>Total slippage</dt>
              <dd><ExactNumber value={item.total_slippage_quote} /></dd>
            </div>
            <div>
              <dt>Bridge residual</dt>
              <dd><ExactNumber value={item.bridge_residual} /></dd>
            </div>
            <div>
              <dt>Routes</dt>
              <dd>{item.route_ids.length > 0 ? item.route_ids.join(' · ') : 'None'}</dd>
            </div>
          </dl>
          <a href={`/paper-operations/${encodeURIComponent(item.operation_id)}`}>
            Inspect paper operation
          </a>
        </article>
      ))}
    </section>
  )
}
