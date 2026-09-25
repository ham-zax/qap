import type { ProductPairStudyContextDto, ProductPairStudySeriesDto } from '../../api/types'
import { formatResearchTimestamp, formatSignedDecimal } from '../../lib/format'
import { interpretRelationshipScore, relationshipSummary } from './researchPresentation'

const toneClass = { neutral: 'text-secondary', info: 'text-info', warning: 'text-warning' } as const

export function PairRelationshipSummary({ context }: {
  context: ProductPairStudyContextDto; series: ProductPairStudySeriesDto | null
}) {
  const relationship = context.relationship
  const score = relationship?.rolling_log_ratio
  const residual = relationship?.residual_ols
  const ratioMeaning = interpretRelationshipScore('ratio', score?.status ?? 'insufficient_history', score?.values.score)
  const residualMeaning = interpretRelationshipScore('residual', residual?.status ?? 'insufficient_history', residual?.values.score)
  return <section className="rounded-lg border border-border-strong bg-panel p-5 md:p-6" aria-label="Relationship summary">
    <p className="m-0 text-xs font-semibold uppercase tracking-wide text-accent">Relationship study</p>
    <h2 className="mt-2 mb-1 text-xl font-semibold text-foreground">What the relationship shows</h2>
    <p className="mt-1 text-sm leading-6 text-secondary">
      {context.question.orientation} on {context.question.venue === 'gate' ? 'Gate' : 'Binance'} through{' '}
      {context.question.safe_cutoff ? formatResearchTimestamp(context.question.safe_cutoff) : 'the available cutoff'}.
      This describes historical price behavior; it does not tell us whether trading it would improve wealth.
    </p>
    <p className="mt-5 rounded-md border border-border bg-subtle p-4 text-sm leading-6 text-foreground">
      {relationshipSummary(ratioMeaning, residualMeaning)}{' '}
      <span className="text-secondary">Descriptive relationship evidence only; not a trading recommendation or proof of profitable economics.</span>
    </p>
    {relationship ? <div className="mt-5 flex flex-wrap gap-x-10 gap-y-4 border-t border-border pt-4">
      <div className="min-w-[13rem] flex-1">
        <p className="m-0 text-sm text-muted">Distance from recent reference level</p>
        <p className="mt-2 mb-1 text-xl font-semibold tabular-nums text-foreground">{ratioMeaning.score === null ? 'Unavailable' : `${formatSignedDecimal(String(ratioMeaning.score), 2).display} standard deviations`}</p>
        <p data-tone={ratioMeaning.tone} className={`mt-1 mb-2 text-sm ${toneClass[ratioMeaning.tone]}`}>{ratioMeaning.label}{ratioMeaning.direction ? ` · ${ratioMeaning.direction}` : ''}</p>
        <p className="m-0 text-xs text-secondary">{ratioMeaning.score === null ? ratioMeaning.explanation : `Based on the log price ratio over ${score?.window_observations} bars. Positive and negative describe direction, not a trading signal by themselves.`}</p>
        <details className="mt-2 text-xs text-secondary">
          <summary className="min-h-11 cursor-pointer py-2 text-accent">What does this measure?</summary>
          <p className="mt-1">How far the current log price ratio is from its rolling average, in standard deviations. A negative value means below that reference.</p>
        </details>
      </div>
      <div className="min-w-[13rem] flex-1">
        <p className="m-0 text-sm text-muted">Against the fitted relationship</p>
        <p className="mt-2 mb-1 text-xl font-semibold tabular-nums text-foreground">{residualMeaning.score === null ? 'Unavailable' : `${formatSignedDecimal(String(residualMeaning.score), 2).display} standard deviations`}</p>
        <p data-tone={residualMeaning.tone} className={`mt-1 mb-2 text-sm ${toneClass[residualMeaning.tone]}`}>{residualMeaning.label}{residualMeaning.direction ? ` · ${residualMeaning.direction}` : ''}</p>
        <p className="m-0 text-xs text-secondary">{residualMeaning.score === null ? residualMeaning.explanation : 'Rolling regression residual; this is not a formal cointegration test.'}</p>
        <details className="mt-2 text-xs text-secondary">
          <summary className="min-h-11 cursor-pointer py-2 text-accent">What does this measure?</summary>
          <p className="mt-1">How far the latest relationship is from the rolling fitted pattern, in standard deviations. This is not a formal cointegration test.</p>
        </details>
      </div>
    </div> : <p className="mt-5 rounded-md border border-warning/45 p-4 text-sm text-secondary">
      {context.data.status === 'ready' ? 'The relationship score is unavailable at this cutoff.' : 'Price history still needs setup.'}
      {' '}A missing score is not evidence for or against this pair.
    </p>}
    <p className="mt-5 mb-0 text-xs leading-5 text-muted">Descriptive measurements use the backend's default window for this period. Advanced backtest settings can use a different window; changing those settings does not recalculate this view.</p>
  </section>
}
