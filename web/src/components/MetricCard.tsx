import type { ReactNode } from 'react'

interface MetricCardProps {
  label: string
  value: ReactNode
  detail?: ReactNode
  status?: 'positive' | 'neutral' | 'negative' | 'informational'
}

export function MetricCard({
  label,
  value,
  detail,
  status = 'informational',
}: MetricCardProps) {
  return (
    <article className="metric-card" data-status={status}>
      <p className="metric-card__label">{label}</p>
      <p className="metric-card__value">{value}</p>
      {detail ? <p className="metric-card__detail">{detail}</p> : null}
    </article>
  )
}
