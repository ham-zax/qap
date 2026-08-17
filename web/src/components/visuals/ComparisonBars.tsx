import { ExactValue } from '../analytics/ExactValue'
import { formatRelativePercent } from '../../lib/format'

export interface ComparisonBarItem {
  label: string
  value: string
}

interface ComparisonBarsProps {
  items: ComparisonBarItem[]
}

export function ComparisonBars({ items }: ComparisonBarsProps) {
  const finiteMagnitudes = items
    .map((item) => Math.abs(Number(item.value)))
    .filter((value) => Number.isFinite(value))
  const maxMagnitude = Math.max(...finiteMagnitudes, 0)

  return (
    <div className="space-y-5">
      {items.map((item) => {
        const numeric = Number(item.value)
        const negative = Number.isFinite(numeric) && numeric < 0
        const magnitude = Number.isFinite(numeric) ? Math.abs(numeric) : 0
        const width = maxMagnitude === 0 ? 0 : Math.min(50, (magnitude / maxMagnitude) * 50)
        const formatted = formatRelativePercent(item.value)

        return (
          <div key={item.label} className="min-w-0">
            <div className="mb-2 flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
              <span className="text-sm font-medium text-secondary">{item.label}</span>
              <span
                className="text-base font-semibold tabular-nums text-foreground"
                data-exact={formatted.exact}
              >
                {formatted.display}
              </span>
            </div>
            <div
              className="relative h-2 overflow-hidden rounded-full bg-subtle"
              aria-hidden="true"
            >
              <span className="absolute inset-y-0 left-1/2 w-px bg-border-strong" />
              <span
                className={`absolute inset-y-0 rounded-full ${negative ? 'bg-negative' : 'bg-positive'}`}
                style={
                  negative
                    ? { right: '50%', width: `${width}%` }
                    : { left: '50%', width: `${width}%` }
                }
              />
            </div>
            <ExactValue value={item.value} />
          </div>
        )
      })}
    </div>
  )
}
