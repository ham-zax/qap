import { useQueries, useQuery } from '@tanstack/react-query'
import { useEffect, useState } from 'react'

import type { QapQueries } from '../../api/queries'
import type { ExperimentDetailDto } from '../../api/types'
import { Badge } from '../../components/ui/Badge'
import { formatDecimal, formatPercent, formatRelativePercent, formatResearchTimestamp } from '../../lib/format'
import { experimentDataRoleLabel, humanizeIdentifier, researchStatusPresentation, researchVerdictHeadline } from '../experiments/presentation'
import { RelativeWealthChart } from '../portfolio/RelativeWealthChart'
import { researchMethodDescription, researchMethodName } from './researchPresentation'

function Value({ value, unit = '', percent = false }: { value: string | null | undefined; unit?: string; percent?: boolean }) {
  if (value == null) return <span>Unavailable</span>
  return <span title={`Exact value: ${value}`} data-exact={value}>{percent ? formatRelativePercent(value).display : formatDecimal(value, 4).display}{unit ? ` ${unit}` : ''}</span>
}

function TestDetails({ data }: { data: ExperimentDetailDto }) {
  const { manifest, result } = data
  const window = manifest.evaluation_window ?? manifest.data_window
  const settings = Object.entries({ ...manifest.relationship.config, ...manifest.policy.config })
    .filter(([key]) => !['base_asset', 'quote_asset', 'evidence_instrument_ids'].includes(key))
  return <details className="mt-5 rounded-md border border-border p-4">
    <summary className="min-h-11 cursor-pointer py-2 font-semibold text-accent">Test details · methods, assumptions, and costs</summary>
    <dl className="mt-3 grid gap-4 text-sm md:grid-cols-2">
      <div><dt className="font-semibold text-foreground">Evaluation period</dt><dd className="ml-0 mt-1 text-secondary">{formatResearchTimestamp(window.start)} to {formatResearchTimestamp(window.end)}</dd></div>
      <div><dt className="font-semibold text-foreground">Decision rule</dt><dd className="ml-0 mt-1 text-secondary">{humanizeIdentifier(manifest.policy.component_id)}</dd></div>
      <div><dt className="font-semibold text-foreground">Execution</dt><dd className="ml-0 mt-1 text-secondary">{manifest.execution.mode === 'direct' ? 'Real direct-market replay' : `Two real market legs through ${manifest.execution.bridge_asset}`}</dd></div>
      <div><dt className="font-semibold text-foreground">Cost assumptions</dt><dd className="ml-0 mt-1 text-secondary">{manifest.execution.fee_bps} basis points fee + {manifest.execution.slippage_bps} basis points slippage per fill.</dd></div>
      <div><dt className="font-semibold text-foreground">Starting holdings</dt><dd className="ml-0 mt-1 text-secondary">{Object.entries(manifest.starting_quantities).map(([asset, quantity]) => `${quantity} ${asset}`).join(' · ')}</dd></div>
      <div><dt className="font-semibold text-foreground">Declared primary control</dt><dd className="ml-0 mt-1 text-secondary">{result.primary_incremental_benchmark}</dd></div>
      <div><dt className="font-semibold text-foreground">Predeclared success threshold</dt><dd className="ml-0 mt-1 text-secondary">{formatPercent(result.success_threshold).display}</dd></div>
      {settings.map(([key, value]) => <div key={key}><dt className="text-xs text-muted">{humanizeIdentifier(key)}</dt><dd className="ml-0 mt-1 break-words text-secondary">{typeof value === 'object' ? JSON.stringify(value) : String(value)}</dd></div>)}
    </dl>
  </details>
}

