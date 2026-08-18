import { createFileRoute } from '@tanstack/react-router'

import { OperationList } from '../features/operations/OperationList'

export const Route = createFileRoute('/operations/')({
  loader: ({ context }) =>
    context.queryClient.ensureQueryData(context.queries.operations()),
  component: OperationsIndexRoute,
})

function OperationsIndexRoute() {
  return <OperationList data={Route.useLoaderData()} />
}
