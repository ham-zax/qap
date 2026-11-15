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
    refresh_coin_directory: 'Refresh coin directory',
    prepare_pair_rotation_data: 'Prepare pair market data',
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
