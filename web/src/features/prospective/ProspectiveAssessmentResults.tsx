import type { ForwardCohortDetailDto } from '../../api/types'
import { Badge } from '../../components/ui/Badge'
import { formatResearchTimestamp } from '../../lib/format'

interface ProspectiveAssessmentResultsProps {
  qualifications: ForwardCohortDetailDto['qualifications']
}

function assessmentPresentation(state: string): {
  label: string
  tone: 'positive' | 'warning' | 'negative' | 'info'
} {
  if (state === 'tradable_now') {
    return { label: 'Current evidence supports this amount', tone: 'positive' }
  }
  if (state === 'small_capacity') {
    return { label: 'Smaller amount supported', tone: 'warning' }
  }
  if (state === 'research_only') {
    return { label: 'Research only', tone: 'info' }
  }
  return { label: state, tone: 'negative' }
}

export function ProspectiveAssessmentResults({
  qualifications,
}: ProspectiveAssessmentResultsProps) {
  return (
    <section className="mt-8" aria-labelledby="results-heading">
      <h2 id="results-heading" className="text-xl font-semibold text-foreground">
        Current capital assessment results
      </h2>
      {qualifications.length === 0 ? (
        <p className="text-secondary">
          No current capital assessment has been published. Missing current evidence is
          not treated as research support.
        </p>
      ) : (
        <div className="mt-4 grid gap-4 lg:grid-cols-2">
          {qualifications.map((qualification) => {
            const presentation = assessmentPresentation(qualification.state)
            return (
              <article
                key={qualification.qualification_id}
                className="rounded-lg border border-border bg-panel p-5"
              >
                <Badge tone={presentation.tone}>{presentation.label}</Badge>
                <h3 className="mt-4 mb-1 text-base font-semibold text-foreground">
                  {qualification.reason}
                </h3>
                <p className="mt-1 text-sm text-secondary">
                  As of {formatResearchTimestamp(qualification.as_of)} · amount{' '}
                  {qualification.requested_capital}
                </p>
                {qualification.state === 'small_capacity' ? (
                  <p className="text-sm text-secondary">
                    Evidence-supported ceiling:{' '}
                    <strong className="text-foreground">
                      {qualification.candidate_capital_ceiling ?? 'not resolved'}
                    </strong>
                  </p>
                ) : null}
                {qualification.state === 'tradable_now' ? (
                  <p className="mt-4 mb-0 text-xs leading-5 text-muted">
                    Research assessment only — QAP does not place or authorize live trades.
                  </p>
                ) : null}
                <details className="mt-4 rounded-md border border-border bg-canvas/35 p-3">
                  <summary className="cursor-pointer text-sm font-semibold text-secondary">
                    Exact assessment evidence
                  </summary>
                  <dl className="mt-3 grid gap-3 text-sm sm:grid-cols-2">
                    <div>
                      <dt className="text-xs text-muted">Exact state</dt>
                      <dd className="m-0 mt-1 font-mono text-xs text-secondary">
                        {qualification.state}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-xs text-muted">Captured observations</dt>
                      <dd className="m-0 mt-1 text-secondary">
                        {qualification.capture_snapshot_ids.length}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-xs text-muted">Safe buy</dt>
                      <dd className="m-0 mt-1 text-secondary">
                        {qualification.q_safe_buy ?? 'unknown'}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-xs text-muted">Safe sell</dt>
                      <dd className="m-0 mt-1 text-secondary">
                        {qualification.q_safe_sell ?? 'unknown'}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-xs text-muted">Eligibility resolved</dt>
                      <dd className="m-0 mt-1 text-secondary">
                        {String(qualification.eligibility_resolved)}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-xs text-muted">Order constraints</dt>
                      <dd className="m-0 mt-1 text-secondary">
                        {String(qualification.order_constraints_satisfied)}
                      </dd>
                    </div>
                  </dl>
                  <p className="mt-3 mb-0 break-all font-mono text-xs text-muted">
                    checkpoint {qualification.checkpoint_id} · baseline/adverse gates{' '}
                    {String(qualification.requested_baseline_gate_passed ?? '—')}/
                    {String(qualification.requested_adverse_gate_passed ?? '—')}
                  </p>
                  <p className="mt-2 mb-0 break-all font-mono text-xs text-muted">
                    current-state QAP {qualification.current_state_qap_run_id ?? 'none'} ·
                    requested-capital QAP {qualification.requested_capital_qap_run_id ?? 'none'}
                  </p>
                  <p className="mt-2 mb-0 break-all font-mono text-xs text-muted">
                    capture snapshots{' '}
                    {qualification.capture_snapshot_ids.length > 0
                      ? qualification.capture_snapshot_ids.join(', ')
                      : 'none'}
                  </p>
                </details>
              </article>
            )
          })}
        </div>
      )}
    </section>
  )
}
