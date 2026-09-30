import type { ReactNode } from 'react'

interface CardProps {
  title?: string
  description?: ReactNode
  action?: ReactNode
  children?: ReactNode
  labelledBy?: string
}

export function Card({ title, description, action, children, labelledBy }: CardProps) {
  const headingId = labelledBy ?? (title ? `card-${title.toLowerCase().replace(/[^a-z0-9]+/g, '-')}` : undefined)
  return (
    <section
      className="min-w-0 rounded-lg border border-border bg-panel p-5 shadow-card md:p-6"
      aria-labelledby={title ? headingId : undefined}
    >
      {title || action ? (
        <header className="mb-4 flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            {title ? (
              <h2 id={headingId} className="m-0 text-lg font-semibold text-foreground">
                {title}
              </h2>
            ) : null}
            {description ? <p className="mt-1 mb-0 max-w-3xl text-sm leading-6 text-secondary">{description}</p> : null}
          </div>
          {action ? <div className="shrink-0">{action}</div> : null}
        </header>
      ) : null}
      {children}
    </section>
  )
}

interface StatProps {
  label: string
  value: ReactNode
  detail?: ReactNode
  tone?: 'neutral' | 'positive' | 'negative'
}

const statTone = {
  neutral: 'text-foreground',
  positive: 'text-positive',
  negative: 'text-negative',
} as const

export function Stat({ label, value, detail, tone = 'neutral' }: StatProps) {
  return (
    <div className="min-w-0 rounded-md border border-border bg-subtle px-4 py-3">
      <p className="m-0 text-xs font-medium tracking-wide text-muted uppercase">{label}</p>
      <p className={`mt-1 mb-0 font-mono text-xl font-semibold tabular-nums ${statTone[tone]}`}>{value}</p>
      {detail ? <p className="mt-1 mb-0 text-xs text-secondary">{detail}</p> : null}
    </div>
  )
}
