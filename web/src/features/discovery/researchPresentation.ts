export function researchMethodName(id: string): string {
  if (id === 'rolling_log_ratio_zscore') return 'Price-ratio mean reversion'
  if (id === 'residual_mean_reversion') return 'Regression-residual mean reversion'
  if (id === 'cross_sectional_relative_log_return') return 'Relative momentum'
  return id.replaceAll('_', ' ')
}

export function researchMethodDescription(id: string): string {
  if (id === 'rolling_log_ratio_zscore') return 'Tests rebalancing when the price ratio moves away from its recent average.'
  if (id === 'residual_mean_reversion') return 'Tests rebalancing when the relationship departs from its recent fitted pattern. This is not a formal cointegration test.'
  return 'Uses the declared relationship method and allocation rule.'
}

export type RelationshipMetricKind = 'ratio' | 'residual'
export type RelationshipBand = 'near_reference' | 'noticeable_displacement' | 'large_displacement' | 'unavailable'
export interface RelationshipInterpretation {
  kind: RelationshipMetricKind
  score: number | null
  band: RelationshipBand
  tone: 'neutral' | 'info' | 'warning'
  label: string
  direction: string | null
  explanation: string
}

export function interpretRelationshipScore(
  kind: RelationshipMetricKind,
  status: 'valid' | 'insufficient_history' | 'insufficient_variance',
  score: number | undefined,
): RelationshipInterpretation {
  if (status !== 'valid' || score === undefined || !Number.isFinite(score)) {
    const explanation = status === 'insufficient_history' ? 'Not enough history at this cutoff.'
      : status === 'insufficient_variance' ? 'The measured series did not vary enough at this cutoff.'
        : 'No valid finite score was returned at this cutoff.'
    return { kind, score: null, band: 'unavailable', tone: 'neutral', label: 'Unavailable', direction: null, explanation }
  }
  const magnitude = Math.abs(score)
  const band = magnitude < 1 ? 'near_reference' : magnitude < 2 ? 'noticeable_displacement' : 'large_displacement'
  const direction = score < 0
    ? kind === 'ratio' ? 'below its recent reference level' : 'below its fitted relationship'
    : score > 0
      ? kind === 'ratio' ? 'above its recent reference level' : 'above its fitted relationship'
      : null
  const label = band === 'near_reference' ? 'Near reference'
    : band === 'noticeable_displacement' ? 'Noticeable displacement' : 'Large displacement'
  const explanation = band === 'near_reference' ? 'Close to the reference in the selected historical window.'
    : `The measure is ${direction ?? 'away from its reference'}; this is descriptive, not a trading signal.`
  return { kind, score, band, tone: band === 'large_displacement' ? 'warning' : band === 'noticeable_displacement' ? 'info' : 'neutral', label, direction, explanation }
}

export function relationshipSummary(ratio: RelationshipInterpretation, residual: RelationshipInterpretation): string {
  const ratioAvailable = ratio.band !== 'unavailable'
  const residualAvailable = residual.band !== 'unavailable'
  if (!ratioAvailable && !residualAvailable) return `Neither relationship measure could be interpreted at this cutoff. ${ratio.explanation} ${residual.explanation}`
  if (!ratioAvailable) return `The price-ratio measure could not be interpreted at this cutoff. The residual is ${residual.label.toLowerCase()} ${residual.direction ?? ''}.`.trim()
  if (!residualAvailable) return `The residual measure could not be interpreted at this cutoff. The price ratio is ${ratio.label.toLowerCase()} ${ratio.direction ?? ''}.`.trim()
  if (ratio.band === 'near_reference' && residual.band === 'near_reference') return 'Both relationship measures are close to their recent or fitted references.'
  if (ratio.band !== 'near_reference' && residual.band === 'near_reference') return 'The price ratio is displaced, while the residual model remains near its fitted relationship.'
  if (ratio.band === 'near_reference' && residual.band !== 'near_reference') return 'The residual model is displaced, while the price ratio remains near its recent reference level.'
  if (Math.sign(ratio.score ?? 0) === Math.sign(residual.score ?? 0)) return 'Both relationship measures are displaced in the same direction.'
  return 'The relationship measures point in different directions; inspect the chart and model details.'
}
