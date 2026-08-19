import type { ScanDetailDto } from '../../api/types'

interface ResearchStageSummaryProps {
  stages: ScanDetailDto['stages']
  claimKind: NonNullable<ScanDetailDto['summary']['claim']>['kind']
}

function timeframeLabel(value: string): string {
  if (value === 'short') return 'Short-term'
  if (value === 'medium') return 'Medium-term'
  if (value === 'swing') return 'Longer-term'
  return value
}

export function ResearchStageSummary({
  stages,
  claimKind,
}: ResearchStageSummaryProps) {
  if (stages.scopes.length === 0) {
    return <p className="text-sm text-secondary">No completed research scopes were published.</p>
  }

  return (
    <div className="grid gap-4 xl:grid-cols-2">
      {stages.scopes.map((scope) => (
        <article
          key={`${scope.venue}-${scope.horizon}`}
          className="rounded-lg border border-border bg-panel p-5"
        >
          <p className="m-0 text-xs font-semibold uppercase tracking-[0.08em] text-muted">
            {scope.venue} · {timeframeLabel(scope.horizon)}
          </p>
          <p className="mt-3 mb-0 text-sm leading-6 text-secondary">
            {scope.scope_asset_count}{' '}
            {claimKind === 'historical_pit'
              ? 'point-in-time admitted assets'
              : claimKind === 'current_approved_retrospective'
                ? 'current-approved assets'
                : 'assets in this frozen scope'}
          </p>
          <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
            <StageCount
              label="Relationships compared"
              value={scope.relationship_comparison_count}
            />
            <StageCount
              label="Relationships retained"
              value={scope.retained_relationship_count}
            />
            <StageCount label="Fixed rules evaluated" value={scope.enumerated_rule_count} />
            <StageCount label="Valid rule evaluations" value={scope.valid_rule_count} />
            <StageCount label="Invalid rule evaluations" value={scope.invalid_rule_count} />
            <StageCount
              label="Selected for deep replay"
              value={scope.selected_for_replay_count}
            />
            <StageCount
              label="Deep replays completed"
              value={scope.completed_replay_count}
            />
            <StageCount
              label="Replay evidence unavailable"
              value={scope.replay_unavailable_count}
            />
            <StageCount
              label="Completed replays rejected"
              value={scope.rejected_replay_count}
            />
            <StageCount label="Research Ideas" value={scope.research_idea_count} />
          </dl>
          <p className="mt-4 mb-0 text-xs leading-5 text-muted">
            Relationship counts and fixed-rule counts describe different scanner stages;
            one retained relationship can produce multiple fixed rule evaluations.
          </p>
        </article>
      ))}
    </div>
  )
}

function StageCount({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-md border border-border p-3">
      <dt className="text-xs text-muted">{label}</dt>
      <dd className="mt-1 mb-0 text-xl font-semibold tabular-nums text-foreground">
        {value}
      </dd>
    </div>
  )
}
