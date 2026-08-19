import type { HistoryDto, RunSummaryDto } from '../../api/types'
import { Badge, type BadgeTone } from '../../components/ui/Badge'
import { formatResearchTimestamp } from '../../lib/format'
import {
  experimentDataRoleLabel,
  humanizeIdentifier,
  researchStatusPresentation,
} from './presentation'

interface HistoryViewProps {
  history: HistoryDto
}

type Presentation = { label: string; tone: BadgeTone }

type HistoryIdea = HistoryDto['research_generations'][number]['research_ideas'][number]

function shortId(value: string): string {
  if (value.length <= 20) return value
  return `${value.slice(0, 10)}…${value.slice(-6)}`
}

function historicalPresentation(
  state: HistoryIdea['longitudinal']['historical_replay_state'],
): Presentation {
  if (state === 'supported') return { label: 'Historical replay supported', tone: 'positive' }
  if (state === 'not_supported') return { label: 'Historical replay not supported', tone: 'warning' }
  if (state === 'unavailable') return { label: 'Historical replay unavailable', tone: 'negative' }
  return { label: 'Historical replay incomplete', tone: 'neutral' }
}

function laterPresentation(state: HistoryIdea['longitudinal']['later_state']): Presentation {
  if (state === 'later_evidence_supported') {
    return { label: 'Later evidence supported', tone: 'positive' }
  }
  if (state === 'later_evidence_not_supported') {
    return { label: 'Later evidence did not support', tone: 'warning' }
  }
  if (state === 'later_evidence_unavailable') {
    return { label: 'Later evidence unavailable', tone: 'negative' }
  }
  if (state === 'later_evidence_accumulating') {
    return { label: 'Later evidence accumulating', tone: 'info' }
  }
  if (state === 'waiting_for_later_evidence') {
    return { label: 'Waiting for later evidence', tone: 'info' }
  }
  return { label: 'Follow-up not started', tone: 'neutral' }
}

function assessmentPresentation(
  state: NonNullable<HistoryIdea['latest_current_assessment']>['state'],
): Presentation {
  if (state === 'tradable_now') {
    return { label: 'Current amount supported', tone: 'positive' }
  }
  if (state === 'small_capacity') {
    return { label: 'Smaller amount supported', tone: 'warning' }
  }
  return { label: 'Research only', tone: 'info' }
}

function basketPresentation(status: string | null | undefined): Presentation {
  if (status === 'basket_development_survivor') {
    return { label: 'Portfolio gates passed', tone: 'positive' }
  }
  if (status === 'basket_development_rejected') {
    return { label: 'Portfolio gates not passed', tone: 'info' }
  }
  return { label: 'Portfolio research recorded', tone: 'neutral' }
}

function boundaryLabel(kind: string | undefined): string {
  if (kind === 'current_approved_retrospective') return 'Data through'
  if (kind === 'historical_pit') return 'Historical cutoff'
  return 'Data boundary'
}

