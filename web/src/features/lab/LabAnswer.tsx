import type { LabProgress } from './labContract'
import type { LabStudy } from './labStudyApi'
import { formatUsdt } from './labReadout'
import './LabAnswer.css'

export type LabAnswerResult = Pick<LabStudy['result'], 'call' | 'proof'> & Partial<Pick<LabStudy['result'], 'wealth'>> & {
  analysis: Pick<LabStudy['result']['analysis'], 'coin_a' | 'coin_b'>
}

interface LabAnswerProps {
  result: LabAnswerResult | null
  progress: LabProgress | null
  error: string | null
  onRetry: () => void
  saved?: boolean
}

type Call = LabAnswerResult['call']
type Proof = LabAnswerResult['proof']

const STATUS_LABELS: Record<Call['status'], string> = {
  into_a: 'Swapping result',
  into_b: 'Swapping result',
  hold: 'Hold',
  no_edge: 'No reliable edge',
  identity_unresolved: 'Identity unresolved',
  execution_data_missing: 'Execution data missing',
  cost_data_missing: 'Costs unknown',
  cost_budget_failed: 'Costs eat the edge',
  insufficient_history: 'Not enough history',
}

const CONTROL_LABELS: Record<string, string> = {
  daily: 'Rebalance daily',
  weekly: 'Rebalance weekly',
  drift: 'Rebalance at 5% drift',
}

function isEligible(status: Call['status']): boolean {
  return status === 'hold' || status === 'into_a' || status === 'into_b'
}

function formatWeight(value: string | null): string | null {
  if (value === null || value.trim() === '') return null
  const weight = Number(value)
  if (!Number.isFinite(weight)) return null
  return `${(weight * 100).toFixed(1)}%`
}

function formatPercent(value: number | null): string {
  if (value === null || !Number.isFinite(value)) return 'Not available'
  return `${value.toLocaleString('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
    signDisplay: 'exceptZero',
  })}%`
}

function formatStat(value: number | null): string {
  if (value === null || !Number.isFinite(value)) return 'Not available'
  return value.toLocaleString('en-US', { maximumSignificantDigits: 4 })
}

function formatCount(value: number): string {
  return Number.isFinite(value) ? value.toLocaleString('en-US') : 'Not available'
}

function formatUtc(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return 'Not available'
  return `${date.toISOString().slice(0, 16).replace('T', ' ')} UTC`
}

function outcomeTone(value: number | null): string {
  if (value === null || !Number.isFinite(value) || value === 0) return ''
  return value > 0 ? 'lab-proof-better' : 'lab-proof-worse'
}

function validationLabel(proof: Proof, status: Call['status']): string {
  if (!proof.passes) return 'Validation does not pass.'
  return isEligible(status) ? 'Validation passes.' : 'Checks pass. Call unavailable.'
}

function CallResult({ result, saved }: { result: LabAnswerResult; saved: boolean }) {
  const { call } = result
  const target = call.status === 'into_a' || call.status === 'into_b'
    ? formatWeight(call.target_weight_a)
    : null
  const tone = isEligible(call.status) ? 'lab-call-status' : 'lab-call-status lab-call-status-blocked'
  const terminal = result.wealth?.terminal_values
  const money = (key: string) => {
    const raw = terminal?.[key]
    if (raw == null || raw.trim() === '') return null
    const value = Number(raw)
    return Number.isFinite(value) ? formatUsdt(value) : null
  }
  const rotating = money('strategy')
  const holding = money('hodl')
  return <>
    {(rotating || holding) && <p>{rotating && `Rotating ended with ${rotating}.`}{rotating && holding && ' '}{holding && `Just holding ended with ${holding}.`}</p>}
    <div className="lab-call-meta">
      <p className={tone}>{STATUS_LABELS[call.status]}</p>
      {saved && <p className="lab-call-saved">Saved result</p>}
    </div>
    <h2 className="lab-call-headline">{call.headline}</h2>
    <p className="lab-call-reason">{call.reason}</p>
    {target !== null && <p className="lab-call-target">Target {result.analysis.coin_a.code}: <span className="lab-value">{target}</span></p>}
  </>
}

