import { CheckCircle2, Clock, TriangleAlert, XCircle } from 'lucide-react'

import type { OperationDto } from '../../api/types'
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { StatusPill } from '@/components/watermelon/live-badge'
import { formatResearchTimestamp } from '../../lib/format'
import {
  operationDuration,
  operationKindLabel,
  operationStatusLabel,
  operationStatusTone,
} from './presentation'

interface OperationDetailProps {
  data: OperationDto
}

function renderValue(value: unknown): string {
  if (value === null) return 'null'
  if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
    return String(value)
  }
  return JSON.stringify(value)
}

export function OperationDetail({ data }: OperationDetailProps) {
  const tone = operationStatusTone(data.status)
  const pillTone =
    data.status === 'completed'
      ? 'positive'
      : tone === 'negative'
        ? 'negative'
        : tone === 'warning'
          ? 'warning'
          : 'info'
  const StatusIcon =
    data.status === 'completed'
      ? CheckCircle2
      : tone === 'negative'
        ? XCircle
        : tone === 'warning'
          ? TriangleAlert
          : Clock

  return (
    <section className="min-w-0 space-y-6">
      <header className="max-w-4xl border-b border-border pb-6">
        <p className="mb-2 text-xs font-semibold uppercase tracking-[0.1em] text-primary">
          Activity record
        </p>
        <h1 className="mb-3 text-3xl font-bold tracking-tight text-foreground md:text-4xl">
          {operationKindLabel(data.kind)}
        </h1>
        <div className="flex flex-wrap items-center gap-2">
          <StatusPill
            label={operationStatusLabel(data.status)}
            tone={pillTone}
            icon={StatusIcon}
          />
          <Badge variant="secondary" className="rounded-md font-mono">
            {operationDuration(data)}
          </Badge>
        </div>
      </header>

      {data.status === 'running' ? (
        <Alert className="border-primary/40 bg-primary/5" aria-live="polite">
          <Clock className="size-4 text-primary" aria-hidden="true" />
          <AlertTitle className="text-sm font-medium text-foreground">
            Background work is still running.
          </AlertTitle>
          <AlertDescription className="text-xs text-muted-foreground">
            Research evidence remains separate and readable.
          </AlertDescription>
        </Alert>
      ) : null}

      {data.failure ? (
        <Alert
          variant="destructive"
          className="border-destructive/45 bg-destructive/5"
          aria-labelledby="failure-heading"
        >
          <XCircle className="size-4" aria-hidden="true" />
          <AlertTitle id="failure-heading" className="text-base font-semibold">
            Operational failure
          </AlertTitle>
          <AlertDescription className="space-y-1 text-sm">
            <p className="m-0 text-foreground">
              {data.failure.code}: {data.failure.message}
            </p>
            <p className="m-0 text-xs text-muted-foreground">
              Scientific evidence is not inferred from this operational failure.
            </p>
          </AlertDescription>
        </Alert>
      ) : null}

      <div className="grid gap-5 lg:grid-cols-2">
        <Card className="shadow-primary gap-2 rounded-xl py-5" aria-labelledby="result-heading">
          <CardHeader className="px-5 pb-0">
            <CardTitle id="result-heading" className="text-base font-semibold text-foreground">
              Research evidence created
            </CardTitle>
          </CardHeader>
          <CardContent className="px-5 text-sm leading-6 text-muted-foreground">
            A completed activity status does not imply a positive research verdict. Read the
            exact result metadata below for the persisted references this task produced.
          </CardContent>
        </Card>

        <Card className="shadow-primary gap-2 rounded-xl py-5" aria-labelledby="timing-heading">
          <CardHeader className="px-5 pb-0">
            <CardTitle id="timing-heading" className="text-base font-semibold text-foreground">
              Lifecycle
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-1 px-5 text-sm text-muted-foreground">
            <p className="m-0">Requested {formatResearchTimestamp(data.requested_at)}</p>
            <p className="m-0">Started {formatResearchTimestamp(data.started_at)}</p>
            <p className="m-0">
              {data.finished_at
                ? `Finished ${formatResearchTimestamp(data.finished_at)}`
                : 'Still running'}
            </p>
          </CardContent>
        </Card>
      </div>

      <Card className="shadow-primary rounded-xl py-2">
        <CardContent className="px-5">
          <Accordion type="single" collapsible>
            <AccordionItem value="metadata" className="border-b-0">
              <AccordionTrigger className="py-3 text-sm font-semibold text-foreground hover:no-underline">
                Exact activity request and result metadata
              </AccordionTrigger>
              <AccordionContent className="space-y-5 pt-2 pb-4">
                <dl className="m-0 grid gap-3 text-sm sm:grid-cols-2">
                  <div className="rounded-lg border border-border bg-muted/40 p-3">
                    <dt className="text-xs font-semibold uppercase tracking-[0.06em] text-muted-foreground">
                      operation kind
                    </dt>
                    <dd className="m-0 mt-1 font-mono text-xs text-foreground">{data.kind}</dd>
                  </div>
                  <div className="rounded-lg border border-border bg-muted/40 p-3">
                    <dt className="text-xs font-semibold uppercase tracking-[0.06em] text-muted-foreground">
                      operation id
                    </dt>
                    <dd className="m-0 mt-1 break-all font-mono text-xs text-foreground">
                      {data.operation_id}
                    </dd>
                  </div>
                </dl>
                <div className="grid gap-5 lg:grid-cols-2">
                  <section aria-labelledby="request-heading">
                    <h2 id="request-heading" className="mb-2 text-sm font-semibold text-foreground">
                      Exact request metadata
                    </h2>
                    <dl className="m-0 space-y-2.5 text-sm">
                      {Object.entries(data.request_summary).map(([key, value]) => (
                        <div key={key} className="rounded-md border border-border bg-muted/30 p-2.5">
                          <dt className="text-xs font-semibold uppercase tracking-[0.06em] text-muted-foreground">
                            {key}
                          </dt>
                          <dd className="m-0 mt-1 break-all font-mono text-xs text-foreground">
                            {renderValue(value)}
                          </dd>
                        </div>
                      ))}
                    </dl>
                  </section>

                  <section aria-labelledby="exact-result-heading">
                    <h2 id="exact-result-heading" className="mb-2 text-sm font-semibold text-foreground">
                      Exact result references
                    </h2>
                    {data.result ? (
                      <dl className="m-0 space-y-2.5 text-sm">
                        {Object.entries(data.result).map(([key, value]) => (
                          <div key={key} className="rounded-md border border-border bg-muted/30 p-2.5">
                            <dt className="text-xs font-semibold uppercase tracking-[0.06em] text-muted-foreground">
                              {key}
                            </dt>
                            <dd className="m-0 mt-1 break-all font-mono text-xs text-foreground">
                              {renderValue(value)}
                            </dd>
                          </div>
                        ))}
                      </dl>
                    ) : (
                      <p className="text-sm text-muted-foreground">
                        No terminal result reference is available yet.
                      </p>
                    )}
                  </section>
                </div>
              </AccordionContent>
            </AccordionItem>
          </Accordion>
        </CardContent>
      </Card>
    </section>
  )
}
