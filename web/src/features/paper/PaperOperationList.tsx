import type { PaperOperationSummaryDto } from '../../api/types'

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
        These are read-only paper-operation artifacts. They are not deployment
        evidence and cannot execute orders from the browser.
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
              <dt>Execution time</dt>
              <dd>{item.execution_timestamp}</dd>
            </div>
            <div>
              <dt>Fill count</dt>
              <dd>{item.fill_count}</dd>
            </div>
            <div>
              <dt>Total fees</dt>
              <dd>{item.total_fee_quote}</dd>
            </div>
            <div>
              <dt>Total slippage</dt>
              <dd>{item.total_slippage_quote}</dd>
            </div>
            <div>
              <dt>Bridge residual</dt>
              <dd>{item.bridge_residual}</dd>
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
