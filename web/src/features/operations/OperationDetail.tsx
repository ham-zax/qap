import type { OperationDto } from '../../api/types'
import { Badge } from '../../components/ui/Badge'
import { formatResearchTimestamp } from '../../lib/format'
import {
  operationDuration,
  operationKindLabel,
  operationResultLinks,
  operationStatusTone,
} from './presentation'

interface OperationDetailProps {
  data: OperationDto
}

function renderValue(value: unknown): string {
  if (value === null) return 'null'
  if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
    return String(value)
  }
  return JSON.stringify(value)
}

export function OperationDetail({ data }: OperationDetailProps) {
  const links = operationResultLinks(data)

  return (
    <section className="min-w-0">
      <header className="mb-8 max-w-4xl">
        <p className="mb-2 text-xs font-semibold uppercase tracking-[0.1em] text-accent">
          Operation record
        </p>
        <h1 className="mb-3 text-3xl font-bold tracking-tight text-foreground md:text-4xl">
          {operationKindLabel(data.kind)}
        </h1>
        <div className="flex flex-wrap gap-2">
          <Badge tone={operationStatusTone(data.status)}>{data.status}</Badge>
          <Badge tone="info">{operationDuration(data)}</Badge>
        </div>
        <p className="mt-3 mb-0 break-all text-sm text-muted">{data.operation_id}</p>
      </header>

      {data.status === 'running' ? (
        <p className="mb-6 rounded-md border border-accent/40 bg-subtle p-3 text-sm text-secondary" aria-live="polite">
          Worker is running. This page polls only operation state; other evidence remains readable.
        </p>
      ) : null}

      {data.failure ? (
        <section className="mb-6 rounded-lg border border-negative/40 bg-panel p-5" aria-labelledby="failure-heading">
          <h2 id="failure-heading" className="mt-0 text-lg font-semibold text-negative">
            Operational failure
          </h2>
          <p className="mb-0 text-sm text-secondary">
            {data.failure.code}: {data.failure.message}
          </p>
          <p className="mt-2 mb-0 text-xs text-muted">
            Scientific evidence is not inferred from this operational failure.
          </p>
        </section>
      ) : null}

      <div className="grid gap-5 lg:grid-cols-2">
        <section className="rounded-lg border border-border bg-panel p-5" aria-labelledby="request-heading">
          <h2 id="request-heading" className="mt-0 text-lg font-semibold text-foreground">Requested intent</h2>
          <dl className="space-y-3 text-sm">
            {Object.entries(data.request_summary).map(([key, value]) => (
              <div key={key}>
                <dt className="text-xs font-semibold uppercase tracking-[0.06em] text-muted">{key}</dt>
                <dd className="m-0 mt-1 break-all text-secondary">{renderValue(value)}</dd>
              </div>
            ))}
          </dl>
        </section>

        <section className="rounded-lg border border-border bg-panel p-5" aria-labelledby="result-heading">
          <h2 id="result-heading" className="mt-0 text-lg font-semibold text-foreground">Authoritative result references</h2>
          {data.result ? (
            <dl className="space-y-3 text-sm">
              {Object.entries(data.result).map(([key, value]) => (
                <div key={key}>
                  <dt className="text-xs font-semibold uppercase tracking-[0.06em] text-muted">{key}</dt>
                  <dd className="m-0 mt-1 break-all text-secondary">{renderValue(value)}</dd>
                </div>
              ))}
            </dl>
          ) : (
            <p className="text-sm text-secondary">No terminal result reference is available yet.</p>
          )}
        </section>
      </div>

      <section className="mt-8 rounded-lg border border-border bg-panel p-5" aria-labelledby="timing-heading">
        <h2 id="timing-heading" className="mt-0 text-lg font-semibold text-foreground">Lifecycle</h2>
        <p className="mb-1 text-sm text-secondary">Requested {formatResearchTimestamp(data.requested_at)}</p>
        <p className="my-1 text-sm text-secondary">Started {formatResearchTimestamp(data.started_at)}</p>
        <p className="mt-1 mb-0 text-sm text-secondary">
          {data.finished_at ? `Finished ${formatResearchTimestamp(data.finished_at)}` : 'Still running'}
        </p>
      </section>

      {links.length ? (
        <nav className="mt-8 flex flex-wrap gap-3" aria-label="Operation result links">
          {links.map((link, index) => (
            <a
              key={link.href}
              className={
                index === 0
                  ? 'inline-flex min-h-11 items-center rounded-md bg-accent px-4 font-semibold text-canvas'
                  : 'inline-flex min-h-11 items-center rounded-md border border-border px-4 font-semibold text-accent'
              }
              href={link.href}
            >
              {link.label}
            </a>
          ))}
        </nav>
      ) : null}
    </section>
  )
}
