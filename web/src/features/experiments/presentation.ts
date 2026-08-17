import type { BadgeTone } from '../../components/ui/Badge'
import { formatRelativePercent } from '../../lib/format'

export function humanizeIdentifier(value: string | null | undefined): string {
  if (!value) return 'Unknown'
  return value
    .split('_')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ')
}

export function researchStatusPresentation(status: string | null | undefined): {
  label: string
  tone: BadgeTone
} {
  switch (status) {
    case 'positive':
      return { label: 'Positive evidence', tone: 'positive' }
    case 'negative':
      return { label: 'Negative evidence', tone: 'negative' }
    case 'neutral':
      return { label: 'Neutral evidence', tone: 'neutral' }
    case 'rejected':
      return { label: 'Rejected', tone: 'warning' }
    default:
      return { label: humanizeIdentifier(status), tone: 'neutral' }
  }
}

export function researchComparisonTone(
  status: string | null | undefined,
  delta: string | null | undefined,
): BadgeTone {
  const numeric = delta == null ? Number.NaN : Number(delta)
  if (status === 'negative' && Number.isFinite(numeric) && numeric > 0) {
    return 'warning'
  }
  return researchStatusPresentation(status).tone
}

export function experimentDataRoleLabel(
  role: string | null | undefined,
  consumed: boolean | null | undefined,
): string {
  if (role === 'final_oos') {
    return `Final OOS · ${consumed ? 'consumed' : 'unconsumed'}`
  }
  return humanizeIdentifier(role)
}

export function researchVerdictHeadline(
  status: string,
  benchmark: string | null | undefined,
  delta: string | null | undefined,
): string {
  const benchmarkLabel = humanizeIdentifier(benchmark ?? 'primary control')
  if (!delta) return `${humanizeIdentifier(status)} evidence against ${benchmarkLabel}`

  const formatted = formatRelativePercent(delta).display
  const magnitude = formatted.replace(/^[+−]/, '')
  const numeric = Number(delta)

  if (status === 'negative') {
    return Number.isFinite(numeric) && numeric < 0
      ? `Underperformed ${benchmarkLabel} by ${magnitude}`
      : `Did not clear the research threshold against ${benchmarkLabel}`
  }

  if (status === 'positive') {
    return Number.isFinite(numeric) && numeric > 0
      ? `Outperformed ${benchmarkLabel} by ${magnitude}`
      : `Positive evidence against ${benchmarkLabel}`
  }

  if (status === 'neutral') {
    return `No material advantage over ${benchmarkLabel}`
  }

  return `${humanizeIdentifier(status)} evidence against ${benchmarkLabel}`
}
