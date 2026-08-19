import { createFileRoute } from '@tanstack/react-router'

import { HistoryView } from '../features/experiments/HistoryView'

export const Route = createFileRoute('/experiments/')({
  loader: ({ context }) => context.queryClient.ensureQueryData(context.queries.history()),
  component: ExperimentsRoute,
})

function ExperimentsRoute() {
  return <HistoryView history={Route.useLoaderData()} />
}
