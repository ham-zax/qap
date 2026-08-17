import { createFileRoute, redirect } from '@tanstack/react-router'

import { PairWorkbench } from '../features/pairs/PairWorkbench'
import {
  canonicalPairSearch,
  parsePairSearch,
  type PairSearch,
} from '../features/pairs/pairSearch'

export const Route = createFileRoute('/pair/$runId/$assetX/$assetY')({
  validateSearch: parsePairSearch,
  beforeLoad: ({ params, search }) => {
    const canonical = canonicalPairSearch(params, search)
    if (canonical.changed) {
      throw redirect({
        to: '/pair/$runId/$assetX/$assetY',
        params,
        search: canonical.search,
        replace: true,
      })
    }
  },
  loaderDeps: ({ search }) => search,
  loader: async ({ context, params, deps }) => {
    const canonical = canonicalPairSearch(params, deps).search
    const [data, evidenceData] = await Promise.all([
      context.queryClient.ensureQueryData(
        context.queries.pairSeries({
          runId: params.runId,
          assetX: params.assetX,
          assetY: params.assetY,
          orientation: canonical.orientation,
        }),
      ),
      context.queryClient.ensureQueryData(
        context.queries.pairEvidence({
          runId: params.runId,
          assetX: params.assetX,
          assetY: params.assetY,
          orientation: canonical.orientation,
        }),
      ),
    ])
    const anchorData =
      canonical.anchor === 'none'
        ? null
        : await context.queryClient.ensureQueryData(
            context.queries.anchorLens({
              runId: params.runId,
              assetX: params.assetX,
              assetY: params.assetY,
              anchor: canonical.anchor,
              orientation: canonical.orientation,
            }),
          )
    return { data, evidenceData, anchorData, search: canonical }
  },
  component: PairRoute,
})

function PairRoute() {
  const loaded = Route.useLoaderData()
  const navigate = Route.useNavigate()
  const handleSearchChange = (search: PairSearch) => {
    void navigate({ search, replace: true })
  }

  return <PairWorkbench {...loaded} onSearchChange={handleSearchChange} />
}
