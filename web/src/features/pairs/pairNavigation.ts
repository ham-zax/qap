import type { ExperimentDetailDto } from '../../api/types'

export function pairWorkbenchHref(
  experiment: ExperimentDetailDto,
  pair: readonly [string, string],
): string {
  const [assetX, assetY] = pair
  const search = new URLSearchParams({
    orientation: `${assetX}/${assetY}`,
    anchor: experiment.manifest.analysis_anchor ?? 'none',
    view: 'ratio',
  })
  return `/pair/${encodeURIComponent(experiment.run_id)}/${encodeURIComponent(assetX)}/${encodeURIComponent(assetY)}?${search}`
}
