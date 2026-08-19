import { useMutation } from '@tanstack/react-query'

import type { QapApiClient } from '../../api/client'
import type { ProductFollowUpDto } from '../../api/types'

interface ProductFollowUpActionProps {
  apiClient: QapApiClient
  scanId: string
  followUp: ProductFollowUpDto | null
}

export function ProductFollowUpAction({
  apiClient,
  scanId,
  followUp,
}: ProductFollowUpActionProps) {
  const start = useMutation({
    mutationFn: () => apiClient.startCurrentApprovedResearchFollowUp(scanId),
  })

  if (!followUp) return null

  if (followUp.state === 'existing' && followUp.cohort_id) {
    return (
      <div className="mt-5 rounded-md border border-positive/40 bg-subtle p-4">
        <p className="m-0 text-sm leading-6 text-secondary">
          Follow-up already exists for all {followUp.survivor_count} Research Idea
          {followUp.survivor_count === 1 ? '' : 's'} from this research generation.
        </p>
        <a
          className="mt-3 inline-flex min-h-11 items-center font-semibold text-accent"
          href={`/prospective/${followUp.cohort_id}`}
        >
          View follow-up
        </a>
      </div>
    )
  }

  if (followUp.state !== 'start_available') {
    return followUp.reason ? (
      <p className="mt-5 rounded-md border border-border bg-panel p-4 text-sm text-secondary">
        {followUp.reason}
      </p>
    ) : null
  }

  return (
    <div className="mt-5 rounded-md border border-border bg-panel p-4">
      <p className="m-0 text-sm leading-6 text-secondary">
        QAP follows all ideas that passed the historical checks so later results are not
        cherry-picked after the fact. The backend records the follow-up boundary for the
        entire research generation.
      </p>
      <button
        type="button"
        className="mt-3 min-h-11 rounded-md bg-accent px-4 font-semibold text-canvas disabled:opacity-50"
        disabled={start.isPending || Boolean(start.data)}
        onClick={() => start.mutate()}
      >
        {start.data
          ? 'Follow-up starting…'
          : start.isPending
            ? 'Starting follow-up…'
            : `Start follow-up for all ${followUp.survivor_count} Research Idea${
                followUp.survivor_count === 1 ? '' : 's'
              }`}
      </button>
      {start.isError ? (
        <p className="mt-3 mb-0 text-sm text-negative">{start.error.message}</p>
      ) : null}
      {start.data ? (
        <p className="mt-3 mb-0 text-sm text-secondary">
          Follow-up is starting for the full generation.{' '}
          <a
            className="font-semibold text-accent"
            href={`/operations/${start.data.operation_id}`}
          >
            View in Activity
          </a>
        </p>
      ) : null}
    </div>
  )
}
