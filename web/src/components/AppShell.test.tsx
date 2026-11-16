import { fireEvent, render, screen, within } from '@testing-library/react'
import { beforeEach, expect, it, vi } from 'vitest'
import { AppShell } from './AppShell'
import { useLabViewMode } from '../features/lab/labStorage'

vi.mock('@tanstack/react-router', () => ({
  useRouterState: () => '/lab',
  Link: ({ children, to }: { children: React.ReactNode; to: string }) => <a href={to}>{children}</a>,
}))

function ModeReadout() {
  const [mode] = useLabViewMode()
  return <output aria-label="Dashboard mode">{mode}</output>
}

beforeEach(() => localStorage.clear())

it('keeps the header switch and dashboard mode synchronized', () => {
  render(<AppShell><ModeReadout /></AppShell>)
  const header = within(screen.getByRole('banner'))
  fireEvent.click(header.getByRole('button', { name: 'Pro' }))
  expect(header.getByRole('button', { name: 'Pro' })).toHaveAttribute('aria-pressed', 'true')
  expect(screen.getByLabelText('Dashboard mode')).toHaveTextContent('advanced')
  fireEvent.click(header.getByRole('button', { name: 'Simple' }))
  expect(screen.getByLabelText('Dashboard mode')).toHaveTextContent('simple')
  expect(screen.getAllByRole('group', { name: 'View mode' })).toHaveLength(1)
})