function ReproducibilityDetails({ data, queries }: { data: ExperimentDetailDto; queries: QapQueries }) {
  const [expanded, setExpanded] = useState(false)
  const lineage = useQuery({ ...queries.researchRecipeRunLineage(data.run_id), enabled: expanded })
  return <details onToggle={(event) => setExpanded(event.currentTarget.open)} className="mt-4 rounded-md border border-border p-4">
    <summary className="min-h-11 cursor-pointer py-2 text-sm font-semibold text-accent">Reproducibility details</summary>
    <p className="text-sm leading-6 text-secondary">These identifiers link the exact code, inputs, and declaration used for this result. They are available for auditing and reproduction.</p>
    <dl className="space-y-3 break-all text-xs text-muted">
      <div><dt>Run</dt><dd className="ml-0 font-mono">{data.run_id}</dd></div>
      <div><dt>Manifest SHA-256</dt><dd className="ml-0 font-mono">{data.provenance.manifest_sha256}</dd></div>
      <div><dt>Code fingerprint</dt><dd className="ml-0 font-mono">{data.provenance.code_fingerprint}</dd></div>
      <div><dt>Code revision</dt><dd className="ml-0 font-mono">{data.provenance.git_commit ?? 'Unrecorded'}{data.provenance.git_dirty ? ' · uncommitted changes present' : ''}</dd></div>
      {data.provenance.data_fingerprints.map((item) => <div key={item.dataset_id}><dt>{item.dataset_id}</dt><dd className="ml-0 font-mono">{item.fingerprint}</dd></div>)}
      {lineage.data?.matches.map((item) => <div key={item.compilation.compilation_sha256}><dt>Recipe / compilation</dt><dd className="ml-0 font-mono">{item.recipe.recipe_sha256}<br />{item.compilation.compilation_sha256}</dd></div>)}
    </dl>
    {lineage.isError ? <p role="alert" className="text-sm text-warning">Recipe provenance could not be loaded. <button type="button" onClick={() => void lineage.refetch()} className="min-h-11 text-accent">Retry</button></p> : null}
  </details>
}

