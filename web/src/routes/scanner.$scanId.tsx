import { createFileRoute } from '@tanstack/react-router'

import { ScanDetail } from '../features/discovery/ScanDetail'

export const Route = createFileRoute('/scanner/$scanId')({
  loader: async ({ context, params }) => {
    const [data, candidates] = await Promise.all([
      context.queryClient.ensureQueryData(context.queries.scan(params.scanId)),
      context.queryClient.ensureQueryData(
        context.queries.scanCandidates(params.scanId),
      ),
    ])
    return { data, candidates }
  },
  component: ScanDetailRoute,
})

function ScanDetailRoute() {
  const { data, candidates } = Route.useLoaderData()
  const { apiClient } = Route.useRouteContext()
  return <ScanDetail apiClient={apiClient} data={data} candidates={candidates} />
}
