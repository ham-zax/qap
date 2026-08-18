import { createFileRoute } from '@tanstack/react-router'

import { BasketHome } from '../features/baskets/BasketHome'

export const Route = createFileRoute('/baskets/')({
  loader: async ({ context }) => {
    const [scans, baskets] = await Promise.all([
      context.queryClient.ensureQueryData(context.queries.scans()),
      context.queryClient.ensureQueryData(context.queries.baskets()),
    ])
    return { scans, baskets }
  },
  component: BasketsIndexRoute,
})

function BasketsIndexRoute() {
  const { scans, baskets } = Route.useLoaderData()
  const { apiClient } = Route.useRouteContext()
  return <BasketHome apiClient={apiClient} baskets={baskets} scans={scans} />
}