function PairResearchRunResult({ queries, runId, index, total }: {
  queries: QapQueries; runId: string; index: number; total: number
}) {
  const experiment = useQuery(queries.experiment(runId))
  const performance = useQuery(queries.performance(runId))
  if (experiment.isPending) return <p role="status" className="rounded-md border border-border p-5 text-secondary">Loading method {index + 1} of {total}…</p>
  if (experiment.isError) return <section className="rounded-md border border-warning/45 p-5">
    <h3 className="text-lg font-semibold text-foreground">This result could not be loaded</h3>
    <p className="text-sm text-secondary">{experiment.error.message}</p>
    <button type="button" onClick={() => void experiment.refetch()} className="min-h-11 font-semibold text-accent">Retry loading result</button>
    <a href={`/experiments/${encodeURIComponent(runId)}`} className="ml-4 text-sm text-accent">Open result record</a>
  </section>
  const data = experiment.data
  const { manifest, result } = data
  const status = researchStatusPresentation(result.status)
  const strategy = result.roles.find((role) => role.role === 'strategy')
  const hodl = result.roles.find((role) => role.role === 'hodl')
  const control = result.roles.find((role) => role.role === `control:${result.primary_incremental_benchmark}`)
  const unit = manifest.execution.numeraire_asset
  const isFinal = result.data_role === 'final_oos' && result.final_oos_consumed
  const verdict = researchVerdictHeadline(result.status, 'simple rebalancing', result.strategy_vs_primary_control)
  return <article className="rounded-lg border border-border-strong bg-panel p-5 md:p-6">
    <div className="flex flex-wrap items-start justify-between gap-3">
      <div><p className="m-0 text-xs font-semibold uppercase tracking-wide text-muted">Method {index + 1} of {total}</p>
        <h3 className="mt-2 mb-1 text-xl font-semibold text-foreground">{researchMethodName(manifest.relationship.component_id)}</h3></div>
      <Badge tone={status.tone}>{status.label}</Badge>
    </div>
    <p className="text-sm leading-6 text-secondary">{researchMethodDescription(manifest.relationship.component_id)}</p>
    <section className="mt-5 rounded-md border border-border bg-subtle p-4" aria-label="Research conclusion">
      <p className="m-0 text-xl font-semibold text-foreground">{verdict}</p>
      <p className="mt-2 mb-0 text-sm leading-6 text-secondary">{result.status === 'negative'
        ? 'The test completed successfully, but the strategy did not meet its declared economic success criterion.'
        : result.status === 'positive' ? 'The strategy met its declared economic success criterion for this test.'
        : 'The recorded result is neutral under the declared criterion.'}
        {' '}{isFinal ? 'This result used the committed final holdout; that holdout is now consumed.' : 'This does not establish untouched final-holdout confirmation.'}</p>
      <p className="mt-2 mb-0 text-xs text-muted">{experimentDataRoleLabel(result.data_role, result.final_oos_consumed)} · {manifest.basket.join(' / ')}</p>
    </section>
    <div className="mt-5 overflow-x-auto">
      <table className="w-full text-left text-sm">
        <caption className="mb-3 text-left font-semibold text-foreground">Ending wealth after modeled costs · {unit}</caption>
        <thead><tr className="border-b border-border text-muted"><th scope="col" className="py-3 pr-4">Approach</th><th scope="col" className="py-3 pr-4">Ending value</th><th scope="col" className="py-3">Fills</th></tr></thead>
        <tbody>{([['Tested strategy', strategy], ['Hold starting assets', hodl], ['Simple rebalancing', control]] as const).map(([name, role]) =>
          <tr key={name} className="border-b border-border"><th scope="row" className="py-3 pr-4 font-medium text-secondary">{name}</th><td className="py-3 pr-4 tabular-nums text-foreground"><Value value={role?.terminal_value} /></td><td className="py-3 tabular-nums text-secondary">{role?.fill_count ?? 'Unavailable'}</td></tr>)}</tbody>
      </table>
    </div>
    <p className="mt-4 text-sm text-secondary">Strategy costs: <Value value={strategy?.fees_value} unit={unit} /> in fees; <Value value={strategy?.slippage_value} unit={unit} /> in slippage. Maximum relative drawdown against holding: {formatPercent(result.maximum_relative_drawdown_vs_hodl).display}.</p>
    {performance.data ? <div className="mt-5"><RelativeWealthChart performance={performance.data} /></div>
      : performance.isError ? <p className="text-sm text-muted">Comparison chart unavailable; the recorded summary above remains available.{' '}
          <button type="button" onClick={() => void performance.refetch()} className="min-h-11 font-semibold text-accent">Retry chart</button>
        </p>
        : <p className="text-sm text-muted">Loading comparison chart…</p>}
    <TestDetails data={data} />
    <ReproducibilityDetails data={data} queries={queries} />
    <a className="mt-4 inline-flex min-h-11 items-center text-sm font-semibold text-accent" href={`/experiments/${encodeURIComponent(runId)}`}>Open full experiment</a>
  </article>
}

