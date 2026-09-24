import type { ResearchRecipeDraftV1 } from '../../api/types'
import { formatResearchTimestamp } from '../../lib/format'
import { researchMethodDescription, researchMethodName } from './researchPresentation'
import { ResearchParameterControls } from './RecipeAuthoringControls'
import { PARAMETER_KEYS } from './researchStudies'

export function PairExperimentPreview({ recipe, busy, onParameters, nextRun = false, open = false, onToggle,
  descriptiveWindowBars, descriptiveMinimumObservations }: {
  recipe: ResearchRecipeDraftV1; busy: boolean; onParameters: (parameters: Record<string, string>) => void
  nextRun?: boolean; open?: boolean; onToggle?: (open: boolean) => void
  descriptiveWindowBars?: number; descriptiveMinimumObservations?: number
}) {
  const window = recipe.data.evaluation_window ?? recipe.data.data_window
  const windowValue = recipe.variants[0]?.relationship.config.window_bars
  const minimumValue = recipe.variants[0]?.relationship.config.min_observations
  const backtestWindowBars = typeof windowValue === 'number' || typeof windowValue === 'string' ? Number(windowValue) : NaN
  const backtestMinimumObservations = typeof minimumValue === 'number' || typeof minimumValue === 'string' ? Number(minimumValue) : NaN
  const settingsDiffer = descriptiveWindowBars !== undefined && descriptiveMinimumObservations !== undefined
    && Number.isFinite(backtestWindowBars) && Number.isFinite(backtestMinimumObservations)
    && (descriptiveWindowBars !== backtestWindowBars || descriptiveMinimumObservations !== backtestMinimumObservations)
  return (
    <section className="rounded-lg border border-border-strong bg-panel p-5 md:p-6" aria-label="Comparison settings">
      <h2 className="m-0 text-lg font-semibold text-foreground">{nextRun ? 'Next run settings' : 'Backtest settings'}</h2>
      <p className="mt-2 mb-0 text-sm leading-6 text-secondary">Two declared methods compare wealth after modeled costs against holding and simple rebalancing.</p>
      {settingsDiffer ? <div className="mt-3 rounded-md border border-warning/45 p-3 text-xs leading-5 text-secondary">
        <p className="m-0">Descriptive view: {descriptiveWindowBars}-bar window, {descriptiveMinimumObservations} observations required.</p>
        <p className="m-0">{nextRun ? 'Next backtest settings' : 'Backtest settings'}: {backtestWindowBars}-bar window, {backtestMinimumObservations} observations required. These are separate calculations.</p>
      </div> : null}
      <details id="comparison-settings" open={open} onToggle={(event) => onToggle?.(event.currentTarget.open)} className="mt-3">
      <summary className="min-h-11 cursor-pointer py-2 text-sm font-semibold text-accent">Advanced settings and assumptions</summary>
      <p className="mt-2 text-sm leading-6 text-secondary">{nextRun ? 'These editable settings apply only to a future attempt. The result above remains unchanged.' : 'Defaults are checked by the backend when you start the backtest.'}</p>
      <div className="mt-4 grid gap-3 md:grid-cols-2">
        {recipe.variants.map((variant) => <article key={variant.variant_id} className="rounded-md border border-border bg-subtle p-4">
          <h3 className="m-0 text-base font-semibold text-foreground">{researchMethodName(variant.relationship.component_id)}</h3>
          <p className="mt-2 mb-0 text-sm leading-6 text-secondary">{researchMethodDescription(variant.relationship.component_id)}</p>
        </article>)}
      </div>
      <dl className="mt-5 grid gap-4 text-sm md:grid-cols-2">
        <div><dt className="font-semibold text-foreground">Period and observations</dt><dd className="ml-0 mt-1 text-secondary">{formatResearchTimestamp(window.start)} to {formatResearchTimestamp(window.end)} · {recipe.data.interval} bars</dd></div>
        <div><dt className="font-semibold text-foreground">Comparisons</dt><dd className="ml-0 mt-1 text-secondary">Hold the same starting assets (HODL), plus the declared simple rebalancing control. Both methods use the same starting holdings and cost assumptions.</dd></div>
        <div><dt className="font-semibold text-foreground">Trading costs</dt><dd className="ml-0 mt-1 text-secondary">{recipe.execution.fee_bps} basis points in fees + {recipe.execution.slippage_bps} basis points in slippage per fill. 1 basis point = 0.01%.</dd></div>
        <div><dt className="font-semibold text-foreground">Execution</dt><dd className="ml-0 mt-1 text-secondary">{recipe.execution.mode === 'direct' ? 'Simulated fills in the real direct market.' : `Simulated fills through two real markets, temporarily using ${recipe.execution.bridge_asset}. Each leg incurs costs.`}</dd></div>
      </dl>
      {recipe.variants[0] ? <div className="mt-5 rounded-md border border-border p-4">
        <h3 className="m-0 text-sm font-semibold text-foreground">Change settings</h3>
        <p className="text-sm leading-6 text-secondary">These settings apply to both methods. The next Run comparison action automatically obtains a fresh backend support check.</p>
        <fieldset disabled={busy} className="min-w-0 border-0 p-0">
          <ResearchParameterControls config={{ ...recipe.variants[0].relationship.config, ...recipe.variants[0].decision_rule.config }}
            onChange={(config) => onParameters(Object.fromEntries(PARAMETER_KEYS.filter((key) => key in config).map((key) => [key, String(config[key])])))} />
        </fieldset>
      </div> : null}
      <details className="mt-5 rounded-md border border-border p-4">
        <summary className="cursor-pointer text-sm font-semibold text-accent">Starting holdings and exact test settings</summary>
        <p className="mt-3 text-sm text-secondary">Starting holdings: {Object.entries(recipe.data.starting_quantities).map(([asset, quantity]) => `${quantity} ${asset}`).join(' · ')}</p>
        {recipe.variants.map((variant) => <div key={variant.variant_id} className="mt-3 text-sm text-secondary">
          <p className="font-semibold">{researchMethodName(variant.relationship.component_id)}</p>
          <dl className="grid gap-2 sm:grid-cols-2">{Object.entries({ ...variant.relationship.config, ...variant.decision_rule.config })
            .filter(([key]) => !['base_asset', 'quote_asset', 'evidence_instrument_ids'].includes(key))
            .map(([key, value]) => <div key={key}><dt className="text-xs text-muted">{key.replaceAll('_', ' ')}</dt><dd className="ml-0 break-words">{typeof value === 'object' ? JSON.stringify(value) : String(value)}</dd></div>)}</dl>
        </div>)}
      </details>
      <p className="mt-4 mb-0 text-xs leading-5 text-muted">This is a development comparison of assets approved today. It does not establish historical universe discovery, untouched holdout performance, or live trading readiness.</p>
      </details>
    </section>
  )
}
