import type { ForwardCohortListDto } from '../../api/types'
import { Badge } from '../../components/ui/Badge'
import { formatResearchTimestamp } from '../../lib/format'

interface ProspectiveHomeProps {
  data: ForwardCohortListDto
}

function shortId(value: string) {
  return value.length <= 18 ? value : `${value.slice(0, 10)}…${value.slice(-6)}`
}

export function ProspectiveHome({ data }: ProspectiveHomeProps) {
  return (
    <section className="min-w-0">
      <header className="mb-8 max-w-4xl">
        <p className="mb-2 text-xs font-semibold uppercase tracking-[0.1em] text-accent">
          Validate
        </p>
        <h1 className="mb-3 text-3xl font-bold tracking-tight text-foreground md:text-4xl">
          Forward validations
        </h1>
        <p className="m-0 text-sm leading-6 text-secondary md:text-base">
          Follow research ideas that were frozen before later evidence, update current
          market evidence when needed, and evaluate hypothetical capital without
          implying live-trading authority.
        </p>
      </header>

      {data.items.length === 0 ? (
        <p className="text-secondary">
          No forward validations exist yet. Start one from an eligible research idea in
          Discover.
        </p>
      ) : (
        <div className="grid gap-4 lg:grid-cols-2">
          {data.items.map((cohort) => (
            <article
              key={cohort.cohort_id}
              className="rounded-lg border border-border bg-panel p-5"
            >
              <div className="flex flex-wrap gap-2">
                <Badge tone={cohort.artifact_status === 'valid' ? 'positive' : 'negative'}>
                  {cohort.artifact_status}
                </Badge>
                {cohort.horizon ? <Badge tone="info">{cohort.horizon}</Badge> : null}
              </div>
              <h2 className="mt-4 mb-2 text-base font-semibold text-foreground">
                Forward validation {shortId(cohort.cohort_id)}
              </h2>
              {cohort.freeze_at ? (
                <p className="m-0 text-sm text-secondary">
                  Frozen {formatResearchTimestamp(cohort.freeze_at)}
                </p>
              ) : null}
              <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
                <div>
                  <p className="m-0 text-xs text-muted">Automatic ideas</p>
                  <p className="mt-1 mb-0 font-semibold text-foreground">
                    {cohort.automatic_member_count ?? 0}
                  </p>
                </div>
                <div>
                  <p className="m-0 text-xs text-muted">Manual ideas</p>
                  <p className="mt-1 mb-0 font-semibold text-foreground">
                    {cohort.manual_member_count ?? 0}
                  </p>
                </div>
                <div>
                  <p className="m-0 text-xs text-muted">Checkpoints</p>
                  <p className="mt-1 mb-0 font-semibold text-foreground">
                    {cohort.checkpoint_count ?? 0}
                  </p>
                </div>
                <div>
                  <p className="m-0 text-xs text-muted">Capital assessments</p>
                  <p className="mt-1 mb-0 font-semibold text-foreground">
                    {cohort.qualification_count ?? 0}
                  </p>
                </div>
              </div>
              {cohort.error ? (
                <p className="mt-3 text-sm text-negative">{cohort.error.message}</p>
              ) : null}
              <a
                className="mt-5 inline-flex min-h-11 items-center font-semibold text-accent"
                href={`/prospective/${cohort.cohort_id}`}
              >
                Continue validation
              </a>
            </article>
          ))}
        </div>
      )}
    </section>
  )
}
