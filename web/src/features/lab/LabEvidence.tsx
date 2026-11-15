import { useState } from 'react'
import type { LabAnalysis, LabGrangerDirection, LabViewMode } from './labContract'

const number = (value: number | null | undefined, digits = 3) => value == null ? 'Unavailable' : value.toLocaleString(undefined, { maximumFractionDigits: digits })
const granger = (direction: LabGrangerDirection | undefined) => direction ? `p = ${number(direction.p_value, 4)} at lag ${direction.lag_bars}` : 'Unavailable'

/** One reading: plain label, value, plain meaning, then the technical name and caveat. */
type Reading = { label: string; value: string; meaning: string; term: string }

export function LabEvidence({ analysis, viewMode = 'simple' }: { analysis: LabAnalysis; viewMode?: LabViewMode }) {
  const m = analysis.measurements
  const a = analysis.coin_a.code
  const b = analysis.coin_b.code
  const [hidden, setHidden] = useState<string[]>([])
  // Group titles ask the question each group answers; the reading order inside a group is fixed.
  const groups: Array<[string, Reading[]]> = [
    ['Do they move together?', [
      { label: 'Move together', value: number(m.correlation?.pearson), meaning: '1 means they always move the same way. 0 means no link.', term: 'Pearson correlation of log returns.' },
      { label: 'Move together (ranked)', value: `${number(m.correlation?.spearman)} / ${number(m.correlation?.kendall)}`, meaning: 'The same question, less affected by a few big days.', term: 'Spearman / Kendall rank dependence.' },
      { label: 'Recent togetherness', value: m.rolling_dependence ? `${number(m.rolling_dependence.latest, 2)}, range ${number(m.rolling_dependence.low, 2)} to ${number(m.rolling_dependence.high, 2)}` : 'Unavailable', meaning: `How closely they moved over the last ${m.rolling_dependence?.window_bars ?? analysis.band_lookback} bars, and how much that changed.`, term: 'Rolling return correlation.' },
    ]],
    ['Does the gap snap back?', [
      { label: 'Gap returns to normal', value: m.cointegration ? `p = ${number(m.cointegration.p_value, 5)}` : 'Unavailable', meaning: 'Smaller is stronger evidence that the price gap drifts back. It does not prove profit.', term: 'Engle–Granger cointegration test.' },
      { label: 'Time to close half the gap', value: m.half_life?.bars != null ? `${number(m.half_life.bars, 1)} bars` : 'No measured reversion', meaning: 'How long a stretched gap took, on average, to shrink by half.', term: 'Half-life of the log ratio.' },
      { label: 'Snap-back or drift', value: m.hurst ? number(m.hurst.exponent) : 'Unavailable', meaning: 'Below 0.5 leans snap-back, above 0.5 leans drift. Short windows can mislead.', term: 'Hurst exponent estimate.' },
      { label: 'Where the gap is now', value: `${number(m.ratio_percentile, 1)}%`, meaning: 'Share of this window when the ratio was at or below today. A flat ratio also reads 100%.', term: 'Ratio percentile.' },
      { label: 'Market mood', value: m.regime ? `${m.regime.volatility}, ${m.regime.trend}` : 'Unavailable', meaning: 'How jumpy and how one-directional prices are now, compared with this window.', term: 'Volatility and path-efficiency regime.' },
    ]],
    ['How many coins balance each other?', [
      { label: 'Balance ratio', value: m.hedge_ratio ? `${number(m.hedge_ratio.ols)} / ${number(m.hedge_ratio.tls)}` : 'Unavailable', meaning: `How much ${a} moves for each 1% move in ${b}. Description only.`, term: 'OLS / TLS hedge ratio of log prices.' },
      { label: 'Balance ratio today', value: m.kalman ? `${number(m.kalman.beta)} ± ${number(m.kalman.standard_error)}, moved ${number(m.kalman.beta_change)}` : 'Unavailable', meaning: 'The same ratio, updated bar by bar. A large move means the balance is unstable.', term: 'Kalman filter hedge slope.' },
    ]],
    ['How do they follow the market?', [
      { label: `${a} follows the anchor`, value: m.anchor_a ? `β ${number(m.anchor_a.beta)}, R² ${number(m.anchor_a.r_squared)}` : 'Unavailable', meaning: `β: how far ${a} moves when the anchor moves 1%. R²: how much of its movement that explains, 0 to 1.`, term: 'Anchor regression. Not proof of cause.' },
      { label: `${b} follows the anchor`, value: m.anchor_b ? `β ${number(m.anchor_b.beta)}, R² ${number(m.anchor_b.r_squared)}` : 'Unavailable', meaning: `The same reading for ${b}.`, term: 'Anchor regression. Not proof of cause.' },
    ]],
    ['Who moves first, and do they crash together?', [
      { label: `${a} moves first`, value: granger(m.granger?.a_to_b), meaning: `Small p: past ${a} moves helped guess the next ${b} move. Not a usable head start.`, term: `Granger test, corrected for ${m.granger?.max_lag ?? 4} lags tried.` },
      { label: `${b} moves first`, value: granger(m.granger?.b_to_a), meaning: `Small p: past ${b} moves helped guess the next ${a} move.`, term: 'Granger test, corrected for the lags tried.' },
      { label: 'Crash or jump together', value: m.copula ? `down ${number(m.copula.lower_tail, 2)}, up ${number(m.copula.upper_tail, 2)}` : 'Unavailable', meaning: 'Chance, 0 to 1, that one coin makes an extreme move when the other does.', term: m.copula ? `Copula tail dependence (${m.copula.family} family), fitted on the latest ${m.copula.observations} returns.` : 'Copula tail dependence.' },
    ]],
  ]
  return <aside className="lab-evidence" aria-label="Relationship evidence">
    <h2>Evidence</h2><p className="lab-muted">What past prices show. Not a trading signal. Tap a reading to see what it means.</p>
    <details className="lab-methods"><summary>Choose readings</summary>
      {groups.flatMap(([, rows]) => rows).map(({ label }) => <label key={label}><input type="checkbox" checked={!hidden.includes(label)}
        onChange={() => setHidden((current) => current.includes(label) ? current.filter((item) => item !== label) : [...current, label])} />{label}</label>)}
    </details>
    {groups.map(([title, all]) => {
      const rows = all.filter(({ label }) => !hidden.includes(label))
      return rows.length > 0 && <section key={title} className="lab-evidence-group" aria-label={title}>
        <h3>{title}</h3>
        {rows.map(({ label, value, meaning, term }) => <details key={label} className="lab-reading" open={viewMode === 'advanced'}>
          <summary><span className="lab-reading-label">{label}</span><span className={value === 'Unavailable' ? 'lab-reading-value lab-unavailable' : 'lab-reading-value'}>{value}</span></summary>
          <p>{meaning}</p><p className="lab-note">{term}</p>
        </details>)}
      </section>
    })}
    <p className="lab-note">Unavailable means the data or fit cannot support this reading.</p>
    <details><summary>Limits of these readings</summary><p>Every reading describes this window only. Some fits use the whole window, so they explain the past. They do not prove a future edge. Only the strategy test checks that.</p></details>
  </aside>
}
