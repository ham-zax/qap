import type { ProductPairStudyContextDto, ResearchRecipeDraftV1 } from '../../api/types'

function path(asset: string): NonNullable<ProductPairStudyContextDto['data']['asset_a_path']> {
  return {
    base_asset: asset, quote_asset: 'USDT', venue: 'gate', venue_symbol: `${asset}_USDT`,
    interval: '4h', coverage_start: '2026-03-01T00:00:00Z', coverage_end_exclusive: '2026-09-01T00:00:00Z',
    dataset_id: `${asset}-fixture`, directory_source_id: 'fixture-directory',
    directory_source_fingerprint: 'a'.repeat(64), semantic_fingerprint: 'b'.repeat(64),
    relative_path: `${asset}.parquet`, provenance_relative_path: `${asset}.json`,
  }
}
const observation = {
  as_of: '2026-09-01T00:00:00Z', model_id: 'fixture', model_version: '1', orientation: 'W/PIXEL',
  status: 'valid' as const, required_observations: 180, window_observations: 180, coverage_observations: 180,
  values: { score: 1, alpha: 0, beta: 1 }, evidence_reciprocity: 'fixture', fit_reciprocity: 'fixture',
  input_fingerprint: 'c'.repeat(64), base_source_fingerprint: 'b'.repeat(64), quote_source_fingerprint: 'b'.repeat(64),
}

export const pairContext: ProductPairStudyContextDto = {
  schema_version: 'qap.api.product_pair_study_context.v1', directory_id: 'fixture-directory', analysis_lens: null,
  question: { asset_a: 'W', asset_b: 'PIXEL', orientation: 'W/PIXEL', canonical_pair: ['PIXEL', 'W'],
    available_venues: ['gate'], venue: 'gate', horizon: 'medium', interval: '4h', coordinate_asset: 'USDT', safe_cutoff: '2026-09-01T00:00:00Z' },
  data: { status: 'ready', asset_a_path: path('W'), asset_b_path: path('PIXEL'), reasons: [],
    direct_market: { base_asset: null, quote_asset: null, generation: null, status: 'unavailable', venue: 'gate', venue_symbol: null } },
  relationship: { raw_ratio_current: 1, log_ratio_current: 0, normalized_base_current: 1, normalized_quote_current: 1,
    rolling_log_ratio: observation, residual_ols: observation },
  economic_expression: { direct_status: 'unavailable', bridge_status: 'ready', default_recipe_declarable: true, reasons: [] },
}

export const pairDraft: ResearchRecipeDraftV1 = {
  schema_version: 'qap.research.recipe-draft.v1', assets: ['W', 'PIXEL'], research_object: 'pair',
  research_family_id: 'fixture-family', fidelity_intent: 'native_qap', source: { metadata: {} },
  selection: { kind: 'report_all' },
  data: { authority: 'pair_study', claim_identity: 'fixture-claim', data_role: 'development',
    horizon: 'medium',
    data_window: { start: '2026-03-01T00:00:00Z', end: '2026-09-01T00:00:00Z' },
    evaluation_window: { start: '2026-06-01T00:00:00Z', end: '2026-09-01T00:00:00Z' },
    generations: [pairContext.data.asset_a_path!, pairContext.data.asset_b_path!].map((source) => ({
      dataset_id: source.dataset_id, semantic_fingerprint: source.semantic_fingerprint, purpose: 'execution' as const,
    })), interval: '4h', starting_quantities: { W: '100', PIXEL: '100' } },
  execution: { mode: 'multi_asset_bridge', bridge_asset: 'USDT', numeraire_asset: 'USDT',
    fee_bps: '10', slippage_bps: '5', minimum_rebalance_notional: '10', market_metadata_mode: 'required' },
  benchmarks: { controls: [], primary_incremental_benchmark: 'fixture-control',
    primary_metric: 'primary_control_relative_terminal_wealth', relationship_alpha_claim: true, success_threshold: '0' },
  variants: ['rolling_log_ratio_zscore', 'residual_mean_reversion'].map((component_id) => ({
    variant_id: component_id, relationship: { component_id, config: { window_bars: 180, min_observations: 180 } },
    decision_rule: { component_id: 'relationship_target', config: { enter_threshold: '1', neutral_threshold: '0.25', maximum_tilt: '0.10' } },
    allocation: { component_id: 'fixture-allocation', config: {} }, risk_overlays: [],
  })),
}

export const runnableSupport = {
  schema_version: 'qap.research.support-report.v1', structure: 'valid', capability: 'executable',
  authority: 'allowed', readiness: 'ready', fidelity: 'native', runnable: true, reasons: [], suggestions: [],
}
