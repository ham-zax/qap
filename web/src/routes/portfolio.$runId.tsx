import { createFileRoute } from '@tanstack/react-router'

import { PortfolioOverview } from '../features/portfolio/PortfolioOverview'

export const Route = createFileRoute('/portfolio/$runId')({
  loader: async ({ context, params }) => {
    const [experiment, snapshot, performance] = await Promise.all([
      context.queryClient.ensureQueryData(context.queries.experiment(params.runId)),
      context.queryClient.ensureQueryData(context.queries.portfolio(params.runId)),
      context.queryClient.ensureQueryData(context.queries.performance(params.runId)),
    ])
    return { experiment, snapshot, performance }
  },
  component: PortfolioRoute,
})

function PortfolioRoute() {
  return <PortfolioOverview {...Route.useLoaderData()} />
}
