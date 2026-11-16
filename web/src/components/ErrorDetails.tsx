import { QapApiError } from '../api/client'

interface ErrorDetailsProps {
  error: Error
}

export function ErrorDetails({ error }: ErrorDetailsProps) {
  if (!(error instanceof QapApiError)) {
    return <p className="m-0 text-sm text-foreground">{error.message}</p>
  }

  return (
    <div className="space-y-4">
      <p className="m-0 text-sm text-foreground">{error.message}</p>
      <dl className="m-0 grid gap-3 text-sm sm:grid-cols-2">
        <div className="rounded-lg border border-border bg-muted/60 p-3">
          <dt className="text-xs font-medium text-muted-foreground">API error code</dt>
          <dd className="m-0 mt-1 font-mono text-xs text-foreground">{error.code}</dd>
        </div>
        <div className="rounded-lg border border-border bg-muted/60 p-3">
          <dt className="text-xs font-medium text-muted-foreground">HTTP status</dt>
          <dd className="m-0 mt-1 font-mono text-xs font-medium tabular-nums text-foreground">
            {error.status}
          </dd>
        </div>
      </dl>
      {Object.keys(error.context).length > 0 ? (
        <ul
          className="m-0 space-y-1 rounded-lg border border-border bg-muted/40 py-2.5 pr-3 pl-7 text-xs text-muted-foreground"
          aria-label="API error context"
        >
          {Object.entries(error.context)
            .sort(([left], [right]) => left.localeCompare(right))
            .map(([key, value]) => (
              <li key={key} className="font-mono">
                {key}: {value}
              </li>
            ))}
        </ul>
      ) : null}
    </div>
  )
}
