import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useState } from 'react'

import type { QapApiClient } from '../../api/client'
import type { QapQueries } from '../../api/queries'
import type {
  CapabilityMetadataV1, ProductPairStudyContextDto, ProductPairStudySeriesDto,
  ResearchRecipeCheckV1, ResearchRecipeDraftV1, WorkspaceStatusDto,
} from '../../api/types'
import { PairResearchCompletion } from './PairResearchCompletion'
import { PairResearchSetup } from './PairResearchSetup'
import { PairStudyResults } from './PairStudyResults'
import { PairRelationshipSummary } from './PairRelationshipSummary'
import { PairExperimentPreview } from './PairExperimentPreview'
import { pairRecipeMatchesContext, pairStudySeriesMatchesContext } from './pairStudyBinding'
import { SupportReportPanel } from './SupportReportPanel'
import { researchAssetOptions, type ResearchAssetSelection } from './researchAssetSearch'
import { applyStudyParameters, studyQuestion, type ResearchStudy } from './researchStudies'

interface PairStudyResult {
  context: ProductPairStudyContextDto
  series: ProductPairStudySeriesDto | null
  capabilities: CapabilityMetadataV1[]
}
interface StudyOptions { venue?: 'binance' | 'gate'; analysisReference?: string; runBacktest?: boolean }
type Intent = Partial<Omit<ResearchStudy, 'id' | 'attempts'>>

