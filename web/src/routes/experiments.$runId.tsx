import { createFileRoute } from '@tanstack/react-router'

import { ExperimentDetail } from '../features/experiments/ExperimentDetail'

export const Route = createFileRoute('/experiments/$runId')({
  loader: ({ context, params }) =>
    context.queryClient.ensureQueryData(context.queries.experiment(params.runId)),
  component: ExperimentDetailRoute,
})

function ExperimentDetailRoute() {
  return <ExperimentDetail data={Route.useLoaderData()} />
}
