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
    currentApprovedReadiness: (horizon: 'short' | 'medium' | 'swing') =>
      queryOptions({
        queryKey: ['current-approved-readiness', horizon] as const,
        queryFn: () => client.getCurrentApprovedResearchReadiness(horizon),
      }),
    scannerProtocol: () =>
      queryOptions({
        queryKey: ['scanner-protocol'] as const,
        queryFn: () => client.getScannerProtocol(),
        staleTime: Number.POSITIVE_INFINITY,
      }),
    scans: () =>
      queryOptions({
        queryKey: ['scans'] as const,
        queryFn: () => client.listScans(),
      }),
    scan: (scanId: string) =>
      queryOptions({
        queryKey: ['scan', scanId] as const,
        queryFn: () => client.getScan(scanId),
      }),
    scanCandidates: (scanId: string) =>
      queryOptions({
        queryKey: ['scan-candidates', scanId] as const,
        queryFn: () => client.listScanCandidates(scanId),
      }),
    scanCandidate: (scanId: string, candidateId: string) =>
      queryOptions({
        queryKey: ['scan-candidate', scanId, candidateId] as const,
        queryFn: () => client.getScanCandidate(scanId, candidateId),
      }),
    forwardCohorts: () =>
      queryOptions({
        queryKey: ['forward-cohorts'] as const,
        queryFn: () => client.listForwardCohorts(),
      }),
    forwardCohort: (cohortId: string) =>
      queryOptions({
        queryKey: ['forward-cohort', cohortId] as const,
        queryFn: () => client.getForwardCohort(cohortId),
      }),
    baskets: () =>
      queryOptions({
        queryKey: ['baskets'] as const,
        queryFn: () => client.listBaskets(),
      }),
    basket: (basketId: string) =>
      queryOptions({
        queryKey: ['basket', basketId] as const,
        queryFn: () => client.getBasket(basketId),
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
    history: () =>
      queryOptions({
        queryKey: ['history'] as const,
        queryFn: () => client.getHistory(),
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
