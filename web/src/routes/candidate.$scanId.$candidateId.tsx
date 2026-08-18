import { createFileRoute } from '@tanstack/react-router'

import { CandidateDetail } from '../features/discovery/CandidateDetail'

export const Route = createFileRoute('/candidate/$scanId/$candidateId')({
  loader: ({ context, params }) =>
    context.queryClient.ensureQueryData(
      context.queries.scanCandidate(params.scanId, params.candidateId),
    ),
  component: CandidateDetailRoute,
})

function CandidateDetailRoute() {
  return <CandidateDetail data={Route.useLoaderData()} />
}
