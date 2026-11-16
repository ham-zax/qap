import { ArrowUpRight, CheckCircle2, Clock, TriangleAlert, XCircle } from 'lucide-react'

import type { OperationListDto } from '../../api/types'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { StatusPill } from '@/components/watermelon/live-badge'
import { formatResearchTimestamp } from '../../lib/format'
import {
  operationDuration,
  operationKindLabel,
  operationStatusLabel,
  operationStatusTone,
} from './presentation'

interface OperationListProps {
  data: OperationListDto
}

function shortId(value: string) {
  return value.length <= 18 ? value : `${value.slice(0, 10)}…${value.slice(-6)}`
}

export function OperationList({ data }: OperationListProps) {
  return (
    <section className="min-w-0 space-y-6">
      <header className="max-w-4xl border-b border-border pb-6">
        <p className="mb-2 text-xs font-semibold uppercase tracking-[0.1em] text-primary">
          Activity
        </p>
        <h1 className="mb-3 text-3xl font-bold tracking-tight text-foreground md:text-4xl">
          Background activity
        </h1>
        <p className="m-0 text-sm leading-6 text-muted-foreground md:text-base">
          Follow tasks started from the Lab. Activity tells you whether the work ran; the
          resulting research evidence is separate and may still be negative or rejected.
        </p>
      </header>

      {data.items.length === 0 ? (
        <Card className="shadow-primary py-8 text-center">
          <CardContent className="text-sm text-muted-foreground">
            No background activity has been started yet.
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {data.items.map((operation) => {
            const tone = operationStatusTone(operation.status)
            const pillTone =
              operation.status === 'completed'
                ? 'positive'
                : tone === 'negative'
                  ? 'negative'
                  : tone === 'warning'
                    ? 'warning'
                    : 'info'
            const StatusIcon =
              operation.status === 'completed'
                ? CheckCircle2
                : tone === 'negative'
                  ? XCircle
                  : tone === 'warning'
                    ? TriangleAlert
                    : Clock

            return (
              <Card
                key={operation.operation_id}
                className="shadow-primary gap-3 rounded-xl py-4"
              >
                <CardHeader className="flex flex-row flex-wrap items-start justify-between gap-4 px-5 pb-0">
                  <div className="space-y-2">
                    <div className="flex flex-wrap items-center gap-2">
                      <StatusPill
                        label={operationStatusLabel(operation.status)}
                        tone={pillTone}
                        icon={StatusIcon}
                      />
                      <Badge variant="secondary" className="rounded-md font-medium">
                        {operationKindLabel(operation.kind)}
                      </Badge>
                    </div>
                    <CardTitle className="text-base font-semibold text-foreground">
                      {operationKindLabel(operation.kind)}
                    </CardTitle>
                    <p className="m-0 text-sm text-muted-foreground">
                      Requested {formatResearchTimestamp(operation.requested_at)} ·{' '}
                      {operationDuration(operation)}
                    </p>
                    <p className="m-0 font-mono text-xs text-muted-foreground">
                      Activity {shortId(operation.operation_id)}
                    </p>
                  </div>
                  <Button asChild variant="outline" size="sm">
                    <a href={`/operations/${operation.operation_id}`} className="no-underline">
                      Review activity
                      <ArrowUpRight className="size-3.5" aria-hidden="true" />
                    </a>
                  </Button>
                </CardHeader>
                {operation.failure ? (
                  <CardContent className="px-5 pt-1">
                    <Alert variant="destructive" className="border-destructive/40 bg-destructive/5">
                      <XCircle className="size-4" aria-hidden="true" />
                      <AlertTitle className="text-sm">
                        The task failed to run: {operation.failure.message}
                      </AlertTitle>
                      <AlertDescription className="text-xs text-muted-foreground">
                        This operational failure does not determine the scientific result.
                      </AlertDescription>
                    </Alert>
                  </CardContent>
                ) : null}
              </Card>
            )
          })}
        </div>
      )}
    </section>
  )
}
