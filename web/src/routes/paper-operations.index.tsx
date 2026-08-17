import { createFileRoute } from '@tanstack/react-router'

import { PaperOperationList } from '../features/paper/PaperOperationList'

export const Route = createFileRoute('/paper-operations/')({
  loader: ({ context }) =>
    context.queryClient.ensureQueryData(context.queries.paperOperations()),
  component: PaperOperationsRoute,
})

function PaperOperationsRoute() {
  const data = Route.useLoaderData()
  return <PaperOperationList items={data} />
}
