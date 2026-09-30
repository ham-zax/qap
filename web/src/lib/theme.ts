import { useSyncExternalStore } from 'react'

export type ThemePreference = 'system' | 'light' | 'dark'
export type ResolvedTheme = 'light' | 'dark'

const STORAGE_KEY = 'qap.theme'
const listeners = new Set<() => void>()

function readStored(): ThemePreference {
  try {
    const value = window.localStorage.getItem(STORAGE_KEY)
    return value === 'light' || value === 'dark' ? value : 'system'
  } catch {
    return 'system'
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
  const root = document.documentElement
  if (preference === 'system') root.removeAttribute('data-theme')
  else root.setAttribute('data-theme', preference)
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
    window.matchMedia('(prefers-color-scheme: light)').addEventListener('change', notify)
  }
}

function subscribe(listener: () => void) {
  listeners.add(listener)
  return () => {
    listeners.delete(listener)
  }
}

function snapshot(): string {
  const preference = typeof window === 'undefined' ? 'system' : readStored()
  const resolved = preference === 'system' ? systemTheme() : preference
  return `${preference}:${resolved}`
}

export function useTheme(): { preference: ThemePreference; resolved: ResolvedTheme } {
  const value = useSyncExternalStore(subscribe, snapshot, () => 'system:dark')
  const [preference, resolved] = value.split(':') as [ThemePreference, ResolvedTheme]
  return { preference, resolved }
}
