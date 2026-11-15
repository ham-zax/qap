import type { components } from './schema'

type WorkspaceStatusDto = components['schemas']['WorkspaceStatusDto']
type ResearchUniverseDto = components['schemas']['ResearchUniverseDto']
type IdentityMappingRequestDto = components['schemas']['IdentityMappingRequestDto']
type AssetAdmissionRequestDto = components['schemas']['AssetAdmissionRequestDto']
type MarketDataPreparationRequestDto =
  components['schemas']['MarketDataPreparationRequestDto']
type ProductMarketDataDto = components['schemas']['ProductMarketDataDto']
type ExperimentListDto = components['schemas']['ExperimentListDto']
type ExperimentDetailDto = components['schemas']['ExperimentDetailDto']
type PortfolioSnapshotDto = components['schemas']['PortfolioSnapshotDto']
type PortfolioPerformanceDto = components['schemas']['PortfolioPerformanceDto']
type PaperOperationDetailDto = components['schemas']['PaperOperationDetailDto']
type PaperOperationSummaryDto = components['schemas']['PaperOperationSummaryDto']
type PairEvidenceDto = components['schemas']['PairEvidenceDto']
type PairSeriesDto = components['schemas']['PairSeriesDto']
type AnchorLensDto = components['schemas']['AnchorLensDto']
type ErrorDetailDto = components['schemas']['ErrorDetailDto']
type OperationDto = components['schemas']['OperationDto']
type OperationListDto = components['schemas']['OperationListDto']

interface ErrorEnvelopeDto {
  error: ErrorDetailDto
}

interface ApiClientOptions {
  baseUrl: string
  fetchImpl?: typeof fetch
}

export class QapApiError extends Error {
  readonly code: string
  readonly status: number
  readonly context: Record<string, string>

  constructor(options: {
    code: string
    message: string
    status: number
    context: Record<string, string>
  }) {
    super(options.message)
    this.name = 'QapApiError'
    this.code = options.code
    this.status = options.status
    this.context = options.context
  }
}

export function createApiClient({
  baseUrl,
  fetchImpl = fetch,
}: ApiClientOptions) {
  const normalizedBaseUrl = baseUrl.replace(/\/+$/, '')

  async function request<T>(path: string, init?: RequestInit): Promise<T> {
    const response = await fetchImpl(`${normalizedBaseUrl}${path}`, {
      ...init,
      headers: {
        Accept: 'application/json',
        ...(init?.body ? { 'Content-Type': 'application/json' } : {}),
        ...init?.headers,
      },
    })
    const payload: unknown = await response.json()
    if (!response.ok) {
      const envelope = payload as ErrorEnvelopeDto
      throw new QapApiError({
        code: envelope.error.code,
        message: envelope.error.message,
        status: response.status,
        context: envelope.error.context,
      })
    }
    return payload as T
  }

  return {
    getWorkspaceStatus: () => request<WorkspaceStatusDto>('/api/workspace'),
    getResearchUniverse: () => request<ResearchUniverseDto>('/api/research-universe'),
    getProductMarketData: () =>
      request<ProductMarketDataDto>('/api/product-market-data'),
    prepareProductMarketData: (command: MarketDataPreparationRequestDto) =>
      request<ProductMarketDataDto>('/api/product-market-data/prepare', {
        method: 'POST',
        body: JSON.stringify(command),
      }),
    refreshProductMarketData: (command: MarketDataPreparationRequestDto) =>
      request<ProductMarketDataDto>('/api/product-market-data/refresh', {
        method: 'POST',
        body: JSON.stringify(command),
      }),
    refreshResearchUniverseDirectory: () =>
      request<ResearchUniverseDto>('/api/research-universe/directory-refresh', {
        method: 'POST',
      }),
    setResearchUniverseIdentityMapping: (command: IdentityMappingRequestDto) =>
      request<ResearchUniverseDto>('/api/research-universe/identity-mappings', {
        method: 'POST',
        body: JSON.stringify(command),
      }),
    setResearchUniverseAdmission: (command: AssetAdmissionRequestDto) =>
      request<ResearchUniverseDto>('/api/research-universe/admission', {
        method: 'POST',
        body: JSON.stringify(command),
      }),
    listExperiments: () => request<ExperimentListDto>('/api/experiments'),
    getExperiment: (runId: string) =>
      request<ExperimentDetailDto>(`/api/experiments/${encodeURIComponent(runId)}`),
    getPortfolio: (runId: string) =>
      request<PortfolioSnapshotDto>(`/api/portfolios/${encodeURIComponent(runId)}`),
    getPortfolioPerformance: (runId: string) =>
      request<PortfolioPerformanceDto>(
        `/api/portfolios/${encodeURIComponent(runId)}/performance`,
      ),
    getPairSeries: (options: {
      runId: string
      assetX: string
      assetY: string
      orientation: string
    }) => {
      const query = new URLSearchParams({
        run_id: options.runId,
        orientation: options.orientation,
      })
      return request<PairSeriesDto>(
        `/api/pairs/${encodeURIComponent(options.assetX)}/${encodeURIComponent(options.assetY)}/series?${query}`,
      )
    },
    listPaperOperations: () =>
      request<PaperOperationSummaryDto[]>('/api/paper-operations'),
    getPaperOperation: (operationId: string) =>
      request<PaperOperationDetailDto>(
        `/api/paper-operations/${encodeURIComponent(operationId)}`,
      ),
    getPairEvidence: (options: {
      runId: string
      assetX: string
      assetY: string
      orientation: string
    }) => {
      const query = new URLSearchParams({
        run_id: options.runId,
        orientation: options.orientation,
      })
      return request<PairEvidenceDto>(
        `/api/pairs/${encodeURIComponent(options.assetX)}/${encodeURIComponent(options.assetY)}/evidence?${query}`,
      )
    },
    listOperations: () => request<OperationListDto>('/api/operations'),
    getOperation: (operationId: string) =>
      request<OperationDto>(`/api/operations/${encodeURIComponent(operationId)}`),
    getAnchorLens: (options: {
      runId: string
      assetX: string
      assetY: string
      anchor: string
      orientation: string
    }) => {
      const query = new URLSearchParams({
        run_id: options.runId,
        anchor: options.anchor,
        orientation: options.orientation,
      })
      return request<AnchorLensDto>(
        `/api/pairs/${encodeURIComponent(options.assetX)}/${encodeURIComponent(options.assetY)}/anchor?${query}`,
      )
    },
  }
}

export type QapApiClient = ReturnType<typeof createApiClient>
