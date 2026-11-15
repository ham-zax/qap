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

  return (
    <section className="lab-card lab-paper-panel" aria-label="Live L2 paper monitor">
      <div className="lab-card-header">
        <h3>Live L2 Paper</h3>
        {session && (
          <span className={session.status === 'active' ? 'lab-chip lab-chip-live' : 'lab-chip'}>
            {session.status === 'active' ? 'Active' : 'Stopped'}
          </span>
        )}
      </div>

      {error && <p className="lab-warning-banner" role="alert">{error}</p>}

      {!session ? (
        <>
          <p className="lab-note">
            Stream live Binance depth20 books and replay swaps with realistic orderbook sweep and RTT drift.
          </p>
          <button
            type="button"
            className="lab-primary"
            disabled={!canStart || busy}
            onClick={onStart}
          >
            {busy ? 'Starting…' : 'Start Live Paper'}
          </button>
        </>
      ) : (
        <>
          <p className="lab-paper-status">{session.simple_status}</p>
          <dl className="lab-kv-list">
            <div>
              <dt>vs HODL</dt>
              <dd className={session.vs_hodl_pct >= 0 ? 'lab-proof-better' : 'lab-proof-worse'}>
                {pct(session.vs_hodl_pct)}
              </dd>
            </div>
            <div>
              <dt>vs Control</dt>
              <dd className={session.vs_control_pct >= 0 ? 'lab-proof-better' : 'lab-proof-worse'}>
                {pct(session.vs_control_pct)}
              </dd>
            </div>
            <div>
              <dt>Strategy Value</dt>
              <dd>{Number(session.portfolios.strategy.value_usdt).toFixed(2)} USDT</dd>
            </div>
            <div>
              <dt>Decisions / Swaps</dt>
              <dd>{session.decisions_count} / {session.trades.length}</dd>
            </div>
          </dl>

          <div className="lab-latency-box" aria-label="Four-clock execution latencies">
            <span className="lab-field-label">4-Clock Latency (ms)</span>
            {latestLatency ? (
              <dl className="lab-kv-list">
                <div>
                  <dt>{latestLatency.t_exch_us != null ? 't_exch → t_recv' : 'Book age L1'}</dt>
                  <dd>
                    {latestLatency.t_exch_us != null
                      ? `${Math.max(0, latestLatency.t_recv_ns / 1e6 - latestLatency.t_exch_us / 1e3).toFixed(1)} ms`
                      : latestLatency.book_age_leg1_ms != null
                        ? `${latestLatency.book_age_leg1_ms.toFixed(1)} ms`
                        : '—'}
                  </dd>
                </div>
                <div>
                  <dt>t_recv → t_decide</dt>
                  <dd>{latestLatency.recv_to_decide_ms.toFixed(2)} ms</dd>
                </div>
                <div>
                  <dt>t_decide → t_fill L1</dt>
                  <dd>{latestLatency.decide_to_fill_leg1_ms.toFixed(1)} ms</dd>
                </div>
                <div>
                  <dt>t_decide → t_fill L2</dt>
                  <dd>{latestLatency.decide_to_fill_leg2_ms.toFixed(1)} ms</dd>
                </div>
              </dl>
            ) : (
              <p className="lab-note">
                Configured RTT {session.order_rtt_ms} ms (max book age {session.max_staleness_ms} ms). Step to sample live books.
              </p>
            )}
          </div>

          <div className="lab-paper-actions">
            {session.status === 'active' ? (
              <>
                <button type="button" disabled={busy} onClick={onStep}>
                  {busy ? 'Stepping…' : 'Step 3s'}
                </button>
                <button type="button" disabled={busy} onClick={onStop}>
                  Stop Session
                </button>
              </>
            ) : (
              <button type="button" className="lab-primary" disabled={!canStart || busy} onClick={onStart}>
                {busy ? 'Starting…' : 'Start Live Paper'}
              </button>
            )}
          </div>
        </>
      )}
    </section>
  )
}
