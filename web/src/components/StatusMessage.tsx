import type { ReactNode } from 'react'

type StatusTone = 'info' | 'warning' | 'error'

interface StatusMessageProps {
  title: string
  tone?: StatusTone
  children: ReactNode
  action?: ReactNode
}

export function StatusMessage({
  title,
  tone = 'info',
  children,
  action,
}: StatusMessageProps) {
  return (
    <section className="status-message" data-tone={tone} aria-live="polite">
      <h1>{title}</h1>
      <div>{children}</div>
      {action ? <div className="status-message__action">{action}</div> : null}
    </section>
  )
}
