import type { OperationListDto } from '../../api/types'
import { Badge } from '../../components/ui/Badge'
import { formatResearchTimestamp } from '../../lib/format'
import {
  operationDuration,
  operationKindLabel,
  operationStatusLabel,
  operationStatusTone,
} from './presentation'

interface OperationListProps {
  data: OperationListDto
}

function shortId(value: string) {
  return value.length <= 18 ? value : `${value.slice(0, 10)}…${value.slice(-6)}`
}

export function OperationList({ data }: OperationListProps) {
  return (
    <section className="min-w-0">
      <header className="mb-8 max-w-4xl">
        <p className="mb-2 text-xs font-semibold uppercase tracking-[0.1em] text-accent">
          Activity
        </p>
        <h1 className="mb-3 text-3xl font-bold tracking-tight text-foreground md:text-4xl">
          Background activity
        </h1>
        <p className="m-0 text-sm leading-6 text-secondary md:text-base">
          Follow tasks started from the Lab. Activity tells you whether the work ran; the
          resulting research evidence is separate and may still be negative or rejected.
        </p>
      </header>

      {data.items.length === 0 ? (
        <p className="text-secondary">No background activity has been started yet.</p>
      ) : (
        <div className="space-y-4">
          {data.items.map((operation) => {
            return (
              <article
                key={operation.operation_id}
                className="rounded-lg border border-border bg-panel p-5"
              >
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div>
                    <div className="flex flex-wrap gap-2">
                      <Badge tone={operationStatusTone(operation.status)}>
                        {operationStatusLabel(operation.status)}
                      </Badge>
                      <Badge tone="info">{operationKindLabel(operation.kind)}</Badge>
                    </div>
                    <h2 className="mt-3 mb-1 text-base font-semibold text-foreground">
                      {operationKindLabel(operation.kind)}
                    </h2>
                    <p className="m-0 text-sm text-secondary">
                      Requested {formatResearchTimestamp(operation.requested_at)} ·{' '}
                      {operationDuration(operation)}
                    </p>
                    <p className="mt-1 mb-0 text-xs text-muted">
                      Activity {shortId(operation.operation_id)}
                    </p>
                  </div>
                  <a
                    className="inline-flex min-h-11 items-center rounded-md border border-border px-4 font-semibold text-accent"
                    href={`/operations/${operation.operation_id}`}
                  >
                    Review activity
                  </a>
                </div>
                {operation.failure ? (
                  <div className="mt-4 rounded-md border border-negative/40 bg-subtle p-3">
                    <p className="m-0 text-sm text-negative">
                      The task failed to run: {operation.failure.message}
                    </p>
                    <p className="mt-2 mb-0 text-xs text-muted">
                      This operational failure does not determine the scientific result.
                    </p>
                  </div>
                ) : null}
              </article>
            )
          })}
        </div>
      )}
    </section>
  )
}
