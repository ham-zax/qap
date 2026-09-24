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
