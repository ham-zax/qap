import { createFileRoute } from '@tanstack/react-router'

import { BasketDetail } from '../features/baskets/BasketDetail'

export const Route = createFileRoute('/baskets/$basketId')({
  loader: async ({ context, params }) => {
    const basket = await context.queryClient.ensureQueryData(
      context.queries.basket(params.basketId),
    )
    const runId = basket.qap_experiment_run_id
    if (!runId) return { basket, experiment: null, portfolio: null, performance: null }
    const [experiment, portfolio, performance] = await Promise.all([
      context.queryClient.ensureQueryData(context.queries.experiment(runId)),
      context.queryClient.ensureQueryData(context.queries.portfolio(runId)),
      context.queryClient.ensureQueryData(context.queries.performance(runId)),
    ])
    return { basket, experiment, portfolio, performance }
  },
  component: BasketDetailRoute,
})

function BasketDetailRoute() {
  return <BasketDetail {...Route.useLoaderData()} />
}
