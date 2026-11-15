import { fireEvent, render, screen, within } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { LabAnswer, type LabAnswerResult } from './LabAnswer'

type Call = LabAnswerResult['call']
type Proof = LabAnswerResult['proof']

function callFixture(overrides: Partial<Call> = {}): Call {
  return {
    headline: 'Rotate into BTC',
    reason: 'The ratio is stretched and the validation window agrees.',
    rotation_fraction: '0.25',
    status: 'into_a',
    target_weight_a: '0.625',
    ...overrides,
  }
}

function proofFixture(overrides: Partial<Proof> = {}): Proof {
  return {
    control: 'weekly',
    corrected_p_value: 0.0123,
    cost_paid_pct: null,
    gross_vs_hodl_pct: null,
    cost_gate_passed: null,
    tuning_cost_pct: null,
    tuning_gross_vs_hodl_pct: null,
    correction: 'Benjamini-Hochberg correction across every setting tried.',
    data_role: 'validation',
    final_oos_used: false,
    folds_passing: 4,
    folds_total: 5,
    limitations: ['Average-price approximation.', 'Validation reuses tuning history.'],
    minimum_passing_folds: 4,
    minimum_trades: 30,
    passes: true,
    proof_end: '2025-07-01T00:00:00Z',
    proof_start: '2025-04-02T00:00:00Z',
    raw_p_value: 0.02,
    settings_tried: 12,
    significance: 0.05,
    tuning_end: '2025-04-01T00:00:00Z',
    tuning_start: '2025-01-01T00:00:00Z',
    validation_reused: false,
    validation_trades: 120,
    vs_control_pct: 1.234,
    vs_hodl_pct: 2.345,
    ...overrides,
  }
}

function study(overrides: { call?: Partial<Call>; proof?: Partial<Proof> } = {}): LabAnswerResult {
  return {
    analysis: {
      coin_a: { code: 'BTC', id: 'binance:BTC', identity_state: 'resolved', name: 'Bitcoin' },
      coin_b: { code: 'W', id: 'binance:W', identity_state: 'resolved', name: 'Wormhole' },
    },
    call: callFixture(overrides.call),
    proof: proofFixture(overrides.proof),
  }
}

function renderAnswer(options: {
  result?: LabAnswerResult | null
  progress?: { stage: string; completed: number; total: number } | null
  error?: string | null
  saved?: boolean
  onRetry?: () => void
} = {}) {
  return render(
    <LabAnswer
      result={options.result ?? null}
      progress={options.progress ?? null}
      error={options.error ?? null}
      onRetry={options.onRetry ?? (() => {})}
      saved={options.saved}
    />,
  )
}

const statusLabels: Array<[Call['status'], string]> = [
  ['into_a', 'Swapping result'],
  ['into_b', 'Swapping result'],
  ['hold', 'Hold'],
  ['no_edge', 'No reliable edge'],
  ['identity_unresolved', 'Identity unresolved'],
  ['execution_data_missing', 'Execution data missing'],
  ['cost_data_missing', 'Costs unknown'],
  ['cost_budget_failed', 'Costs eat the edge'],
  ['insufficient_history', 'Not enough history'],
]

