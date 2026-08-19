import { createFileRoute } from '@tanstack/react-router'

import { HomeWorkspace } from '../features/home/HomeWorkspace'

export const Route = createFileRoute('/')({
  loader: async ({ context }) => {
    const workspace = await context.queryClient.ensureQueryData(
      context.queries.workspaceStatus(),
    )
    const [experiments, operations, forwardCohorts] = await Promise.all([
      context.queryClient.ensureQueryData(context.queries.experiments()),
      context.queryClient.ensureQueryData(context.queries.operations()),
      context.queryClient.ensureQueryData(context.queries.forwardCohorts()),
    ])
    const readinessChecks =
      workspace.workspace_mode === 'local_market'
        ? await Promise.all(
            (['short', 'medium', 'swing'] as const).map(async (horizon) => {
              try {
                return await context.queryClient.ensureQueryData(
                  context.queries.currentApprovedReadiness(horizon),
                )
              } catch {
                return null
              }
            }),
          )
        : []
    const readiness = readinessChecks.filter((item) => item !== null)
    const readinessUnavailable = readinessChecks.some((item) => item === null)
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
