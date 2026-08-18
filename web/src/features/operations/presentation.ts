import type { OperationDto } from '../../api/types'

export function operationStatusTone(
  status: OperationDto['status'],
): 'positive' | 'warning' | 'negative' | 'info' {
  if (status === 'completed') return 'positive'
  if (status === 'running') return 'info'
  if (status === 'interrupted') return 'warning'
  return 'negative'
}

export function operationKindLabel(kind: string): string {
  return kind
    .split('_')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ')
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

  if (scanId) links.push({ label: 'Scan evidence', href: `/scanner/${scanId}` })
  if (!scanId && sourceScanId) {
    links.push({ label: 'Source scan', href: `/scanner/${sourceScanId}` })
  }
  if (cohortId) {
    links.push({ label: 'Prospective cohort', href: `/prospective/${cohortId}` })
  }
  if (basketId) links.push({ label: 'Basket evidence', href: `/baskets/${basketId}` })
  if (qapRunId) {
    links.push({ label: 'QAP experiment', href: `/experiments/${qapRunId}` })
    links.push({ label: 'Portfolio economics', href: `/portfolio/${qapRunId}` })
  }
  return links
}
