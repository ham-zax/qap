import type { LabStudy } from './labStudyApi'

interface LabScorecardProps {
  study: LabStudy | null
}

function money(raw: unknown): string {
  if (typeof raw !== 'string' && typeof raw !== 'number') return '—'
  const val = Number(raw)
  if (!Number.isFinite(val)) return '—'
  return `${val.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} USDT`
}

function pct(raw: unknown): string {
  if (typeof raw !== 'number' || !Number.isFinite(raw)) return '—'
  return `${raw.toFixed(2)}%`
}

export function LabScorecard({ study }: LabScorecardProps) {
  const stats = study?.result.statistics?.strategy as Record<string, unknown> | undefined
  if (!study || !stats) {
    return (
      <section className="lab-card lab-scorecard" aria-label="Backtest scorecard">
        <h3>Backtest Scorecard</h3>
        <p className="lab-note">Run a test to inspect drawdown, swap count, fees, slippage, and ending inventory.</p>
      </section>
    )
  }

  const holdings = (stats.terminal_holdings ?? {}) as Record<string, string>
  const holdingEntries = Object.entries(holdings)

  return (
    <section className="lab-card lab-scorecard" aria-label="Backtest scorecard">
      <h3>Backtest Scorecard</h3>
      <dl className="lab-kv-list">
        <div>
          <dt>Max Drawdown</dt>
          <dd>{pct(stats.maximum_drawdown_pct)}</dd>
        </div>
        <div>
          <dt>Total Swaps</dt>
          <dd>{typeof stats.rotations === 'number' ? stats.rotations.toLocaleString('en-US') : '—'}</dd>
        </div>
        <div>
          <dt>Fees USDT</dt>
          <dd>{money(stats.fees_usdt)}</dd>
        </div>
        <div>
          <dt>Slippage USDT</dt>
          <dd>{money(stats.slippage_usdt)}</dd>
        </div>
      </dl>

      {holdingEntries.length > 0 && (
        <div className="lab-holdings-box">
          <span className="lab-field-label">Ending Coin Holdings</span>
          <dl className="lab-kv-list">
            {holdingEntries.map(([asset, qty]) => (
              <div key={asset}>
                <dt>{asset.replace('binance:', '')}</dt>
                <dd>{Number(qty).toLocaleString('en-US', { maximumSignificantDigits: 6 })}</dd>
              </div>
            ))}
          </dl>
        </div>
      )}
    </section>
  )
}
