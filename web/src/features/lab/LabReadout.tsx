import { cn } from '@/lib/utils'
import { readoutSentence, type Readout } from './labReadout'

/**
 * Values under the crosshair. Pointer users see the hovered bar. Without a hovered
 * bar the strip shows the latest bar. Screen readers get one stable sentence about
 * the latest bar, so hover movement never floods a live region.
 */
export function LabReadout({
  title,
  current,
  latest,
}: {
  title: string
  current: Readout | null
  latest: Readout | null
}) {
  if (!current || !latest) return null
  return (
    <div className="mt-1 mb-3">
      <p className="sr-only">{readoutSentence(title, latest)}</p>
      <div
        className="lab-readout-strip flex flex-wrap items-start gap-x-6 gap-y-2.5 rounded-lg border border-border bg-muted/40 px-3 py-2.5"
        aria-hidden="true"
        data-latest={current.latest}
      >
        <p className="m-0 flex min-w-40 flex-col gap-0.5">
          <span
            className={cn(
              'text-[11px] font-medium',
              current.latest ? 'text-muted-foreground' : 'text-primary',
            )}
          >
            {current.latest ? 'Latest bar' : 'Hovered bar'}
          </span>
          <time className="font-mono text-xs text-foreground tabular-nums">{current.time}</time>
        </p>
        <dl className="m-0 grid flex-1 grid-cols-2 gap-x-5 gap-y-2 sm:flex sm:flex-wrap">
          {current.rows.map((row) => {
            const unavailable = row.value === 'Unavailable'
            return (
              <div key={row.key} className="flex min-w-24 flex-col gap-0.5">
                <dt className="flex items-center gap-1.5 text-[11px] whitespace-nowrap text-muted-foreground">
                  {row.swatch && (
                    <i
                      className={cn(
                        'w-3.5 flex-none border-t-2',
                        row.swatch.dashed ? 'border-dashed' : 'border-solid',
                      )}
                      style={{ color: `var(${row.swatch.token})` }}
                    />
                  )}
                  {row.label}
                </dt>
                <dd
                  className={cn(
                    'm-0 whitespace-nowrap',
                    unavailable
                      ? 'text-xs text-muted-foreground'
                      : 'font-mono text-sm font-medium text-foreground tabular-nums',
                  )}
                >
                  {row.value}
                </dd>
              </div>
            )
          })}
        </dl>
      </div>
    </div>
  )
}
