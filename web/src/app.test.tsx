import { render, screen, within } from '@testing-library/react'
import { createMemoryHistory } from '@tanstack/react-router'
import { describe, expect, it, vi } from 'vitest'

import { App, createQapApp } from './app'

describe('QAP route errors', () => {
  it('opens the Lab as the local workspace entry point', async () => {
    const app = createQapApp({
      fetchImpl: vi.fn<typeof fetch>().mockImplementation(async () => new Response(JSON.stringify({
        schema_version: 'qap.api.workspace_status.v1', workspace_mode: 'local_market',
        workspace_root: '/test', market_data_status: 'catalog_detected',
        market_data_catalog_updated_at: null, product_maintenance_status: 'idle',
        current_evidence_collector_status: 'not_running',
      }), { headers: { 'Content-Type': 'application/json' } })),
      history: createMemoryHistory({ initialEntries: ['/'] }),
    })
    await app.router.load()
    expect(app.router.state.location.pathname).toBe('/lab')
  })

  it('renders an unknown route inside exactly one application shell', async () => {
    const workspace = {
      schema_version: 'qap.api.workspace_status.v1', workspace_mode: 'local_market',
      workspace_root: '/test', market_data_status: 'catalog_detected',
      market_data_catalog_updated_at: null, product_maintenance_status: 'idle',
      current_evidence_collector_status: 'not_running',
    }
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
            code: 'paper_operation_not_found',
            message: 'Paper operation was not found.',
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
        initialEntries: ['/paper-operations/missing-operation'],
      }),
    })

    await app.router.load()
    render(<App {...app} />)

    expect(
      await screen.findByRole('heading', { name: 'Evidence could not be loaded' }),
    ).toBeVisible()
    expect(screen.getByRole('link', { name: 'QAP' })).toHaveAttribute('href', '/')
    const nav = screen.getByRole('navigation', { name: 'Primary navigation' })
    expect(within(nav).getByRole('link', { name: 'Research' })).toHaveAttribute('href', '/research')
    expect(within(nav).getByRole('link', { name: 'Portfolios' })).toHaveAttribute('href', '/baskets')
    expect(within(nav).getByRole('link', { name: 'History' })).toHaveAttribute('href', '/experiments')
    expect(screen.getByRole('button', { name: 'Retry' })).toBeVisible()
    expect(screen.getByText('paper_operation_not_found')).toBeVisible()
  })
})
