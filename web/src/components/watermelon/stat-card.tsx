import type { ReactNode } from 'react'
import type { LucideIcon } from 'lucide-react'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { cn } from '@/lib/utils'

const TONE_BADGE: Record<'info' | 'positive' | 'warning' | 'neutral', string> = {
  info: 'bg-info/15 text-info',
  positive: 'bg-positive/15 text-positive',
  warning: 'bg-warning/15 text-warning',
  neutral: 'bg-muted text-muted-foreground',
}

export function StatCard({
  label,
  value,
  sub,
  icon: Icon,
  tone = 'info',
  tip,
  className,
}: {
  label: string
  value: ReactNode
  sub?: ReactNode
  icon?: LucideIcon
  tone?: 'info' | 'positive' | 'warning' | 'neutral'
  tip?: ReactNode
  className?: string
}) {
  return (
    <Card
      className={cn(
        'shadow-primary min-w-0 gap-2 rounded-xl border-border bg-card py-3.5 ring-0',
        className,
      )}
    >
      <CardHeader className="flex flex-row items-center justify-between gap-2 px-4 pb-0">
        <div className="flex min-w-0 items-center gap-2">
          {Icon ? (
            <span
              className={cn(
                'flex size-6 shrink-0 items-center justify-center rounded-full shadow-[inset_0_1px_4px_rgba(255,255,255,0.2)]',
                TONE_BADGE[tone],
              )}
            >
              <Icon className="size-3.5" aria-hidden="true" />
            </span>
          ) : null}
          <CardTitle className="truncate text-xs font-medium text-muted-foreground">
            {label}
          </CardTitle>
        </div>
        {tip ? <div className="shrink-0">{tip}</div> : null}
      </CardHeader>
      <CardContent className="flex flex-col gap-1 px-4">
        <div className="font-mono text-lg font-semibold tracking-tight text-foreground tabular-nums">
          {value}
        </div>
        {sub ? <div className="text-xs text-muted-foreground">{sub}</div> : null}
      </CardContent>
    </Card>
  )
}
