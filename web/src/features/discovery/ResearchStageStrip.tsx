import type { ResearchMode } from './researchStudies'

export type ResearchStage = 'idle' | 'resolving_data' | 'measuring_relationship'
  | 'waiting_for_authority' | 'checking_comparison' | 'running_comparison'
  | 'loading_results' | 'complete' | 'blocked' | 'failed'

export function ResearchStageStrip({ mode, stage, hasRelationship = false }: {
  mode: ResearchMode; stage: ResearchStage; hasRelationship?: boolean
}) {
  const labels = mode === 'relationship' ? ['Data', 'Relationship', 'Ready']
    : ['Data', 'Relationship', 'Simulation', 'Result']
  const active = stage === 'idle' ? -1
    : stage === 'resolving_data' ? 0
      : stage === 'measuring_relationship' ? 1
        : stage === 'waiting_for_authority' || stage === 'checking_comparison' || stage === 'running_comparison'
          ? 2 : stage === 'loading_results' || stage === 'complete' ? labels.length - 1
            : hasRelationship ? mode === 'backtest_comparison' ? 2 : 1 : 0
  const complete = stage === 'complete'
  return <ol aria-label="Research progress" className={`m-0 grid gap-2 border-b border-border pb-4 text-xs sm:text-sm ${mode === 'relationship' ? 'grid-cols-3' : 'grid-cols-4'}`}>
    {labels.map((label, index) => <li key={label} aria-current={!complete && active === index ? 'step' : undefined}
      className={`min-w-0 rounded-md px-2 py-2 text-center ${index < active || complete ? 'bg-subtle text-foreground' : index === active ? 'border border-accent text-accent' : 'text-muted'}`}>
      {label}{index < active || complete ? ' ✓' : ''}
    </li>)}
  </ol>
}
