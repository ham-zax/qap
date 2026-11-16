import { Moon, Sun } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { setThemePreference, useTheme } from '@/lib/theme'

export function ThemeToggle() {
  const { resolved } = useTheme()
  const dark = resolved === 'dark'

  return (
    <Button
      type="button"
      variant="outline"
      size="icon-sm"
      onClick={() => setThemePreference(dark ? 'light' : 'dark')}
      aria-label={dark ? 'Switch to light theme' : 'Switch to dark theme'}
      title={dark ? 'Light theme' : 'Dark theme'}
      className="h-8 w-8 border-border bg-transparent text-muted-foreground hover:bg-muted hover:text-foreground"
    >
      {dark ? <Sun className="size-4" aria-hidden="true" /> : <Moon className="size-4" aria-hidden="true" />}
    </Button>
  )
}
