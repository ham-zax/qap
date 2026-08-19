import type { ResearchIdeaLongitudinalDto } from '../../api/types'
import { Badge, type BadgeTone } from '../../components/ui/Badge'
import { formatResearchTimestamp } from '../../lib/format'

interface ResearchIdeaEvidenceLayersProps {
  data: ResearchIdeaLongitudinalDto
}

type Presentation = {
  label: string
  description: string
  tone: BadgeTone
}

function historicalReplayPresentation(
  state: ResearchIdeaLongitudinalDto['historical_replay_state'],
): Presentation {
  if (state === 'supported') {
    return {
      label: 'Historical implementation supported',
      description:
        'The exact historical implementation passed its declared QAP, HODL, and primary-control checks. This does not establish later persistence or current capacity.',
      tone: 'positive',
    }
  }
  if (state === 'not_supported') {
    return {
      label: 'Historical implementation not supported',
      description:
        'The historical evaluation completed, but this implementation did not pass its declared economic checks.',
      tone: 'warning',
    }
  }
  if (state === 'unavailable') {
    return {
      label: 'Historical economic evidence unavailable',
      description:
        'The required historical replay evidence could not be completed, so QAP does not claim an economic result.',
      tone: 'negative',
    }
  }
  return {
    label: 'Historical replay not completed',
    description:
      'The historical rule exists, but no completed economic replay verdict is attached to it.',
    tone: 'neutral',
  }
}

function laterPresentation(
  state: ResearchIdeaLongitudinalDto['later_state'],
): Presentation {
  if (state === 'not_started') {
    return {
      label: 'Follow-up not started',
      description:
        'No prospective evidence stream has been frozen for this historical Research Idea yet.',
      tone: 'neutral',
    }
  }
  if (state === 'waiting_for_later_evidence') {
    return {
      label: 'Waiting for genuinely later evidence',
      description:
        'Follow-up exists, but no later checkpoint has produced an evaluated prospective result yet.',
      tone: 'info',
    }
  }
  if (state === 'later_evidence_accumulating') {
    return {
      label: 'Later evidence accumulating',
      description:
        'A prospective checkpoint has been evaluated, but the predefined forward window has not matured. This is not a final later-evidence verdict.',
      tone: 'info',
    }
  }
  if (state === 'later_evidence_supported') {
    return {
      label: 'Later evidence supported the idea',
      description:
        'The matured prospective evidence passed the declared baseline and adverse economic gates. The earlier historical evidence remains a separate claim.',
      tone: 'positive',
    }
  }
  if (state === 'later_evidence_not_supported') {
    return {
      label: 'Later evidence did not support the idea',
      description:
        'The matured prospective evidence did not pass the declared later-evidence checks. This does not retroactively invalidate the historical result.',
      tone: 'warning',
    }
  }
  return {
    label: 'Later evidence unavailable',
    description:
      'The prospective evaluation could not produce the required later evidence. The historical result remains preserved separately.',
    tone: 'negative',
  }
}

function currentAssessmentPresentation(
  state: ResearchIdeaLongitudinalDto['current_assessments'][number]['state'],
): { label: string; tone: BadgeTone } {
  if (state === 'tradable_now') {
    return {
      label: 'Current research evidence supports this hypothetical amount',
      tone: 'positive',
    }
  }
  if (state === 'small_capacity') {
    return {
      label: 'A smaller amount is supported by the current evidence',
      tone: 'warning',
    }
  }
  return { label: 'Research only', tone: 'info' }
}

function EvidenceCard({
  eyebrow,
  presentation,
  children,
}: {
  eyebrow: string
  presentation: Presentation
  children?: React.ReactNode
}) {
  return (
    <article className="rounded-lg border border-border bg-panel p-5">
      <p className="m-0 text-xs font-semibold uppercase tracking-[0.08em] text-muted">
        {eyebrow}
      </p>
      <div className="mt-3">
        <Badge tone={presentation.tone}>{presentation.label}</Badge>
      </div>
      <p className="mt-3 mb-0 text-sm leading-6 text-secondary">
        {presentation.description}
      </p>
      {children}
    </article>
  )
}

