import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useMemo, useState } from 'react'

import type { QapApiClient } from '../../api/client'
import type { QapQueries } from '../../api/queries'
import type {
  CapabilityMetadataV1,
  OperationDto,
  ProductPairStudyContextDto,
  ProductPairStudySeriesDto,
  ResearchRecipeCheckV1,
  ResearchUniverseDto,
  WorkspaceStatusDto,
} from '../../api/types'
import { Badge } from '../../components/ui/Badge'
import {
  ResearchAssetSelector,
  type ResearchAssetSelection,
} from './ResearchAssetSelector'
import { PairResearchCompletion } from './PairResearchCompletion'
import { PairStudyResults } from './PairStudyResults'
import { SupportReportPanel } from './SupportReportPanel'

type Horizon = 'short' | 'medium' | 'swing'

const TIMEFRAMES: Array<{ value: Horizon; label: string; description: string }> = [
  { value: 'short', label: 'Short-term', description: 'Faster relationship windows.' },
  { value: 'medium', label: 'Medium-term', description: 'A broader multi-day research window.' },
  { value: 'swing', label: 'Longer-term', description: 'The longest Product research window.' },
]

interface PairResearchProps {
  apiClient: QapApiClient
  queries: QapQueries
  workspace: WorkspaceStatusDto
}

interface IdentityDraft {
  canonicalAssetId: string
  assetIdentityVersion: string
}

interface PairStudyResult {
  context: ProductPairStudyContextDto
  series: ProductPairStudySeriesDto | null
  capabilities: CapabilityMetadataV1[]
}

interface PairStudyRequestOptions {
  venue?: 'binance' | 'gate'
  analysisReference?: string
}

function resultRunIds(operation: OperationDto | undefined): string[] {
  const value = operation?.result?.run_ids
  if (!Array.isArray(value)) return []
  return value.filter((item): item is string => typeof item === 'string')
}

function resultCompilation(operation: OperationDto | undefined): string | null {
  const value = operation?.result?.compilation_sha256
  return typeof value === 'string' ? value : null
}

function canonicalSelection(
  universe: ResearchUniverseDto,
  canonicalAssetId: string,
): ResearchAssetSelection | null {
  const asset = universe.assets.find(
    (item) => item.canonical_asset_id === canonicalAssetId,
  )
  if (!asset) return null
  return {
    key: `asset:${asset.canonical_asset_id}`,
    symbol: asset.canonical_asset_id,
    canonicalAssetId: asset.canonical_asset_id,
    approved: asset.approved,
    identityState: asset.identity_state,
    venueSymbols: asset.venues.map((venue) => venue.venue_symbol),
  }
}

