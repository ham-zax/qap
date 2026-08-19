import { createFileRoute } from '@tanstack/react-router'

import { HomeWorkspace } from '../features/home/HomeWorkspace'

export const Route = createFileRoute('/')({
  loader: async ({ context }) => {
    const [workspace, experiments, operations, forwardCohorts] = await Promise.all([
      context.queryClient.ensureQueryData(context.queries.workspaceStatus()),
      context.queryClient.ensureQueryData(context.queries.experiments()),
      context.queryClient.ensureQueryData(context.queries.operations()),
      context.queryClient.ensureQueryData(context.queries.forwardCohorts()),
    ])
    return { workspace, experiments, forwardCohorts, operations }
  },
  component: HomeRoute,
})

function HomeRoute() {
  return <HomeWorkspace {...Route.useLoaderData()} />
}
