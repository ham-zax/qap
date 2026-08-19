import { createFileRoute } from '@tanstack/react-router'

import { ResearchUniverse } from '../features/home/ResearchUniverse'

export const Route = createFileRoute('/universe')({
  loader: async ({ context }) => {
    const [workspace, universe] = await Promise.all([
      context.queryClient.ensureQueryData(context.queries.workspaceStatus()),
      context.queryClient.ensureQueryData(context.queries.researchUniverse()),
    ])
    return { workspace, universe }
  },
  component: ResearchUniverseRoute,
})

function ResearchUniverseRoute() {
  const { apiClient } = Route.useRouteContext()
  const { workspace, universe } = Route.useLoaderData()
  return (
    <ResearchUniverse
      apiClient={apiClient}
      workspace={workspace}
      data={universe}
    />
  )
}
