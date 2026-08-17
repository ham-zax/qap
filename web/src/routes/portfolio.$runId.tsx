import { createFileRoute, redirect } from '@tanstack/react-router'

import { PortfolioOverview } from '../features/portfolio/PortfolioOverview'
import {
  canonicalPortfolioSearch,
  parsePortfolioSearch,
} from '../features/portfolio/portfolioSearch'

export const Route = createFileRoute('/portfolio/$runId')({
  validateSearch: parsePortfolioSearch,
  loaderDeps: ({ search }) => search,
  loader: async ({ context, params, deps }) => {
    const [experiment, snapshot, performance] = await Promise.all([
      context.queryClient.ensureQueryData(context.queries.experiment(params.runId)),
      context.queryClient.ensureQueryData(context.queries.portfolio(params.runId)),
      context.queryClient.ensureQueryData(context.queries.performance(params.runId)),
    ])
    const canonical = canonicalPortfolioSearch(deps, snapshot.rebalance_audit)
    if (canonical.changed) {
      throw redirect({
        to: '/portfolio/$runId',
        params,
        search: canonical.search,
        replace: true,
      })
    }
    return { experiment, snapshot, performance }
  },
  component: PortfolioRoute,
})

function PortfolioRoute() {
  const loaded = Route.useLoaderData()
  const search = Route.useSearch()
  const navigate = Route.useNavigate()

  return (
    <PortfolioOverview
      {...loaded}
      selectedDecisionId={search.decision}
      onDecisionChange={(decision) => {
        void navigate({ search: { decision }, replace: true })
      }}
    />
  )
}