describe('LabAnswer', () => {
  it('leads with available final amounts and omits missing amounts', () => {
    const result = study()
    result.wealth = {
      time: [], value: {}, coins_a: {}, coins_b: {},
      terminal_values: { strategy: '10250', hodl: '10100' }, window_kind: 'validation',
    }
    const view = renderAnswer({ result })
    const call = screen.getByRole('region', { name: 'Rotation call' })
    expect(call.firstElementChild).toHaveTextContent('Rotating ended with 10,250.00 USDT. Just holding ended with 10,100.00 USDT.')
    view.unmount()
    result.wealth.terminal_values = { strategy: '10250' }
    renderAnswer({ result })
    expect(screen.getByText('Rotating ended with 10,250.00 USDT.')).toBeVisible()
    expect(screen.queryByText(/Just holding ended/)).not.toBeInTheDocument()
  })

  it.each(statusLabels)('shows the %s call and reason verbatim as %s', (status, label) => {
    const headline = `Backend headline for ${status}`
    const reason = `Backend reason for ${status}`
    renderAnswer({ result: study({ call: { status, headline, reason } }) })

    expect(screen.getByRole('heading', { level: 2, name: headline })).toBeVisible()
    expect(screen.getByText(reason)).toBeVisible()
    expect(screen.getByText(label)).toBeVisible()
  })

  it('never turns attractive benchmark outcomes into a rotation for a no-edge call', () => {
    renderAnswer({
      result: study({
        call: {
          status: 'no_edge',
          headline: 'No reliable edge right now.',
          reason: 'Holding is as good as rotating.',
          target_weight_a: null,
          rotation_fraction: '0.6',
        },
        proof: { passes: true, vs_hodl_pct: 9.99, vs_control_pct: 7.5 },
      }),
    })

    expect(screen.getByRole('heading', { name: 'No reliable edge right now.' })).toBeVisible()
    expect(screen.getByText('No reliable edge')).toBeVisible()
    expect(screen.getByText('Checks pass. Call unavailable.')).toBeVisible()
    expect(screen.queryByText('Swapping result')).not.toBeInTheDocument()
    expect(screen.queryByText(/^Target /)).not.toBeInTheDocument()
    expect(screen.queryByText('60.0%')).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /trade|rotate|execute/i })).not.toBeInTheDocument()
  })

  it('keeps an unresolved identity blocked even when the proof passes', () => {
    renderAnswer({
      result: study({
        call: { status: 'identity_unresolved', headline: 'Identity unresolved.', reason: 'No economic call while the coin identity is unresolved.' },
        proof: { passes: true, vs_hodl_pct: 4.5 },
      }),
    })

    expect(screen.getByText('Checks pass. Call unavailable.')).toHaveClass('lab-proof-validation-blocked')
    expect(screen.queryByText('Validation passes.')).not.toBeInTheDocument()
  })

  it('reports validation outcome separately from call eligibility', () => {
    const first = renderAnswer({ result: study({ call: { status: 'hold' }, proof: { passes: true } }) })
    expect(screen.getByText('Validation passes.')).toBeVisible()
    first.unmount()

    renderAnswer({ result: study({ call: { status: 'hold' }, proof: { passes: false } }) })
    expect(screen.getByText('Validation does not pass.')).toBeVisible()
  })

  it('formats the target weight once, and never promotes rotation_fraction to a size', () => {
    const first = renderAnswer({ result: study({ call: { status: 'into_a', target_weight_a: '0.625' } }) })
    const call = screen.getByRole('region', { name: 'Rotation call' })
    expect(call).toHaveTextContent('Target BTC: 62.5%')
    expect(within(call).getByText('62.5%')).toHaveClass('lab-value')
    expect(screen.queryByText('25.0%')).not.toBeInTheDocument()
    expect(screen.queryByText('0.25')).not.toBeInTheDocument()
    first.unmount()

    renderAnswer({ result: study({ call: { status: 'into_a', target_weight_a: null } }) })
    expect(screen.queryByText(/^Target /)).not.toBeInTheDocument()
    expect(screen.queryByText('0.0%')).not.toBeInTheDocument()
  })

  it('keeps zero as a real target and handles full allocation', () => {
    const first = renderAnswer({ result: study({ call: { status: 'into_b', target_weight_a: '0' } }) })
    expect(screen.getByText('0.0%')).toBeVisible()
    first.unmount()

    renderAnswer({ result: study({ call: { status: 'into_a', target_weight_a: '1' } }) })
    expect(screen.getByText('100.0%')).toBeVisible()
  })

  it('renders backend percent units once, with signs, semantic tone and honest gaps', () => {
    const first = renderAnswer({ result: study({ proof: { vs_hodl_pct: 1.23, vs_control_pct: -0.45 } }) })
    const proof = screen.getByRole('region', { name: 'After-cost proof' })
    expect(within(proof).getByText('+1.23%')).toHaveClass('lab-proof-better')
    expect(within(proof).getByText('-0.45%')).toHaveClass('lab-proof-worse')
    expect(within(proof).queryByText('123.00%')).not.toBeInTheDocument()
    expect(within(proof).queryByText('-45.00%')).not.toBeInTheDocument()
    first.unmount()

    renderAnswer({ result: study({ proof: { vs_hodl_pct: 0, vs_control_pct: null } }) })
    const secondProof = screen.getByRole('region', { name: 'After-cost proof' })
    expect(within(secondProof).getByText('0.00%')).toBeVisible()
    expect(within(secondProof).getByText('Not available')).toBeVisible()
  })

  it('uses the supplied control label and falls back for an unknown control', () => {
    const first = renderAnswer({ result: study({ proof: { control: 'daily' } }) })
    expect(screen.getByText('vs Rebalance daily')).toBeVisible()
    first.unmount()

    renderAnswer({ result: study({ proof: { control: null } }) })
    expect(screen.getByText('vs Selected control')).toBeVisible()
  })

  it.each([true, false])('explains validation reuse only when validation_reused is %s', (reused) => {
    renderAnswer({ result: study({ proof: { validation_reused: reused } }) })
    const proof = within(screen.getByRole('region', { name: 'After-cost proof' }))
    const explanation = proof.queryByText('An earlier study on this pair used overlapping validation data.')
    if (reused) expect(explanation).toBeVisible()
    else expect(explanation).not.toBeInTheDocument()
  })

  it('keeps counts, periods, correction and limitations inside native How we checked this', () => {
    renderAnswer({ result: study({ proof: { validation_reused: true } }) })
    expect(screen.getByText('Validation data reused.')).toBeVisible()

    const details = screen.getByText('How we checked this').closest('details')
    if (!details) throw new Error('How we checked this must be a native details element')
    expect(details.tagName).toBe('DETAILS')
    expect(within(details).getByText('4 of 5')).toBeInTheDocument()
    expect(within(details).getByText('Required minimum folds').nextElementSibling).toHaveTextContent('4')
    expect(within(details).getByText('Validation rotations').nextElementSibling).toHaveTextContent('120')
    expect(within(details).getByText('Required minimum rotations').nextElementSibling).toHaveTextContent('30')
    expect(within(details).getByText('Settings tried').nextElementSibling).toHaveTextContent('12')
    expect(within(details).getByText('Corrected p-value').nextElementSibling).toHaveTextContent('0.0123')
    expect(within(details).getByText('Raw p-value').nextElementSibling).toHaveTextContent('0.02')
    expect(within(details).getByText('Significance level').nextElementSibling).toHaveTextContent('0.05')
    expect(within(details).getByText('2025-01-01 00:00 UTC')).toBeInTheDocument()
    expect(within(details).getByText('2025-04-01 00:00 UTC')).toBeInTheDocument()
    expect(within(details).getByText('2025-04-02 00:00 UTC')).toBeInTheDocument()
    expect(within(details).getByText('2025-07-01 00:00 UTC')).toBeInTheDocument()
    expect(within(details).getByText('Benjamini-Hochberg correction across every setting tried.')).toBeInTheDocument()
    expect(within(details).getByText('Average-price approximation.')).toBeInTheDocument()
    expect(within(details).getByText('Validation reuses tuning history.')).toBeInTheDocument()
    expect(within(details).queryByText('+2.35%')).not.toBeInTheDocument()
  })

  it('shows an indeterminate progress state and suppresses a stale result', () => {
    renderAnswer({
      result: study(),
      progress: { stage: 'Loading validated window', completed: 8, total: 8 },
    })

    expect(screen.getByRole('heading', { name: 'Updating analysis' })).toBeVisible()
    expect(screen.getByText('Loading validated window')).toBeVisible()
    const bar = screen.getByRole('progressbar', { name: 'Analysis progress' })
    expect(bar).not.toHaveAttribute('value')
    expect(screen.queryByText('Rotate into BTC')).not.toBeInTheDocument()
    expect(screen.queryByText('+2.35%')).not.toBeInTheDocument()
    expect(screen.queryByText('How we checked this')).not.toBeInTheDocument()
    expect(screen.getByText('Proof unavailable.')).toBeVisible()
  })

  it('shows the error, hides a stale result and retries', () => {
    const onRetry = vi.fn()
    renderAnswer({ result: study(), error: 'The study request failed.', onRetry })

    expect(screen.getByRole('heading', { name: 'Analysis unavailable' })).toBeVisible()
    expect(screen.getByRole('alert')).toHaveTextContent('The study request failed.')
    expect(screen.queryByText('Rotate into BTC')).not.toBeInTheDocument()
    expect(screen.queryByText('+2.35%')).not.toBeInTheDocument()
    expect(screen.getByText('Proof unavailable.')).toBeVisible()
    fireEvent.click(screen.getByRole('button', { name: 'Retry analysis' }))
    expect(onRetry).toHaveBeenCalledTimes(1)
  })

  it('starts empty in the final two-region shape', () => {
    renderAnswer()

    expect(screen.getByRole('region', { name: 'Rotation call' })).toBeVisible()
    expect(screen.getByRole('region', { name: 'After-cost proof' })).toBeVisible()
    expect(screen.getByRole('heading', { name: 'Choose two coins to begin.' })).toBeVisible()
    expect(screen.getByText('Proof unavailable.')).toBeVisible()
  })

  it('shows Saved result once for a saved result only', () => {
    const first = renderAnswer({ result: study(), saved: true })
    expect(screen.getAllByText('Saved result')).toHaveLength(1)
    first.unmount()

    renderAnswer({ result: study() })
    expect(screen.queryByText('Saved result')).not.toBeInTheDocument()
  })

  it('shows before-costs edge and costs paid when provided', () => {
    renderAnswer({
      result: study({
        call: { status: 'cost_budget_failed', headline: 'Costs eat the edge' },
        proof: { gross_vs_hodl_pct: 0.86, cost_paid_pct: 5.09 },
      }),
    })

    expect(screen.getByText('Before costs vs holding')).toBeInTheDocument()
    expect(screen.getByText('+0.86%')).toBeInTheDocument()
    expect(screen.getByText('Costs paid')).toBeInTheDocument()
    expect(screen.getByText('5.09%')).toBeInTheDocument()
  })
})
