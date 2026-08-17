import type { components } from './schema'

type ExperimentListDto = components['schemas']['ExperimentListDto']
type ExperimentDetailDto = components['schemas']['ExperimentDetailDto']
type PortfolioSnapshotDto = components['schemas']['PortfolioSnapshotDto']
type PortfolioPerformanceDto = components['schemas']['PortfolioPerformanceDto']
type PairEvidenceDto = components['schemas']['PairEvidenceDto']
type PairSeriesDto = components['schemas']['PairSeriesDto']
type AnchorLensDto = components['schemas']['AnchorLensDto']
type ErrorDetailDto = components['schemas']['ErrorDetailDto']

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

  async function request<T>(path: string): Promise<T> {
    const response = await fetchImpl(`${normalizedBaseUrl}${path}`, {
      headers: { Accept: 'application/json' },
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
