import { useQuery } from '@tanstack/react-query'
import { createFileRoute } from '@tanstack/react-router'

import { OperationDetail } from '../features/operations/OperationDetail'

export const Route = createFileRoute('/operations/$operationId')({
  loader: ({ context, params }) =>
    context.queryClient.ensureQueryData(
      context.queries.operation(params.operationId),
    ),
  component: OperationDetailRoute,
})

function OperationDetailRoute() {
  const initial = Route.useLoaderData()
  const params = Route.useParams()
  const { queries } = Route.useRouteContext()
  const query = useQuery({
    ...queries.operation(params.operationId),
    initialData: initial,
  })
  return <OperationDetail data={query.data} />
}
