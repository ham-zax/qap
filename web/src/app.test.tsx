import { render, screen } from '@testing-library/react'
import { createMemoryHistory } from '@tanstack/react-router'
import { describe, expect, it, vi } from 'vitest'

import { App, createQapApp } from './app'

describe('QAP route errors', () => {
  it('renders an unknown route inside exactly one application shell', async () => {
    const app = createQapApp({
      fetchImpl: vi.fn<typeof fetch>(),
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
    expect(screen.getByRole('link', { name: 'Research runs' })).toHaveAttribute(
      'href',
      '/experiments',
    )
    expect(
      screen.getByRole('link', { name: 'Paper operations' }),
    ).toHaveAttribute('href', '/paper-operations')
    expect(screen.getByRole('button', { name: 'Retry' })).toBeVisible()
    expect(screen.getByText('paper_operation_not_found')).toBeVisible()
  })
})
