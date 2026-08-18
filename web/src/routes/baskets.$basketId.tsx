import { createFileRoute } from '@tanstack/react-router'

import { BasketDetail } from '../features/baskets/BasketDetail'

export const Route = createFileRoute('/baskets/$basketId')({
  loader: async ({ context, params }) => {
    const basket = await context.queryClient.ensureQueryData(
      context.queries.basket(params.basketId),
    )
    const runId = basket.qap_experiment_run_id
    if (!runId) return { basket, experiment: null, portfolio: null }
    const [experiment, portfolio] = await Promise.all([
      context.queryClient.ensureQueryData(context.queries.experiment(runId)),
      context.queryClient.ensureQueryData(context.queries.portfolio(runId)),
    ])
    return { basket, experiment, portfolio }
  },
  component: BasketDetailRoute,
})

function BasketDetailRoute() {
  return <BasketDetail {...Route.useLoaderData()} />
}
