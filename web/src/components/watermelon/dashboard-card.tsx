import type { ReactNode } from 'react'

import { cn } from '@/lib/utils'

export function DashboardCard({
  children,
  className,
  ...props
}: React.ComponentProps<'section'>) {
  return (
    <section
      className={cn(
        'shadow-primary min-w-0 rounded-xl border border-border bg-card p-4 text-card-foreground',
        className,
      )}
      {...props}
    >
      {children}
    </section>
  )
}

export function DetailHeader({
  title,
  subtitle,
  children,
  className,
}: {
  title: ReactNode
  subtitle?: ReactNode
  children?: ReactNode
  className?: string
}) {
  return (
    <div className={cn('flex min-w-0 flex-wrap items-start justify-between gap-3', className)}>
      <div className="min-w-0 flex-1">
        <h2 className="m-0 truncate text-sm font-semibold leading-5 text-foreground">{title}</h2>
        {subtitle ? (
          <div className="mt-1 truncate text-xs leading-4 text-muted-foreground">{subtitle}</div>
        ) : null}
      </div>
      {children ? (
        <div className="flex min-w-0 flex-wrap items-center justify-end gap-2">{children}</div>
      ) : null}
    </div>
  )
}

export function DetailTag({
  children,
  tone = 'info',
  className,
}: {
  children: ReactNode
  tone?: 'positive' | 'negative' | 'warning' | 'info' | 'neutral'
  className?: string
}) {
  const toneStyle =
    tone === 'positive'
      ? 'bg-positive/12 text-positive border-positive/30'
      : tone === 'negative'
        ? 'bg-negative/12 text-negative border-negative/30'
        : tone === 'warning'
          ? 'bg-warning/12 text-warning border-warning/30'
          : tone === 'info'
            ? 'bg-info/12 text-info border-info/30'
            : 'bg-muted text-muted-foreground border-border'

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-md border px-2 py-0.5 font-mono text-xs font-medium tabular-nums',
        toneStyle,
        className,
      )}
    >
      {children}
    </span>
  )
}
