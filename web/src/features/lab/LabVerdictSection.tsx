import { CheckCircle2 } from 'lucide-react'

import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { DetailTag } from '@/components/watermelon/dashboard-card'
import { InfoTip } from './InfoTip'
import type { LabAnalysis, LabStrategyFormSettings } from './labContract'
import type { LabStudy } from './labStudyApi'

function money(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return '—'
  return `$${value.toLocaleString('en-US', { maximumFractionDigits: 0 })}`
}

function signedPct(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return '—'
  return `${value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2, signDisplay: 'exceptZero' })}%`
}

function deltaTone(value: number | null | undefined): 'positive' | 'negative' | 'neutral' {
  if (value == null || !Number.isFinite(value) || value === 0) return 'neutral'
  return value > 0 ? 'positive' : 'negative'
}

export function LabVerdictSection({
  analysis,
  settings,
  study,
  studyRunning,
  studyError,
}: {
  analysis: LabAnalysis | null
  settings: LabStrategyFormSettings
  study: LabStudy | null
  studyRunning: boolean
  studyError: string | null
}) {
  const proof = study?.result.proof ?? null
  const call = study?.result.call ?? null
  const wealth = study?.result.wealth ?? null
  const rotating = wealth ? Number(wealth.terminal_values.strategy) : null
  const holding = wealth ? Number(wealth.terminal_values.hodl) : null
  const targetWeightA = call?.target_weight_a == null ? null : Number(call.target_weight_a)
  const targetPct =
    call == null || targetWeightA == null || !Number.isFinite(targetWeightA)
      ? null
      : Math.round((call.status === 'into_a' ? targetWeightA : 1 - targetWeightA) * 100)
  const coinCode = call?.status === 'into_b' ? analysis?.coin_b.code ?? 'Coin B' : analysis?.coin_a.code ?? 'Coin A'
  const proofGateSummary = proof
    ? `3-Gate Check — Cost Gate (tuning add-back gross >= 2× paid costs): ${proof.cost_gate_passed ? 'PASS' : 'FAIL'} · Walk-Forward (${proof.folds_passing}/${proof.folds_total} folds, need >= ${proof.minimum_passing_folds}): ${proof.folds_passing >= proof.minimum_passing_folds ? 'PASS' : 'FAIL'} · SPA corrected p=${proof.corrected_p_value != null ? proof.corrected_p_value.toFixed(3) : '—'} (need < ${proof.significance}): ${proof.corrected_p_value != null && proof.corrected_p_value < proof.significance ? 'PASS' : 'FAIL'}.`
    : ''

  return (
    <section className="space-y-2.5" aria-label="Backtest verdict">
      <div className="flex items-center justify-between gap-2">
        <h2 className="m-0 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          Verdict
        </h2>
        <Badge variant="secondary" className="rounded-md font-mono text-[11px]">
          $10,000 base
        </Badge>
      </div>

      {studyRunning ? (
        <div className="space-y-2 rounded-lg border border-border bg-muted/30 p-3">
          <p className="m-0 text-xs text-muted-foreground">
            Simulating $10,000 across walk-forward folds…
          </p>
          <Progress value={60} aria-label="Strategy test progress" />
        </div>
      ) : studyError ? (
        <Alert variant="destructive">
          <AlertDescription className="text-xs">{studyError}</AlertDescription>
        </Alert>
      ) : study && proof && call ? (
        <div className="space-y-2.5 rounded-lg border border-border bg-muted/35 p-3">
          <div className="flex flex-wrap items-center gap-1.5">
            <DetailTag tone={proof.passes ? 'positive' : 'neutral'}>
              {proof.passes ? <CheckCircle2 className="size-3.5" aria-hidden="true" /> : null}
              {proof.passes ? `Validated Edge (${proof.folds_passing}/${proof.folds_total} Folds)` : call.headline}
            </DetailTag>
            <InfoTip label="Validation gate criteria" text={proofGateSummary} />
          </div>
          <dl className="m-0 grid gap-1.5">
            <div className="flex items-baseline justify-between gap-2">
              <dt className="text-xs text-muted-foreground">Strategy</dt>
              <dd className="m-0 font-mono text-base font-semibold text-foreground tabular-nums">
                $10,000 → {money(rotating)}
              </dd>
            </div>
            <div className="flex items-baseline justify-between gap-2">
              <dt className="text-xs text-muted-foreground">Hold 50/50</dt>
              <dd className="m-0 font-mono text-sm font-medium text-foreground/90 tabular-nums">
                {money(holding)}
              </dd>
            </div>
          </dl>
          <p className="m-0 flex flex-wrap gap-2 font-mono text-xs tabular-nums">
            <DetailTag tone={deltaTone(proof.vs_hodl_pct)}>{signedPct(proof.vs_hodl_pct)} vs ending Hold</DetailTag>
            <DetailTag tone={deltaTone(proof.vs_control_pct)}>{signedPct(proof.vs_control_pct)} vs ending Rebalance</DetailTag>
          </p>
          <p className="m-0 font-mono text-[11px] text-muted-foreground tabular-nums">
            {proof.validation_trades} swaps · {proof.cost_paid_pct?.toFixed(2) ?? '0.00'}% of start paid in fees &amp; slippage
            {proof.gross_vs_hodl_pct != null ? ` · add-back gross ${signedPct(proof.gross_vs_hodl_pct)} vs Hold` : ''}
          </p>
          {(call.status === 'into_a' || call.status === 'into_b') && (
            <Badge variant="outline" className="border-primary/40 bg-primary/10 text-primary">
              Signal: Swap toward {coinCode}
              {targetPct == null ? '' : ` (${targetPct}%)`}
            </Badge>
          )}
        </div>
      ) : (
        <p className="m-0 rounded-lg border border-border bg-muted/25 p-3 text-xs leading-relaxed text-muted-foreground">
          {analysis
            ? `${analysis.coin_a.code}/${analysis.coin_b.code} ready (${analysis.bars_used} candles). Select a strategy below to backtest $10,000 after ${(settings.fee_bps / 100).toFixed(2)}% spot fees.`
            : `Choose two coins to load market candles, then backtest $10,000 after ${(settings.fee_bps / 100).toFixed(2)}% spot fees.`}
        </p>
      )}
    </section>
  )
}
