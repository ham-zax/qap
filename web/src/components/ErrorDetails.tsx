import { QapApiError } from '../api/client'

interface ErrorDetailsProps {
  error: Error
}

export function ErrorDetails({ error }: ErrorDetailsProps) {
  if (!(error instanceof QapApiError)) {
    return <p>{error.message}</p>
  }

  return (
    <div className="error-details">
      <p>{error.message}</p>
      <dl className="mb-4 grid gap-3 text-sm sm:grid-cols-2">
        <div className="rounded-md border border-border bg-canvas/35 p-3">
          <dt className="text-xs font-medium text-muted">API error code</dt>
          <dd className="mt-1 mb-0 font-mono text-xs text-secondary">{error.code}</dd>
        </div>
        <div className="rounded-md border border-border bg-canvas/35 p-3">
          <dt className="text-xs font-medium text-muted">HTTP status</dt>
          <dd className="mt-1 mb-0 font-medium tabular-nums text-secondary">{error.status}</dd>
        </div>
      </dl>
      {Object.keys(error.context).length > 0 ? (
        <ul className="m-0 space-y-1 pl-5 text-sm text-secondary" aria-label="API error context">
          {Object.entries(error.context)
            .sort(([left], [right]) => left.localeCompare(right))
            .map(([key, value]) => (
              <li key={key}>
                {key}: {value}
              </li>
            ))}
        </ul>
      ) : null}
    </div>
  )
}
