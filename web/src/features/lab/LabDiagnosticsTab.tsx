import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { DetailTag } from '@/components/watermelon/dashboard-card'
import type { LabAnalysis, LabViewMode } from './labContract'
import type { LabStudy } from './labStudyApi'

const DASH = '—'

function fixed(raw: unknown, digits = 2): string {
  return typeof raw === 'number' && Number.isFinite(raw) ? raw.toFixed(digits) : DASH
}

function signedPct(raw: unknown): string {
  if (typeof raw !== 'number' || !Number.isFinite(raw)) return DASH
  return `${raw >= 0 ? '+' : ''}${raw.toFixed(2)}%`
}

function foldWindow(row: Record<string, unknown>): string {
  const start = row.test_start ?? row.start
  const end = row.test_end ?? row.end
  return start == null || end == null ? DASH : `${String(start).slice(0, 10)} → ${String(end).slice(0, 10)}`
}

export function LabDiagnosticsTab({
  analysis,
  study,
  viewMode,
}: {
  analysis: LabAnalysis | null
  study: LabStudy | null
  viewMode: LabViewMode
}) {
  const measurements = analysis?.measurements ?? null
  const folds = study?.result.folds ?? []
  const proof = study?.result.proof ?? null
  const datasets = analysis?.datasets ?? []
  const coinA = analysis?.coin_a.code ?? 'A'
  const coinB = analysis?.coin_b.code ?? 'B'

  const econometrics = [
    {
      test: 'Log-Price Cointegration (ADF)',
      reading: measurements?.cointegration ? `stat ${measurements.cointegration.statistic.toFixed(2)}` : DASH,
      detail: measurements?.cointegration
        ? `p = ${measurements.cointegration.p_value.toFixed(4)} · ${measurements.cointegration.passes ? 'Passes' : 'Fails'} (static OLS log-price residual)`
        : 'Unavailable',
    },
    {
      test: 'Log-Price Hedge Slopes',
      reading: measurements?.hedge_ratio
        ? `OLS ${measurements.hedge_ratio.ols.toFixed(3)} · TLS ${measurements.hedge_ratio.tls.toFixed(3)}`
        : DASH,
      detail: measurements?.kalman
        ? `Adaptive Kalman β ${measurements.kalman.beta.toFixed(3)} ± ${measurements.kalman.standard_error.toFixed(3)} (time-varying, not fixed equilibrium)`
        : 'Kalman unavailable',
    },
    {
      test: 'Return-Copula Tail Dependence',
      reading: measurements?.copula
        ? `λL ${measurements.copula.lower_tail.toFixed(2)} · λU ${measurements.copula.upper_tail.toFixed(2)}`
        : DASH,
      detail: measurements?.copula
        ? `${measurements.copula.family} · ${measurements.copula.observations} log returns (distinct from traded spread conditional rank)`
        : 'Unavailable',
    },
    {
      test: 'Linear Granger Test (Returns)',
      reading: measurements?.granger ? `${coinA}→${coinB} p ${measurements.granger.a_to_b.p_value.toFixed(3)}` : DASH,
      detail: measurements?.granger
        ? `${coinB}→${coinA} p ${measurements.granger.b_to_a.p_value.toFixed(3)} · lag ${measurements.granger.max_lag} (in-sample linear VAR)`
        : 'Unavailable',
    },
  ]

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <section className="min-w-0 space-y-2.5" aria-label="Econometric and dependence tests">
        <h3 className="m-0 text-sm font-semibold text-foreground">
          Econometric &amp; dependence tests
        </h3>
        {viewMode === 'simple' && (
          <p className="m-0 text-xs text-muted-foreground">
            Pro mode adds strategy controls and a signal chart. These tables stay available in either mode.
          </p>
        )}
        <div className="overflow-hidden rounded-lg border border-border">
          <Table>
            <TableHeader className="bg-muted/60">
              <TableRow>
                <TableHead className="h-9 text-xs">Test</TableHead>
                <TableHead className="h-9 text-xs">Reading</TableHead>
                <TableHead className="h-9 text-xs">Detail</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {econometrics.map((row) => (
                <TableRow key={row.test}>
                  <TableCell className="text-xs font-medium">{row.test}</TableCell>
                  <TableCell className="font-mono text-xs tabular-nums">{row.reading}</TableCell>
                  <TableCell className="text-xs text-muted-foreground">{row.detail}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </section>

      <section className="min-w-0 space-y-3" aria-label="Walk-forward folds and audit provenance">
        <h3 className="m-0 text-sm font-semibold text-foreground">
          Walk-forward folds &amp; audit provenance
        </h3>
        {folds.length === 0 ? (
          <p className="m-0 text-xs text-muted-foreground">
            Run a strategy test to inspect validation folds and SPA p-values.
          </p>
        ) : (
          <div className="overflow-hidden rounded-lg border border-border">
            <Table>
              <TableHeader className="bg-muted/60">
                <TableRow>
                  <TableHead className="h-9 text-xs">Fold</TableHead>
                  <TableHead className="h-9 text-xs">Test window</TableHead>
                  <TableHead className="h-9 text-right text-xs">Strategy return</TableHead>
                  <TableHead className="h-9 text-right text-xs">Control return</TableHead>
                  <TableHead className="h-9 text-xs">Passed</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {folds.map((fold, index) => (
                  <TableRow key={index}>
                    <TableCell className="font-mono text-xs tabular-nums">
                      {String(fold.fold ?? index + 1)}
                    </TableCell>
                    <TableCell className="font-mono text-xs tabular-nums">{foldWindow(fold)}</TableCell>
                    <TableCell className="text-right font-mono text-xs tabular-nums">
                      {signedPct(fold.strategy_return_pct)}
                    </TableCell>
                    <TableCell className="text-right font-mono text-xs tabular-nums">
                      {signedPct(fold.control_return_pct)}
                    </TableCell>
                    <TableCell>
                      {fold.passes === true ? (
                        <DetailTag tone="positive">Yes</DetailTag>
                      ) : fold.passes === false ? (
                        <DetailTag tone="negative">No</DetailTag>
                      ) : (
                        DASH
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}

        {proof && (
          <div className="space-y-2">
            <dl className="m-0 grid grid-cols-3 gap-2.5" aria-label="SPA significance">
              <div className="rounded-lg border border-border bg-muted/35 px-3 py-2">
                <dt className="text-[11px] text-muted-foreground">SPA raw p</dt>
                <dd className="m-0 mt-0.5 font-mono text-xs font-semibold text-foreground tabular-nums">
                  {fixed(proof.raw_p_value, 4)}
                </dd>
              </div>
              <div className="rounded-lg border border-border bg-muted/35 px-3 py-2">
                <dt className="text-[11px] text-muted-foreground">SPA corrected p</dt>
                <dd className="m-0 mt-0.5 font-mono text-xs font-semibold text-foreground tabular-nums">
                  {fixed(proof.corrected_p_value, 4)}
                </dd>
              </div>
              <div className="rounded-lg border border-border bg-muted/35 px-3 py-2">
                <dt className="text-[11px] text-muted-foreground">Settings tried</dt>
                <dd className="m-0 mt-0.5 font-mono text-xs font-semibold text-foreground tabular-nums">
                  {proof.settings_tried.toLocaleString('en-US')}
                </dd>
              </div>
            </dl>
            <p className="m-0 text-[11px] text-muted-foreground">
              Protocol: {proof.proof_protocol ?? 'legacy v1 (499 SPA reps)'} · Signal:{' '}
              {proof.signal_provenance === 'walk_forward_stitched'
                ? 'Walk-forward stitched'
                : 'Legacy (missing stitched provenance)'}
            </p>
          </div>
        )}

        <h4 className="m-0 pt-1 text-xs font-semibold text-muted-foreground">Dataset SHA-256</h4>
        {datasets.length === 0 ? (
          <p className="m-0 text-xs text-muted-foreground">No dataset loaded.</p>
        ) : (
          <div className="overflow-hidden rounded-lg border border-border">
            <Table>
              <TableHeader className="bg-muted/60">
                <TableRow>
                  <TableHead className="h-9 text-xs">Market</TableHead>
                  <TableHead className="h-9 text-xs">Interval</TableHead>
                  <TableHead className="h-9 text-xs">SHA-256</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {datasets.map((dataset) => (
                  <TableRow key={dataset.dataset_id}>
                    <TableCell className="text-xs font-medium">{dataset.venue_symbol}</TableCell>
                    <TableCell className="font-mono text-xs">{dataset.interval}</TableCell>
                    <TableCell className="break-all font-mono text-[11px] text-muted-foreground">
                      {dataset.semantic_fingerprint}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </section>
    </div>
  )
}
