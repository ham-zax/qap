interface LineageItem {
  label: string
  value: string
  href?: string
}

interface LineageTrailProps {
  items: LineageItem[]
}

function shortId(value: string) {
  return value.length <= 20 ? value : `${value.slice(0, 10)}…${value.slice(-6)}`
}

export function LineageTrail({ items }: LineageTrailProps) {
  return (
    <nav aria-label="Research lineage" className="rounded-lg border border-border bg-panel p-4">
      <ol className="m-0 flex flex-wrap items-center gap-x-2 gap-y-3 p-0 text-sm">
        {items.map((item) => (
          <li key={`${item.label}-${item.value}`} className="flex items-center gap-2">
            <span className="text-xs font-semibold uppercase tracking-[0.06em] text-muted">{item.label}</span>
            {item.href ? (
              <a className="font-semibold text-accent" href={item.href} title={item.value}>
                {shortId(item.value)}
              </a>
            ) : (
              <span className="font-medium text-foreground" title={item.value}>{shortId(item.value)}</span>
            )}
          </li>
        ))}
      </ol>
    </nav>
  )
}
