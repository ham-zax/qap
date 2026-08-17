import type { PaperOperationSummaryDto } from '../../api/types'
import { ExactNumber } from '../../components/ExactNumber'
import { Badge } from '../../components/ui/Badge'
import { formatResearchTimestamp } from '../../lib/format'

interface PaperOperationListProps {
  items: PaperOperationSummaryDto[]
}

function shortId(value: string): string {
  if (value.length <= 28) return value
  return `${value.slice(0, 15)}…${value.slice(-8)}`
}

export function PaperOperationList({ items }: PaperOperationListProps) {
  if (items.length === 0) {
    return <p>No forward-paper operations are available.</p>
  }

  return (
    <section className="min-w-0" aria-labelledby="paper-operation-list-heading">
      <header className="mb-8 max-w-3xl">
        <p className="mb-2 text-xs font-semibold uppercase tracking-[0.1em] text-accent">
          Operational evidence
        </p>
        <h1
          id="paper-operation-list-heading"
          className="mb-3 text-3xl font-bold tracking-tight text-foreground md:text-4xl"
        >
          Paper operations
        </h1>
        <p className="m-0 text-sm leading-6 text-secondary md:text-base">
          Read-only forward-paper dry runs. They show execution and reconciliation
          outcomes, but they are not candidate or deployment evidence and cannot place
          orders from the browser.
        </p>
      </header>

      <div className="grid gap-5 lg:grid-cols-2">
        {items.map((item) => {
          if (item.artifact_status === 'invalid') {
            return (
              <article
                key={item.operation_id}
                aria-label={item.operation_id}
                className="flex min-w-0 flex-col rounded-lg border border-negative/45 bg-panel p-4 md:p-5"
              >
                <div className="mb-4 flex flex-wrap items-center gap-2">
                  <Badge tone="negative">Invalid artifact</Badge>
                </div>
                <h2 className="mb-2 text-base font-semibold text-foreground">
                  Paper operation unavailable
                </h2>
                <p className="m-0 text-sm leading-6 text-secondary">
                  {item.error?.message ?? 'The persisted operation could not be validated.'}
                </p>
                <p className="mt-4 mb-0 break-all text-xs text-muted" title={item.operation_id}>
                  Operation {shortId(item.operation_id)}
                </p>
              </article>
            )
          }

          const reconciled = item.reconciliation_matches === true
          const executionTimestamp = item.execution_timestamp!
          const fillCount = item.fill_count!
          const totalFeeQuote = item.total_fee_quote!
          const totalSlippageQuote = item.total_slippage_quote!
          const bridgeResidual = item.bridge_residual!
          return (
            <article
              key={item.operation_id}
              aria-label={item.operation_id}
              className={`flex min-w-0 flex-col rounded-lg border bg-panel p-4 md:p-5 ${reconciled ? 'border-border' : 'border-negative/45'}`}
            >
              <div className="mb-4 flex flex-wrap items-center gap-2">
                <Badge tone={reconciled ? 'positive' : 'negative'}>
                  {reconciled ? 'Reconciled' : 'Reconciliation mismatch'}
                </Badge>
                <Badge tone="info">Forward paper · operational dry run</Badge>
              </div>

              <h2 className="mb-2 text-base font-semibold text-foreground">Paper rebalance</h2>
              <p className="mt-0 mb-5 text-sm text-secondary">
                {formatResearchTimestamp(executionTimestamp)}
              </p>

              <div className="grid grid-cols-2 gap-3 border-y border-border py-4">
                <div>
                  <p className="m-0 text-xs text-muted">Fills</p>
                  <p className="mt-1 mb-0 text-lg font-semibold tabular-nums text-foreground">
                    {fillCount}
                  </p>
                </div>
                <div>
                  <p className="m-0 text-xs text-muted">Fees</p>
                  <p className="mt-1 mb-0 text-lg font-semibold tabular-nums text-foreground">
                    <ExactNumber value={totalFeeQuote} />
                  </p>
                </div>
                <div>
                  <p className="m-0 text-xs text-muted">Slippage</p>
                  <p className="mt-1 mb-0 font-semibold tabular-nums text-foreground">
                    <ExactNumber value={totalSlippageQuote} />
                  </p>
                </div>
                <div>
                  <p className="m-0 text-xs text-muted">Bridge residual</p>
                  <p className="mt-1 mb-0 font-semibold tabular-nums text-foreground">
                    <ExactNumber value={bridgeResidual} />
                  </p>
                </div>
              </div>

              <p className="mt-4 mb-0 text-xs font-medium text-warning">
                Not candidate or deployment evidence
              </p>
              <p className="mt-2 mb-0 break-all text-xs text-muted" title={item.operation_id}>
                Operation {shortId(item.operation_id)}
              </p>

              <a
                className="mt-5 inline-flex min-h-11 w-fit items-center rounded-md bg-accent px-4 py-2 text-sm font-semibold text-canvas no-underline hover:opacity-90"
                href={`/paper-operations/${encodeURIComponent(item.operation_id)}`}
              >
                Inspect operation
              </a>
            </article>
          )
        })}
      </div>
    </section>
  )
}
