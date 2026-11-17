import { Activity, AlertTriangle, Play, Square, StepForward } from 'lucide-react'

import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { DetailTag } from '@/components/watermelon/dashboard-card'
import { LiveBadge } from '@/components/watermelon/live-badge'
import type { LivePaperSession } from './labPaperApi'

interface LabLivePaperPanelProps {
  session: LivePaperSession | null
  busy: boolean
  error: string | null
  canStart: boolean
  onStart: () => void
  onStep: () => void
  onStop: () => void
}

function pct(value: number): string {
  if (!Number.isFinite(value)) return '—'
  return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`
}

function fmtDelay(ms: number | null | undefined): string {
  if (ms == null || !Number.isFinite(ms)) return 'No fill'
  return `${ms.toFixed(1)} ms`
}

export function LabLivePaperPanel({
  session,
  busy,
  error,
  canStart,
  onStart,
  onStep,
  onStop,
}: LabLivePaperPanelProps) {
  const latestLatency = session?.latency_audit.at(-1) ?? null
  const isLegacy = session?.can_step === false && session.status === 'active'
  const leg1Delay = latestLatency?.legacy_clock
    ? latestLatency.decide_to_fill_leg1_ms
    : latestLatency?.actual_decide_to_fill_leg1_ms
  const leg2Delay = latestLatency?.legacy_clock
    ? latestLatency.decide_to_fill_leg2_ms
    : latestLatency?.actual_decide_to_fill_leg2_ms

  return (
    <Card role="region" className="shadow-primary gap-3 rounded-xl py-4" aria-label="Live L2 paper monitor">
      <CardHeader className="flex flex-row items-center justify-between gap-2 px-4 pb-0">
        <div className="flex items-center gap-2">
          <Activity className="size-4 text-primary" aria-hidden="true" />
          <CardTitle>
            <h3 className="m-0 text-sm font-semibold text-foreground">Live L2 Paper</h3>
          </CardTitle>
        </div>
        <div className="flex items-center gap-2">
          {session?.track_record_mode === 'catchup_observed' && (
            <Badge variant="outline" className="text-[10px]">
              Catch-up observed
            </Badge>
          )}
          {session && <LiveBadge live={session.status === 'active'} />}
        </div>
      </CardHeader>

      <CardContent className="space-y-3 px-4">
        {error && (
          <Alert variant="destructive">
            <AlertDescription className="text-xs">{error}</AlertDescription>
          </Alert>
        )}

        {!session ? (
          <div className="space-y-3">
            <p className="m-0 max-w-2xl text-xs leading-relaxed text-muted-foreground">
              Stream live Binance depth20 books and replay swaps with realistic orderbook sweep, venue constraints, and completed-candle timing.
            </p>
            <Button type="button" disabled={!canStart || busy} onClick={onStart} className="gap-1.5">
              <Play className="size-3.5" aria-hidden="true" />
              {busy ? 'Starting…' : 'Start Live Paper'}
            </Button>
          </div>
        ) : (
          <div className="space-y-3">
            <p className="m-0 text-xs text-muted-foreground">{session.simple_status}</p>

            {isLegacy && (
              <Alert className="border-warning/45 bg-warning/10 py-2 text-warning">
                <AlertTriangle className="size-4" aria-hidden="true" />
                <AlertDescription className="text-xs text-warning">
                  {session.step_block_reason ?? 'Legacy v1 session uses untimed closes. Start a new session.'}
                </AlertDescription>
              </Alert>
            )}

            {session.pending_target && (
              <Alert className="border-warning/45 bg-warning/10 py-2 text-warning">
                <AlertDescription className="text-xs text-warning">
                  Partial rotation pending retry ({session.pending_target.status}, {session.pending_target.fills_count} fill(s) recorded). Step with fresh books to reconcile remaining inventory.
                </AlertDescription>
              </Alert>
            )}

            <dl className="m-0 grid grid-cols-2 gap-2.5 sm:grid-cols-4">
              <div className="rounded-lg border border-border bg-muted/35 p-2.5">
                <dt className="text-[11px] text-muted-foreground">vs HODL</dt>
                <dd className="m-0 mt-1">
                  <DetailTag tone={session.vs_hodl_pct >= 0 ? 'positive' : 'negative'}>
                    {pct(session.vs_hodl_pct)}
                  </DetailTag>
                </dd>
              </div>
              <div className="rounded-lg border border-border bg-muted/35 p-2.5">
                <dt className="text-[11px] text-muted-foreground">vs Control</dt>
                <dd className="m-0 mt-1">
                  <DetailTag tone={session.vs_control_pct >= 0 ? 'positive' : 'negative'}>
                    {pct(session.vs_control_pct)}
                  </DetailTag>
                </dd>
              </div>
              <div className="rounded-lg border border-border bg-muted/35 p-2.5">
                <dt className="text-[11px] text-muted-foreground">Strategy Value</dt>
                <dd className="m-0 mt-1 font-mono text-sm font-semibold text-foreground tabular-nums">
                  {Number(session.portfolios.strategy.value_usdt).toFixed(2)} USDT
                </dd>
              </div>
              <div className="rounded-lg border border-border bg-muted/35 p-2.5">
                <dt className="text-[11px] text-muted-foreground">Candles / Swaps</dt>
                <dd className="m-0 mt-1 font-mono text-sm font-semibold text-foreground tabular-nums">
                  {session.decisions_count} / {session.trades.length}
                  {session.book_observations_count != null && (
                    <span className="mt-0.5 block text-[10px] font-normal text-muted-foreground">
                      {session.book_observations_count} book checks
                    </span>
                  )}
                </dd>
              </div>
            </dl>

            <div className="rounded-lg border border-border bg-muted/25 p-3" aria-label="Execution latencies">
              <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
                <span className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
                  Configured RTT ({session.order_rtt_ms} ms) vs Measured Simulation Delay
                </span>
                {latestLatency?.legacy_clock && (
                  <Badge variant="outline" className="text-[10px]">
                    Legacy nominal clock
                  </Badge>
                )}
              </div>
              {latestLatency ? (
                <dl className="m-0 grid grid-cols-2 gap-2.5 sm:grid-cols-4">
                  <div>
                    <dt className="text-[11px] text-muted-foreground">
                      {latestLatency.t_exch_us != null ? 't_exch → t_recv' : 'Book age L1'}
                    </dt>
                    <dd className="m-0 mt-0.5 font-mono text-xs font-medium text-foreground tabular-nums">
                      {latestLatency.t_exch_us != null
                        ? `${Math.max(0, latestLatency.t_recv_ns / 1e6 - latestLatency.t_exch_us / 1e3).toFixed(1)} ms`
                        : latestLatency.book_age_leg1_ms != null
                          ? `${latestLatency.book_age_leg1_ms.toFixed(1)} ms`
                          : '—'}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-[11px] text-muted-foreground">t_recv → t_decide</dt>
                    <dd className="m-0 mt-0.5 font-mono text-xs font-medium text-foreground tabular-nums">
                      {latestLatency.recv_to_decide_ms.toFixed(2)} ms
                    </dd>
                  </div>
                  <div>
                    <dt className="text-[11px] text-muted-foreground">Actual delay L1</dt>
                    <dd className="m-0 mt-0.5 font-mono text-xs font-medium text-foreground tabular-nums">
                      {fmtDelay(leg1Delay)}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-[11px] text-muted-foreground">Actual delay L2</dt>
                    <dd className="m-0 mt-0.5 font-mono text-xs font-medium text-foreground tabular-nums">
                      {fmtDelay(leg2Delay)}
                    </dd>
                  </div>
                </dl>
              ) : (
                <p className="m-0 text-xs text-muted-foreground">
                  Configured RTT {session.order_rtt_ms} ms (max book age {session.max_staleness_ms} ms). Step to sample live books.
                </p>
              )}
            </div>

            <div className="flex flex-wrap gap-2">
              {session.status === 'active' ? (
                <>
                  {!isLegacy && (
                    <Button type="button" variant="outline" disabled={busy} onClick={onStep} className="gap-1.5">
                      <StepForward className="size-3.5" aria-hidden="true" />
                      {busy ? 'Stepping…' : session.pending_target ? 'Retry Pending Swap' : 'Step 3s'}
                    </Button>
                  )}
                  <Button type="button" variant="outline" disabled={busy} onClick={onStop} className="gap-1.5">
                    <Square className="size-3.5" aria-hidden="true" />
                    Stop Session
                  </Button>
                  {isLegacy && (
                    <Button type="button" disabled={!canStart || busy} onClick={onStart} className="gap-1.5">
                      <Play className="size-3.5" aria-hidden="true" />
                      Start New Session
                    </Button>
                  )}
                </>
              ) : (
                <Button type="button" disabled={!canStart || busy} onClick={onStart} className="gap-1.5">
                  <Play className="size-3.5" aria-hidden="true" />
                  {busy ? 'Starting…' : 'Start Live Paper'}
                </Button>
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
