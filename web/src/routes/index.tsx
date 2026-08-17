import { createFileRoute } from '@tanstack/react-router'

import { ExperimentList } from '../features/experiments/ExperimentList'

export const Route = createFileRoute('/')({
  loader: ({ context }) =>
    context.queryClient.ensureQueryData(context.queries.experiments()),
  component: HomeRoute,
})

function HomeRoute() {
  return <ExperimentList data={Route.useLoaderData()} />
}
