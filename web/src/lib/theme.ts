import { useSyncExternalStore } from 'react'

export type ThemePreference = 'system' | 'light' | 'dark'
export type ResolvedTheme = 'light' | 'dark'

const STORAGE_KEY = 'qap.theme'
const listeners = new Set<() => void>()

/**
 * A trading terminal opens dark, like Binance Spot. Only an explicit stored
 * choice overrides that, so a first visit never depends on the OS setting.
 */
function readStored(): ThemePreference {
  try {
    const value = window.localStorage.getItem(STORAGE_KEY)
    return value === 'light' || value === 'dark' ? value : 'dark'
  } catch {
    return 'dark'
  }
}

function systemTheme(): ResolvedTheme {
  if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') return 'dark'
  return window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark'
}

function notify() {
  for (const listener of listeners) listener()
}

export function applyThemePreference(preference: ThemePreference) {
  const resolved = preference === 'system' ? systemTheme() : preference
  document.documentElement.setAttribute('data-theme', resolved)
}

export function setThemePreference(preference: ThemePreference) {
  try {
    if (preference === 'system') window.localStorage.removeItem(STORAGE_KEY)
    else window.localStorage.setItem(STORAGE_KEY, preference)
  } catch {
    // Storage can be unavailable (private mode); the choice still applies to this page.
  }
  applyThemePreference(preference)
  notify()
}

export function initializeTheme() {
  applyThemePreference(readStored())
  if (typeof window.matchMedia === 'function') {
    window.matchMedia('(prefers-color-scheme: light)').addEventListener('change', () => {
      applyThemePreference(readStored())
      notify()
    })
  }
}

function subscribe(listener: () => void) {
  listeners.add(listener)
  return () => {
    listeners.delete(listener)
  }
}

function snapshot(): string {
  const preference = typeof window === 'undefined' ? 'dark' : readStored()
  const resolved = preference === 'system' ? systemTheme() : preference
  return `${preference}:${resolved}`
}

export function useTheme(): { preference: ThemePreference; resolved: ResolvedTheme } {
  const value = useSyncExternalStore(subscribe, snapshot, () => 'dark:dark')
  const [preference, resolved] = value.split(':') as [ThemePreference, ResolvedTheme]
  return { preference, resolved }
}
