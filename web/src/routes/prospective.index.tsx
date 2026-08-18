import { createFileRoute } from '@tanstack/react-router'

import { ProspectiveHome } from '../features/prospective/ProspectiveHome'

export const Route = createFileRoute('/prospective/')({
  loader: ({ context }) =>
    context.queryClient.ensureQueryData(context.queries.forwardCohorts()),
  component: ProspectiveIndexRoute,
})

function ProspectiveIndexRoute() {
  return <ProspectiveHome data={Route.useLoaderData()} />
}
