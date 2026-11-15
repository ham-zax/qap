import { createFileRoute, redirect } from '@tanstack/react-router'

import type { CurrentApprovedReadinessDto } from '../api/types'
import { HomeWorkspace } from '../features/home/HomeWorkspace'

export const Route = createFileRoute('/')({
  loader: async ({ context }) => {
    const workspace = await context.queryClient.ensureQueryData(
      context.queries.workspaceStatus(),
    )
    if (workspace.workspace_mode === 'local_market') {
      throw redirect({ to: '/lab' })
    }
    const [experiments, operations, forwardCohorts] = await Promise.all([
      context.queryClient.ensureQueryData(context.queries.experiments()),
      context.queryClient.ensureQueryData(context.queries.operations()),
      context.queryClient.ensureQueryData(context.queries.forwardCohorts()),
    ])
    const readiness: CurrentApprovedReadinessDto[] = []
    const readinessUnavailable = false
    return {
      workspace,
      readiness,
      readinessUnavailable,
      experiments,
      forwardCohorts,
      operations,
    }
  },
  component: HomeRoute,
})

function HomeRoute() {
  return <HomeWorkspace {...Route.useLoaderData()} />
}
