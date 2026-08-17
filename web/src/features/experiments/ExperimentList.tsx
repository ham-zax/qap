import type { ExperimentListDto, RunSummaryDto } from '../../api/types'
import { ExactNumber } from '../../components/ExactNumber'

interface ExperimentListProps {
  data: ExperimentListDto
}

function label(value: string | null | undefined): string {
  if (!value) return 'Unknown'
  return value
    .split('_')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ')
}

function ExperimentCard({ run }: { run: RunSummaryDto }) {
  const title = run.experiment_name ?? run.run_id
  if (run.artifact_status === 'invalid') {
    return (
      <article aria-label={title}>
        <h2>{title}</h2>
        <p>Invalid artifact</p>
        {run.error ? <p>{run.error.message}</p> : null}
      </article>
    )
  }

  return (
    <article aria-label={title}>
      <header>
        <h2>{title}</h2>
        <p>{label(run.status)}</p>
      </header>
      <dl>
        <div>
          <dt>Research family</dt>
          <dd>{run.research_family_id}</dd>
        </div>
        <div>
          <dt>Data role</dt>
          <dd>{label(run.data_role)}</dd>
        </div>
        <div>
          <dt>Basket</dt>
          <dd>{run.basket?.join(' · ') ?? 'Unavailable'}</dd>
        </div>
        <div>
          <dt>Anchor</dt>
          <dd>Anchor: {run.analysis_anchor ?? 'none'}</dd>
        </div>
        <div>
          <dt>Model</dt>
          <dd>Model: {run.relationship_id ?? 'Unavailable'}</dd>
        </div>
        <div>
          <dt>Policy</dt>
          <dd>Policy: {run.policy_id ?? 'Unavailable'}</dd>
        </div>
        <div>
          <dt>Primary control</dt>
          <dd>Primary control: {run.primary_incremental_benchmark ?? 'none'}</dd>
        </div>
        <div>
          <dt>Increment vs primary control</dt>
          <dd>
            Increment vs primary control:{' '}
            {run.incremental_vs_primary_control ? (
              <ExactNumber value={run.incremental_vs_primary_control} />
            ) : (
              'not applicable'
            )}
          </dd>
        </div>
      </dl>
      {run.final_oos_consumed ? <p>Final OOS consumed</p> : null}
      {run.git_dirty ? <p>Dirty code snapshot</p> : null}
      <a href={`/experiments/${encodeURIComponent(run.run_id)}`}>Inspect evidence</a>
    </article>
  )
}

export function ExperimentList({ data }: ExperimentListProps) {
  if (data.items.length === 0) {
    return <p>No persisted experiments are available.</p>
  }

  return (
    <section aria-labelledby="experiment-list-heading">
      <h1 id="experiment-list-heading">Experiment evidence</h1>
      {data.items.map((run) => (
        <ExperimentCard key={run.run_id} run={run} />
      ))}
    </section>
  )
}
