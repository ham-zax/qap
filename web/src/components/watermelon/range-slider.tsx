import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

export function RangeSliderField({
  label,
  valueText,
  badge,
  value,
  min,
  max,
  step,
  onChange,
  className,
}: {
  label: string
  valueText: string
  badge?: string
  value: number
  min: number
  max: number
  step: number
  onChange: (value: number) => void
  className?: string
}) {
  const clamped = Math.min(max, Math.max(min, value))
  const pct = max > min ? ((clamped - min) / (max - min)) * 100 : 0

  return (
    <label className={cn('flex flex-col gap-1.5 text-xs text-muted-foreground', className)}>
      <span className="flex items-baseline justify-between gap-2">
        <span className="font-medium text-foreground/90">{label}</span>
        <span className="inline-flex items-center gap-1.5 font-mono text-xs text-foreground tabular-nums">
          <strong className="font-semibold">{valueText}</strong>
          {badge ? (
            <Badge variant="secondary" className="rounded px-1.5 py-0 text-[10.5px] font-medium">
              {badge}
            </Badge>
          ) : null}
        </span>
      </span>
      <span className="relative flex h-6 w-full items-center">
        <span
          aria-hidden="true"
          className="pointer-events-none relative h-1.5 w-full overflow-hidden rounded-full bg-border-strong/65"
        >
          <span
            className="absolute inset-y-0 left-0 rounded-full bg-primary transition-[width] duration-75"
            style={{ width: `${pct}%` }}
          />
        </span>
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={clamped}
          onChange={(event) => {
            const parsed = Number(event.target.value)
            if (Number.isFinite(parsed)) onChange(parsed)
          }}
          className="peer absolute inset-0 z-10 h-6 w-full cursor-pointer opacity-0"
        />
        <span
          aria-hidden="true"
          className="pointer-events-none absolute top-1/2 size-4 -translate-y-1/2 rounded-full border-2 border-primary bg-background shadow-sm transition-transform peer-hover:scale-110 peer-focus-visible:ring-2 peer-focus-visible:ring-ring peer-focus-visible:ring-offset-2 peer-focus-visible:ring-offset-card"
          style={{ left: `calc(${pct}% - ${(pct / 100) * 16}px)` }}
        />
      </span>
    </label>
  )
}
