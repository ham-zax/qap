import { createFileRoute } from '@tanstack/react-router'

import { PaperOperationDetail } from '../features/paper/PaperOperationDetail'

export const Route = createFileRoute('/paper-operations/$operationId')({
  loader: ({ context, params }) =>
    context.queryClient.ensureQueryData(
      context.queries.paperOperation(params.operationId),
    ),
  component: PaperOperationDetailRoute,
})

function PaperOperationDetailRoute() {
  const data = Route.useLoaderData()
  return <PaperOperationDetail data={data} />
}