function ResearchIdeaCard({ idea }: { idea: HistoryIdea }) {
  const historical = historicalPresentation(idea.longitudinal.historical_replay_state)
  const later = laterPresentation(idea.longitudinal.later_state)
  const assessment = idea.latest_current_assessment
  const current = assessment ? assessmentPresentation(assessment.state) : null
  const hasReselection = idea.longitudinal.memberships.some(
    (membership) => membership.membership_kind === 'reselection',
  )

  return (
    <article className="rounded-lg border border-border bg-panel p-5">
      <div className="flex flex-wrap gap-2">
        <Badge tone={historical.tone}>{historical.label}</Badge>
        <Badge tone={later.tone}>{later.label}</Badge>
      </div>
      <h4 className="mt-4 mb-2 text-lg font-semibold text-foreground">
        {idea.candidate.pair_id}
      </h4>
      <p className="m-0 text-sm text-secondary">
        {idea.candidate.venue} · {idea.candidate.horizon} timeframe ·{' '}
        {idea.candidate.resolution}
      </p>

      <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        <div className="rounded-md border border-border bg-canvas/35 p-4">
          <p className="m-0 text-xs font-semibold uppercase tracking-[0.08em] text-muted">
            Later evidence
          </p>
          <p className="mt-2 mb-0 text-sm font-medium text-foreground">{later.label}</p>
          {idea.longitudinal.later_reason ? (
            <p className="mt-2 mb-0 text-xs leading-5 text-secondary">
              {idea.longitudinal.later_reason}
            </p>
          ) : null}
          <p className="mt-2 mb-0 text-xs text-muted">
            {idea.longitudinal.memberships.length} follow-up membership
            {idea.longitudinal.memberships.length === 1 ? '' : 's'}
          </p>
        </div>

        <div className="rounded-md border border-border bg-canvas/35 p-4">
          <p className="m-0 text-xs font-semibold uppercase tracking-[0.08em] text-muted">
            Latest current assessment
          </p>
          {assessment && current ? (
            <>
              <div className="mt-2">
                <Badge tone={current.tone}>{current.label}</Badge>
              </div>
              <p className="mt-2 mb-0 text-xs leading-5 text-secondary">
                As of {formatResearchTimestamp(assessment.as_of)} · hypothetical amount{' '}
                {assessment.requested_capital}
              </p>
            </>
          ) : (
            <p className="mt-2 mb-0 text-sm text-secondary">
              No persisted current-capacity assessment.
            </p>
          )}
        </div>

        <div className="rounded-md border border-border bg-canvas/35 p-4">
          <p className="m-0 text-xs font-semibold uppercase tracking-[0.08em] text-muted">
            Portfolio expression
          </p>
          <p className="mt-2 mb-0 text-sm text-secondary">
            {idea.basket_memberships.length === 0
              ? 'Not used by completed portfolio research.'
              : `${idea.basket_memberships.length} completed portfolio ${idea.basket_memberships.length === 1 ? 'study' : 'studies'}.`}
          </p>
          {idea.basket_memberships.length ? (
            <div className="mt-2 flex flex-wrap gap-3 text-xs">
              {idea.basket_memberships.map((basket) => (
                <a
                  key={basket.basket_id}
                  className="font-semibold text-accent"
                  href={`/baskets/${basket.basket_id}`}
                >
                  Portfolio {shortId(basket.basket_id)}
                </a>
              ))}
            </div>
          ) : null}
        </div>
      </div>

      {hasReselection ? (
        <p className="mt-4 mb-0 rounded-md border border-info/35 bg-canvas/35 p-3 text-sm leading-6 text-secondary">
          A later research generation reselected this idea into an existing active evidence
          stream. The original selection and active freeze remain separately identified.
        </p>
      ) : null}

      <div className="mt-4 flex flex-wrap gap-x-4 gap-y-2 text-sm">
        <a
          className="font-semibold text-accent"
          href={`/candidate/${idea.candidate.scan_id}/${idea.candidate.candidate_id}`}
        >
          Review Research Idea
        </a>
        {idea.candidate.deep_replay_run_id ? (
          <a
            className="font-semibold text-accent"
            href={`/experiments/${idea.candidate.deep_replay_run_id}`}
          >
            Historical QAP evidence
          </a>
        ) : null}
        {idea.forward_cohort_ids.map((cohortId) => (
          <a
            key={cohortId}
            className="font-semibold text-accent"
            href={`/prospective/${cohortId}`}
          >
            Forward evidence {shortId(cohortId)}
          </a>
        ))}
      </div>
    </article>
  )
}

function OtherRunCard({ run }: { run: RunSummaryDto }) {
  if (run.artifact_status === 'invalid') {
    return (
      <article className="rounded-lg border border-negative/45 bg-panel p-5">
        <Badge tone="negative">Invalid artifact</Badge>
        <h3 className="mt-3 mb-2 text-base font-semibold text-foreground">
          {run.experiment_name ?? run.run_id}
        </h3>
        <p className="m-0 text-sm text-secondary">
          {run.error?.message ?? 'The persisted evidence could not be validated.'}
        </p>
      </article>
    )
  }
  const status = researchStatusPresentation(run.status)
  return (
    <article className="rounded-lg border border-border bg-panel p-5">
      <div className="flex flex-wrap gap-2">
        <Badge tone={status.tone}>{status.label}</Badge>
        <Badge tone="info">
          {experimentDataRoleLabel(run.data_role, run.final_oos_consumed)}
        </Badge>
      </div>
      <h3 className="mt-3 mb-2 text-base font-semibold text-foreground">
        {run.experiment_name ?? run.basket?.join(' · ') ?? 'QAP research run'}
      </h3>
      <p className="m-0 text-sm text-secondary">
        {humanizeIdentifier(run.relationship_id ?? 'relationship unavailable')}
        {run.created_timestamp
          ? ` · ${formatResearchTimestamp(run.created_timestamp)}`
          : ''}
      </p>
      <a
        className="mt-4 inline-flex min-h-11 items-center font-semibold text-accent"
        href={`/experiments/${run.run_id}`}
      >
        Review specialist QAP run
      </a>
    </article>
  )
}

