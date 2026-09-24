import type { ProductPairStudyContextDto, ProductPairStudySeriesDto, ResearchRecipeDraftV1 } from '../../api/types'

/** Separate API reads are only one result when their question and source generations agree. */
export function pairStudySeriesMatchesContext(
  context: ProductPairStudyContextDto, series: ProductPairStudySeriesDto,
): boolean {
  const a = context.data.asset_a_path
  const b = context.data.asset_b_path
  if (!a || !b) return false
  const question = context.question
  const other = series.question
  return question.asset_a === other.asset_a
    && question.asset_b === other.asset_b
    && question.orientation === other.orientation
    && question.horizon === other.horizon
    && question.interval === other.interval
    && question.venue === other.venue
    && question.coordinate_asset === other.coordinate_asset
    && question.safe_cutoff === other.safe_cutoff
    && a.dataset_id === series.asset_a_path.dataset_id
    && b.dataset_id === series.asset_b_path.dataset_id
    && a.semantic_fingerprint === series.asset_a_path.semantic_fingerprint
    && b.semantic_fingerprint === series.asset_b_path.semantic_fingerprint
    && a.semantic_fingerprint === series.base_source_fingerprint
    && b.semantic_fingerprint === series.quote_source_fingerprint
    && (context.analysis_lens?.status !== 'ready' || (
      context.analysis_lens.asset === series.analysis_reference?.asset
      && context.analysis_lens.generation?.dataset_id === series.analysis_reference?.generation.dataset_id
      && context.analysis_lens.generation?.semantic_fingerprint === series.analysis_reference?.generation.semantic_fingerprint
    ))
}

/** The recipe is independently declared; never present or run it as this read's economics if its data moved. */
export function pairRecipeMatchesContext(
  context: ProductPairStudyContextDto, recipe: ResearchRecipeDraftV1,
): boolean {
  const a = context.data.asset_a_path
  const b = context.data.asset_b_path
  const cutoff = context.question.safe_cutoff
  if (context.data.status !== 'ready' || !a || !b || !cutoff) return false
  const bindings = recipe.data.generations
  const hasPath = (path: NonNullable<typeof a>) => bindings.some((binding) =>
    binding.dataset_id === path.dataset_id
    && binding.semantic_fingerprint === path.semantic_fingerprint)
  return recipe.research_object === 'pair'
    && recipe.assets.length === 2
    && recipe.assets[0] === context.question.asset_a
    && recipe.assets[1] === context.question.asset_b
    && recipe.data.authority === 'pair_study'
    && recipe.data.horizon === context.question.horizon
    && recipe.data.interval === context.question.interval
    && recipe.data.data_window.end === cutoff
    && recipe.data.evaluation_window?.end === cutoff
    && hasPath(a) && hasPath(b)
}
