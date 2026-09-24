import { useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import type { QapApiClient } from '../../api/client'
import type { QapQueries } from '../../api/queries'
import type {
  CapabilityMetadataV1,
  OperationDto,
  ResearchRecipeCheckV1,
  ResearchRecipeDraftV1,
  WorkspaceStatusDto,
} from '../../api/types'
import { Badge } from '../../components/ui/Badge'
import {
  ResearchAssetSelector,
  type ResearchAssetSelection,
} from './ResearchAssetSelector'
import {
  ComponentSelect,
  JsonConfigEditor,
  ResearchParameterControls,
} from './RecipeAuthoringControls'
import { SupportReportPanel } from './SupportReportPanel'

type Horizon = 'short' | 'medium' | 'swing'
type ResearchObject = 'pair' | 'fixed_basket'

type Variant = ResearchRecipeDraftV1['variants'][number]

type ComponentKind = CapabilityMetadataV1['kind']

interface ExperimentLabProps {
  apiClient: QapApiClient
  queries: QapQueries
  workspace: WorkspaceStatusDto
}

function humanize(value: string): string {
  return value.replaceAll('_', ' ')
}

function runIds(operation: OperationDto | undefined): string[] {
  const value = operation?.result?.run_ids
  return Array.isArray(value)
    ? value.filter((item): item is string => typeof item === 'string')
    : []
}

function componentOptions(
  catalog: CapabilityMetadataV1[],
  kind: ComponentKind,
  researchObject: ResearchObject,
) {
  return catalog.filter(
    (item) =>
      item.kind === kind && item.allowed_research_objects.includes(researchObject),
  )
}

function updateVariant(
  draft: ResearchRecipeDraftV1,
  index: number,
  next: Variant,
): ResearchRecipeDraftV1 {
  return {
    ...draft,
    variants: draft.variants.map((variant, position) =>
      position === index ? next : variant,
    ),
  }
}

export function ExperimentLab({ apiClient, queries, workspace }: ExperimentLabProps) {
  const queryClient = useQueryClient()
  const [researchObject, setResearchObject] = useState<ResearchObject>('pair')
  const [assets, setAssets] = useState<ResearchAssetSelection[]>([])
  const [horizon, setHorizon] = useState<Horizon>('short')
  const [draft, setDraft] = useState<ResearchRecipeDraftV1 | null>(null)
  const currentDraft = useRef(draft)
  useLayoutEffect(() => { currentDraft.current = draft }, [draft])
  const [checked, setChecked] = useState<ResearchRecipeCheckV1 | null>(null)
  const [operationId, setOperationId] = useState<string | null>(null)

  const universe = useQuery(queries.researchUniverse())
  const canonicalAssets = assets
    .map((asset) => asset.canonicalAssetId)
    .filter((asset): asset is string => asset !== null)
  const selectionComplete =
    canonicalAssets.length === assets.length &&
    (researchObject === 'pair' ? canonicalAssets.length === 2 : canonicalAssets.length >= 2)
  const context = useQuery({
    ...queries.researchRecipeProductContext({
      researchObject,
      horizon,
      assets: selectionComplete ? canonicalAssets : undefined,
    }),
    enabled: workspace.workspace_mode === 'local_market',
  })
  const operation = useQuery({
    ...queries.operation(operationId ?? ''),
    enabled: operationId !== null,
  })

  useEffect(() => {
    setDraft(context.data?.default_draft ?? null)
    setChecked(null)
    setOperationId(null)
  }, [context.data?.default_draft])

  const capabilities = context.data?.capabilities ?? []
  const relationshipOptions = useMemo(
    () => componentOptions(capabilities, 'relationship', researchObject),
    [capabilities, researchObject],
  )
  const decisionOptions = useMemo(
    () => componentOptions(capabilities, 'decision_rule', researchObject),
    [capabilities, researchObject],
  )
  const allocationOptions = useMemo(
    () => componentOptions(capabilities, 'allocation', researchObject),
    [capabilities, researchObject],
  )
  const selectionOptions = useMemo(
    () => componentOptions(capabilities, 'selection', researchObject),
    [capabilities, researchObject],
  )

  const launch = useMutation({
    mutationFn: async () => {
      if (!draft) throw new Error('Choose assets and settings before running the experiment.')
      const submittedDraft = draft
      const next = await apiClient.checkResearchRecipeSupport({
        schema_version: 'qap.api.research-recipe-check-request.v1',
        recipe: submittedDraft,
      })
      if (currentDraft.current !== submittedDraft) {
        throw new Error('Settings changed while support was checked. Review the current draft and run again.')
      }
      setChecked(next)
      if (!next.support.runnable || !next.recipe) return null
      return apiClient.runResearchRecipe({
        schema_version: 'qap.api.research-recipe-run-request.v1',
        recipe: next.recipe,
      })
    },
    onSuccess: (ref) => {
      if (ref) setOperationId(ref.operation_id)
    },
  })
  const prepare = useMutation({
    mutationFn: () => apiClient.prepareProductMarketData({ horizons: [horizon] }),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['product-market-data'] }),
        queryClient.invalidateQueries({ queryKey: ['current-approved-readiness', horizon] }),
        queryClient.invalidateQueries({ queryKey: ['research-recipe-product-context'] }),
      ])
    },
  })

  if (workspace.workspace_mode === 'sample') {
    return (
      <section className="rounded-lg border border-warning/45 bg-panel p-5">
        <Badge tone="warning">Sample Workspace</Badge>
        <h2 className="mt-3 mb-2 text-xl font-semibold text-foreground">Experiment Lab</h2>
        <p className="m-0 text-sm text-secondary">
          Recipe authoring requires the Local Market workspace so exact current data
          bindings can be frozen before support checking.
        </p>
      </section>
    )
  }

  const exactRunIds = runIds(operation.data)

  return (
    <section className="mt-8 rounded-lg border border-border bg-panel p-5 md:p-6" aria-labelledby="experiment-lab-heading">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="m-0 text-xs font-semibold uppercase tracking-[0.08em] text-muted">
            Advanced research
          </p>
          <h2 id="experiment-lab-heading" className="mt-2 mb-2 text-xl font-semibold text-foreground">
            Experiment Lab
          </h2>
          <p className="m-0 max-w-4xl text-sm leading-6 text-secondary">
            Choose a method and adjust its settings, then check whether the experiment
            can run. Each attempt uses a declared comparison and records its assumptions.
          </p>
        </div>
      </div>

      <fieldset disabled={launch.isPending} className="m-0 min-w-0 border-0 p-0 disabled:opacity-70">
      <div className="mt-5 grid gap-4 md:grid-cols-2">
        <label className="text-sm font-semibold text-secondary">
          Research object
          <select
            className="mt-2 min-h-11 w-full rounded-md border border-border bg-canvas px-3 text-foreground"
            value={researchObject}
            onChange={(event) => {
              setResearchObject(event.target.value as ResearchObject)
              setAssets([])
              setDraft(null)
              setChecked(null)
            }}
          >
            <option value="pair">Pair</option>
            <option value="fixed_basket">Fixed basket</option>
          </select>
        </label>
        <label className="text-sm font-semibold text-secondary">
          Product timeframe
          <select
            className="mt-2 min-h-11 w-full rounded-md border border-border bg-canvas px-3 text-foreground"
            value={horizon}
            onChange={(event) => {
              setHorizon(event.target.value as Horizon)
              setChecked(null)
            }}
          >
            <option value="short">Short-term</option>
            <option value="medium">Medium-term</option>
            <option value="swing">Longer-term</option>
          </select>
        </label>
      </div>

      {universe.data ? (
        <div className="mt-5">
          <div className="flex flex-wrap gap-2">
            {assets.map((asset, index) => (
              <button
                key={asset.key}
                type="button"
                className="min-h-10 rounded-md border border-border px-3 text-sm font-semibold text-foreground"
                onClick={() => {
                  setAssets((current) => current.filter((_, position) => position !== index))
                  setChecked(null)
                }}
              >
                {asset.symbol} ×
              </button>
            ))}
          </div>
          {(researchObject === 'pair' ? assets.length < 2 : assets.length < 6) ? (
            <div className="mt-3 max-w-2xl">
              <ResearchAssetSelector
                label={assets.length ? 'Add another asset' : 'Choose research assets'}
                universe={universe.data}
                selected={null}
                excludeCanonicalAssetIds={canonicalAssets}
                onSelect={(selection) => {
                  setAssets((current) => [...current, selection])
                  setChecked(null)
                }}
                onClear={() => undefined}
              />
            </div>
          ) : null}
          {assets.some((asset) => !asset.canonicalAssetId) ? (
            <p className="mt-3 rounded-md border border-warning/40 bg-subtle p-3 text-sm text-secondary">
              Resolve unresolved venue identities in Research Universe before an exact
              Experiment Lab recipe can be frozen.
            </p>
          ) : null}
        </div>
      ) : null}

      {selectionComplete && context.data?.default_issue ? (
        <div className="mt-5 rounded-md border border-warning/40 bg-subtle p-4">
          <p className="m-0 text-sm font-semibold text-foreground">
            {context.data.default_issue.detail}
          </p>
          {context.data.default_issue.code === 'requires_market_data' ? (
            <button
              type="button"
              className="mt-3 min-h-11 rounded-md bg-accent px-4 font-semibold text-canvas disabled:opacity-50"
              disabled={prepare.isPending}
              onClick={() => prepare.mutate()}
            >
              {prepare.isPending ? 'Preparing…' : 'Prepare Product data'}
            </button>
          ) : (
            <a className="mt-3 inline-flex min-h-11 items-center font-semibold text-accent" href="/universe">
              Resolve asset setup
            </a>
          )}
        </div>
      ) : null}

      {draft ? (
        <div className="mt-6 space-y-5">
          <section className="rounded-lg border border-border bg-subtle p-5">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h3 className="m-0 text-lg font-semibold text-foreground">Declared variants</h3>
                <p className="mt-1 mb-0 text-sm text-secondary">
                  Component IDs come from the backend capability catalog. Exact config JSON
                  is still validated by M10-A and the canonical experiment owners.
                </p>
              </div>
              <button
                type="button"
                className="min-h-10 rounded-md border border-border px-3 text-sm font-semibold text-foreground"
                onClick={() => {
                  const source = draft.variants[0]
                  if (!source) return
                  setDraft({
                    ...draft,
                    variants: [
                      ...draft.variants,
                      { ...source, variant_id: `variant-${draft.variants.length + 1}` },
                    ],
                    selection: { ...draft.selection, kind: 'precommitted_variants', selected_variant_id: null },
                  })
                  setChecked(null)
                }}
              >
                Add declared variant
              </button>
            </div>

            <div className="mt-5 space-y-5">
              {draft.variants.map((variant, index) => (
                <article key={`${variant.variant_id}-${index}`} className="rounded-md border border-border bg-panel p-4">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <label className="text-xs font-semibold text-secondary">
                      Variant ID
                      <input
                        className="mt-1 min-h-10 rounded-md border border-border bg-canvas px-3 text-sm text-foreground"
                        value={variant.variant_id}
                        onChange={(event) => {
                          const variantId = event.target.value
                          const next = updateVariant(draft, index, {
                            ...variant,
                            variant_id: variantId,
                          })
                          setDraft({
                            ...next,
                            selection: {
                              ...next.selection,
                              selected_variant_id:
                                next.selection.selected_variant_id === variant.variant_id
                                  ? variantId
                                  : next.selection.selected_variant_id,
                            },
                          })
                          setChecked(null)
                        }}
                      />
                    </label>
                    {draft.variants.length > 1 ? (
                      <button
                        type="button"
                        className="min-h-10 rounded-md border border-border px-3 text-xs font-semibold text-secondary"
                        onClick={() => {
                          const variants = draft.variants.filter((_, position) => position !== index)
                          setDraft({
                            ...draft,
                            variants,
                            selection: {
                              ...draft.selection,
                              selected_variant_id:
                                draft.selection.selected_variant_id === variant.variant_id
                                  ? null
                                  : draft.selection.selected_variant_id,
                            },
                          })
                          setChecked(null)
                        }}
                      >
                        Remove variant
                      </button>
                    ) : null}
                  </div>

                  <ResearchParameterControls config={variant.relationship.config} onChange={(config) => {
                    setDraft(updateVariant(draft, index, { ...variant, relationship: { ...variant.relationship, config: config as Variant['relationship']['config'] } }))
                    setChecked(null)
                  }} />
                  <ResearchParameterControls config={variant.decision_rule.config} onChange={(config) => {
                    setDraft(updateVariant(draft, index, { ...variant, decision_rule: { ...variant.decision_rule, config: config as Variant['decision_rule']['config'] } }))
                    setChecked(null)
                  }} />
                  <div className="mt-4 grid gap-3 md:grid-cols-3">
                    <ComponentSelect
                      label="Relationship / evidence"
                      value={variant.relationship.component_id}
                      options={relationshipOptions}
                      onChange={(componentId) => {
                        setDraft(
                          updateVariant(draft, index, {
                            ...variant,
                            relationship: { ...variant.relationship, component_id: componentId },
                          }),
                        )
                        setChecked(null)
                      }}
                    />
                    <ComponentSelect
                      label="Decision rule"
                      value={variant.decision_rule.component_id}
                      options={decisionOptions}
                      onChange={(componentId) => {
                        setDraft(
                          updateVariant(draft, index, {
                            ...variant,
                            decision_rule: { ...variant.decision_rule, component_id: componentId },
                          }),
                        )
                        setChecked(null)
                      }}
                    />
                    <ComponentSelect
                      label="Allocation"
                      value={variant.allocation.component_id}
                      options={allocationOptions}
                      onChange={(componentId) => {
                        setDraft(
                          updateVariant(draft, index, {
                            ...variant,
                            allocation: { ...variant.allocation, component_id: componentId },
                          }),
                        )
                        setChecked(null)
                      }}
                    />
                  </div>

                  <details className="mt-4 rounded-md border border-border p-3">
                    <summary className="cursor-pointer text-sm font-semibold text-accent">
                      Exact variant parameters
                    </summary>
                    <div className="mt-4 grid gap-4 lg:grid-cols-2">
                      <JsonConfigEditor
                        label="Relationship config"
                        value={variant.relationship.config}
                        onApply={(config) => {
                          setDraft(
                            updateVariant(draft, index, {
                              ...variant,
                              relationship: { ...variant.relationship, config },
                            }),
                          )
                          setChecked(null)
                        }}
                      />
                      <JsonConfigEditor
                        label="Decision-rule config"
                        value={variant.decision_rule.config}
                        onApply={(config) => {
                          setDraft(
                            updateVariant(draft, index, {
                              ...variant,
                              decision_rule: { ...variant.decision_rule, config },
                            }),
                          )
                          setChecked(null)
                        }}
                      />
                    </div>
                  </details>
                </article>
              ))}
            </div>
          </section>

          <section className="rounded-lg border border-border bg-panel p-5">
            <h3 className="m-0 text-lg font-semibold text-foreground">Evaluation declaration</h3>
            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <label className="text-sm font-semibold text-secondary">
                Data role
                <select
                  className="mt-2 min-h-11 w-full rounded-md border border-border bg-canvas px-3 text-foreground"
                  value={draft.data.data_role}
                  onChange={(event) => {
                    setDraft({
                      ...draft,
                      data: {
                        ...draft.data,
                        data_role: event.target.value as ResearchRecipeDraftV1['data']['data_role'],
                      },
                    })
                    setChecked(null)
                  }}
                >
                  <option value="exploratory">Exploratory</option>
                  <option value="development">Development</option>
                  <option value="final_oos">Final OOS</option>
                </select>
              </label>
              <label className="text-sm font-semibold text-secondary">
                Fidelity intent
                <select
                  className="mt-2 min-h-11 w-full rounded-md border border-border bg-canvas px-3 text-foreground"
                  value={draft.fidelity_intent}
                  onChange={(event) => {
                    setDraft({
                      ...draft,
                      fidelity_intent: event.target.value as ResearchRecipeDraftV1['fidelity_intent'],
                      derived_from_recipe_sha256:
                        event.target.value === 'adaptation'
                          ? draft.derived_from_recipe_sha256
                          : null,
                    })
                    setChecked(null)
                  }}
                >
                  <option value="native_qap">Native QAP</option>
                  <option value="faithful_replication">Faithful external replication</option>
                  <option value="adaptation">Explicit adaptation</option>
                </select>
              </label>
            </div>

            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <label className="text-sm font-semibold text-secondary">
                Selection protocol
                <select
                  className="mt-2 min-h-11 w-full rounded-md border border-border bg-canvas px-3 text-foreground"
                  value={draft.selection.kind}
                  onChange={(event) => {
                    const kind = event.target.value
                    setDraft({
                      ...draft,
                      selection: {
                        kind,
                        selected_variant_id:
                          kind === 'fixed' && draft.variants.length === 1
                            ? draft.variants[0]?.variant_id ?? null
                            : null,
                      },
                    })
                    setChecked(null)
                  }}
                >
                  {selectionOptions.map((item) => (
                    <option key={item.component_id} value={item.component_id}>
                      {humanize(item.component_id)} · {humanize(item.capability)}
                    </option>
                  ))}
                </select>
              </label>
              <label className="text-sm font-semibold text-secondary">
                Selected variant
                <select
                  className="mt-2 min-h-11 w-full rounded-md border border-border bg-canvas px-3 text-foreground"
                  value={draft.selection.selected_variant_id ?? ''}
                  onChange={(event) => {
                    setDraft({
                      ...draft,
                      selection: {
                        ...draft.selection,
                        selected_variant_id: event.target.value || null,
                      },
                    })
                    setChecked(null)
                  }}
                >
                  <option value="">No single variant selected</option>
                  {draft.variants.map((variant) => (
                    <option key={variant.variant_id} value={variant.variant_id}>
                      {variant.variant_id}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            {draft.data.data_role === 'final_oos' ? (
              <div className="mt-4 grid gap-4 md:grid-cols-2">
                <label className="block text-sm font-semibold text-secondary">
                  Frozen prior compilation SHA-256
                  <input
                    className="mt-2 min-h-11 w-full rounded-md border border-border bg-canvas px-3 font-mono text-xs text-foreground"
                    value={draft.selected_from_compilation_sha256 ?? ''}
                    onChange={(event) => {
                      setDraft({
                        ...draft,
                        selected_from_compilation_sha256: event.target.value || null,
                      })
                      setChecked(null)
                    }}
                    placeholder="Required for final OOS selection lineage"
                  />
                </label>
                <label className="block text-sm font-semibold text-secondary">
                  Frozen research family ID
                  <input
                    className="mt-2 min-h-11 w-full rounded-md border border-border bg-canvas px-3 font-mono text-xs text-foreground"
                    value={draft.research_family_id}
                    onChange={(event) => {
                      setDraft({ ...draft, research_family_id: event.target.value })
                      setChecked(null)
                    }}
                    placeholder="Must match the referenced development family"
                  />
                </label>
              </div>
            ) : null}

            {draft.fidelity_intent === 'adaptation' ? (
              <label className="mt-4 block text-sm font-semibold text-secondary">
                Source recipe SHA-256
                <input
                  className="mt-2 min-h-11 w-full rounded-md border border-border bg-canvas px-3 font-mono text-xs text-foreground"
                  value={draft.derived_from_recipe_sha256 ?? ''}
                  onChange={(event) => {
                    setDraft({ ...draft, derived_from_recipe_sha256: event.target.value || null })
                    setChecked(null)
                  }}
                  placeholder="Required for an explicit scientific adaptation"
                />
              </label>
            ) : null}
          </section>

          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              className="min-h-11 rounded-md bg-accent px-5 font-semibold text-canvas disabled:opacity-50"
              disabled={launch.isPending || operation.data?.status === 'running'}
              onClick={() => launch.mutate()}
            >
              {launch.isPending ? 'Checking and starting…' : 'Run experiment'}
            </button>
            <details className="rounded-md border border-border px-4 py-2 text-sm">
              <summary className="cursor-pointer font-semibold text-accent">Exact structured draft</summary>
              <pre className="mt-3 max-h-96 max-w-full overflow-auto text-xs text-muted">
                {JSON.stringify(draft, null, 2)}
              </pre>
            </details>
          </div>
          {launch.isError ? <p className="text-sm text-negative">{launch.error.message}</p> : null}
        </div>
      ) : selectionComplete && context.isPending ? (
        <p className="mt-5 text-sm text-secondary">Freezing an exact backend-owned starting recipe…</p>
      ) : null}
      </fieldset>

      {checked ? (
        <details className="mt-6 rounded-md border border-border p-4" open={!checked.support.runnable}>
          <summary className="min-h-11 cursor-pointer py-2 text-sm font-semibold text-accent">
            {checked.support.runnable ? 'Support details' : 'Why this experiment cannot run'}
          </summary>
          <SupportReportPanel report={checked.support} />
        </details>
      ) : null}

      {operationId ? (
        <section className="mt-6 rounded-md border border-border bg-subtle p-4">
          <div className="flex flex-wrap gap-2">
            <Badge tone={operation.data?.status === 'failed' ? 'negative' : operation.data?.status === 'running' ? 'info' : 'neutral'}>
              {operation.data?.status ?? 'starting'}
            </Badge>
          </div>
          <a className="mt-3 inline-flex min-h-11 items-center font-semibold text-accent" href={`/operations/${operationId}`}>
            View operation in Activity
          </a>
          {exactRunIds.length ? (
            <div className="mt-4 flex flex-wrap gap-3 border-t border-border pt-4">
              {exactRunIds.map((runId, index) => (
                <a key={runId} className="font-semibold text-accent" href={`/experiments/${runId}`}>
                  Exact result {index + 1}
                </a>
              ))}
            </div>
          ) : null}
        </section>
      ) : null}
    </section>
  )
}