function Section({
  eyebrow,
  title,
  description,
  empty,
  emptyText,
  children,
}: {
  eyebrow: string
  title: string
  description: string
  empty: boolean
  emptyText: string
  children: React.ReactNode
}) {
  return (
    <section className="mt-10">
      <div className="mb-4 max-w-4xl">
        <p className="m-0 text-xs font-semibold uppercase tracking-[0.08em] text-muted">
          {eyebrow}
        </p>
        <h2 className="mt-2 mb-2 text-xl font-semibold text-foreground">{title}</h2>
        <p className="m-0 text-sm leading-6 text-secondary">{description}</p>
      </div>
      {empty ? (
        <p className="rounded-lg border border-border bg-panel p-5 text-sm text-secondary">
          {emptyText}
        </p>
      ) : (
        <div className="space-y-4">{children}</div>
      )}
    </section>
  )
}

export function HistoryView({ history }: HistoryViewProps) {
  return (
    <section aria-labelledby="history-heading" className="min-w-0">
      <header className="mb-8 max-w-4xl">
        <p className="mb-2 text-xs font-semibold uppercase tracking-[0.1em] text-accent">
          History
        </p>
        <h1
          id="history-heading"
          className="mb-3 text-3xl font-bold tracking-tight text-foreground md:text-4xl"
        >
          Research history
        </h1>
        <p className="m-0 text-sm leading-6 text-secondary md:text-base">
          Follow each Research Idea from its frozen historical generation through later
          evidence, time-specific current assessments, and portfolio expression. History
          does not apply today&apos;s mutable asset approval or data readiness to older evidence;
          exact specialist artifacts remain available without becoming separate Product verdicts.
        </p>
      </header>

      <Section
        eyebrow="Research generations"
        title="Research Ideas over time"
        description="Each generation preserves its original research claim and data boundary. Later evidence can weaken or remain unavailable without rewriting the historical replay result."
        empty={history.research_generations.length === 0}
        emptyText="No completed research generations are available yet."
      >
        {history.research_generations.map((generation) => {
          const summary = generation.summary
          return (
            <article
              key={summary.scan_id}
              className="rounded-lg border border-border-strong bg-subtle p-5"
            >
              <div className="flex flex-wrap gap-2">
                <Badge tone={summary.artifact_status === 'valid' ? 'info' : 'negative'}>
                  {summary.artifact_status === 'valid'
                    ? summary.claim?.label ?? 'Versioned research claim'
                    : 'Invalid research artifact'}
                </Badge>
              </div>
              <div className="mt-4 flex flex-wrap items-start justify-between gap-4">
                <div>
                  <h3 className="m-0 text-xl font-semibold text-foreground">
                    {generation.research_ideas.length} Research Idea
                    {generation.research_ideas.length === 1 ? '' : 's'}
                  </h3>
                  <p className="mt-2 mb-0 text-sm text-secondary">
                    {summary.eligible_information_end
                      ? `${boundaryLabel(summary.claim?.kind)} ${formatResearchTimestamp(summary.eligible_information_end)}`
                      : 'Frozen data boundary unavailable'}
                  </p>
                </div>
                <a className="font-semibold text-accent" href={`/scanner/${summary.scan_id}`}>
                  Full generation evidence
                </a>
              </div>
              {summary.error ? (
                <p className="mt-4 mb-0 text-sm text-negative">{summary.error.message}</p>
              ) : generation.research_ideas.length ? (
                <div className="mt-5 grid gap-4 xl:grid-cols-2">
                  {generation.research_ideas.map((idea) => (
                    <ResearchIdeaCard key={idea.candidate.candidate_id} idea={idea} />
                  ))}
                </div>
              ) : (
                <p className="mt-5 mb-0 rounded-md border border-border bg-panel p-4 text-sm leading-6 text-secondary">
                  No Research Idea survived the declared historical replay gates in this
                  generation. The full generation remains available as valid negative
                  research evidence.
                </p>
              )}
            </article>
          )
        })}
      </Section>

      <Section
        eyebrow="Portfolio expression"
        title="Portfolio research"
        description="Portfolio results keep their persisted source research claim and QAP result. They do not change the underlying Research Idea evidence."
        empty={history.portfolio_research.length === 0}
        emptyText="No completed portfolio research is available yet."
      >
        {history.portfolio_research.map((basket) => {
          const result = basketPresentation(basket.economic_gate_status)
          return (
            <article key={basket.basket_id} className="rounded-lg border border-border bg-panel p-5">
              <div className="flex flex-wrap gap-2">
                <Badge tone={basket.artifact_status === 'valid' ? result.tone : 'negative'}>
                  {basket.artifact_status === 'valid' ? result.label : 'Invalid portfolio artifact'}
                </Badge>
                {basket.source_claim ? <Badge tone="info">{basket.source_claim.label}</Badge> : null}
              </div>
              <h3 className="mt-3 mb-2 text-base font-semibold text-foreground">
                {basket.economic_assets.join(' · ') || `Portfolio ${shortId(basket.basket_id)}`}
              </h3>
              <p className="m-0 text-sm text-secondary">
                {basket.horizon ?? 'timeframe unavailable'} ·{' '}
                {basket.decision_resolution ?? 'resolution unavailable'}
              </p>
              <div className="mt-4 flex flex-wrap gap-x-4 gap-y-2 text-sm">
                <a className="font-semibold text-accent" href={`/baskets/${basket.basket_id}`}>
                  Review portfolio result
                </a>
                {basket.qap_run_id ? (
                  <a className="font-semibold text-accent" href={`/experiments/${basket.qap_run_id}`}>
                    Exact QAP result
                  </a>
                ) : null}
              </div>
            </article>
          )
        })}
      </Section>

      <Section
        eyebrow="Specialist evidence"
        title="Forward evidence not attached to a Research Idea"
        description="These persisted forward cohorts remain reachable for audit because the History composer could not attach them to a surviving Research Idea. They are not discarded or reclassified."
        empty={history.specialist_forward_evidence.length === 0}
        emptyText="All readable forward evidence is attached to a Research Idea history entry."
      >
        {history.specialist_forward_evidence.map((cohort) => (
          <article key={cohort.cohort_id} className="rounded-lg border border-border bg-panel p-5">
            <Badge tone={cohort.artifact_status === 'valid' ? 'info' : 'negative'}>
              {cohort.artifact_status === 'valid' ? 'Specialist forward evidence' : 'Invalid artifact'}
            </Badge>
            <h3 className="mt-3 mb-2 text-base font-semibold text-foreground">
              {cohort.horizon ?? 'Forward cohort'}
            </h3>
            <p className="m-0 text-sm text-secondary">
              {cohort.freeze_at
                ? `Frozen ${formatResearchTimestamp(cohort.freeze_at)}`
                : 'Freeze time unavailable'}
            </p>
            <a
              className="mt-4 inline-flex min-h-11 items-center font-semibold text-accent"
              href={`/prospective/${cohort.cohort_id}`}
            >
              Review exact forward evidence
            </a>
          </article>
        ))}
      </Section>

      <Section
        eyebrow="Other specialist research"
        title="Unowned QAP research runs"
        description="QAP runs already referenced by a Research Idea or portfolio are shown through those higher-level objects above. Remaining exact runs stay available here for audit."
        empty={history.other_research_runs.length === 0}
        emptyText="No additional unowned QAP research runs are available."
      >
        {history.other_research_runs.map((run) => (
          <OtherRunCard key={run.run_id} run={run} />
        ))}
      </Section>

      <Section
        eyebrow="Operational evidence"
        title="Paper dry runs"
        description="Paper execution and reconciliation records are operational evidence only. They do not strengthen or weaken a scientific Research Idea."
        empty={history.paper_operations.length === 0}
        emptyText="No paper operational evidence is available yet."
      >
        {history.paper_operations.map((paper) => (
          <article key={paper.operation_id} className="rounded-lg border border-border bg-panel p-5">
            <div className="flex flex-wrap gap-2">
              <Badge tone={paper.artifact_status === 'valid' ? 'info' : 'negative'}>
                {paper.artifact_status === 'valid' ? 'Operational dry run' : 'Invalid artifact'}
              </Badge>
              <Badge tone="neutral">Not scientific support</Badge>
            </div>
            <h3 className="mt-3 mb-2 text-base font-semibold text-foreground">
              Forward-paper evidence
            </h3>
            <p className="m-0 text-sm text-secondary">
              {paper.execution_timestamp
                ? formatResearchTimestamp(paper.execution_timestamp)
                : 'Execution time unavailable'}
              {paper.fill_count == null ? '' : ` · ${paper.fill_count} fills`}
            </p>
            <a
              className="mt-4 inline-flex min-h-11 items-center font-semibold text-accent"
              href={`/paper-operations/${paper.operation_id}`}
            >
              Review paper evidence
            </a>
          </article>
        ))}
      </Section>
    </section>
  )
}
