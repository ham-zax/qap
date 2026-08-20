import { Link } from '@tanstack/react-router'

import type {
  CurrentApprovedReadinessDto,
  ExperimentListDto,
  ForwardCohortListDto,
  OperationListDto,
  WorkspaceStatusDto,
} from '../../api/types'
import { Badge } from '../../components/ui/Badge'
import { formatResearchTimestamp } from '../../lib/format'
import { researchStatusPresentation } from '../experiments/presentation'

interface HomeWorkspaceProps {
  workspace: WorkspaceStatusDto
  readiness: CurrentApprovedReadinessDto[]
  readinessUnavailable: boolean
  experiments: ExperimentListDto
  forwardCohorts: ForwardCohortListDto
  operations: OperationListDto
}

const researchUniverseGoal = {
  title: 'Choose research assets',
  description: 'Approve canonical assets and review their current Binance/Gate availability.',
  to: '/universe' as const,
}

const goals = [
  {
    title: 'Research a pair or scan the market',
    description: 'Start with a pair question, scan your approved universe, or open the advanced Experiment Lab.',
    to: '/scanner' as const,
  },
  {
    title: 'Continue validation',
    description: 'Return to ideas being checked against genuinely later evidence.',
    to: '/prospective' as const,
  },
  {
    title: 'Analyze a portfolio',
    description: 'Combine supported ideas and compare the result with declared controls.',
    to: '/baskets' as const,
  },
  {
    title: 'Review history',
    description: 'Open finished research and its preserved evidence.',
    to: '/experiments' as const,
  },
]

