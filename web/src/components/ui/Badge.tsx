import type { ReactNode } from 'react'

export type BadgeTone = 'positive' | 'negative' | 'neutral' | 'warning' | 'info'

interface BadgeProps {
  children: ReactNode
  tone?: BadgeTone
}

const toneClasses: Record<BadgeTone, string> = {
  positive: 'border-positive/45 bg-positive/10 text-positive',
  negative: 'border-negative/45 bg-negative/10 text-negative',
  neutral: 'border-border-strong bg-subtle text-secondary',
  warning: 'border-warning/45 bg-warning/10 text-warning',
  info: 'border-info/45 bg-info/10 text-info',
}

export function Badge({ children, tone = 'neutral' }: BadgeProps) {
  return (
    <span
      className={`inline-flex min-h-6 items-center rounded-full border px-2 py-0.5 text-xs font-semibold tracking-wide ${toneClasses[tone]}`}
    >
      {children}
    </span>
  )
}
