import { setThemePreference, useTheme, type ThemePreference } from '../../lib/theme'

const OPTIONS: { value: ThemePreference; label: string }[] = [
  { value: 'system', label: 'Auto' },
  { value: 'light', label: 'Light' },
  { value: 'dark', label: 'Dark' },
]

export function ThemeToggle() {
  const { preference } = useTheme()
  return (
    <div role="group" aria-label="Color theme" className="inline-flex rounded-md border border-border bg-subtle p-0.5">
      {OPTIONS.map((option) => {
        const active = preference === option.value
        return (
          <button
            key={option.value}
            type="button"
            aria-pressed={active}
            onClick={() => setThemePreference(option.value)}
            className={`!min-h-8 rounded-sm !border-0 px-2.5 !py-1 text-xs font-semibold ${
              active ? '!bg-panel !text-foreground shadow-card' : '!bg-transparent text-muted hover:text-foreground'
            }`}
          >
            {option.label}
          </button>
        )
      })}
    </div>
  )
}
