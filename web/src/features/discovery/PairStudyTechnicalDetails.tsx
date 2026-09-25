import type { CapabilityMetadataV1, ProductPairStudyContextDto, ProductPairStudySeriesDto } from '../../api/types'
import { formatDecimal, formatResearchTimestamp, formatSignedDecimal } from '../../lib/format'

function value(input: number | undefined, signed = false) {
  if (input === undefined) return 'Unavailable at this cutoff'
  return (signed ? formatSignedDecimal : formatDecimal)(String(input), 6).display
}

export function PairStudyTechnicalDetails({ context, series, capabilities }: {
  context: ProductPairStudyContextDto
  series: ProductPairStudySeriesDto | null
  capabilities: readonly CapabilityMetadataV1[]
}) {
  const relationship = context.relationship
  const paths = [context.data.asset_a_path, context.data.asset_b_path].filter((path) => path !== null)
  return <div className="mt-5 space-y-2 border-t border-border pt-4 text-sm">
    <details>
      <summary className="min-h-11 cursor-pointer py-3 font-semibold text-accent">Model details</summary>
      {relationship ? <div className="grid gap-5 pb-4 md:grid-cols-2">
        <section>
          <h3 className="m-0 font-semibold text-foreground">Rolling log-ratio z-score</h3>
          <dl className="mt-2 space-y-1 text-secondary">
            <div><dt className="inline">Status: </dt><dd className="inline">{relationship.rolling_log_ratio.status}</dd></div>
            <div><dt className="inline">Model: </dt><dd className="inline">{relationship.rolling_log_ratio.model_id} v{relationship.rolling_log_ratio.model_version}</dd></div>
            <div><dt className="inline">Score: </dt><dd className="inline">{value(relationship.rolling_log_ratio.values.score, true)}</dd></div>
            <div><dt className="inline">Log ratio: </dt><dd className="inline">{value(relationship.log_ratio_current, true)}</dd></div>
            <div><dt className="inline">Normalized {context.question.asset_a}: </dt><dd className="inline">{value(relationship.normalized_base_current)}</dd></div>
            <div><dt className="inline">Normalized {context.question.asset_b}: </dt><dd className="inline">{value(relationship.normalized_quote_current)}</dd></div>
            <div><dt className="inline">Required / coverage / window: </dt><dd className="inline">{relationship.rolling_log_ratio.required_observations} / {relationship.rolling_log_ratio.coverage_observations} / {relationship.rolling_log_ratio.window_observations}</dd></div>
            <div><dt className="inline">Evidence reciprocity: </dt><dd className="inline">{relationship.rolling_log_ratio.evidence_reciprocity}</dd></div>
            <div><dt className="inline">Input fingerprint: </dt><dd className="inline break-all">{relationship.rolling_log_ratio.input_fingerprint}</dd></div>
          </dl>
        </section>
        <section>
          <h3 className="m-0 font-semibold text-foreground">Residual / OLS</h3>
          <dl className="mt-2 space-y-1 text-secondary">
            <div><dt className="inline">Status: </dt><dd className="inline">{relationship.residual_ols.status}</dd></div>
            <div><dt className="inline">Model: </dt><dd className="inline">{relationship.residual_ols.model_id} v{relationship.residual_ols.model_version}</dd></div>
            <div><dt className="inline">Orientation: </dt><dd className="inline">{relationship.residual_ols.orientation}</dd></div>
            <div><dt className="inline">Alpha: </dt><dd className="inline">{value(relationship.residual_ols.values.alpha, true)}</dd></div>
            <div><dt className="inline">Beta: </dt><dd className="inline">{value(relationship.residual_ols.values.beta, true)}</dd></div>
            <div><dt className="inline">Score: </dt><dd className="inline">{value(relationship.residual_ols.values.score, true)}</dd></div>
            <div><dt className="inline">Required / coverage / window: </dt><dd className="inline">{relationship.residual_ols.required_observations} / {relationship.residual_ols.coverage_observations} / {relationship.residual_ols.window_observations}</dd></div>
            <div><dt className="inline">Fit reciprocity: </dt><dd className="inline">{relationship.residual_ols.fit_reciprocity}</dd></div>
            <div><dt className="inline">Input fingerprint: </dt><dd className="inline break-all">{relationship.residual_ols.input_fingerprint}</dd></div>
          </dl>
        </section>
      </div> : <p className="text-secondary">No model observations at this cutoff.</p>}
    </details>
    <details>
      <summary className="min-h-11 cursor-pointer py-3 font-semibold text-accent">Evidence &amp; provenance</summary>
      <p className="text-secondary">{context.question.orientation} · {context.question.venue} · {context.question.interval} · through {context.question.safe_cutoff ? formatResearchTimestamp(context.question.safe_cutoff) : 'unknown cutoff'} · data {context.data.status}.</p>
      <p className="text-secondary">Available venues: {context.question.available_venues.join(', ') || 'none'}. Analysis reference: {context.analysis_lens ? `${context.analysis_lens.asset} · ${context.analysis_lens.status}` : 'none'}.</p>
      <div className="grid gap-4 pb-4 md:grid-cols-2">{paths.map((path) => <dl key={path.dataset_id} className="min-w-0 break-all text-xs text-secondary">
        <dt className="font-semibold text-foreground">{path.base_asset}/{path.quote_asset} · {path.venue_symbol}</dt>
        <dd className="ml-0 mt-1">Dataset: {path.dataset_id}</dd>
        <dd className="ml-0 mt-1">Generation: {path.semantic_fingerprint}</dd>
        <dd className="ml-0 mt-1">Coverage: {formatResearchTimestamp(path.coverage_start)} to {formatResearchTimestamp(path.coverage_end_exclusive)}</dd>
        <dd className="ml-0 mt-1">Directory source: {path.directory_source_id} · {path.directory_source_fingerprint}</dd>
        <dd className="ml-0 mt-1">Data: {path.relative_path}</dd>
        <dd className="ml-0 mt-1">Provenance: {path.provenance_relative_path}</dd>
      </dl>)}</div>
      {series ? <p className="break-all text-xs text-muted">Chart sources: {series.base_source_fingerprint} · {series.quote_source_fingerprint}</p> : null}
      {context.data.reasons.map((reason) => <p key={reason.code} className="text-secondary">{reason.message}</p>)}
    </details>
    <details>
      <summary className="min-h-11 cursor-pointer py-3 font-semibold text-accent">Methodology</summary>
      <p className="text-secondary">These are same-venue {context.question.coordinate_asset} price paths used for description. A ready relationship does not imply a direct exchange market or profitable replay.</p>
      <p className="text-secondary">Economic expression: direct market {context.economic_expression.direct_status}; bridge {context.economic_expression.bridge_status}; default recipe {context.economic_expression.default_recipe_declarable ? 'declarable' : 'not declarable'}.</p>
      <p className="text-secondary">Rolling residual OLS is not a formal cointegration test. Positive and negative scores describe direction, not desirability.</p>
      <ul className="space-y-1 pl-5 text-secondary">{capabilities.filter((item) => item.kind === 'relationship').map((item) =>
        <li key={item.component_id}>{item.component_id}: {item.capability}</li>)}</ul>
      <p className="text-secondary">Student-t Copula is known but not implemented; that is not evidence against this pair.</p>
    </details>
  </div>
}
