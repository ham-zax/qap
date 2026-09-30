import { createFileRoute } from '@tanstack/react-router'

import { ResearchHome } from '../features/discovery/ResearchHome'

export const Route = createFileRoute('/research/')({
  loader: async ({ context }) => {
    const [workspace, protocol, scans] = await Promise.all([
      context.queryClient.ensureQueryData(context.queries.workspaceStatus()),
      context.queryClient.ensureQueryData(context.queries.scannerProtocol()),
      context.queryClient.ensureQueryData(context.queries.scans()),
    ])
    return { workspace, protocol, scans }
  },
  component: ResearchIndexRoute,
})

function ResearchIndexRoute() {
  const { workspace, protocol, scans } = Route.useLoaderData()
  const { apiClient, queries } = Route.useRouteContext()
  return (
    <ResearchHome
      apiClient={apiClient}
      queries={queries}
      workspace={workspace}
      protocol={protocol}
      scans={scans}
    />
  )
}
