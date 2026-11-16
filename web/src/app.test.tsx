import { fireEvent, render, screen, within } from '@testing-library/react'
import { createMemoryHistory } from '@tanstack/react-router'
import { describe, expect, it, vi } from 'vitest'

import { App, createQapApp } from './app'

const workspace = {
  schema_version: 'qap.api.workspace_status.v1', workspace_mode: 'local_market',
  workspace_root: '/test', market_data_status: 'catalog_detected',
  market_data_catalog_updated_at: null, product_maintenance_status: 'idle',
  current_evidence_collector_status: 'not_running',
}

describe('QAP route errors', () => {
  it('opens the Lab as the local workspace entry point', async () => {
    const app = createQapApp({
      fetchImpl: vi.fn<typeof fetch>().mockImplementation(async () =>
        new Response(JSON.stringify(workspace), {
          headers: { 'Content-Type': 'application/json' },
        }),
      ),
      history: createMemoryHistory({ initialEntries: ['/'] }),
    })
    await app.router.load()
    expect(app.router.state.location.pathname).toBe('/lab')
  })

  it('renders an unknown route inside exactly one application shell', async () => {
    const app = createQapApp({
      fetchImpl: vi.fn<typeof fetch>().mockImplementation(async () =>
        new Response(JSON.stringify(workspace), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }),
      ),
      history: createMemoryHistory({ initialEntries: ['/missing-route'] }),
    })

    await app.router.load()
    render(<App {...app} />)

    expect(await screen.findByRole('heading', { name: 'Page not found' })).toBeVisible()
    expect(document.querySelectorAll('main')).toHaveLength(1)
    expect(
      screen.getAllByRole('navigation', { name: 'Primary navigation' }),
    ).toHaveLength(1)
  })

  it('keeps primary navigation available when evidence cannot be loaded', async () => {
    const fetchImpl = vi.fn<typeof fetch>().mockImplementation(async () =>
      new Response(
        JSON.stringify({
          error: {
            code: 'operation_not_found',
            message: 'Operation was not found.',
            context: { operation_id: 'missing-operation' },
          },
        }),
        {
          status: 404,
          headers: { 'Content-Type': 'application/json' },
        },
      ),
    )
    const app = createQapApp({
      fetchImpl,
      history: createMemoryHistory({
        initialEntries: ['/operations/missing-operation'],
      }),
    })

    await app.router.load()
    render(<App {...app} />)

    expect(
      await screen.findByRole('heading', { name: 'Evidence could not be loaded' }),
    ).toBeVisible()
    expect(screen.getByRole('link', { name: 'QAP' })).toHaveAttribute('href', '/')
    const nav = screen.getByRole('navigation', { name: 'Primary navigation' })
    expect(within(nav).getByRole('link', { name: 'Lab' })).toHaveAttribute('href', '/lab')
    expect(within(nav).getByRole('link', { name: 'Activity' })).toHaveAttribute(
      'href',
      '/operations',
    )
    expect(screen.getByRole('button', { name: 'Retry' })).toBeVisible()
    expect(screen.getByText('operation_not_found')).toBeVisible()
  })

  it('keeps the header to one slim row with a single theme button', async () => {
    const app = createQapApp({
      fetchImpl: vi.fn<typeof fetch>().mockImplementation(async () =>
        new Response(JSON.stringify(workspace), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }),
      ),
      history: createMemoryHistory({ initialEntries: ['/missing-route'] }),
    })

    await app.router.load()
    render(<App {...app} />)

    expect(await screen.findByRole('heading', { name: 'Page not found' })).toBeVisible()
    expect(screen.queryByText('Local workspace')).not.toBeInTheDocument()
    expect(screen.queryByText('Read-only examples')).not.toBeInTheDocument()
    expect(screen.queryByRole('group', { name: 'Color theme' })).not.toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Background collection is stopped' })).toHaveAttribute(
      'href',
      '/operations',
    )

    const toggle = screen.getByRole('button', { name: 'Switch to light theme' })
    expect(toggle).toHaveAttribute('title', 'Light theme')
    fireEvent.click(toggle)
    expect(await screen.findByRole('button', { name: 'Switch to dark theme' })).toBeVisible()
    expect(document.documentElement.dataset.theme).toBe('light')
    localStorage.clear()
  })
})
