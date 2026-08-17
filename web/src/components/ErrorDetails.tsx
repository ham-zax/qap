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
      <dl>
        <div>
          <dt>API error code</dt>
          <dd>{error.code}</dd>
        </div>
        <div>
          <dt>HTTP status</dt>
          <dd>{error.status}</dd>
        </div>
      </dl>
      {Object.keys(error.context).length > 0 ? (
        <ul aria-label="API error context">
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
