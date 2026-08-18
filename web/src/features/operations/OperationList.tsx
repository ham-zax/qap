import type { OperationListDto } from '../../api/types'
import { Badge } from '../../components/ui/Badge'
import { formatResearchTimestamp } from '../../lib/format'
import {
  operationDuration,
  operationKindLabel,
  operationResultLinks,
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
          Local operation history
        </p>
        <h1 className="mb-3 text-3xl font-bold tracking-tight text-foreground md:text-4xl">
          Operations
        </h1>
        <p className="m-0 text-sm leading-6 text-secondary md:text-base">
          Operational state answers whether a requested task ran. It does not convert a
          negative or rejected research result into success.
        </p>
      </header>

      {data.items.length === 0 ? (
        <p className="text-secondary">No browser-triggered research operations yet.</p>
      ) : (
        <div className="space-y-4">
          {data.items.map((operation) => {
            const links = operationResultLinks(operation)
            return (
              <article
                key={operation.operation_id}
                className="rounded-lg border border-border bg-panel p-5"
              >
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div>
                    <div className="flex flex-wrap gap-2">
                      <Badge tone={operationStatusTone(operation.status)}>
                        {operation.status}
                      </Badge>
                      <Badge tone="info">{operationKindLabel(operation.kind)}</Badge>
                    </div>
                    <h2 className="mt-3 mb-1 text-base font-semibold text-foreground">
                      {shortId(operation.operation_id)}
                    </h2>
                    <p className="m-0 text-sm text-secondary">
                      Requested {formatResearchTimestamp(operation.requested_at)} ·{' '}
                      {operationDuration(operation)}
                    </p>
                  </div>
                  <a
                    className="inline-flex min-h-11 items-center rounded-md border border-border px-4 font-semibold text-accent"
                    href={`/operations/${operation.operation_id}`}
                  >
                    Inspect operation
                  </a>
                </div>
                {operation.failure ? (
                  <p className="mt-4 rounded-md border border-negative/40 bg-subtle p-3 text-sm text-negative">
                    {operation.failure.code}: {operation.failure.message}
                  </p>
                ) : null}
                {links.length ? (
                  <div className="mt-4 flex flex-wrap gap-3">
                    {links.map((link) => (
                      <a key={link.href} className="text-sm font-semibold text-accent" href={link.href}>
                        {link.label}
                      </a>
                    ))}
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
