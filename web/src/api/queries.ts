import { queryOptions } from '@tanstack/react-query'

import type { QapApiClient } from './client'

export function createQapQueries(client: QapApiClient) {
  return {
    workspaceStatus: () =>
      queryOptions({
        queryKey: ['workspace-status'] as const,
        queryFn: () => client.getWorkspaceStatus(),
        refetchInterval: 5_000,
      }),
    researchUniverse: () =>
      queryOptions({
        queryKey: ['research-universe'] as const,
        queryFn: () => client.getResearchUniverse(),
      }),
    productMarketData: () =>
      queryOptions({
        queryKey: ['product-market-data'] as const,
        queryFn: () => client.getProductMarketData(),
      }),
    operations: () =>
      queryOptions({
        queryKey: ['operations'] as const,
        queryFn: () => client.listOperations(),
        refetchInterval: 2_000,
      }),
    operation: (operationId: string) =>
      queryOptions({
        queryKey: ['operation', operationId] as const,
        queryFn: () => client.getOperation(operationId),
        refetchInterval: (query) =>
          query.state.data?.status === 'running' ? 1_000 : false,
      }),
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
    paperOperations: () =>
      queryOptions({
        queryKey: ['paper-operations'] as const,
        queryFn: () => client.listPaperOperations(),
      }),
    paperOperation: (operationId: string) =>
      queryOptions({
        queryKey: ['paper-operation', operationId] as const,
        queryFn: () => client.getPaperOperation(operationId),
      }),
    pairEvidence: (options: {
      runId: string
      assetX: string
      assetY: string
      orientation: string
    }) =>
      queryOptions({
        queryKey: [
          'pair-evidence',
          options.runId,
          options.assetX,
          options.assetY,
          options.orientation,
        ] as const,
        queryFn: () => client.getPairEvidence(options),
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