function ProofBody({ result }: { result: LabAnswerResult }) {
  const { proof } = result
  const control = proof.control === null ? 'Selected control' : CONTROL_LABELS[proof.control] ?? 'Selected control'
  const blocked = proof.passes && !isEligible(result.call.status)
  const rows: Array<[string, string]> = [
    ['Folds passing', `${formatCount(proof.folds_passing)} of ${formatCount(proof.folds_total)}`],
    ['Required minimum folds', formatCount(proof.minimum_passing_folds)],
    ['Validation rotations', formatCount(proof.validation_trades)],
    ['Required minimum rotations', formatCount(proof.minimum_trades)],
    ['Settings tried', formatCount(proof.settings_tried)],
    ['Corrected p-value', formatStat(proof.corrected_p_value)],
  ]
  if (proof.gross_vs_hodl_pct !== null && Number.isFinite(proof.gross_vs_hodl_pct)) {
    rows.push(['Before costs vs holding', formatPercent(proof.gross_vs_hodl_pct)])
  }
  if (proof.cost_paid_pct !== null && Number.isFinite(proof.cost_paid_pct)) {
    rows.push(['Costs paid', `${proof.cost_paid_pct.toFixed(2)}%`])
  }
  if (proof.raw_p_value !== null && Number.isFinite(proof.raw_p_value)) {
    rows.push(['Raw p-value', formatStat(proof.raw_p_value)])
  }
  rows.push(
    ['Significance level', formatStat(proof.significance)],
    ['Tuning start', formatUtc(proof.tuning_start)],
    ['Tuning end', formatUtc(proof.tuning_end)],
    ['Validation start', formatUtc(proof.proof_start)],
    ['Validation end', formatUtc(proof.proof_end)],
  )
  return <>
    <p className="lab-proof-scope">Validation only. This is not untouched final data.</p>
    <p className={`lab-proof-validation ${blocked ? 'lab-proof-validation-blocked' : proof.passes ? 'lab-proof-validation-pass' : 'lab-proof-validation-fail'}`}>
      {validationLabel(proof, result.call.status)}
    </p>
    {proof.validation_reused && <>
      <p className="lab-proof-reused">Validation data reused.</p>
      <p className="lab-proof-scope">An earlier study on this pair used overlapping validation data.</p>
    </>}
    <dl className="lab-proof-benchmarks">
      <div><dt>vs Just holding</dt><dd className={outcomeTone(proof.vs_hodl_pct)}>{formatPercent(proof.vs_hodl_pct)}</dd></div>
      <div><dt>vs {control}</dt><dd className={outcomeTone(proof.vs_control_pct)}>{formatPercent(proof.vs_control_pct)}</dd></div>
    </dl>
    <details className="lab-proof-details">
      <summary>How we checked this</summary>
      <p>Walk-forward checks use later periods after choosing settings on earlier periods.</p>
      <p>Folds are the separate periods used for these checks.</p>
      <p>Settings tried are the different choices tested.</p>
      <p>The corrected p-value accounts for the settings tested when measuring how surprising the result is.</p>
      <dl>{rows.map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}</dl>
      <p>{proof.correction}</p>
      {proof.limitations.length > 0 && <>
        <p className="lab-proof-limit-label">Limitations</p>
        <ul>{proof.limitations.map((limitation, index) => <li key={`${index}-${limitation}`}>{limitation}</li>)}</ul>
      </>}
    </details>
  </>
}

export function LabAnswer({ result, progress, error, onRetry, saved = false }: LabAnswerProps) {
  const current = error === null && progress === null ? result : null
  return <div className="lab-answer-grid">
    <section className="lab-answer lab-call-answer" aria-label="Rotation call">
      {error !== null ? <>
        <h2>Analysis unavailable</h2>
        <p role="alert">{error}</p>
        <button type="button" className="lab-answer-retry" onClick={onRetry}>Retry analysis</button>
      </> : progress !== null ? <>
        <h2>Updating analysis</h2>
        <p>{progress.stage}</p>
        <progress aria-label="Analysis progress" />
      </> : current !== null ? <CallResult result={current} saved={saved} /> : <>
        <h2>Choose two coins to begin.</h2>
      </>}
    </section>
    <section className="lab-answer lab-proof-answer" aria-label="After-cost proof">
      <h2>After-cost proof</h2>
      {current !== null ? <ProofBody result={current} /> : <p>Proof unavailable.</p>}
    </section>
  </div>
}