export function PairResearch({ apiClient, queries, workspace }: PairResearchProps) {
  const queryClient = useQueryClient()
  const [assetA, setAssetA] = useState<ResearchAssetSelection | null>(null)
  const [assetB, setAssetB] = useState<ResearchAssetSelection | null>(null)
  const [horizon, setHorizon] = useState<Horizon>('short')
  const [identityDraft, setIdentityDraft] = useState<IdentityDraft>({
    canonicalAssetId: '',
    assetIdentityVersion: '',
  })
  const [checked, setChecked] = useState<ResearchRecipeCheckV1 | null>(null)
  const [operationId, setOperationId] = useState<string | null>(null)
  const [studyResult, setStudyResult] = useState<PairStudyResult | null>(null)
  const [useBtcReference, setUseBtcReference] = useState(false)

  const universe = useQuery(queries.researchUniverse())
  const canonicalAssets = useMemo<[string, string] | null>(
    () =>
      assetA?.canonicalAssetId && assetB?.canonicalAssetId
        ? [assetA.canonicalAssetId, assetB.canonicalAssetId]
        : null,
    [assetA, assetB],
  )
  const operation = useQuery({
    ...queries.operation(operationId ?? ''),
    enabled: operationId !== null,
  })

  const clearResult = () => {
    setStudyResult(null)
    setChecked(null)
    setOperationId(null)
    setUseBtcReference(false)
  }

  const acceptUniverse = (next: ResearchUniverseDto) => {
    queryClient.setQueryData(['research-universe'], next)
  }

  const refreshRecipeReads = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ['research-universe'] }),
      queryClient.invalidateQueries({ queryKey: ['current-approved-readiness', horizon] }),
      queryClient.invalidateQueries({ queryKey: ['research-recipe-product-context'] }),
      queryClient.invalidateQueries({ queryKey: ['product-pair-study-context'] }),
      queryClient.invalidateQueries({ queryKey: ['product-pair-study-series'] }),
      queryClient.invalidateQueries({ queryKey: ['product-market-data'] }),
    ])
  }

  const identity = useMutation({
    mutationFn: async (selection: ResearchAssetSelection) => {
      if (!selection.venue || !selection.venueAssetCode) {
        throw new Error('The selected venue identity cannot be confirmed from this item.')
      }
      return apiClient.setResearchUniverseIdentityMapping({
        venue: selection.venue,
        venue_asset_code: selection.venueAssetCode,
        canonical_asset_id: identityDraft.canonicalAssetId,
        asset_identity_version: identityDraft.assetIdentityVersion,
      })
    },
    onSuccess: async (next, selection) => {
      acceptUniverse(next)
      const resolved = canonicalSelection(next, identityDraft.canonicalAssetId.trim().toUpperCase())
      if (resolved) {
        if (assetA?.key === selection.key) setAssetA(resolved)
        if (assetB?.key === selection.key) setAssetB(resolved)
      }
      setIdentityDraft({ canonicalAssetId: '', assetIdentityVersion: '' })
      clearResult()
      await refreshRecipeReads()
    },
  })

  const admission = useMutation({
    mutationFn: (selection: ResearchAssetSelection) => {
      if (!selection.canonicalAssetId) throw new Error('Canonical asset identity is required.')
      return apiClient.setResearchUniverseAdmission({
        canonical_asset_id: selection.canonicalAssetId,
        approved: true,
      })
    },
    onSuccess: async (next, selection) => {
      acceptUniverse(next)
      if (selection.canonicalAssetId) {
        const resolved = canonicalSelection(next, selection.canonicalAssetId)
        if (resolved) {
          if (assetA?.key === selection.key) setAssetA(resolved)
          if (assetB?.key === selection.key) setAssetB(resolved)
        }
      }
      clearResult()
      await refreshRecipeReads()
    },
  })

  const researchPair = useMutation({
    mutationFn: async (options: PairStudyRequestOptions = {}): Promise<{
      study: PairStudyResult
      check: ResearchRecipeCheckV1 | null
    }> => {
      if (!canonicalAssets) throw new Error('Choose two canonical assets first.')
      const [assetAId, assetBId] = canonicalAssets
      const analysisReference = options.analysisReference
      const orientation = `${assetAId}/${assetBId}`
      const pairOptions = {
        assetA: assetAId,
        assetB: assetBId,
        horizon,
        orientation,
        venue: options.venue,
        analysisReference,
      }

      let context = await queryClient.fetchQuery(
        queries.productPairStudyContext(pairOptions),
      )
      const referenceNeedsData =
        analysisReference !== undefined && context.analysis_lens?.status === 'needs_data'
      if (context.data.status === 'needs_setup' || referenceNeedsData) {
        await apiClient.prepareProductMarketData({
          horizons: [horizon],
          asset_ids: [assetAId, assetBId],
          analysis_reference_ids: analysisReference ? [analysisReference] : [],
        })
        await queryClient.invalidateQueries({ queryKey: ['product-market-data'] })
        await queryClient.invalidateQueries({ queryKey: ['product-pair-study-context'] })
        context = await queryClient.fetchQuery(
          queries.productPairStudyContext(pairOptions),
        )
      }

      const series =
        context.data.status === 'ready'
          ? await queryClient.fetchQuery(
              queries.productPairStudySeries({
                ...pairOptions,
                venue: context.question.venue,
                analysisReference:
                  context.analysis_lens?.status === 'ready' ? analysisReference : undefined,
              }),
            )
          : null

      const recipeContext = await apiClient.getResearchRecipeProductContext({
        researchObject: 'pair',
        horizon,
        assets: canonicalAssets,
        orientation: context.question.orientation,
        venue: context.question.venue,
      })
      const check =
        context.economic_expression.default_recipe_declarable && recipeContext.default_draft
          ? await apiClient.checkResearchRecipeSupport({
              schema_version: 'qap.api.research-recipe-check-request.v1',
              recipe: recipeContext.default_draft,
            })
          : null

      return {
        study: {
          context,
          series,
          capabilities: recipeContext.capabilities,
        },
        check,
      }
    },
    onSuccess: ({ study, check }) => {
      setStudyResult(study)
      setChecked(check)
      setOperationId(null)
    },
  })

  const grantBridgeAuthority = useMutation({
    mutationFn: () => apiClient.grantProductPairStudyTransientUsdtAuthority(),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['research-recipe-product-context'] }),
        queryClient.invalidateQueries({ queryKey: ['product-pair-study-context'] }),
      ])
      if (studyResult) {
        researchPair.mutate({
          venue: studyResult.context.question.venue,
          analysisReference:
            studyResult.context.analysis_lens?.status === 'ready'
              ? studyResult.context.analysis_lens.asset
              : undefined,
        })
      }
    },
  })

  const runRecipe = useMutation({
    mutationFn: () => {
      if (!checked?.support.runnable || !checked.recipe) {
        throw new Error('The backend has not authorized this exact recipe to run.')
      }
      return apiClient.runResearchRecipe({
        schema_version: 'qap.api.research-recipe-run-request.v1',
        recipe: checked.recipe,
      })
    },
    onSuccess: (ref) => setOperationId(ref.operation_id),
  })

  if (workspace.workspace_mode === 'sample') {
    return (
      <section className="rounded-lg border border-warning/45 bg-panel p-5">
        <Badge tone="warning">Sample Workspace</Badge>
        <h2 className="mt-3 mb-2 text-xl font-semibold text-foreground">Research a pair</h2>
        <p className="m-0 text-sm leading-6 text-secondary">
          Pair Research freezes current Local Market identity and market-data generations.
          Sample Workspace remains read-only evidence.
        </p>
      </section>
    )
  }

  const unresolved = [assetA, assetB].find(
    (selection) => selection && selection.canonicalAssetId === null,
  ) ?? null
  const needsApproval = [assetA, assetB].find(
    (selection) => selection?.canonicalAssetId && !selection.approved,
  ) ?? null
  const runIds = resultRunIds(operation.data)
  const compilation = resultCompilation(operation.data)
  const selectedPairVenues = canonicalAssets
    ? canonicalAssets
        .map(
          (assetId) =>
            universe.data?.assets.find((asset) => asset.canonical_asset_id === assetId)
              ?.venues ?? [],
        )
        .map((venues) => new Set(venues.map((venue) => venue.venue)))
        .reduce<Array<'binance' | 'gate'>>(
          (common, venues, index) =>
            index === 0 ? [...venues] : common.filter((venue) => venues.has(venue)),
          [],
        )
    : []
  const btcReference = universe.data?.assets.find(
    (asset) => asset.canonical_asset_id === 'BTC' && asset.identity_state === 'resolved',
  )
  const btcReferenceResolved = btcReference !== undefined
  const btcReferenceEligible =
    canonicalAssets !== null &&
    !canonicalAssets.includes('BTC') &&
    btcReference !== undefined &&
    btcReference.venues.some((venue) => selectedPairVenues.includes(venue.venue))
  const analysisReference = useBtcReference && btcReferenceEligible ? 'BTC' : undefined

  return (
    <section className="rounded-lg border border-border-strong bg-panel p-5 md:p-6" aria-labelledby="pair-research-heading">
      <p className="m-0 text-xs font-semibold uppercase tracking-[0.08em] text-accent">
        Start here
      </p>
      <h2 id="pair-research-heading" className="mt-2 mb-2 text-2xl font-semibold text-foreground">
        Research a pair
      </h2>
      <p className="m-0 max-w-4xl text-sm leading-6 text-secondary">
        Choose two assets and one timeframe. QAP studies their same-venue relationship first,
        preparing only this pair when needed. Economic replay and recipe support are a later,
        separate question.
      </p>

      {universe.data ? (
        <div className="mt-5 grid gap-4 lg:grid-cols-2">
          <ResearchAssetSelector
            label="Asset A"
            universe={universe.data}
            selected={assetA}
            excludeCanonicalAssetIds={assetB?.canonicalAssetId ? [assetB.canonicalAssetId] : []}
            onSelect={(selection) => {
              setAssetA(selection)
              clearResult()
            }}
            onClear={() => {
              setAssetA(null)
              clearResult()
            }}
          />
          <ResearchAssetSelector
            label="Asset B"
            universe={universe.data}
            selected={assetB}
            excludeCanonicalAssetIds={assetA?.canonicalAssetId ? [assetA.canonicalAssetId] : []}
            onSelect={(selection) => {
              setAssetB(selection)
              clearResult()
            }}
            onClear={() => {
              setAssetB(null)
              clearResult()
            }}
          />
        </div>
      ) : universe.isPending ? (
        <p className="mt-5 text-sm text-secondary">Loading current research assets…</p>
      ) : (
        <p className="mt-5 text-sm text-negative">{universe.error?.message}</p>
      )}

      <fieldset className="mt-6 border-0 p-0">
        <legend className="text-sm font-semibold text-foreground">Product timeframe</legend>
        <div className="mt-3 grid gap-3 md:grid-cols-3">
          {TIMEFRAMES.map((item) => (
            <label key={item.value} className="flex min-h-20 cursor-pointer gap-3 rounded-md border border-border p-4">
              <input
                type="radio"
                name="pair-research-timeframe"
                checked={horizon === item.value}
                onChange={() => {
                  setHorizon(item.value)
                  clearResult()
                }}
              />
              <span>
                <strong className="block text-sm text-foreground">{item.label}</strong>
                <span className="mt-1 block text-xs leading-5 text-muted">{item.description}</span>
              </span>
            </label>
          ))}
        </div>
      </fieldset>

      {unresolved ? (
        <section className="mt-6 rounded-lg border border-warning/45 bg-subtle p-5">
          <Badge tone="warning">One-time setup</Badge>
          <h3 className="mt-3 mb-2 text-lg font-semibold text-foreground">
            {unresolved.symbol} needs identity confirmation
          </h3>
          <p className="m-0 text-sm leading-6 text-secondary">
            QAP found this venue code, but matching ticker text is not identity proof.
            Confirm the canonical economic asset and identity version from independent
            evidence. Your pair and timeframe stay selected.
          </p>
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            <label className="text-sm font-medium text-secondary">
              Canonical asset
              <input
                className="mt-2 min-h-11 w-full rounded-md border border-border bg-canvas px-3 text-foreground"
                value={identityDraft.canonicalAssetId}
                onChange={(event) =>
                  setIdentityDraft((current) => ({
                    ...current,
                    canonicalAssetId: event.target.value.toUpperCase(),
                  }))
                }
                placeholder={unresolved.symbol}
              />
            </label>
            <label className="text-sm font-medium text-secondary">
              Confirmed identity version
              <input
                className="mt-2 min-h-11 w-full rounded-md border border-border bg-canvas px-3 text-foreground"
                value={identityDraft.assetIdentityVersion}
                onChange={(event) =>
                  setIdentityDraft((current) => ({
                    ...current,
                    assetIdentityVersion: event.target.value,
                  }))
                }
                placeholder="Confirmed token/contract identity"
              />
            </label>
          </div>
          <button
            type="button"
            className="mt-4 min-h-11 rounded-md bg-accent px-4 font-semibold text-canvas disabled:opacity-50"
            disabled={
              identity.isPending ||
              !identityDraft.canonicalAssetId.trim() ||
              !identityDraft.assetIdentityVersion.trim()
            }
            onClick={() => identity.mutate(unresolved)}
          >
            {identity.isPending ? 'Saving…' : `Confirm ${unresolved.symbol}`}
          </button>
          {identity.isError ? <p className="mt-3 text-sm text-negative">{identity.error.message}</p> : null}
        </section>
      ) : needsApproval ? (
        <section className="mt-6 rounded-lg border border-warning/45 bg-subtle p-5">
          <Badge tone="warning">One-time setup</Badge>
          <h3 className="mt-3 mb-2 text-lg font-semibold text-foreground">
            Allow {needsApproval.symbol} in Product research
          </h3>
          <p className="m-0 text-sm leading-6 text-secondary">
            Identity and approval are separate. This action records that this operator allows
            QAP to include the canonical asset in Product research; it does not change the
            selected pair.
          </p>
          <button
            type="button"
            className="mt-4 min-h-11 rounded-md bg-accent px-4 font-semibold text-canvas disabled:opacity-50"
            disabled={admission.isPending}
            onClick={() => admission.mutate(needsApproval)}
          >
            {admission.isPending ? 'Saving…' : `Approve ${needsApproval.symbol}`}
          </button>
          {admission.isError ? <p className="mt-3 text-sm text-negative">{admission.error.message}</p> : null}
        </section>
      ) : canonicalAssets ? (
        <section className="mt-6 rounded-lg border border-border bg-subtle p-5">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="m-0 text-xs font-semibold uppercase tracking-[0.08em] text-muted">
                Research question
              </p>
              <h3 className="mt-2 mb-1 text-lg font-semibold text-foreground">
                {assetA?.symbol} / {assetB?.symbol} ·{' '}
                {TIMEFRAMES.find((item) => item.value === horizon)?.label}
              </h3>
              <p className="m-0 max-w-2xl text-sm leading-6 text-secondary">
                One action reads Pair Study context, prepares the exact selected pair only if
                needed, and returns backend-owned relationship values on this screen.
              </p>
            </div>
            <button
              type="button"
              className="min-h-11 rounded-md border border-border px-4 text-sm font-semibold text-accent"
              onClick={() => {
                const previousA = assetA
                setAssetA(assetB)
                setAssetB(previousA)
                clearResult()
              }}
            >
              Reverse orientation
            </button>
          </div>

          {!canonicalAssets.includes('BTC') ? (
            <label className="mt-4 flex max-w-2xl items-start gap-3 rounded-md border border-border bg-panel p-4 text-sm text-secondary">
              <input
                type="checkbox"
                className="mt-1"
                checked={useBtcReference}
                disabled={!btcReferenceEligible || researchPair.isPending}
                onChange={(event) => {
                  setUseBtcReference(event.target.checked)
                  setStudyResult(null)
                  setChecked(null)
                  setOperationId(null)
                }}
              />
              <span>
                <strong className="block text-foreground">Add a descriptive BTC lens</strong>
                <span className="mt-1 block leading-5">
                  {btcReferenceEligible
                    ? 'Optional analysis only. BTC is not added to this economic pair, scanner scope, or execution.'
                    : btcReferenceResolved
                      ? 'Unavailable because BTC has no resolved same-venue path with this pair. Pair Research does not require it.'
                      : 'Unavailable until canonical BTC reference identity is resolved. Pair Research does not require it.'}
                </span>
              </span>
            </label>
          ) : null}

          <div className="mt-5 flex flex-wrap items-center gap-3">
            <button
              type="button"
              className="min-h-12 rounded-md bg-accent px-6 font-semibold text-canvas disabled:opacity-50"
              disabled={researchPair.isPending}
              onClick={() => researchPair.mutate({ analysisReference })}
            >
              {researchPair.isPending ? 'Researching this pair…' : 'Research this pair'}
            </button>
            <span className="text-xs leading-5 text-muted">
              Pair Study readiness is independent from direct-market recipe readiness.
            </span>
          </div>
          {researchPair.isError ? (
            <p className="mt-4 text-sm leading-6 text-negative">
              Pair setup or data preparation could not complete: {researchPair.error.message}{' '}
              This is an operational state, not a negative relationship result.
            </p>
          ) : null}
        </section>
      ) : null}

      {studyResult ? (
        <PairStudyResults
          context={studyResult.context}
          series={studyResult.series}
          capabilities={studyResult.capabilities}
          busy={researchPair.isPending}
          bridgeAuthorityBusy={grantBridgeAuthority.isPending}
          bridgeAuthorityError={
            grantBridgeAuthority.isError ? grantBridgeAuthority.error.message : null
          }
          onGrantBridgeAuthority={() => grantBridgeAuthority.mutate()}
          onVenueChange={(venue) => researchPair.mutate({ venue, analysisReference })}
        />
      ) : null}

      {checked ? (
        <div className="mt-6 space-y-4">
          <div>
            <p className="m-0 text-xs font-semibold uppercase tracking-[0.08em] text-muted">
              Downstream economic recipe
            </p>
            <h3 className="mt-2 mb-3 text-lg font-semibold text-foreground">
              Default economic replay support
            </h3>
            <SupportReportPanel report={checked.support} />
          </div>
          <button
            type="button"
            className="min-h-11 rounded-md bg-accent px-5 font-semibold text-canvas disabled:opacity-50"
            disabled={!checked.support.runnable || !checked.recipe || runRecipe.isPending || operation.data?.status === 'running'}
            onClick={() => runRecipe.mutate()}
          >
            {runRecipe.isPending ? 'Starting…' : 'Run this exact recipe'}
          </button>
          {runRecipe.isError ? <p className="text-sm text-negative">{runRecipe.error.message}</p> : null}
        </div>
      ) : null}

      {operationId ? (
        <section className="mt-6 rounded-lg border border-border bg-panel p-5">
          <div className="flex flex-wrap items-center gap-2">
            <Badge tone={operation.data?.status === 'failed' ? 'negative' : operation.data?.status === 'running' ? 'info' : 'neutral'}>
              {operation.data?.status ?? 'starting'}
            </Badge>
          </div>
          <h3 className="mt-3 mb-2 text-lg font-semibold text-foreground">Research operation</h3>
          <p className="m-0 text-sm text-secondary">
            Activity remains the authoritative lifecycle record. Completed operation state
            does not imply a positive research result.
          </p>
          <a className="mt-3 inline-flex min-h-11 items-center font-semibold text-accent" href={`/operations/${operationId}`}>
            View in Activity
          </a>
          {runIds.length ? (
            <div className="mt-5 border-t border-border pt-4">
              <h4 className="m-0 text-sm font-semibold text-foreground">Exact recipe runs</h4>
              <div className="mt-3 flex flex-wrap gap-3">
                {runIds.map((runId, index) => (
                  <a key={runId} className="font-semibold text-accent" href={`/experiments/${runId}`}>
                    Variant {index + 1} result
                  </a>
                ))}
              </div>
              {compilation ? (
                <details className="mt-4 text-xs text-muted">
                  <summary className="cursor-pointer font-semibold text-accent">Exact recipe lineage</summary>
                  <p className="mt-2 mb-0 break-all">Compilation: {compilation}</p>
                </details>
              ) : null}
            </div>
          ) : null}
        </section>
      ) : null}

      {operationId && operation.data?.status === 'completed' && runIds.length > 0 && studyResult ? (
        <PairResearchCompletion
          queries={queries}
          context={studyResult.context}
          runIds={runIds}
          operationId={operationId}
          compilationSha256={compilation}
        />
      ) : null}
    </section>
  )
}
