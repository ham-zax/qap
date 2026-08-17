import { queryOptions } from '@tanstack/react-query'

import type { QapApiClient } from './client'

export function createQapQueries(client: QapApiClient) {
  return {
    experiments: () =>
      queryOptions({
        queryKey: ['experiments'] as const,
        queryFn: () => client.listExperiments(),
      }),
    experiment: (runId: string) =>
      queryOptions({
        queryKey: ['experiment', runId] as const,
        queryFn: () => client.getExperiment(runId),
      }),
    portfolio: (runId: string) =>
      queryOptions({
        queryKey: ['portfolio', runId] as const,
        queryFn: () => client.getPortfolio(runId),
      }),
    performance: (runId: string) =>
      queryOptions({
        queryKey: ['portfolio-performance', runId] as const,
        queryFn: () => client.getPortfolioPerformance(runId),
      }),
    pairSeries: (options: {
      runId: string
      assetX: string
      assetY: string
      orientation: string
    }) =>
      queryOptions({
        queryKey: [
          'pair-series',
          options.runId,
          options.assetX,
          options.assetY,
          options.orientation,
        ] as const,
        queryFn: () => client.getPairSeries(options),
      }),
    anchorLens: (options: {
      runId: string
      assetX: string
      assetY: string
      anchor: string
      orientation: string
    }) =>
      queryOptions({
        queryKey: [
          'anchor-lens',
          options.runId,
          options.assetX,
          options.assetY,
          options.anchor,
          options.orientation,
        ] as const,
        queryFn: () => client.getAnchorLens(options),
      }),
  }
}

export type QapQueries = ReturnType<typeof createQapQueries>
