import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useMemo, useState } from 'react'

import type { QapApiClient } from '../../api/client'
import type { QapQueries } from '../../api/queries'
import type {
  OperationDto,
  ResearchRecipeCheckV1,
  ResearchUniverseDto,
  WorkspaceStatusDto,
} from '../../api/types'
import { Badge } from '../../components/ui/Badge'
import {
  ResearchAssetSelector,
  type ResearchAssetSelection,
} from './ResearchAssetSelector'
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

  const universe = useQuery(queries.researchUniverse())
  const canonicalAssets = useMemo(
    () =>
      assetA?.canonicalAssetId && assetB?.canonicalAssetId
        ? [assetA.canonicalAssetId, assetB.canonicalAssetId]
        : null,
    [assetA, assetB],
  )
  const productContext = useQuery({
    ...queries.researchRecipeProductContext({
      researchObject: 'pair',
      horizon,
      assets: canonicalAssets ?? undefined,
    }),
    enabled: workspace.workspace_mode === 'local_market' && canonicalAssets !== null,
  })
  const operation = useQuery({
    ...queries.operation(operationId ?? ''),
    enabled: operationId !== null,
  })

  const clearResult = () => {
    setChecked(null)
    setOperationId(null)
  }

  const acceptUniverse = (next: ResearchUniverseDto) => {
    queryClient.setQueryData(['research-universe'], next)
  }

  const refreshRecipeReads = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ['research-universe'] }),
      queryClient.invalidateQueries({ queryKey: ['current-approved-readiness', horizon] }),
      queryClient.invalidateQueries({ queryKey: ['research-recipe-product-context'] }),
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

  const prepare = useMutation({
    mutationFn: () => apiClient.prepareProductMarketData({ horizons: [horizon] }),
    onSuccess: async () => {
      clearResult()
      await refreshRecipeReads()
    },
  })

  const checkSupport = useMutation({
    mutationFn: () => {
      const draft = productContext.data?.default_draft
      if (!draft) throw new Error('The backend has not produced an exact pair recipe yet.')
      return apiClient.checkResearchRecipeSupport({
        schema_version: 'qap.api.research-recipe-check-request.v1',
        recipe: draft,
      })
    },
    onSuccess: setChecked,
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

  return (
    <section className="rounded-lg border border-border-strong bg-panel p-5 md:p-6" aria-labelledby="pair-research-heading">
      <p className="m-0 text-xs font-semibold uppercase tracking-[0.08em] text-accent">
        Start here
      </p>
      <h2 id="pair-research-heading" className="mt-2 mb-2 text-2xl font-semibold text-foreground">
        Research a pair
      </h2>
      <p className="m-0 max-w-4xl text-sm leading-6 text-secondary">
        Choose the two assets and one timeframe. QAP supplies the versioned default pair
        recipe, checks exact support, and runs only the canonical recipe the backend marks
        runnable.
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
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="m-0 text-xs font-semibold uppercase tracking-[0.08em] text-muted">
                Backend-owned Product recipe
              </p>
              <h3 className="mt-2 mb-1 text-lg font-semibold text-foreground">
                {assetA?.symbol} / {assetB?.symbol} · {TIMEFRAMES.find((item) => item.value === horizon)?.label}
              </h3>
              <p className="m-0 text-sm text-secondary">
                {productContext.data?.default_recipe_version ?? 'Loading versioned default…'}
              </p>
            </div>
            {productContext.data?.default_draft ? <Badge tone="info">Exact draft frozen</Badge> : null}
          </div>

          {productContext.isPending ? (
            <p className="mt-4 text-sm text-secondary">Freezing exact Product inputs…</p>
          ) : productContext.data?.default_issue ? (
            <div className="mt-4 rounded-md border border-warning/40 bg-panel p-4">
              <p className="m-0 font-semibold text-foreground">
                {productContext.data.default_issue.detail}
              </p>
              {productContext.data.default_issue.code === 'requires_market_data' ? (
                <button
                  type="button"
                  className="mt-3 min-h-11 rounded-md bg-accent px-4 font-semibold text-canvas disabled:opacity-50"
                  disabled={prepare.isPending}
                  onClick={() => prepare.mutate()}
                >
                  {prepare.isPending ? 'Preparing…' : 'Prepare data for this research'}
                </button>
              ) : null}
              {prepare.isError ? <p className="mt-3 text-sm text-negative">{prepare.error.message}</p> : null}
            </div>
          ) : productContext.data?.default_draft ? (
            <div className="mt-4 flex flex-wrap items-center gap-3">
              <button
                type="button"
                className="min-h-11 rounded-md bg-accent px-5 font-semibold text-canvas disabled:opacity-50"
                disabled={checkSupport.isPending}
                onClick={() => checkSupport.mutate()}
              >
                {checkSupport.isPending ? 'Checking…' : checked ? 'Check support again' : 'Check support'}
              </button>
              <span className="text-xs text-muted">
                QAP checks capability, authority, readiness, fidelity, and exact data binding.
              </span>
            </div>
          ) : productContext.isError ? (
            <p className="mt-4 text-sm text-negative">{productContext.error.message}</p>
          ) : null}
        </section>
      ) : null}

      {checked ? (
        <div className="mt-6 space-y-4">
          <SupportReportPanel report={checked.support} />
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
    </section>
  )
}
