import type { ExperimentDetailDto } from '../../api/types'
import { ExactNumber } from '../../components/ExactNumber'

interface ExperimentDetailProps {
  data: ExperimentDetailDto
}

function titleCase(value: string): string {
  return value
    .split('_')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ')
}

function dataRoleLabel(role: string, consumed: boolean): string {
  if (role === 'final_oos') {
    return `Final OOS · ${consumed ? 'consumed' : 'unconsumed'}`
  }
  return titleCase(role)
}

function pairWorkbenchHref(data: ExperimentDetailDto): string | null {
  const [assetX, assetY] = data.manifest.basket
  if (!assetX || !assetY) return null
  const search = new URLSearchParams({
    orientation: `${assetX}/${assetY}`,
    anchor: data.manifest.analysis_anchor ?? 'none',
    view: 'ratio',
  })
  return `/pair/${encodeURIComponent(data.run_id)}/${encodeURIComponent(assetX)}/${encodeURIComponent(assetY)}?${search}`
}

export function ExperimentDetail({ data }: ExperimentDetailProps) {
  const { manifest, provenance, result, final_oos_commitment: commitment } = data
  const pairHref = pairWorkbenchHref(data)

  return (
    <article aria-labelledby="experiment-detail-heading">
      <header>
        <p>{dataRoleLabel(result.data_role, result.final_oos_consumed)}</p>
        <h1 id="experiment-detail-heading">{manifest.experiment_name}</h1>
        <p>{titleCase(result.status)}</p>
        <p>{manifest.description}</p>
      </header>

      <section aria-labelledby="research-context-heading">
        <h2 id="research-context-heading">Research context</h2>
        <p>Research family: {result.research_family_id}</p>
        <p>Sibling trials: {data.sibling_trial_count}</p>
        <p>Parent run: {result.parent_run_id ?? 'none'}</p>
        <p>Universe: {titleCase(manifest.universe_mode)}</p>
        <p>Basket: {manifest.basket.join(' · ')}</p>
        <p>Anchor: {manifest.analysis_anchor ?? 'none'}</p>
        <p>Relationship model: {manifest.relationship.component_id}</p>
        <p>Policy: {manifest.policy.component_id}</p>
      </section>

      <section aria-labelledby="benchmark-evidence-heading">
        <h2 id="benchmark-evidence-heading">Benchmark evidence</h2>
        <p>
          Primary control: {result.primary_incremental_benchmark ?? 'not applicable'}
        </p>
        <p>
          Increment vs primary control:{' '}
          {result.strategy_vs_primary_control ? (
            <ExactNumber value={result.strategy_vs_primary_control} />
          ) : (
            'not applicable'
          )}
        </p>
        <p>Strategy vs HODL: <ExactNumber value={result.strategy_vs_hodl} /></p>
        <p>
          Strategy vs matched contribution:{' '}
          {result.strategy_vs_matched_contribution ? (
            <ExactNumber value={result.strategy_vs_matched_contribution} />
          ) : (
            'not applicable'
          )}
        </p>
        <p>Primary metric: {result.primary_metric}</p>
        <p>Primary metric value: <ExactNumber value={result.primary_metric_value} /></p>
      </section>

      <section aria-labelledby="holdout-heading">
        <h2 id="holdout-heading">Holdout and data</h2>
        {commitment ? (
          <>
            <p>Holdout: {commitment.holdout_id}</p>
            <p>Holdout execution: {commitment.execution_status}</p>
          </>
        ) : (
          <p>No final-OOS commitment applies to this run.</p>
        )}
        <p>
          Data window: {manifest.data_window.start} to {manifest.data_window.end}
        </p>
        {provenance.data_fingerprints.map((dataset) => (
          <div key={dataset.dataset_id}>
            <p>Dataset: {dataset.dataset_id}</p>
            <p>Fingerprint: {dataset.fingerprint}</p>
          </div>
        ))}
      </section>

      <section aria-labelledby="provenance-heading">
        <h2 id="provenance-heading">Provenance</h2>
        <p>Git commit: {provenance.git_commit}</p>
        <p>Code snapshot: {provenance.git_dirty ? 'dirty' : 'clean'}</p>
        <p>Code fingerprint: {provenance.code_fingerprint}</p>
        <p>Manifest fingerprint: {provenance.manifest_sha256}</p>
      </section>

      <nav aria-label="Run evidence links">
        <a href={`/portfolio/${encodeURIComponent(data.run_id)}`}>
          Open portfolio economics
        </a>
        {pairHref ? <a href={pairHref}>Open pair workbench</a> : null}
      </nav>
    </article>
  )
}
