interface ScreenGuideContent {
  intent: string
  action: string
  example: string
  next: string
  boundary: string
}

const guides = {
  operations: {
    intent: 'Monitor background operational tasks separately from scientific research results.',
    action:
      'Check which task is running, completed, failed, or interrupted. Open a task when you need its failure reason or its exact result metadata.',
    example:
      'A market-data or research task can fail because of an operational problem even though no negative scientific conclusion was reached.',
    next: 'Return to the Lab to retry or continue after resolving the operational issue.',
    boundary:
      'Activity status is operational state. Failed or interrupted does not mean the research hypothesis was rejected.',
  },
  operationDetail: {
    intent: 'Diagnose one background operation and read the exact result it produced, if any.',
    action:
      'Read status and failure information first, then timing, request summary, and the exact result metadata when one exists.',
    example:
      'An interrupted data preparation has an operational record but no implied scientific conclusion.',
    next: 'Return to the Lab for the next valid action.',
    boundary:
      'The operation record reports execution state; it is not the scientific or economic authority for the resulting artifact.',
  },
} satisfies Record<string, ScreenGuideContent>

function normalizedPath(pathname: string) {
  if (pathname === '/') return pathname
  return pathname.replace(/\/+$/, '')
}

export function screenGuideForPath(pathname: string): ScreenGuideContent | null {
  const path = normalizedPath(pathname)
  const parts = path.split('/').filter(Boolean)

  if (parts[0] !== 'operations') return null
  return parts.length === 1 ? guides.operations : guides.operationDetail
}

function GuideItem({ label, children }: { label: string; children: string }) {
  return (
    <div className="rounded-md border border-border bg-canvas/40 p-4">
      <p className="m-0 text-xs font-semibold uppercase tracking-[0.08em] text-muted">
        {label}
      </p>
      <p className="mt-2 mb-0 text-sm leading-6 text-secondary">{children}</p>
    </div>
  )
}

export function ScreenGuide({ guide }: { guide: ScreenGuideContent }) {
  return (
    <details className="mt-12 border-t border-border pt-4">
      <summary className="min-h-11 cursor-pointer py-2 text-sm text-muted">
        Help with this page
      </summary>
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <GuideItem label="Intent">{guide.intent}</GuideItem>
        <GuideItem label="What to do">{guide.action}</GuideItem>
        <GuideItem label="Example">{guide.example}</GuideItem>
        <GuideItem label="What happens next">{guide.next}</GuideItem>
      </div>
      <p className="mt-4 mb-0 rounded-md border border-warning/35 bg-canvas/35 p-3 text-sm leading-6 text-secondary">
        <strong className="text-foreground">This does not mean:</strong> {guide.boundary}
      </p>
    </details>
  )
}