export function PairResearchCompletion({ queries, runIds, operationId, compilationSha256, onRunAgain = () => undefined, busy = false }: {
  queries: QapQueries; runIds: string[]; operationId: string; compilationSha256: string | null
  onRunAgain?: () => void; busy?: boolean
}) {
  const experiments = useQueries({ queries: runIds.map((runId) => queries.experiment(runId)) })
  const [selectedRunId, setSelectedRunId] = useState(runIds[0] ?? '')

  useEffect(() => {
    if (!runIds.includes(selectedRunId)) setSelectedRunId(runIds[0] ?? '')
  }, [runIds, selectedRunId])

  const selectedIndex = Math.max(0, runIds.indexOf(selectedRunId))
  const firstAvailable = experiments.find((query) => query.data)?.data
  const selected = experiments[selectedIndex]?.data ?? firstAvailable
  const window = selected ? selected.manifest.evaluation_window ?? selected.manifest.data_window : null

  return <section className="space-y-5" aria-label="Research results">
    <header className="flex flex-wrap items-end justify-between gap-4">
      <div>
        <p className="mb-1 text-xs font-semibold uppercase tracking-[0.08em] text-muted">Results</p>
        <h2 className="m-0 text-2xl font-semibold text-foreground">
          {selected?.manifest.basket.join(' / ') ?? 'Comparison'}
        </h2>
        <p className="mt-2 mb-0 text-sm text-secondary">
          {window ? <>{formatResearchTimestamp(window.start)} to {formatResearchTimestamp(window.end)}</> : 'Loading tested dates…'}
        </p>
      </div>
      <div className="flex flex-wrap gap-3">
        <a href="#comparison-settings" className="inline-flex min-h-11 items-center text-sm font-semibold text-accent">Change settings</a>
        <button type="button" disabled={busy} onClick={onRunAgain}
          className="min-h-11 rounded-md border border-border px-4 text-sm font-semibold text-foreground disabled:opacity-50">
          Run again
        </button>
      </div>
    </header>
    <div className="overflow-x-auto rounded-lg border border-border bg-panel">
      <table className="w-full min-w-[42rem] text-left text-sm">
        <caption className="sr-only">Method comparison summary</caption>
        <thead><tr className="border-b border-border text-muted">
          <th scope="col" className="px-4 py-3">Method</th>
          <th scope="col" className="px-4 py-3">vs Holding</th>
          <th scope="col" className="px-4 py-3">vs Rebalancing</th>
          <th scope="col" className="px-4 py-3">Recorded result</th>
        </tr></thead>
        <tbody>
          {experiments.map((query, index) => {
            const runId = runIds[index]
            if (!runId) return null
            if (query.isPending) return <tr key={runId} className="border-b border-border"><td className="px-4 py-4 text-secondary" colSpan={4}>Loading method {index + 1}…</td></tr>
            if (query.isError) return <tr key={runId} className="border-b border-border"><td className="px-4 py-4 text-warning" colSpan={4}>
              Result unavailable. <button type="button" className="min-h-11 font-semibold text-accent" onClick={() => void query.refetch()}>Retry</button>
            </td></tr>
            if (!query.data) return null
            const status = researchStatusPresentation(query.data.result.status)
            return <tr key={runId} className={selectedRunId === runId ? 'bg-subtle' : 'border-b border-border'}>
              <th scope="row" className="px-4 py-3">
                <button type="button" onClick={() => setSelectedRunId(runId)} aria-pressed={selectedRunId === runId}
                  className="min-h-11 text-left font-semibold text-accent">
                  {researchMethodName(query.data.manifest.relationship.component_id)}
                </button>
              </th>
              <td className="px-4 py-3 tabular-nums text-foreground"><Value value={query.data.result.strategy_vs_hodl} percent /></td>
              <td className="px-4 py-3 tabular-nums text-foreground"><Value value={query.data.result.strategy_vs_primary_control} percent /></td>
              <td className="px-4 py-3"><Badge tone={status.tone}>{status.label}</Badge></td>
            </tr>
          })}
        </tbody>
      </table>
    </div>
    {runIds[selectedIndex] ? <PairResearchRunResult key={runIds[selectedIndex]} queries={queries}
      runId={runIds[selectedIndex]} index={selectedIndex} total={runIds.length} /> : null}
    <section className="rounded-lg border border-border bg-subtle p-5">
      <h3 className="m-0 text-lg font-semibold text-foreground">What this lets you conclude</h3>
      <p className="mb-0 text-sm leading-6 text-secondary">These results describe the stated assets, history, rules and modeled costs. They do not prove future profitability, live execution capacity, or that a relationship caused the difference. Changing settings creates another development attempt; keep earlier attempts in the comparison.</p>
    </section>
    <details className="rounded-md border border-border p-4 text-xs text-muted"><summary className="cursor-pointer py-2 font-semibold text-accent">Attempt references</summary>
      <p className="break-all">Operation: {operationId}</p><p className="break-all">Compilation: {compilationSha256 ?? 'Unavailable'}</p>
    </details>
  </section>
}
