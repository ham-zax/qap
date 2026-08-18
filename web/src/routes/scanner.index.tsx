import { createFileRoute } from '@tanstack/react-router'

import { DiscoveryHome } from '../features/discovery/DiscoveryHome'

export const Route = createFileRoute('/scanner/')({
  loader: async ({ context }) => {
    const [protocol, scans] = await Promise.all([
      context.queryClient.ensureQueryData(context.queries.scannerProtocol()),
      context.queryClient.ensureQueryData(context.queries.scans()),
    ])
    return { protocol, scans }
  },
  component: ScannerIndexRoute,
})

function ScannerIndexRoute() {
  const { protocol, scans } = Route.useLoaderData()
  const { apiClient } = Route.useRouteContext()
  return <DiscoveryHome apiClient={apiClient} protocol={protocol} scans={scans} />
}
