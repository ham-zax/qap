import { createFileRoute } from '@tanstack/react-router'

import { ExperimentList } from '../features/experiments/ExperimentList'

export const Route = createFileRoute('/experiments/')({
  loader: ({ context }) =>
    context.queryClient.ensureQueryData(context.queries.experiments()),
  component: ExperimentsRoute,
})

function ExperimentsRoute() {
  return <ExperimentList data={Route.useLoaderData()} />
}
