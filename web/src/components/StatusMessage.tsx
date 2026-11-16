import { AlertCircle, AlertTriangle, Info } from 'lucide-react'
import type { ReactNode } from 'react'

import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { cn } from '@/lib/utils'

type StatusTone = 'info' | 'warning' | 'error'

interface StatusMessageProps {
  title: string
  tone?: StatusTone
  children: ReactNode
  action?: ReactNode
}

const TONE_CLASSES: Record<StatusTone, string> = {
  info: 'border-border',
  warning: 'border-warning/60',
  error: 'border-destructive/70 border-dashed',
}

export function StatusMessage({
  title,
  tone = 'info',
  children,
  action,
}: StatusMessageProps) {
  const Icon = tone === 'error' ? AlertCircle : tone === 'warning' ? AlertTriangle : Info
  const iconTone =
    tone === 'error' ? 'text-destructive' : tone === 'warning' ? 'text-warning' : 'text-info'

  return (
    <Card
      className={cn('shadow-primary max-w-4xl rounded-xl py-5', TONE_CLASSES[tone])}
      data-tone={tone}
      aria-live="polite"
    >
      <CardHeader className="flex flex-row items-center gap-3 pb-0">
        <Icon className={cn('size-5 shrink-0', iconTone)} aria-hidden="true" />
        <CardTitle>
          <h1 className="m-0 text-xl font-semibold tracking-tight text-foreground">{title}</h1>
        </CardTitle>
      </CardHeader>
      <CardContent className="text-sm text-muted-foreground">{children}</CardContent>
      {action ? <CardFooter>{action}</CardFooter> : null}
    </Card>
  )
}
