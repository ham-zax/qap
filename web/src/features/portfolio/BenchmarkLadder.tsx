import type { ExperimentDetailDto } from '../../api/types'
import { ComparisonBars } from '../../components/visuals/ComparisonBars'
import { formatPercent, formatRelativePercent } from '../../lib/format'
import { humanizeIdentifier } from '../experiments/presentation'

type ExactSign = -1 | 0 | 1

function exactSign(value: string): ExactSign {
  const trimmed = value.trim()
  const negative = trimmed.startsWith('-')
  const unsigned = trimmed.replace(/^[+-]/, '')
  const mantissa = unsigned.split(/[eE]/, 1)[0] ?? ''
  const nonZero = /[1-9]/.test(mantissa)
  if (!nonZero) return 0
  return negative ? -1 : 1
}

function magnitudePercent(value: string): string {
  return formatRelativePercent(value).display.replace(/^[+−]/, '')
}

interface BenchmarkLadderProps {
  experiment: ExperimentDetailDto
}

export function BenchmarkLadder({ experiment }: BenchmarkLadderProps) {
  const { manifest, result } = experiment
  const primaryControl = result.primary_incremental_benchmark
  const primaryIncrement = result.strategy_vs_primary_control
  const matchedIncrement = result.strategy_vs_matched_contribution
  const hasExternalFlows = manifest.external_flows.length > 0
  const primaryControlIsSuccessMetric =
    result.primary_metric === 'primary_control_relative_terminal_wealth'
  const missedDeclaredThreshold =
    primaryControlIsSuccessMetric && result.status === 'negative'
  const primaryLabel = humanizeIdentifier(primaryControl ?? 'primary control')
  const comparisons = [
    ...(primaryIncrement != null
      ? [{ label: `Primary control · ${primaryLabel}`, value: primaryIncrement }]
      : []),
    { label: 'Strict inventory HODL', value: result.strategy_vs_hodl },
    ...(matchedIncrement != null
      ? [{ label: 'Matched-contribution HODL', value: matchedIncrement }]
      : []),
  ]

  return (
    <section
      className="rounded-lg border border-border bg-panel p-5 md:p-6"
      aria-labelledby="benchmark-ladder-heading"
    >
      <h2 id="benchmark-ladder-heading" className="mb-2 text-lg font-semibold text-foreground">
        Benchmark comparison
      </h2>
      <p className="mt-0 mb-5 max-w-3xl text-sm leading-6 text-secondary">
        Every comparison uses the persisted matched run economics. Zero is parity;
        the research verdict still follows the predeclared success rule.
      </p>
      <ComparisonBars items={comparisons} />

      <div className="mt-6 space-y-3 border-t border-border pt-5 text-sm leading-6 text-secondary">
        {manifest.benchmarks.relationship_alpha_claim && primaryIncrement != null ? (
          exactSign(primaryIncrement) > 0 ? (
            <p className="m-0">
              Relationship intelligence added a {magnitudePercent(primaryIncrement)} increment over{' '}
              {primaryLabel}
              {missedDeclaredThreshold && result.success_threshold != null ? (
                <>
                  , but this run did not meet the predeclared{' '}
                  {formatPercent(result.success_threshold).display} success threshold.
                </>
              ) : (
                <> in this run.</>
              )}
            </p>
          ) : exactSign(primaryIncrement) < 0 ? (
            <p className="m-0">
              Relationship intelligence underperformed {primaryLabel} by{' '}
              {magnitudePercent(primaryIncrement)}.
            </p>
          ) : (
            <p className="m-0">Relationship intelligence was at parity with {primaryLabel}.</p>
          )
        ) : null}

        {hasExternalFlows && matchedIncrement != null ? (
          exactSign(matchedIncrement) > 0 ? (
            <p className="m-0">
              Contribution timing outperformed matched-contribution static HODL by{' '}
              {magnitudePercent(matchedIncrement)}; that is necessary evidence for
              timing value, not automatic proof of alpha.
            </p>
          ) : exactSign(matchedIncrement) < 0 ? (
            <p className="m-0">
              Contribution timing underperformed matched-contribution static HODL by{' '}
              {magnitudePercent(matchedIncrement)}.
            </p>
          ) : (
            <p className="m-0">Contribution timing was at parity with matched-contribution static HODL.</p>
          )
        ) : null}
      </div>
    </section>
  )
}
