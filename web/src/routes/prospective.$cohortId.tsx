import { createFileRoute } from '@tanstack/react-router'

import { ProspectiveDetail } from '../features/prospective/ProspectiveDetail'

export const Route = createFileRoute('/prospective/$cohortId')({
  loader: ({ context, params }) =>
    context.queryClient.ensureQueryData(
      context.queries.forwardCohort(params.cohortId),
    ),
  component: ProspectiveDetailRoute,
})

function ProspectiveDetailRoute() {
  const { apiClient } = Route.useRouteContext()
  return <ProspectiveDetail apiClient={apiClient} data={Route.useLoaderData()} />
}