export function PairResearch({ apiClient, queries, workspace, study, onChange, onAttempt, onBusyChange }: {
  apiClient: QapApiClient; queries: QapQueries; workspace: WorkspaceStatusDto
  study: ResearchStudy; onChange: (patch: Intent) => void
  onAttempt: (operationId: string, question: string) => void; onBusyChange: (busy: boolean) => void
}) {
  const client = useQueryClient()
  const [studyResult, setStudyResult] = useState<PairStudyResult | null>(null)
  const [draft, setDraft] = useState<ResearchRecipeDraftV1 | null>(null)
  const [checked, setChecked] = useState<ResearchRecipeCheckV1 | null>(null)
  const [supportError, setSupportError] = useState<string | null>(null)
  const [chartError, setChartError] = useState<string | null>(null)
  const [progress, setProgress] = useState('')
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [setupBusy, setSetupBusy] = useState(false)
  const [operationId, setOperationId] = useState<string | null>(
    study.mode === 'backtest_comparison' ? study.attempts.at(-1)?.operationId ?? null : null,
  )
  const universe = useQuery(queries.researchUniverse())
  const options = universe.data ? researchAssetOptions(universe.data) : []
  const currentSelection = (saved: ResearchAssetSelection | null) => saved
    ? options.find((option) => option.key === saved.key)
      ?? { ...saved, approved: false, identityState: 'review_required' as const }
    : null
  const assetA = currentSelection(study.assetA)
  const assetB = currentSelection(study.assetB)
  const readyToStudy = !!(assetA?.approved && assetB?.approved
    && assetA.identityState === 'resolved' && assetB.identityState === 'resolved'
    && assetA.canonicalAssetId && assetB.canonicalAssetId
    && assetA.canonicalAssetId !== assetB.canonicalAssetId)
  const operation = useQuery({ ...queries.operation(operationId ?? ''), enabled: operationId !== null })
  const restoredRecipe = useQuery({
    ...queries.researchRecipeProductContext({ researchObject: 'pair', horizon: study.horizon,
      assets: readyToStudy ? [assetA!.canonicalAssetId!, assetB!.canonicalAssetId!] : undefined,
      orientation: readyToStudy ? `${assetA!.canonicalAssetId}/${assetB!.canonicalAssetId}` : undefined }),
    enabled: operationId !== null && readyToStudy && study.mode === 'backtest_comparison',
  })
  const visibleDraft = draft ?? (restoredRecipe.data?.default_draft
    ? applyStudyParameters(restoredRecipe.data.default_draft, study.parameters ?? {}) : null)
  const result = operation.data?.result
  const runIds = Array.isArray(result?.run_ids)
    ? result.run_ids.filter((value): value is string => typeof value === 'string') : []
  const compilation = typeof result?.compilation_sha256 === 'string' ? result.compilation_sha256 : null

  const comparison = useMutation({
    mutationFn: async ({ runBacktest, ...settings }: StudyOptions = {}) => {
      if (!readyToStudy || !assetA?.canonicalAssetId || !assetB?.canonicalAssetId) {
        throw new Error('Confirm and allow both selected assets first.')
      }
      setChecked(null)
      setDraft(null)
      setSupportError(null)
      setChartError(null)
      setStudyResult(null)
      setOperationId(null)
      const pairOptions = {
        assetA: assetA.canonicalAssetId,
        assetB: assetB.canonicalAssetId,
        horizon: study.horizon,
        orientation: `${assetA.canonicalAssetId}/${assetB.canonicalAssetId}`,
        ...settings,
      }

      setProgress('Checking price history…')
      let context = await apiClient.getProductPairStudyContext(pairOptions)
      if (context.data.status === 'needs_setup'
        || (settings.analysisReference && context.analysis_lens?.status === 'needs_data')) {
        setProgress('Preparing the selected price history…')
        await apiClient.prepareProductMarketData({
          horizons: [study.horizon],
          asset_ids: [pairOptions.assetA, pairOptions.assetB],
          analysis_reference_ids: settings.analysisReference ? [settings.analysisReference] : [],
        })
        await client.invalidateQueries({ queryKey: ['product-market-data'] })
        context = await apiClient.getProductPairStudyContext(pairOptions)
      }

      setStudyResult({ context, series: null, capabilities: [] })
      setProgress('Measuring the relationship…')
      let series: ProductPairStudySeriesDto | null = null
      if (context.data.status === 'ready') {
        try {
          const loaded = await apiClient.getProductPairStudySeries({
            ...pairOptions,
            venue: context.question.venue,
            analysisReference: context.analysis_lens?.status === 'ready'
              ? settings.analysisReference
              : undefined,
          })
          if (pairStudySeriesMatchesContext(context, loaded)) series = loaded
          else setChartError('The chart came from a different data snapshot. The relationship summary is retained; retry the chart.')
        } catch (error) {
          setChartError(error instanceof Error ? error.message : 'The relationship chart could not be loaded.')
        }
      }
      setStudyResult({ context, series, capabilities: [] })
      if (context.data.status !== 'ready') return null
      if (!runBacktest && study.mode === 'relationship') return null

      if (context.economic_expression.direct_status !== 'ready'
        && context.economic_expression.bridge_status === 'needs_transient_authority') {
        return null
      }

      setProgress('Checking the declared settings…')
      try {
        const recipe = await apiClient.getResearchRecipeProductContext({
          researchObject: 'pair',
          horizon: study.horizon,
          assets: [pairOptions.assetA, pairOptions.assetB],
          orientation: context.question.orientation,
          venue: context.question.venue,
        })
        setStudyResult({ context, series, capabilities: recipe.capabilities })
        const declared = recipe.default_draft
          ? applyStudyParameters(recipe.default_draft, study.parameters ?? {})
          : null
        if (recipe.default_issue) {
          setSupportError(recipe.default_issue.detail)
          return null
        }
        if (!context.economic_expression.default_recipe_declarable || !declared) {
          setSupportError('An economic comparison is not available for this pair yet.')
          return null
        }
        if (!pairRecipeMatchesContext(context, declared)) {
          setSupportError('Comparison data changed while preparing this study. The relationship view is retained; retry to bind a fresh comparison.')
          return null
        }
        setDraft(declared)

        const next = await apiClient.checkResearchRecipeSupport({
          schema_version: 'qap.api.research-recipe-check-request.v1',
          recipe: declared,
        })
        setChecked(next)
        if (!next.support.runnable || !next.recipe) return null

        setProgress('Starting the comparison…')
        const question = studyQuestion({ ...study, mode: 'backtest_comparison' })
        const ref = await apiClient.runResearchRecipe({
          schema_version: 'qap.api.research-recipe-run-request.v1',
          recipe: next.recipe,
        })
        return { ref, question }
      } catch (error) {
        setSupportError(
          error instanceof Error ? error.message : 'The comparison settings could not be checked.',
        )
        return null
      }
    },
    onSuccess: (launched) => {
      if (!launched) return
      onAttempt(launched.ref.operation_id, launched.question)
      setOperationId(launched.ref.operation_id)
      void client.invalidateQueries({ queryKey: ['operations'] })
    },
    onSettled: () => setProgress(''),
  })
  const chartRetry = useMutation({
    mutationFn: async () => {
      const context = studyResult?.context
      if (!context) return
      const loaded = await apiClient.getProductPairStudySeries({
        assetA: context.question.asset_a, assetB: context.question.asset_b,
        horizon: context.question.horizon, orientation: context.question.orientation,
        venue: context.question.venue,
        analysisReference: study.useBtcReference && canUseReference ? 'BTC' : undefined,
      })
      if (!pairStudySeriesMatchesContext(context, loaded)) throw new Error('The chart still belongs to a different data snapshot. Try the study again later.')
      setStudyResult((current) => current ? { ...current, series: loaded } : current)
      setChartError(null)
    },
    onError: (error) => setChartError(error.message),
  })
  const bridge = useMutation({
    mutationFn: () => apiClient.grantProductPairStudyTransientUsdtAuthority(),
    onSuccess: () => comparison.mutate({
      venue: studyResult?.context.question.venue,
      analysisReference: study.useBtcReference && canUseReference ? 'BTC' : undefined,
      runBacktest: true,
    }),
  })
  const busy = setupBusy || comparison.isPending || bridge.isPending
    || (operationId !== null && (operation.isPending || operation.data?.status === 'running'))
  useEffect(() => { onBusyChange(busy) }, [busy, onBusyChange])
  useEffect(() => () => onBusyChange(false), [onBusyChange])

  const change = (patch: Intent) => {
    setStudyResult(null)
    setDraft(null)
    setChecked(null)
    setSupportError(null)
    setChartError(null)
    setOperationId(null)
    comparison.reset()
    onChange(patch)
  }
  const referenceAvailable = universe.data?.assets.some((asset) => asset.canonical_asset_id === 'BTC' && asset.identity_state === 'resolved')
  const canUseReference = referenceAvailable && assetA?.canonicalAssetId !== 'BTC' && assetB?.canonicalAssetId !== 'BTC'
  const comparisonOptions = {
    venue: studyResult?.context.question.venue,
    analysisReference: study.useBtcReference && canUseReference ? 'BTC' : undefined,
  }

  if (workspace.workspace_mode === 'sample') return <p className="rounded-lg border border-warning/45 p-5 text-secondary">This sample workspace contains read-only examples. Use Local Market to start your own study.</p>

  return (
    <section className="min-w-0 space-y-6" aria-label="Pair research study">
      <div className="grid min-w-0 items-start gap-5 lg:grid-cols-[minmax(19rem,0.36fr)_minmax(0,0.64fr)]">
      <div className="min-w-0 rounded-lg border border-border bg-panel p-5 md:p-6">
        {universe.data ? <PairResearchSetup apiClient={apiClient} universe={universe.data}
          study={study} assetA={assetA} assetB={assetB} busy={busy} onChange={change} onBusyChange={setSetupBusy} />
          : <p role="status" className="text-secondary">{universe.isPending ? 'Loading available assets…' : universe.error?.message}</p>}
        {readyToStudy ? (
          <div className="mt-5 border-t border-border pt-5">
            <details className="mb-3 text-sm text-secondary">
              <summary className="cursor-pointer py-2">Additional relationship views</summary>
              <label className="flex min-h-11 items-center gap-3">
                <input type="checkbox" checked={study.useBtcReference} disabled={busy || !canUseReference}
                  onChange={(event) => change({ useBtcReference: event.target.checked })} /> Compare both assets with BTC
              </label>
              {!canUseReference ? <p className="text-xs text-muted">Requires a separately identified BTC reference distinct from the selected pair.</p> : null}
              <button type="button" disabled={busy} className="min-h-11 text-accent" onClick={() => change({ assetA: study.assetB, assetB: study.assetA })}>Reverse pair orientation</button>
            </details>
            <div className="flex flex-wrap items-center gap-3">
              <button type="button" disabled={busy} onClick={() => comparison.mutate(comparisonOptions)}
                className="min-h-12 rounded-md bg-accent px-6 font-semibold text-canvas disabled:opacity-50">
                {comparison.isPending ? 'Starting research…' : 'Start research'}
              </button>
              <span className="text-xs text-muted">{study.mode === 'relationship' ? 'Historical relationship only · no backtest' : 'Two methods · holding and simple rebalancing controls · modeled costs'}</span>
            </div>
            {progress ? <p role="status" className="mt-3 text-sm text-accent">{progress} Your comparison stays saved.</p> : null}
            {comparison.isError ? <p role="alert" className="mt-3 text-sm text-negative">{comparison.error.message} Your comparison is retained; resolve the setup above and retry.</p> : null}
          </div>
        ) : null}
      </div>
      <div className="min-w-0 space-y-5" aria-label="Research canvas">
      {!studyResult && !operationId && !comparison.isPending ? <div className="rounded-lg border border-border bg-panel p-6">
        <h2 className="m-0 text-lg font-semibold text-foreground">Your research canvas</h2>
        <p className="mb-0 mt-2 text-sm leading-6 text-secondary">Choose two assets and start research. The relationship view and any backtest result will appear here.</p>
      </div> : null}

      {studyResult && (study.mode === 'relationship' || !operationId) ? <>
        <PairRelationshipSummary context={studyResult.context} series={studyResult.series} />
        {chartError ? <p role="alert" className="rounded-md border border-warning/45 p-4 text-sm text-warning">Chart unavailable: {chartError} <button type="button" disabled={chartRetry.isPending} className="min-h-11 font-semibold text-accent" onClick={() => chartRetry.mutate()}>Retry chart</button></p> : null}
        {study.mode === 'backtest_comparison'
          && studyResult.context.economic_expression.direct_status !== 'ready'
          && studyResult.context.economic_expression.bridge_status === 'needs_transient_authority' ? <section className="rounded-lg border border-warning/45 bg-panel p-5">
            <h2 className="m-0 text-lg font-semibold text-foreground">Allow research-only bridge holdings?</h2>
            <p className="mt-2 text-sm leading-6 text-secondary">This permission applies to the current Local Market workspace and verified USDT identity, not just this study. It allows temporary owned USDT residue during two-leg spot replay. It does not approve USDT as a portfolio target or place live orders.</p>
            <button type="button" disabled={busy} onClick={() => bridge.mutate()}
              className="min-h-11 rounded-md bg-accent px-4 font-semibold text-canvas disabled:opacity-50">{bridge.isPending ? 'Saving permission…' : 'Allow workspace bridge replay and continue'}</button>
            {bridge.isError ? <p role="alert" className="text-sm text-negative">{bridge.error.message}</p> : null}
          </section> : null}
        {study.mode === 'relationship' && studyResult.context.data.status === 'ready' ? <button type="button" disabled={busy}
          className="min-h-12 rounded-md bg-accent px-5 font-semibold text-canvas disabled:opacity-50"
          onClick={() => { onChange({ mode: 'backtest_comparison' }); comparison.mutate({ ...comparisonOptions, runBacktest: true }) }}>Backtest this pair</button> : null}
      </> : null}
      {studyResult ? <details className="rounded-lg border border-border bg-panel p-5">
        <summary className="cursor-pointer py-2 text-sm font-semibold text-accent">Evidence, data sources, and technical detail</summary>
        <PairStudyResults context={studyResult.context} series={studyResult.series} capabilities={studyResult.capabilities}
          backtestMode={study.mode === 'backtest_comparison'}
          busy={busy} bridgeAuthorityBusy={bridge.isPending} bridgeAuthorityError={bridge.isError ? bridge.error.message : null}
          onGrantBridgeAuthority={() => bridge.mutate()} onVenueChange={(venue) => comparison.mutate({ ...comparisonOptions, venue })} />
      </details> : null}
      {visibleDraft && study.mode === 'backtest_comparison' && !operationId ? <PairExperimentPreview recipe={visibleDraft} busy={busy}
        descriptiveWindowBars={studyResult?.context.relationship?.rolling_log_ratio.window_observations}
        descriptiveMinimumObservations={studyResult?.context.relationship?.rolling_log_ratio.required_observations}
        open={settingsOpen} onToggle={setSettingsOpen} onParameters={(parameters) => {
        setDraft(applyStudyParameters(visibleDraft, parameters))
        setChecked(null)
        onChange({ parameters })
      }} /> : null}
      {supportError ? <div role="alert" className="rounded-md border border-warning/45 p-4 text-sm text-warning">
        <p className="mt-0">The relationship study is available. The comparison needs attention: {supportError}</p>
        <button type="button" disabled={busy} className="min-h-11 font-semibold text-accent" onClick={() => comparison.mutate(comparisonOptions)}>Retry comparison</button>
      </div> : null}
      {checked && !checked.support.runnable ? <section className="rounded-lg border border-warning/45 bg-panel p-5">
        <p className="mt-0 font-semibold text-foreground">These settings cannot run yet</p>
        <div className="text-sm text-secondary">
          {checked.support.reasons.map((reason, i) => <p key={i}>{reason.detail}</p>)}
          {checked.support.suggestions.length ? <ul className="space-y-2 pl-5">{checked.support.suggestions.map((suggestion) => <li key={suggestion}>{suggestion}</li>)}</ul> : null}
        </div>
        <details className="mt-4"><summary className="cursor-pointer py-2 text-sm text-accent">Technical support details</summary><SupportReportPanel report={checked.support} /></details>
      </section> : null}

      {study.attempts.length > 0 ? <details className="rounded-lg border border-border bg-panel px-5 py-3">
        <summary className="min-h-11 cursor-pointer py-2 text-sm font-semibold text-accent">
          Earlier runs · {study.attempts.length}
        </summary>
        <p className="text-sm text-secondary">Reopen a recorded run without changing the current draft.</p>
        <div className="flex flex-wrap gap-2">{study.attempts.map((attempt, i) => <button key={attempt.operationId} type="button"
          disabled={busy} aria-pressed={operationId === attempt.operationId} onClick={() => setOperationId(attempt.operationId)}
          className={`min-h-11 rounded-md border px-4 py-2 text-left text-sm ${operationId === attempt.operationId ? 'border-accent text-accent' : 'border-border text-secondary'}`}>
          <span className="block font-semibold">Run {i + 1} · {attempt.question}</span>
          <span className="text-xs">{new Date(attempt.createdAt).toLocaleString()}</span>
        </button>)}</div>
      </details> : null}
      {operationId ? <section aria-live="polite" className="rounded-lg border border-border bg-panel p-5">
        <h2 className="m-0 text-lg font-semibold text-foreground">{operation.isError ? 'Could not load this attempt' : operation.isPending ? 'Loading your attempt…' : operation.data.status === 'running' ? 'Backtest in progress' : operation.data.status === 'completed' ? 'Backtest complete' : 'Backtest needs attention'}</h2>
        <p className="text-sm leading-6 text-secondary">{operation.isError ? operation.error.message : operation.data?.status === 'running'
          ? 'QAP is simulating the declared methods and comparisons. You can return to this study later.'
          : operation.data?.status === 'completed' ? 'The calculations finished. The results below explain whether the methods helped.'
          : operation.data?.failure?.message ?? 'Your question and this attempt are saved. Open run details for the recorded status.'}</p>
        <a className="inline-flex min-h-11 items-center text-sm font-semibold text-accent" href={`/operations/${encodeURIComponent(operationId)}`}>Run details</a>
        {operation.isError ? <button type="button" className="ml-4 min-h-11 text-accent" onClick={() => void operation.refetch()}>Retry loading</button> : null}
      </section> : null}
      {operationId && runIds.length > 0 ? <PairResearchCompletion queries={queries} runIds={runIds}
        operationId={operationId} compilationSha256={compilation} busy={busy}
        canChangeSettings={visibleDraft !== null} onChangeSettings={() => setSettingsOpen(true)}
        onRunAgain={() => comparison.mutate(comparisonOptions)} /> : null}
      {operationId && study.mode === 'backtest_comparison' && readyToStudy && !visibleDraft && restoredRecipe.isError ?
        <p role="alert" className="rounded-md border border-warning/45 p-4 text-sm text-warning">
          Next-run settings unavailable: {restoredRecipe.error.message}. Your recorded result is unchanged.{' '}
          <button type="button" className="min-h-11 font-semibold text-accent" onClick={() => void restoredRecipe.refetch()}>Retry loading settings</button>
        </p> : null}
      {visibleDraft && study.mode === 'backtest_comparison' && operationId ? <PairExperimentPreview recipe={visibleDraft} busy={busy}
        descriptiveWindowBars={studyResult?.context.relationship?.rolling_log_ratio.window_observations}
        descriptiveMinimumObservations={studyResult?.context.relationship?.rolling_log_ratio.required_observations}
        nextRun open={settingsOpen} onToggle={setSettingsOpen} onParameters={(parameters) => {
        setDraft(applyStudyParameters(visibleDraft, parameters))
        setChecked(null)
        onChange({ parameters })
      }} /> : null}
      </div>
      </div>
    </section>
  )
}
