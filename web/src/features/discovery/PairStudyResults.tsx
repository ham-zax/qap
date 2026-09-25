import { useState } from 'react'

import type { CapabilityMetadataV1, ProductPairStudyContextDto, ProductPairStudySeriesDto } from '../../api/types'
import { TimeSeriesChart } from '../../components/charts/TimeSeriesChart'
import type { TimeSeriesDefinition } from '../../components/charts/chartData'
import { formatDecimal } from '../../lib/format'
import { PairStudyTechnicalDetails } from './PairStudyTechnicalDetails'

type ChartView = 'normalized' | 'ratio' | 'log' | 'reference'

function chartDefinition(view: ChartView, data: ProductPairStudySeriesDto): {
  title: string; description: string; series: TimeSeriesDefinition[]
} {
  const orientation = data.question.orientation
  if (view === 'normalized') return {
    title: `${orientation} normalized paths`,
    description: 'Backend price paths rebased to one at the study window start; not a backtest.',
    series: [
      { name: data.question.asset_a, unit: 'normalized path', points: data.normalized_base },
      { name: data.question.asset_b, unit: 'normalized path', points: data.normalized_quote },
    ],
  }
  if (view === 'log') return {
    title: `${orientation} log ratio`, description: 'Backend-produced natural log of the pair ratio.',
    series: [{ name: orientation, unit: 'log ratio', points: data.log_ratio }],
  }
  if (view === 'reference' && data.analysis_reference) return {
    title: `Relative to ${data.analysis_reference.asset}`,
    description: 'Descriptive reference only; the reference asset is not added to execution.',
    series: [
      { name: `${data.question.asset_a}/${data.analysis_reference.asset}`, unit: 'reference ratio', points: data.analysis_reference.base_to_reference },
      { name: `${data.question.asset_b}/${data.analysis_reference.asset}`, unit: 'reference ratio', points: data.analysis_reference.quote_to_reference },
    ],
  }
  return {
    title: `${orientation} ratio`, description: 'Backend-produced ratio from synchronized same-venue observations.',
    series: [{ name: orientation, unit: 'ratio', points: data.ratio }],
  }
}

export function PairStudyResults({ context, series, capabilities }: {
  context: ProductPairStudyContextDto
  series: ProductPairStudySeriesDto | null
  capabilities: readonly CapabilityMetadataV1[]
}) {
  const [view, setView] = useState<ChartView>('normalized')
  const chart = series ? chartDefinition(view, series) : null
  const option = (value: ChartView, label: string) => <button key={value} type="button"
    aria-pressed={view === value} onClick={() => setView(value)}
    className={`min-h-11 rounded-md border px-3 text-sm font-semibold ${view === value ? 'border-accent bg-accent text-canvas' : 'border-border text-accent'}`}>{label}</button>

  return <section className="min-w-0 rounded-lg border border-border-strong bg-panel p-5 md:p-6" aria-label="Relationship chart and details">
    <div className="flex flex-wrap items-end justify-between gap-3">
      <div>
        <h2 className="m-0 text-xl font-semibold text-foreground">Relationship chart</h2>
        <p className="mb-0 mt-1 text-sm text-secondary">Compare the same historical prices in the view that makes sense to you.</p>
      </div>
      {series ? <div role="group" aria-label="Relationship chart view" className="flex flex-wrap gap-2">
        {option('normalized', 'Normalized paths')}{option('ratio', 'Ratio')}
        <details className="relative text-sm">
          <summary className="flex min-h-11 cursor-pointer items-center rounded-md border border-border px-3 font-semibold text-accent">More views</summary>
          <div className="mt-2 flex flex-wrap gap-2">{option('log', 'Log ratio')}{series.analysis_reference ? option('reference', `Relative to ${series.analysis_reference.asset}`) : null}</div>
        </details>
      </div> : null}
    </div>
    {chart ? <div className="mt-5"><TimeSeriesChart title={chart.title} description={chart.description} series={chart.series} height={380} /></div>
      : <p role="status" className="mt-5 text-sm text-secondary">The chart is not available yet. The relationship measurements remain below.</p>}
    {context.relationship ? <dl className="mt-5 flex flex-wrap gap-x-8 gap-y-3 border-t border-border pt-4 text-sm">
      <div><dt className="text-muted">Raw ratio</dt><dd className="ml-0 mt-1 font-semibold tabular-nums text-foreground">{context.relationship.raw_ratio_current === undefined ? 'Unavailable' : formatDecimal(String(context.relationship.raw_ratio_current), 6).display}</dd></div>
      <div><dt className="text-muted">History available</dt><dd className="ml-0 mt-1 text-foreground">{context.relationship.rolling_log_ratio.coverage_observations} observations · {context.relationship.rolling_log_ratio.required_observations} required · {context.relationship.rolling_log_ratio.window_observations}-bar window</dd></div>
    </dl> : null}
    <PairStudyTechnicalDetails context={context} series={series} capabilities={capabilities} />
  </section>
}
