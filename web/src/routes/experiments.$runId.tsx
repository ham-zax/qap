import { createFileRoute } from '@tanstack/react-router'

import { ExperimentDetail } from '../features/experiments/ExperimentDetail'

export const Route = createFileRoute('/experiments/$runId')({
  loader: async ({ context, params }) => {
    const [data, lineage] = await Promise.all([
      context.queryClient.ensureQueryData(context.queries.experiment(params.runId)),
      context.queryClient.ensureQueryData(
        context.queries.researchRecipeRunLineage(params.runId),
      ),
    ])
    return { data, lineage }
  },
  component: ExperimentDetailRoute,
})

function ExperimentDetailRoute() {
  return <ExperimentDetail {...Route.useLoaderData()} />
}
