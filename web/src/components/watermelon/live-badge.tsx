import type { LucideIcon } from 'lucide-react'

import { cn } from '@/lib/utils'

export function LiveBadge({
  live,
  label,
  size = 'md',
  className,
}: {
  live: boolean
  label?: string
  size?: 'sm' | 'md'
  className?: string
}) {
  const text = label ?? (live ? 'Active' : 'Stopped')
  return (
    <span
      className={cn(
        'inline-flex items-center justify-center rounded-lg font-medium',
        live ? 'bg-positive/12 text-positive' : 'bg-muted text-muted-foreground',
        size === 'md' && 'gap-1.5 px-2.5 py-1 text-xs leading-4',
        size === 'sm' && 'gap-1 px-2 py-0.5 text-[11px] leading-4',
        className,
      )}
    >
      <span
        aria-hidden="true"
        className={cn(
          'rounded-full',
          live ? 'bg-positive animate-pulse' : 'bg-muted-foreground',
          size === 'md' ? 'size-2' : 'size-1.5',
        )}
      />
      {text}
    </span>
  )
}

export function StatusPill({
  label,
  tone = 'neutral',
  icon: Icon,
  className,
}: {
  label: string
  tone?: 'positive' | 'negative' | 'warning' | 'info' | 'neutral'
  icon?: LucideIcon
  className?: string
}) {
  const toneClass =
    tone === 'positive'
      ? 'bg-positive/12 text-positive'
      : tone === 'negative'
        ? 'bg-negative/12 text-negative'
        : tone === 'warning'
          ? 'bg-warning/12 text-warning'
          : tone === 'info'
            ? 'bg-info/12 text-info'
            : 'bg-muted text-muted-foreground'

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs font-medium',
        toneClass,
        className,
      )}
    >
      {Icon ? <Icon className="size-3.5 shrink-0" aria-hidden="true" /> : null}
      {label}
    </span>
  )
}