export function HomeWorkspace({
  workspace,
  readiness,
  readinessUnavailable,
  experiments,
  forwardCohorts,
  operations,
}: HomeWorkspaceProps) {
  const activeOperation = operations.items.find(
    (operation) => operation.status === 'running',
  )
  const latestOperation = operations.items[0]
  const attentionOperation =
    !activeOperation &&
    latestOperation &&
    (latestOperation.status === 'failed' || latestOperation.status === 'interrupted')
      ? latestOperation
      : null
  const productResearchReady = readiness.some((item) => item.ready_for_research)
  const validations = forwardCohorts.items
    .filter((cohort) => cohort.artifact_status === 'valid')
    .slice(0, 3)
  const recentResults = experiments.items.slice(0, 3)
  const availableGoals =
    workspace.workspace_mode === 'local_market'
      ? [researchUniverseGoal, ...goals]
      : goals

  return (
    <div className="min-w-0">
      <section aria-labelledby="home-heading">
        <header className="mb-8 max-w-4xl">
          <p className="mb-2 text-xs font-semibold uppercase tracking-[0.1em] text-accent">
            Research workspace
          </p>
          <h1
            id="home-heading"
            className="mb-3 text-3xl font-bold tracking-tight text-foreground md:text-4xl"
          >
            What do you want to do?
          </h1>
          <p className="m-0 text-sm leading-6 text-secondary md:text-base">
            Start a new research task or return to evidence already in progress.
            QAP remains a research system and does not place or authorize live trades.
          </p>
        </header>

        {workspace.workspace_mode === 'local_market' && !productResearchReady ? (
          <section
            aria-labelledby="local-market-setup-heading"
            className="mb-8 rounded-lg border border-warning/45 bg-panel p-5"
          >
            <Badge tone={readinessUnavailable ? 'negative' : 'warning'}>
              {readinessUnavailable ? 'Readiness unavailable' : 'Research setup'}
            </Badge>
            <h2
              id="local-market-setup-heading"
              className="mt-3 mb-2 text-xl font-semibold text-foreground"
            >
              {readinessUnavailable
                ? 'Research readiness could not be checked'
                : 'Current-approved research is not ready yet'}
            </h2>
            <p className="m-0 max-w-3xl text-sm leading-6 text-secondary">
              {readinessUnavailable
                ? 'QAP could not confirm readiness for every Research timeframe, so Home does not infer a ready/not-ready conclusion. Open Research to inspect the backend error directly.'
                : 'This guidance comes from backend research readiness rather than catalog presence. Open Research to choose one timeframe and see the backend-owned identity, current-market, history, maintenance, and direct-market evidence.'}
            </p>
            <Link
              className="mt-4 inline-flex min-h-11 items-center font-semibold text-accent"
              to="/scanner"
            >
              Review research readiness →
            </Link>
          </section>
        ) : null}

        <div className="grid gap-4 md:grid-cols-2">
          {availableGoals.map((goal) => (
            <Link
              key={goal.to}
              className="group flex min-h-40 flex-col justify-between rounded-lg border border-border bg-panel p-5 text-foreground no-underline transition-[background-color,border-color] duration-150 hover:border-border-strong hover:bg-subtle"
              to={goal.to}
            >
              <div>
                <h2 className="mb-2 text-xl font-semibold">{goal.title}</h2>
                <p className="m-0 text-sm leading-6 text-secondary">
                  {goal.description}
                </p>
              </div>
              <span className="mt-5 text-sm font-semibold text-accent">
                Open workspace →
              </span>
            </Link>
          ))}
        </div>
      </section>

      <section className="mt-12" aria-labelledby="current-activity-heading">
        <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
          <div>
            <p className="mb-1 text-xs font-semibold uppercase tracking-[0.1em] text-accent">
              Resume
            </p>
            <h2 id="current-activity-heading" className="m-0 text-xl font-semibold">
              Current activity
            </h2>
          </div>
          <Link className="text-sm font-semibold text-accent" to="/operations">
            View all activity
          </Link>
        </div>

        {activeOperation ? (
          <article className="rounded-lg border border-info/45 bg-panel p-5">
            <Badge tone="info">Running</Badge>
            <h3 className="mt-3 mb-2 text-base font-semibold text-foreground">
              Background research is in progress
            </h3>
            <p className="m-0 text-sm text-secondary">
              Started {formatResearchTimestamp(activeOperation.started_at)}. Other
              evidence remains available while it runs.
            </p>
            <Link
              className="mt-4 inline-flex min-h-11 items-center font-semibold text-accent"
              params={{ operationId: activeOperation.operation_id }}
              to="/operations/$operationId"
            >
              View in Activity
            </Link>
          </article>
        ) : attentionOperation ? (
          <article className="rounded-lg border border-warning/45 bg-panel p-5">
            <Badge tone={attentionOperation.status === 'failed' ? 'negative' : 'warning'}>
              {attentionOperation.status === 'failed' ? 'Failed' : 'Interrupted'}
            </Badge>
            <h3 className="mt-3 mb-2 text-base font-semibold text-foreground">
              Background task needs attention
            </h3>
            <p className="m-0 text-sm leading-6 text-secondary">
              {attentionOperation.failure?.message ??
                'The latest background task did not complete normally.'}{' '}
              This is an operational state, not a negative research result.
            </p>
            <Link
              className="mt-4 inline-flex min-h-11 items-center font-semibold text-accent"
              params={{ operationId: attentionOperation.operation_id }}
              to="/operations/$operationId"
            >
              Review in Activity
            </Link>
          </article>
        ) : (
          <p className="rounded-lg border border-border bg-panel p-5 text-sm text-secondary">
            No background task is running right now.
          </p>
        )}
      </section>

      <div className="mt-12 grid gap-10 xl:grid-cols-2">
        <section aria-labelledby="validations-heading">
          <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
            <h2 id="validations-heading" className="m-0 text-xl font-semibold">
              Validations to resume
            </h2>
            <Link className="text-sm font-semibold text-accent" to="/prospective">
              View all validations
            </Link>
          </div>

          {validations.length ? (
            <div className="space-y-3">
              {validations.map((cohort) => {
                const updateCount = cohort.checkpoint_count ?? 0
                return (
                  <article
                    key={cohort.cohort_id}
                    className="rounded-lg border border-border bg-panel p-4"
                  >
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge tone="info">Forward validation</Badge>
                      {cohort.horizon ? (
                        <Badge tone="neutral">{cohort.horizon} timeframe</Badge>
                      ) : null}
                    </div>
                    <h3 className="mt-3 mb-1 text-base font-semibold text-foreground">
                      Continue frozen research evidence
                    </h3>
                    <p className="m-0 text-sm text-secondary">
                      {cohort.freeze_at
                        ? `Started ${formatResearchTimestamp(cohort.freeze_at)} · `
                        : ''}
                      {updateCount} evidence {updateCount === 1 ? 'update' : 'updates'}
                    </p>
                    <Link
                      className="mt-3 inline-flex min-h-11 items-center font-semibold text-accent"
                      params={{ cohortId: cohort.cohort_id }}
                      to="/prospective/$cohortId"
                    >
                      Continue validation
                    </Link>
                  </article>
                )
              })}
            </div>
          ) : (
            <p className="rounded-lg border border-border bg-panel p-5 text-sm text-secondary">
              No forward validation is available to resume. Start from a Research Idea
              in Research.
            </p>
          )}
        </section>

        <section aria-labelledby="recent-results-heading">
          <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
            <h2 id="recent-results-heading" className="m-0 text-xl font-semibold">
              Recent research results
            </h2>
            <Link className="text-sm font-semibold text-accent" to="/experiments">
              View History
            </Link>
          </div>

          {recentResults.length ? (
            <div className="space-y-3">
              {recentResults.map((run) => {
                const status = researchStatusPresentation(run.status)
                return (
                  <article
                    key={run.run_id}
                    className="rounded-lg border border-border bg-panel p-4"
                  >
                    <Badge tone={run.artifact_status === 'invalid' ? 'negative' : status.tone}>
                      {run.artifact_status === 'invalid'
                        ? 'Evidence unavailable'
                        : status.label}
                    </Badge>
                    <h3 className="mt-3 mb-1 text-base font-semibold text-foreground">
                      {run.experiment_name ?? run.basket?.join(' · ') ?? 'Research result'}
                    </h3>
                    {run.created_timestamp ? (
                      <p className="m-0 text-sm text-secondary">
                        Recorded {formatResearchTimestamp(run.created_timestamp)}
                      </p>
                    ) : null}
                    <Link
                      className="mt-3 inline-flex min-h-11 items-center font-semibold text-accent"
                      params={{ runId: run.run_id }}
                      to="/experiments/$runId"
                    >
                      Review result
                    </Link>
                  </article>
                )
              })}
            </div>
          ) : (
            <p className="rounded-lg border border-border bg-panel p-5 text-sm text-secondary">
              No finished research results are available yet.
            </p>
          )}
        </section>
      </div>
    </div>
  )
}
