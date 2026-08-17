import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { TimeSeriesChart } from './TimeSeriesChart'

describe('TimeSeriesChart accessibility shell', () => {
  it('does not emit duplicate-key errors when distinct series share a display name', () => {
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => undefined)

    render(
      <TimeSeriesChart
        title="Reduced anchor decomposition"
        description="Two semantically distinct reduced series can share an orientation label."
        series={[
          {
            name: 'BTC/USDT',
            unit: 'log anchor ratio',
            points: [{ timestamp: '2025-01-01T00:00:00Z', value: 1 }],
          },
          {
            name: 'BTC/USDT',
            unit: 'pair log ratio',
            points: [{ timestamp: '2025-01-01T00:00:00Z', value: 1 }],
          },
        ]}
      />,
    )

    expect(
      consoleError.mock.calls.some((call) =>
        call.some(
          (value) => typeof value === 'string' && value.includes('same key'),
        ),
      ),
    ).toBe(false)
    consoleError.mockRestore()
  })

  it('does not hide the container that receives the focusable attribution link', () => {
    const { container } = render(
      <TimeSeriesChart
        title="Evidence curve"
        description="A backend-produced series."
        series={[
          {
            name: 'QAP vs HODL',
            unit: 'relative wealth',
            points: [
              { timestamp: '2025-01-01T00:00:00Z', value: 0 },
              { timestamp: '2025-01-01T01:00:00Z', value: -0.01 },
            ],
          },
        ]}
      />,
    )

    expect(screen.getByRole('figure', { name: 'Evidence curve' })).toBeInTheDocument()
    const chartCanvas = container.querySelector('.chart-canvas')
    expect(chartCanvas).not.toHaveAttribute('aria-hidden')
    expect(chartCanvas).toHaveStyle({ height: '320px' })
  })
})
