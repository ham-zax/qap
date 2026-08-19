import type { OperationDto } from '../../api/types'

export function operationStatusTone(
  status: OperationDto['status'],
): 'neutral' | 'warning' | 'negative' | 'info' {
  if (status === 'completed') return 'neutral'
  if (status === 'running') return 'info'
  if (status === 'interrupted') return 'warning'
  return 'negative'
}

export function operationStatusLabel(status: OperationDto['status']): string {
  if (status === 'completed') return 'Completed'
  if (status === 'running') return 'In progress'
  if (status === 'interrupted') return 'Interrupted'
  return 'Failed to run'
}

export function operationKindLabel(kind: string): string {
  const labels: Record<string, string> = {
    run_scan: 'Find research ideas',
    generate_asset_momentum: 'Update pair-blind market context',
    freeze_forward_cohort: 'Start forward validation',
    advance_forward_cohort: 'Update forward evidence',
    capture_public_evidence: 'Update current market evidence',
    qualify_candidate: 'Evaluate amount',
    run_basket: 'Analyze portfolio',
  }
  return labels[kind] ?? kind.replaceAll('_', ' ')
}

export function operationDuration(operation: OperationDto): string {
  const started = new Date(operation.started_at).getTime()
  const finished = operation.finished_at
    ? new Date(operation.finished_at).getTime()
    : Date.now()
  const seconds = Math.max(0, Math.round((finished - started) / 1000))
  if (seconds < 60) return `${seconds}s`
  const minutes = Math.floor(seconds / 60)
  return `${minutes}m ${seconds % 60}s`
}

export function operationResultLinks(operation: OperationDto) {
  const result = operation.result ?? {}
  const links: { label: string; href: string }[] = []
  const scanId = typeof result.scan_id === 'string' ? result.scan_id : null
  const sourceScanId =
    typeof result.source_scan_id === 'string' ? result.source_scan_id : null
  const cohortId = typeof result.cohort_id === 'string' ? result.cohort_id : null
  const basketId = typeof result.basket_id === 'string' ? result.basket_id : null
  const qapRunId = typeof result.qap_run_id === 'string' ? result.qap_run_id : null

  if (scanId) links.push({ label: 'Research ideas', href: `/scanner/${scanId}` })
  if (!scanId && sourceScanId) {
    links.push({ label: 'Historical research', href: `/scanner/${sourceScanId}` })
  }
  if (cohortId) {
    links.push({ label: 'Forward validation', href: `/prospective/${cohortId}` })
  }
  if (basketId) links.push({ label: 'Portfolio result', href: `/baskets/${basketId}` })
  if (qapRunId) {
    links.push({ label: 'Research run', href: `/experiments/${qapRunId}` })
    links.push({ label: 'Portfolio economics', href: `/portfolio/${qapRunId}` })
  }
  return links
}
