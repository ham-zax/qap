import { createFileRoute } from '@tanstack/react-router'

import { ExperimentList } from '../features/experiments/ExperimentList'

export const Route = createFileRoute('/experiments/')({
  loader: async ({ context }) => {
    const [experiments, scans, validations, baskets, paperOperations] = await Promise.all([
      context.queryClient.ensureQueryData(context.queries.experiments()),
      context.queryClient.ensureQueryData(context.queries.scans()),
      context.queryClient.ensureQueryData(context.queries.forwardCohorts()),
      context.queryClient.ensureQueryData(context.queries.baskets()),
      context.queryClient.ensureQueryData(context.queries.paperOperations()),
    ])
    return { experiments, scans, validations, baskets, paperOperations }
  },
  component: ExperimentsRoute,
})

function ExperimentsRoute() {
  return <ExperimentList {...Route.useLoaderData()} />
}
