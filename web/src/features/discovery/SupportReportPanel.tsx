import type { SupportReportV1 } from '../../api/types'
import { Badge, type BadgeTone } from '../../components/ui/Badge'

function label(value: string): string {
  return value.replaceAll('_', ' ')
}

function toneForAxis(axis: string, value: string): BadgeTone {
  if (axis === 'structure') return value === 'valid' ? 'positive' : 'negative'
  if (axis === 'capability') {
    if (value === 'executable') return 'positive'
    if (value === 'diagnostic_only') return 'info'
    if (value === 'unimplemented') return 'warning'
    return 'negative'
  }
  if (axis === 'authority') return value === 'allowed' ? 'positive' : 'negative'
  if (axis === 'readiness') return value === 'ready' ? 'positive' : 'warning'
  if (axis === 'fidelity') {
    if (value === 'native' || value === 'faithful_replication') return 'positive'
    if (value === 'adaptation_required') return 'warning'
    return 'neutral'
  }
  return 'neutral'
}

export function SupportReportPanel({ report }: { report: SupportReportV1 }) {
  const axes = [
    ['structure', report.structure],
    ['capability', report.capability],
    ['authority', report.authority],
    ['readiness', report.readiness],
    ['fidelity', report.fidelity],
  ] as const

  return (
    <section className="rounded-lg border border-border bg-panel p-5" aria-labelledby="support-report-heading">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="m-0 text-xs font-semibold uppercase tracking-[0.08em] text-muted">
            Backend support check
          </p>
          <h3 id="support-report-heading" className="mt-2 mb-0 text-lg font-semibold text-foreground">
            Recipe support
          </h3>
        </div>
        <Badge tone={report.runnable ? 'positive' : 'warning'}>
          {report.runnable ? 'Runnable' : 'Not runnable'}
        </Badge>
      </div>

      <dl className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
        {axes.map(([axis, value]) => (
          <div key={axis} className="rounded-md border border-border bg-canvas/35 p-3">
            <dt className="text-xs font-semibold uppercase tracking-[0.06em] text-muted">
              {axis}
            </dt>
            <dd className="mt-2 mb-0">
              <Badge tone={toneForAxis(axis, value)}>{label(value)}</Badge>
            </dd>
          </div>
        ))}
      </dl>

      {report.reasons.length ? (
        <div className="mt-5">
          <h4 className="m-0 text-sm font-semibold text-foreground">Why</h4>
          <div className="mt-3 space-y-2">
            {report.reasons.map((reason, index) => (
              <div
                key={`${reason.code}-${reason.component}-${index}`}
                className="rounded-md border border-border bg-canvas/30 p-3 text-sm"
              >
                <div className="flex flex-wrap gap-2">
                  <Badge tone="neutral">{label(reason.category)}</Badge>
                  <strong className="text-foreground">{label(reason.code)}</strong>
                </div>
                <p className="mt-2 mb-0 leading-6 text-secondary">{reason.detail}</p>
                <p className="mt-1 mb-0 text-xs text-muted">
                  Component: {reason.component}
                  {reason.nearest_capability
                    ? ` · nearest current capability: ${label(reason.nearest_capability)}`
                    : ''}
                </p>
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {report.suggestions.length ? (
        <div className="mt-5">
          <h4 className="m-0 text-sm font-semibold text-foreground">Possible next actions</h4>
          <ul className="mt-2 mb-0 space-y-2 pl-5 text-sm leading-6 text-secondary">
            {report.suggestions.map((suggestion) => (
              <li key={suggestion}>{suggestion}</li>
            ))}
          </ul>
        </div>
      ) : null}
    </section>
  )
}
