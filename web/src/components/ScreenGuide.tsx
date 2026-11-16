import { HelpCircle } from 'lucide-react'

import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

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
    <Card className="gap-2 rounded-lg bg-muted/40 py-3.5 shadow-none">
      <CardHeader className="px-4 pb-0">
        <CardTitle className="text-xs font-semibold uppercase tracking-[0.08em] text-muted-foreground">
          {label}
        </CardTitle>
      </CardHeader>
      <CardContent className="px-4 text-sm leading-6 text-foreground/85">{children}</CardContent>
    </Card>
  )
}

export function ScreenGuide({ guide }: { guide: ScreenGuideContent }) {
  return (
    <Accordion type="single" collapsible className="mt-10 border-t border-border pt-2">
      <AccordionItem value="screen-guide" className="border-b-0">
        <AccordionTrigger className="py-3 text-sm text-muted-foreground hover:text-foreground hover:no-underline">
          <span className="inline-flex items-center gap-2">
            <HelpCircle className="size-4" aria-hidden="true" />
            Help with this page
          </span>
        </AccordionTrigger>
        <AccordionContent className="space-y-4 pb-2">
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            <GuideItem label="Intent">{guide.intent}</GuideItem>
            <GuideItem label="What to do">{guide.action}</GuideItem>
            <GuideItem label="Example">{guide.example}</GuideItem>
            <GuideItem label="What happens next">{guide.next}</GuideItem>
          </div>
          <Alert className="border-warning/40 bg-warning/5">
            <AlertTitle className="text-xs font-semibold uppercase tracking-wide text-warning">
              This does not mean:
            </AlertTitle>
            <AlertDescription className="text-sm text-foreground/85">
              {guide.boundary}
            </AlertDescription>
          </Alert>
        </AccordionContent>
      </AccordionItem>
    </Accordion>
  )
}
