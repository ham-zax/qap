import type { ExperimentDetailDto } from '../../api/types'
import { ExactNumber } from '../../components/ExactNumber'
import { MetricCard } from '../../components/MetricCard'

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

function metricStatus(value: string): 'positive' | 'neutral' | 'negative' {
  const sign = exactSign(value)
  if (sign > 0) return 'positive'
  if (sign < 0) return 'negative'
  return 'neutral'
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

  return (
    <section aria-labelledby="benchmark-ladder-heading">
      <h2 id="benchmark-ladder-heading">Benchmark ladder</h2>
      <div className="metric-grid">
        <MetricCard
          label="HODL-relative wealth"
          value={<ExactNumber value={result.strategy_vs_hodl} />}
          status={metricStatus(result.strategy_vs_hodl)}
          detail="Strategy terminal wealth relative to strict inventory HODL."
        />
        {primaryIncrement != null ? (
          <MetricCard
            label="Primary control increment"
            value={<ExactNumber value={primaryIncrement} />}
            status={metricStatus(primaryIncrement)}
            detail={`Relative to ${primaryControl ?? 'the predeclared simple control'}.`}
          />
        ) : null}
        {matchedIncrement != null ? (
          <MetricCard
            label="Matched-contribution increment"
            value={<ExactNumber value={matchedIncrement} />}
            status={metricStatus(matchedIncrement)}
            detail="Relative to matched-contribution static HODL."
          />
        ) : null}
      </div>

      {manifest.benchmarks.relationship_alpha_claim && primaryIncrement != null ? (
        exactSign(primaryIncrement) > 0 ? (
          <p>
            Relationship intelligence added incremental value over{' '}
            {primaryControl ?? 'the predeclared primary control'} in this run.
          </p>
        ) : (
          <p>
            Relationship intelligence did not add incremental value over{' '}
            {primaryControl ?? 'the predeclared primary control'}.
          </p>
        )
      ) : null}

      {hasExternalFlows && matchedIncrement != null ? (
        exactSign(matchedIncrement) > 0 ? (
          <p>
            The strategy beat matched-contribution static HODL; that is necessary
            evidence for contribution-timing value, not automatic proof of alpha.
          </p>
        ) : (
          <p>
            Contribution timing did not beat matched-contribution static HODL.
          </p>
        )
      ) : null}
    </section>
  )
}
