import type { components } from './schema'

type WorkspaceStatusDto = components['schemas']['WorkspaceStatusDto']
type ResearchUniverseDto = components['schemas']['ResearchUniverseDto']
type CurrentApprovedReadinessDto = components['schemas']['CurrentApprovedReadinessDto']
type CurrentApprovedResearchRequestDto =
  components['schemas']['CurrentApprovedResearchRequestDto']
type IdentityMappingRequestDto = components['schemas']['IdentityMappingRequestDto']
type AssetAdmissionRequestDto = components['schemas']['AssetAdmissionRequestDto']
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
type ScannerProtocolDto = components['schemas']['ScannerProtocolDto']
type ScanListDto = components['schemas']['ScanListDto']
type ScanDetailDto = components['schemas']['ScanDetailDto']
type CandidateListDto = components['schemas']['CandidateListDto']
type CandidateDetailDto = components['schemas']['CandidateDetailDto']
type ForwardCohortListDto = components['schemas']['ForwardCohortListDto']
type ForwardCohortDetailDto = components['schemas']['ForwardCohortDetailDto']
type CaptureReadinessDto = components['schemas']['CaptureReadinessDto']
type BasketListDto = components['schemas']['BasketListDto']
type BasketDetailDto = components['schemas']['BasketDetailDto']
type OperationRefDto = components['schemas']['OperationRefDto']
type OperationDto = components['schemas']['OperationDto']
type OperationListDto = components['schemas']['OperationListDto']
type RunScanRequestDto = components['schemas']['RunScanRequestDto']
type MomentumGenerationRequestDto = components['schemas']['MomentumGenerationRequestDto']
type FreezeForwardCohortRequestDto = components['schemas']['FreezeForwardCohortRequestDto']
type AdvanceForwardCohortRequestDto = components['schemas']['AdvanceForwardCohortRequestDto']
type CapturePublicEvidenceRequestDto = components['schemas']['CapturePublicEvidenceRequestDto']
type QualificationRequestDto = components['schemas']['QualificationRequestDto']
type BasketRunRequestDto = components['schemas']['BasketRunRequestDto']

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
    getCurrentApprovedResearchReadiness: (horizon: 'short' | 'medium' | 'swing') => {
      const query = new URLSearchParams({ horizon })
      return request<CurrentApprovedReadinessDto>(
        `/api/product-research/readiness?${query}`,
      )
    },
    runCurrentApprovedResearch: (command: CurrentApprovedResearchRequestDto) =>
      request<OperationRefDto>('/api/product-research', {
        method: 'POST',
        body: JSON.stringify(command),
      }),
    startCurrentApprovedResearchFollowUp: (scanId: string) =>
      request<OperationRefDto>(
        `/api/product-research/${encodeURIComponent(scanId)}/follow-up`,
        { method: 'POST' },
      ),
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
    getScannerProtocol: () => request<ScannerProtocolDto>('/api/scanner/protocol'),
    listScans: () => request<ScanListDto>('/api/scans'),
    getScan: (scanId: string) =>
      request<ScanDetailDto>(`/api/scans/${encodeURIComponent(scanId)}`),
    listScanCandidates: (scanId: string) =>
      request<CandidateListDto>(
        `/api/scans/${encodeURIComponent(scanId)}/candidates`,
      ),
    getScanCandidate: (scanId: string, candidateId: string) =>
      request<CandidateDetailDto>(
        `/api/scans/${encodeURIComponent(scanId)}/candidates/${encodeURIComponent(candidateId)}`,
      ),
    listForwardCohorts: () =>
      request<ForwardCohortListDto>('/api/forward/cohorts'),
    getForwardCohort: (cohortId: string) =>
      request<ForwardCohortDetailDto>(
        `/api/forward/cohorts/${encodeURIComponent(cohortId)}`,
      ),
    getForwardCaptureReadiness: (
      cohortId: string,
      options: { checkpointId: string; asOf: string },
    ) => {
      const query = new URLSearchParams({
        checkpoint_id: options.checkpointId,
        as_of: options.asOf,
      })
      return request<CaptureReadinessDto>(
        `/api/forward/cohorts/${encodeURIComponent(cohortId)}/capture-readiness?${query}`,
      )
    },
    listBaskets: () => request<BasketListDto>('/api/baskets'),
    getBasket: (basketId: string) =>
      request<BasketDetailDto>(`/api/baskets/${encodeURIComponent(basketId)}`),
    listOperations: () => request<OperationListDto>('/api/operations'),
    getOperation: (operationId: string) =>
      request<OperationDto>(`/api/operations/${encodeURIComponent(operationId)}`),
    runScan: (command: RunScanRequestDto) =>
      request<OperationRefDto>('/api/scans', {
        method: 'POST',
        body: JSON.stringify(command),
      }),
    generateAssetMomentum: (scanId: string, command: MomentumGenerationRequestDto) =>
      request<OperationRefDto>(
        `/api/scans/${encodeURIComponent(scanId)}/momentum-generations`,
        { method: 'POST', body: JSON.stringify(command) },
      ),
    freezeForwardCohort: (command: FreezeForwardCohortRequestDto) =>
      request<OperationRefDto>('/api/forward/cohorts', {
        method: 'POST',
        body: JSON.stringify(command),
      }),
    advanceForwardCohort: (
      cohortId: string,
      command: AdvanceForwardCohortRequestDto,
    ) =>
      request<OperationRefDto>(
        `/api/forward/cohorts/${encodeURIComponent(cohortId)}/advances`,
        { method: 'POST', body: JSON.stringify(command) },
      ),
    capturePublicEvidence: (command: CapturePublicEvidenceRequestDto) =>
      request<OperationRefDto>('/api/captures', {
        method: 'POST',
        body: JSON.stringify(command),
      }),
    qualifyCandidate: (command: QualificationRequestDto) =>
      request<OperationRefDto>('/api/qualifications', {
        method: 'POST',
        body: JSON.stringify(command),
      }),
    runBasket: (command: BasketRunRequestDto) =>
      request<OperationRefDto>('/api/basket-runs', {
        method: 'POST',
        body: JSON.stringify(command),
      }),
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
