import { formatPercent } from '../../lib/format'

export interface CompositionItem {
  asset: string
  weight: string
}

interface CompositionBarsProps {
  label: string
  items: CompositionItem[]
}

const SERIES_COLORS = [
  'var(--chart-series-1)',
  'var(--chart-series-2)',
  'var(--chart-series-3)',
  'var(--chart-series-4)',
  'var(--chart-series-5)',
]

export function CompositionBars({ label, items }: CompositionBarsProps) {
  return (
    <div className="min-w-0" role="group" aria-label={label}>
      <div
        className="flex h-3 w-full overflow-hidden rounded-full bg-subtle"
        aria-hidden="true"
      >
        {items.map((item, index) => {
          const numeric = Number(item.weight)
          const width = Number.isFinite(numeric) ? Math.max(0, numeric * 100) : 0
          return (
            <span
              key={item.asset}
              style={{
                width: `${width}%`,
                backgroundColor: SERIES_COLORS[index % SERIES_COLORS.length],
              }}
            />
          )
        })}
      </div>
      <ul className="mt-3 grid list-none gap-2 p-0 text-sm sm:grid-cols-2">
        {items.map((item, index) => {
          const formatted = formatPercent(item.weight)
          return (
            <li key={item.asset} className="flex min-w-0 items-center justify-between gap-3">
              <span className="flex min-w-0 items-center gap-2 text-secondary">
                <span
                  className="h-2.5 w-2.5 shrink-0 rounded-sm"
                  aria-hidden="true"
                  style={{ backgroundColor: SERIES_COLORS[index % SERIES_COLORS.length] }}
                />
                <span className="truncate">{item.asset}</span>
              </span>
              <span className="shrink-0 font-medium tabular-nums text-foreground" data-exact={formatted.exact}>
                {formatted.display}
              </span>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