export function ResearchIdeaEvidenceLayers({ data }: ResearchIdeaEvidenceLayersProps) {
  const historicalReplay = historicalReplayPresentation(data.historical_replay_state)
  const later = laterPresentation(data.later_state)

  return (
    <section className="mt-8" aria-labelledby="evidence-layers-heading">
      <header className="mb-4 max-w-4xl">
        <p className="m-0 text-xs font-semibold uppercase tracking-[0.08em] text-muted">
          Longitudinal evidence
        </p>
        <h2 id="evidence-layers-heading" className="mt-2 mb-2 text-xl font-semibold text-foreground">
          What changed, and what did not
        </h2>
        <p className="m-0 text-sm leading-6 text-secondary">
          Historical, later, and current-capacity evidence answer different questions. A
          weaker later result does not rewrite evidence that was valid at the earlier layer.
        </p>
      </header>

      <div className="grid gap-4 xl:grid-cols-3">
        <EvidenceCard
          eyebrow="Historical discovery"
          presentation={
            data.historical_discovery_state === 'evaluated'
              ? {
                  label: 'Historical rule evaluated',
                  description:
                    'The frozen discovery process retained and evaluated this relationship rule. That alone does not establish causality, profitability, future persistence, or current capacity.',
                  tone: 'info',
                }
              : {
                  label: 'Historical discovery evidence unavailable',
                  description:
                    'The fixed historical rule did not have usable discovery evidence for a normal conclusion.',
                  tone: 'negative',
                }
          }
        />
        <EvidenceCard eyebrow="Historical economic replay" presentation={historicalReplay} />
        <EvidenceCard eyebrow="Later forward evidence" presentation={later}>
          {data.later_reason ? (
            <p className="mt-3 mb-0 text-xs leading-5 text-muted">{data.later_reason}</p>
          ) : null}
        </EvidenceCard>
      </div>

      <section className="mt-5 rounded-lg border border-border bg-panel p-5" aria-labelledby="follow-up-lineage-heading">
        <h3 id="follow-up-lineage-heading" className="mt-0 text-lg font-semibold text-foreground">
          Follow-up lineage
        </h3>
        {data.memberships.length === 0 ? (
          <p className="mb-0 text-sm text-secondary">
            No prospective membership has been recorded for this Research Idea.
          </p>
        ) : (
          <div className="mt-4 space-y-4">
            {data.memberships.map((membership) => (
              <article
                key={`${membership.selection_cohort_id}-${membership.active_freeze_id}`}
                className="rounded-md border border-border bg-canvas/35 p-4"
              >
                <div className="flex flex-wrap gap-2">
                  <Badge tone="info">
                    {membership.membership_kind === 'reselection'
                      ? 'Linked to active follow-up'
                      : 'New frozen follow-up'}
                  </Badge>
                  <Badge tone="neutral">
                    {membership.automatic_selected ? 'Automatic selection' : 'Manual selection'}
                  </Badge>
                </div>
                <p className="mt-3 mb-0 text-sm leading-6 text-secondary">
                  Selected {formatResearchTimestamp(membership.selected_at)} · forward window{' '}
                  {formatResearchTimestamp(membership.forward_start)} →{' '}
                  {formatResearchTimestamp(membership.forward_end)}.
                </p>
                {membership.membership_kind === 'reselection' ? (
                  <p className="mt-2 mb-0 text-sm leading-6 text-secondary">
                    QAP linked this new historical selection to an already-active frozen
                    evidence stream instead of starting an overlapping prospective experiment.
                  </p>
                ) : null}
                <div className="mt-3 flex flex-wrap gap-4 text-sm">
                  <a
                    className="font-semibold text-accent"
                    href={`/prospective/${membership.selection_cohort_id}`}
                  >
                    Selection follow-up
                  </a>
                  {membership.active_cohort_id !== membership.selection_cohort_id ? (
                    <a
                      className="font-semibold text-accent"
                      href={`/prospective/${membership.active_cohort_id}`}
                    >
                      Active evidence stream
                    </a>
                  ) : null}
                </div>
                <details className="mt-3 text-xs text-muted">
                  <summary className="min-h-11 cursor-pointer py-2 font-semibold text-accent">
                    Exact follow-up lineage
                  </summary>
                  <p className="m-0 break-all">Selection cohort: {membership.selection_cohort_id}</p>
                  <p className="mt-1 mb-0 break-all">Active cohort: {membership.active_cohort_id}</p>
                  <p className="mt-1 mb-0 break-all">Active freeze: {membership.active_freeze_id}</p>
                  <p className="mt-1 mb-0 break-all">Active candidate: {membership.active_candidate_id}</p>
                  <p className="mt-1 mb-0">
                    {membership.checkpoints.length} persisted forward checkpoint
                    {membership.checkpoints.length === 1 ? '' : 's'} ·{' '}
                    {membership.assessments.length} persisted capital assessment
                    {membership.assessments.length === 1 ? '' : 's'}
                  </p>
                </details>
              </article>
            ))}
          </div>
        )}
      </section>

      <section className="mt-5 rounded-lg border border-border bg-panel p-5" aria-labelledby="current-assessments-heading">
        <h3 id="current-assessments-heading" className="mt-0 text-lg font-semibold text-foreground">
          Current public-market / capacity evidence
        </h3>
        {data.current_assessments.length === 0 ? (
          <p className="mb-0 text-sm leading-6 text-secondary">
            No persisted current-capital assessment exists for this evidence stream. QAP does
            not infer current readiness from historical or forward evidence.
          </p>
        ) : (
          <div className="mt-4 grid gap-4 lg:grid-cols-2">
            {data.current_assessments.map((assessment) => {
              const presentation = currentAssessmentPresentation(assessment.state)
              return (
                <article
                  key={assessment.qualification_id}
                  className="rounded-md border border-border bg-canvas/35 p-4"
                >
                  <Badge tone={presentation.tone}>{presentation.label}</Badge>
                  <p className="mt-3 mb-0 text-sm text-secondary">
                    As of {formatResearchTimestamp(assessment.as_of)} · hypothetical amount{' '}
                    {assessment.requested_capital}
                  </p>
                  <p className="mt-2 mb-0 text-sm text-secondary">
                    {assessment.reason.replaceAll('_', ' ')}
                  </p>
                  {assessment.state === 'small_capacity' ? (
                    <p className="mt-2 mb-0 text-sm text-secondary">
                      Evidence-supported ceiling:{' '}
                      <strong className="text-foreground">
                        {assessment.candidate_capital_ceiling ?? 'not resolved'}
                      </strong>
                    </p>
                  ) : null}
                  <details className="mt-3 text-xs text-muted">
                    <summary className="min-h-11 cursor-pointer py-2 font-semibold text-accent">
                      Exact assessment lineage
                    </summary>
                    <p className="m-0 break-all">Qualification: {assessment.qualification_id}</p>
                    <p className="mt-1 mb-0 break-all">Checkpoint: {assessment.checkpoint_id}</p>
                    <p className="mt-1 mb-0 break-all">Active cohort: {assessment.active_cohort_id}</p>
                    <p className="mt-1 mb-0 break-all">
                      Exact assessment: {assessment.state} · {assessment.reason}
                    </p>
                  </details>
                </article>
              )
            })}
          </div>
        )}
        <p className="mt-4 mb-0 text-xs leading-5 text-muted">
          These are time-specific research assessments, not continuously current readiness.
          Research assessment only — QAP does not place or authorize live trades.
        </p>
      </section>
    </section>
  )
}
