import { describe, expect, it } from 'vitest'

import { pairContext } from './researchStudy.test-fixtures'
import { pairDraft } from './researchStudy.test-fixtures'
import { pairRecipeMatchesContext, pairStudySeriesMatchesContext } from './pairStudyBinding'
import type { ProductPairStudySeriesDto } from '../../api/types'

const matching: ProductPairStudySeriesDto = {
  schema_version: 'qap.api.product_pair_study_series.v1', question: pairContext.question,
  asset_a_path: pairContext.data.asset_a_path!, asset_b_path: pairContext.data.asset_b_path!,
  base_source_fingerprint: pairContext.data.asset_a_path!.semantic_fingerprint,
  quote_source_fingerprint: pairContext.data.asset_b_path!.semantic_fingerprint,
  ratio: [], log_ratio: [], normalized_base: [], normalized_quote: [], analysis_reference: null,
}

describe('pair study result binding', () => {
  it('accepts series for the same question and data generations', () => {
    expect(pairStudySeriesMatchesContext(pairContext, matching)).toBe(true)
  })

  it.each([
    { question: { ...matching.question, safe_cutoff: '2026-08-01T00:00:00Z' } },
    { question: { ...matching.question, venue: 'binance' as const } },
    { base_source_fingerprint: 'changed' },
    { asset_a_path: { ...matching.asset_a_path, semantic_fingerprint: 'changed' } },
    { asset_b_path: { ...matching.asset_b_path, dataset_id: 'new-generation' } },
  ])('rejects a series from a different context', (patch) => {
    expect(pairStudySeriesMatchesContext(pairContext, { ...matching, ...patch })).toBe(false)
  })

  it('rejects a missing analysis reference when that lens was requested and ready', () => {
    const context = { ...pairContext, analysis_lens: { status: 'ready' as const, asset: 'BTC',
      generation: pairContext.data.asset_a_path!, reason: null } }
    expect(pairStudySeriesMatchesContext(context, matching)).toBe(false)
  })

  it('accepts a recipe bound to the same pair, horizon, cutoff, interval, and source generations', () => {
    expect(pairRecipeMatchesContext(pairContext, pairDraft)).toBe(true)
  })

  it.each([
    { assets: ['PIXEL', 'W'] },
    { data: { ...pairDraft.data, horizon: 'short' as const } },
    { data: { ...pairDraft.data, interval: '1h' } },
    { data: { ...pairDraft.data, evaluation_window: { ...pairDraft.data.evaluation_window!, end: '2026-08-01T00:00:00Z' } } },
    { data: { ...pairDraft.data, generations: pairDraft.data.generations.slice(0, 1) } },
    { data: { ...pairDraft.data, generations: pairDraft.data.generations.map((binding, index) => index === 0
      ? { ...binding, semantic_fingerprint: 'changed' } : binding) } },
  ])('rejects a recipe declared for a different relationship snapshot', (patch) => {
    expect(pairRecipeMatchesContext(pairContext, { ...pairDraft, ...patch })).toBe(false)
  })
})
